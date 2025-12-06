import requests
import pandas as pd
import time
import random
import re
from datetime import datetime
from config import GITHUB_TOKEN
from langdetect import detect_langs, LangDetectException


class GitHubScraper:
    def __init__(self, token):
        self.token = token
        self.endpoint = "https://api.github.com/graphql"
        self.headers = {"Authorization": f"Bearer {token}"}
        self.rate_limit_remaining = 5000
        self.rate_limit_reset = None
        self.seen_repos = set()  # Track collected repos to avoid duplicates

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
        print(f"Rate limit: {self.rate_limit_remaining} remaining, resets at {self.rate_limit_reset}")

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
        
        # Check original text for CJK characters (Chinese/Japanese/Korean)
        cjk_pattern = re.compile(r'[\u4e00-\u9fff\u3040-\u309f\u30a0-\u30ff\uac00-\ud7af]+')
        cjk_chars = len(cjk_pattern.findall(text))
        if cjk_chars > 20:  # More than 20 CJK characters = likely not English
            print(f"    Rejected: Contains {cjk_chars} CJK characters")
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

    def get_contributor_count(self, owner, name, max_retries=3):
        """Fetch actual contributor count via REST API"""
        url = f"https://api.github.com/repos/{owner}/{name}/contributors"
        params = {"per_page": 1, "anon": "true"}
        
        for attempt in range(max_retries):
            try:
                r = requests.get(url, headers=self.headers, params=params, timeout=10)
                if r.status_code == 200:
                    # Check Link header for total count
                    link_header = r.headers.get('Link', '')
                    if 'rel="last"' in link_header:
                        # Extract page number from last page URL
                        match = re.search(r'page=(\d+)>; rel="last"', link_header)
                        if match:
                            return int(match.group(1))
                    # If no pagination, return array length
                    return len(r.json())
                elif r.status_code == 204:
                    return 0
                elif r.status_code in (403, 429):
                    if attempt < max_retries - 1:
                        time.sleep(2 ** attempt)
                        continue
                    return 0
                else:
                    return 0
            except Exception as e:
                if attempt < max_retries - 1:
                    time.sleep(1)
                    continue
                return 0
        return 0

    def fetch_repositories(self, language, stars_range, cursor=None, year_range=None, max_retries=5):
        query = """
        query($query: String!, $cursor: String) {
          search(query: $query, type: REPOSITORY, first: 15, after: $cursor) {
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
              }
            }
          }
          rateLimit {
            remaining
            resetAt
          }
        }
        """

        # Add random sorting using pushed date ranges for pseudo-randomization
        search_query = f"language:{language} stars:{stars_range} fork:false sort:updated"
        if year_range:
            search_query += f" created:{year_range}"
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
        owner = node['owner'].get('login', '')
        name = node.get('name', '')
        
        # Get actual contributor count via REST API
        contributors = self.get_contributor_count(owner, name)
        
        return {
            'name': name,
            'owner': owner,
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

    def scrape_repos(self, target_count=10000):
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
        
        # Add date ranges for better randomization
        year_ranges = [
            '2024-01-01..2025-12-31',
            '2023-01-01..2023-12-31',
            '2022-01-01..2022-12-31', 
            '2021-01-01..2021-12-31',
            '2020-01-01..2020-12-31',
            '2019-01-01..2019-12-31',
            '2018-01-01..2018-12-31',
            '2017-01-01..2017-12-31',
            '2016-01-01..2016-12-31',
            '2015-01-01..2015-12-31'
        ]

        all_repos = []
        print(f"Starting scrape for {target_count} repositories...\n")
        self.check_rate_limit()
        
        stuck_counter = 0
        last_count = 0

        while len(all_repos) < target_count:
            # Check if we're stuck (no progress in last iteration)
            if len(all_repos) == last_count:
                stuck_counter += 1
                if stuck_counter >= 3:
                    print(f"\n⚠️ Stuck at {len(all_repos)} repos for 3 iterations.")
                    print("Expanding search to lower star ranges...")
                    # Add more lenient star ranges
                    if '1..5' not in star_ranges:
                        star_ranges.extend(['1..5', '0..1'])
                    stuck_counter = 0
            else:
                stuck_counter = 0
            
            last_count = len(all_repos)
            
            # Shuffle for diversity
            random.shuffle(languages)
            random.shuffle(star_ranges)
            random.shuffle(year_ranges)

            for language in languages:
                if len(all_repos) >= target_count:
                    break

                for star_range in star_ranges:
                    if len(all_repos) >= target_count:
                        break
                    
                    # Randomly pick a year range for this query
                    year_range = random.choice(year_ranges)

                    print(f"\nFetching {language} repos with {star_range} stars, created {year_range}...")
                    print(f"Progress: {len(all_repos)}/{target_count} valid repos | Seen: {len(self.seen_repos)} total")
                    
                    cursor = None
                    pages = 0
                    max_pages = 20
                    found_new_in_query = False

                    while pages < max_pages and len(all_repos) < target_count:
                        if self.rate_limit_remaining < 100:
                            print("Rate limit low, waiting...")
                            time.sleep(60)
                            self.check_rate_limit()

                        result = self.fetch_repositories(language, star_range, cursor, year_range)
                        if not result or not result.get('nodes'):
                            break

                        for node in result['nodes']:
                            if not node:
                                continue
                            
                            # Check for duplicates first
                            repo_id = f"{node['owner']['login']}/{node['name']}"
                            if repo_id in self.seen_repos:
                                print(f"  ⊘ Duplicate: {repo_id}")
                                continue
                            
                            self.seen_repos.add(repo_id)
                            data = self.parse_repo_data(node)
                            
                            if self.is_valid_repo(data):
                                all_repos.append(data)
                                found_new_in_query = True
                                print(f"  ✓ Added: {data['owner']}/{data['name']} ({len(all_repos)}/{target_count})")
                                
                                if len(all_repos) >= target_count:
                                    print(f"\n🎉 Reached target: {target_count} valid repos collected!")
                                    random.shuffle(all_repos)
                                    return all_repos
                            else:
                                print(f"  ✗ Filtered out: {data['owner']}/{data['name']}")

                        # Save intermediate results
                        if len(all_repos) > 0 and len(all_repos) % 500 == 0:
                            self.save_to_csv(all_repos, f'github_repos_intermediate_{len(all_repos)}.csv')

                        info = result.get('pageInfo', {})
                        if not info.get('hasNextPage'):
                            break

                        cursor = info.get('endCursor')
                        pages += 1
                    
                    # Break out of this combo early if no new repos found
                    if not found_new_in_query and pages > 5:
                        print("  → No new repos in this combo, moving on...")
                        break

            # Safety check: if we've done multiple full passes with no progress
            if len(all_repos) < target_count and stuck_counter == 0:
                print(f"\nCompleted search cycle. Collected {len(all_repos)}/{target_count}")
                if len(all_repos) < target_count * 0.7:
                    print("⚠️ May not reach target with current filters. Consider:")
                    print("  - Lowering min_prose_length")
                    print("  - Reducing confidence_threshold")
                    print("  - Accepting single-contributor repos")

        random.shuffle(all_repos)
        return all_repos


    def save_to_csv(self, repos, filename='raw_repos.csv'):
        df = pd.DataFrame(repos)
        if 'is_fork' in df.columns:
            df = df.drop(columns=['is_fork'])
        df.to_csv(filename, index=False, encoding='utf-8')
        print(f"\nSaved {len(repos)} repositories to {filename}")
        return df


if __name__ == "__main__":
    scraper = GitHubScraper(GITHUB_TOKEN)
    repos = scraper.scrape_repos(target_count=10000)
    df = scraper.save_to_csv(repos, 'raw_repos.csv')
    print(f"\n✅ Final count: {len(df)} repositories")
