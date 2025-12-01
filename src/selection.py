from config import GITHUB_TOKEN
import random
import re
import time
from datetime import datetime, timezone

import pandas as pd
import requests

from langdetect import LangDetectException, detect_langs


class GitHubScraper:
    def __init__(self, token):
        self.token = token
        self.endpoint = "https://api.github.com/graphql"
        self.headers = {"Authorization": f"Bearer {token}"}
        self.rate_limit_remaining = 5000
        self.rate_limit_reset = None

    def check_rate_limit(self):
        query = """
        query {
          rateLimit {
            remaining
            resetAt
          }
        }
        """
        r = requests.post(self.endpoint, json={'query': query}, headers=self.headers)
        data = r.json()
        self.rate_limit_remaining = data['data']['rateLimit']['remaining']
        self.rate_limit_reset = data['data']['rateLimit']['resetAt']
        reset = datetime.astimezone(datetime.fromisoformat(self.rate_limit_reset.replace("Z", "+00:00")))
        print(f"Rate limit: {self.rate_limit_remaining} remaining, resets at {reset}")

        now = datetime.now().astimezone()
        print(f"Resets in {reset - now}")

    def exponential_backoff(self, attempt):
        wait = min(300, (2 ** attempt) + random.uniform(0, 1))
        print(f"Backing off for {wait:.2f} seconds...")
        time.sleep(wait)

    def extract_prose_only(self, text):
        if not text:
            return ""
        text = re.sub(r'```[\s\S]*?```', '', text)
        text = re.sub(r'`[^`]+`', '', text)
        text = re.sub(r'https?://\S+', '', text)
        text = re.sub(r'!\[.*?\]\(.*?\)', '', text)
        text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
        text = re.sub(r'<[^>]+>', '', text)
        text = re.sub(r'<\?[\s\S]*?\?>', '', text)
        text = re.sub(r'[\w\-_]+\.(js|py|java|ts|cpp|h|md|txt|json|xml|yaml|yml)', '', text, flags=re.IGNORECASE)
        text = re.sub(r'\b[a-z]+[A-Z][a-zA-Z]*\b', ' ', text)
        text = re.sub(r'\b[a-z]+_[a-z_]+\b', ' ', text)
        return text.strip()

    def is_english(self, text, min_prose_length=150, confidence_threshold=0.9):
        if not text or not text.strip():
            return False
        prose = self.extract_prose_only(text)
        if len(prose) < min_prose_length:
            print(f"    Rejected: Insufficient prose ({len(prose)} chars)")
            return False
        try:
            detected = detect_langs(prose)
            en_prob = 0.0
            lang = detected[0].lang
            for lp in detected:
                if lp.lang == "en":
                    en_prob = lp.prob
            if lang != "en" or en_prob < confidence_threshold:
                print(f"    Rejected: Language={lang}, EN confidence={en_prob:.2f}")
                return False
            return True
        except LangDetectException:
            print("    Rejected: Language detection failed")
            return False

    def fetch_repositories(self, language, stars_range, cursor=None, max_retries=5):
        query = """
        query($query: String!, $cursor: String) {
          search(query: $query, type: REPOSITORY, first: 10, after: $cursor) {
            pageInfo {
              hasNextPage
              endCursor
            }
            nodes {
              ... on Repository {
                name
                owner { login }
                stargazerCount
                forkCount
                isFork
                createdAt
                primaryLanguage { name }
                defaultBranchRef {
                  target {
                    ... on Commit {
                      history { totalCount }
                    }
                  }
                }
                object(expression: "HEAD:README.md") {
                  ... on Blob { text }
                }
                mentionableUsers(first: 1) { totalCount }
              }
            }
          }
          rateLimit {
            remaining
            resetAt
          }
        }
        """

        search_query = f"language:{language} stars:{stars_range} fork:false"
        variables = {"query": search_query, "cursor": cursor}

        for attempt in range(max_retries):
            try:
                r = requests.post(
                    self.endpoint,
                    json={'query': query, 'variables': variables},
                    headers=self.headers,
                    timeout=30
                )
                if r.status_code == 200:
                    data = r.json()
                    if 'data' in data and 'rateLimit' in data['data']:
                        rl = data['data']['rateLimit']
                        self.rate_limit_remaining = rl['remaining']
                        self.rate_limit_reset = rl['resetAt']
                    if 'errors' in data:
                        print(f"GraphQL errors: {data['errors'][0]}")
                        if attempt < max_retries - 1:
                            self.exponential_backoff(attempt)
                            continue
                        return None
                    return data['data']['search']
                if r.status_code in (403, 429):
                    print(f"Rate limited. Status {r.status_code}")
                    if attempt < max_retries - 1:
                        self.exponential_backoff(attempt)
                        continue
                    return None
                print(f"HTTP Error {r.status_code}: {r.text}")
                if attempt < max_retries - 1:
                    self.exponential_backoff(attempt)
                    continue
                return None
            except requests.exceptions.RequestException as e:
                print(f"Request exception: {e}")
                if attempt < max_retries - 1:
                    self.exponential_backoff(attempt)
                    continue
                return None
        return None

    def parse_repo_data(self, node):
        readme = node.get('object', {}).get('text', '') if node.get('object') else ''
        commits = node.get('defaultBranchRef', {}) \
                      .get('target', {}) \
                      .get('history', {}) \
                      .get('totalCount', 0)
        contributors = node.get('mentionableUsers', {}).get('totalCount', 0)
        return {
            'name': node.get('name', ''),
            'owner': node['owner'].get('login', ''),
            'stars': node.get('stargazerCount', 0),
            'forks': node.get('forkCount', 0),
            'contributors': contributors,
            'commits': commits,
            'language': node.get('primaryLanguage', {}).get('name', ''),
            'created_at': node.get('createdAt', ''),
            'is_fork': node.get('isFork', False),
            'readme': readme
        }

    def is_valid_repo(self, r):
        if r['is_fork']:
            return False
        if r['contributors'] <= 1:
            return False
        if not r['readme'].strip():
            return False
        if not self.is_english(r['readme']):
            return False
        return True

    def scrape_repos(self, target_count=10000, repos_per_language=1000):
        languages = [
            'JavaScript', 'Python', 'Java', 'TypeScript', 'C#',
            'C++', 'PHP', 'Shell', 'C', 'Ruby'
        ]
        star_ranges = [
            '3500..5000',
            '3000..3500',
            '2500..3000',
            '2000..2500',
            '1500..2000',
            '1000..1500',
            '500..1000',
            '100..500',
            '50..100',
            '5..50'
        ]

        all_repos = []
        total = 0

        print(f"Starting scrape for {target_count} repositories...\n")
        self.check_rate_limit()
        random.shuffle(languages)

        for language in languages:
            if total >= target_count:
                break

            print(f"\n--- Scraping {language} ---")
            language_repos = []

            ranges = star_ranges.copy()
            random.shuffle(ranges)

            for star_range in ranges:
                if total >= target_count or len(language_repos) >= repos_per_language:
                    break

                print(f"Fetching {language} repos with {star_range} stars...")
                cursor = None
                pages = 0

                while pages < 10 and len(language_repos) < repos_per_language and total < target_count:
                    if self.rate_limit_remaining < 10:
                        print("Rate limit low, waiting...")
                        self.check_rate_limit()
                        exit()

                    result = self.fetch_repositories(language, star_range, cursor)
                    if not result or not result.get('nodes'):
                        break

                    for node in result['nodes']:
                        if not node:
                            continue
                        data = self.parse_repo_data(node)
                        if self.is_valid_repo(data):
                            language_repos.append(data)
                            all_repos.append(data)
                            total += 1
                            if total >= target_count:
                                print("Reached global target.")
                                return all_repos
                            if len(language_repos) >= repos_per_language:
                                break

                    print(f" Valid so far in {language}: {len(language_repos)}/{repos_per_language}")

                    info = result.get('pageInfo', {})
                    if not info.get('hasNextPage'):
                        break

                    cursor = info.get('endCursor')
                    pages += 1

                # end while
            # end star range loop

            print(f"Collected so far: {total}/{target_count}")

            if total and total % 1000 == 0:
                self.save_to_csv(all_repos, f'github_repos_intermediate_{total}.csv')

        random.shuffle(all_repos)
        return all_repos[:target_count]

    def save_to_csv(self, repos, filename='raw_repos.csv'):
        df = pd.DataFrame(repos)
        if 'is_fork' in df.columns:
            df = df.drop(columns=['is_fork'])
        df.to_csv(filename, index=False, encoding='utf-8')
        print(f"\nSaved {len(repos)} repositories to {filename}")
        return df

    def test_language_detection(self, sample_size=50):
        print("Testing language detection...")
        repos = self.scrape_repos(target_count=sample_size, repos_per_language=5)
        for r in repos:
            print(f"\n{r['owner']}/{r['name']}")
            prose = self.extract_prose_only(r['readme'])
            print(f"Prose length: {len(prose)}")
            print(prose[:200])


if __name__ == "__main__":
    scraper = GitHubScraper(GITHUB_TOKEN)
    repos = scraper.scrape_repos(target_count=10000, repos_per_language=1000)
    df = scraper.save_to_csv(repos, 'raw_repos.csv')
    print(f"Total repositories: {len(df)}")
