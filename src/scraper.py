import random
import time
from datetime import datetime

import pandas as pd
import requests
from langdetect import LangDetectException, detect

from config import GITHUB_TOKEN


class GitHubScraper:
    def __init__(self, token):
        self.token = token
        self.endpoint = "https://api.github.com/graphql"
        self.headers = {"Authorization": f"Bearer {token}"}
        self.rate_limit_remaining = 5000
        self.rate_limit_reset = None

    def check_rate_limit(self):
        """Check current rate limit status"""
        query = """
        query {
          rateLimit {
            remaining
            resetAt
          }
        }
        """
        response = requests.post(self.endpoint, json={'query': query}, headers=self.headers)
        data = response.json()
        self.rate_limit_remaining = data['data']['rateLimit']['remaining']
        self.rate_limit_reset = data['data']['rateLimit']['resetAt']
        print(f"Rate limit: {self.rate_limit_remaining} remaining, resets at {self.rate_limit_reset}")

    def exponential_backoff(self, attempt):
        """Calculate wait time with exponential backoff"""
        wait_time = min(300, (2 ** attempt) + random.uniform(0, 1))
        print(f"Backing off for {wait_time:.2f} seconds...")
        time.sleep(wait_time)

    def is_english(self, text):
        if not text or not text.strip():
            return False
        try:
            return detect(text) == "en"
        except LangDetectException:
            return False

    def fetch_repositories(self, language, stars_range, cursor=None, max_retries=5):
        """Fetch repositories for a given language and star range"""
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
                owner {
                  login
                }
                stargazerCount
                forkCount
                isFork
                createdAt
                primaryLanguage {
                  name
                }
                defaultBranchRef {
                  target {
                    ... on Commit {
                      history {
                        totalCount
                      }
                    }
                  }
                }
                object(expression: "HEAD:README.md") {
                  ... on Blob {
                    text
                  }
                }
                mentionableUsers(first: 1) {
                  totalCount
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

        # Explicitly exclude forks in the search query
        search_query = f"language:{language} stars:{stars_range} fork:false"
        variables = {"query": search_query, "cursor": cursor}

        for attempt in range(max_retries):
            try:
                response = requests.post(
                    self.endpoint,
                    json={'query': query, 'variables': variables},
                    headers=self.headers,
                    timeout=30
                )

                if response.status_code == 200:
                    data = response.json()

                    # Update rate limit
                    if 'data' in data and 'rateLimit' in data['data']:
                        self.rate_limit_remaining = data['data']['rateLimit']['remaining']
                        self.rate_limit_reset = data['data']['rateLimit']['resetAt']

                    # Check for errors
                    if 'errors' in data:
                        print(f"GraphQL errors: {data['errors'][0] if data['errors'] else 'Unknown'}")
                        if attempt < max_retries - 1:
                            self.exponential_backoff(attempt)
                            continue
                        return None

                    return data['data']['search']

                elif response.status_code == 403 or response.status_code == 429:
                    print(f"Rate limited or forbidden. Status: {response.status_code}")
                    if attempt < max_retries - 1:
                        self.exponential_backoff(attempt)
                    else:
                        return None
                else:
                    print(f"HTTP Error {response.status_code}: {response.text}")
                    if attempt < max_retries - 1:
                        self.exponential_backoff(attempt)
                    else:
                        return None

            except requests.exceptions.RequestException as e:
                print(f"Request exception: {e}")
                if attempt < max_retries - 1:
                    self.exponential_backoff(attempt)
                else:
                    return None

        return None

    def parse_repo_data(self, node):
        """Parse repository node into structured data"""
        readme_text = None
        if node.get('object') and node['object']:
            readme_text = node['object'].get('text', '')

        commits = 0
        if (node.get('defaultBranchRef') and node['defaultBranchRef'] and node['defaultBranchRef'].get('target') and node['defaultBranchRef']['target'].get('history')):
            commits = node['defaultBranchRef']['target']['history'].get('totalCount', 0)

        # Get contributor count from mentionableUsers
        contributors = 0
        if node.get('mentionableUsers') and node['mentionableUsers']:
            contributors = node['mentionableUsers'].get('totalCount', 0)

        return {
            'name': node.get('name', ''),
            'owner': node['owner'].get('login', ''),
            'stars': node.get('stargazerCount', 0),
            'forks': node.get('forkCount', 0),
            'contributors': contributors,
            'commits': commits,
            'language': node.get('primaryLanguage', {}).get('name', '') if node.get('primaryLanguage') else '',
            'created_at': node.get('createdAt', ''),
            'is_fork': node.get('isFork', False),
            'readme': readme_text if readme_text else ''
        }

    def is_valid_repo(self, repo_data):
        """Check if repository meets criteria: not a fork, has >1 contributor, has README"""
        if repo_data['is_fork']:
            return False
        if repo_data['contributors'] <= 1:
            return False
        if not repo_data['readme'] or repo_data['readme'].strip() == '':
            return False
        if not self.is_english(repo_data['readme']):
            return False
        return True

    def scrape_repos(self, target_count=10000, repos_per_language=1000):
        """Main scraping function with random sampling"""
        # Top 10 programming languages on GitHub
        languages = [
            'JavaScript', 'Python', 'Java', 'TypeScript', 'C#',
            'C++', 'PHP', 'Shell', 'C', 'Ruby'
        ]

        # Star ranges for sampling diversity
        star_ranges = [
            '1000..5000',
            '500..1000',
            '100..500',
            '50..100',
            '5..50'
        ]

        all_repos = []
        repos_collected = 0

        print(f"Starting scrape for {target_count} repositories...")
        print("Filtering: fork:false, contributors>1, has README\n")
        self.check_rate_limit()

        # Shuffle languages for random sampling
        random.shuffle(languages)

        for language in languages:
            if repos_collected >= target_count:
                break

            print(f"\n--- Scraping {language} repositories ---")
            language_repos = []
            attempts = 0
            max_attempts_per_language = 3000  # Max repos to check per language

            # Shuffle star ranges for variety
            shuffled_ranges = star_ranges.copy()
            random.shuffle(shuffled_ranges)

            for star_range in shuffled_ranges:
                if len(language_repos) >= repos_per_language:
                    break

                print(f"Fetching {language} repos with {star_range} stars...")
                cursor = None
                pages_fetched = 0
                max_pages = 10  # More pages since we're getting fewer per page

                while pages_fetched < max_pages and len(language_repos) < repos_per_language:
                    # Rate limit check
                    if self.rate_limit_remaining < 100:
                        print("Rate limit low, waiting...")
                        time.sleep(60)
                        self.check_rate_limit()

                    result = self.fetch_repositories(language, star_range, cursor)

                    if not result or not result.get('nodes'):
                        break

                    # Parse and filter repos
                    for node in result['nodes']:
                        if not node:
                            continue

                        attempts += 1
                        repo_data = self.parse_repo_data(node)

                        # Apply filters
                        if self.is_valid_repo(repo_data):
                            language_repos.append(repo_data)

                        if attempts >= max_attempts_per_language:
                            print(f"  Reached max attempts for {language}")
                            break

                    valid_count = len(language_repos)
                    print(f"  Valid {language} repos: {valid_count}/{repos_per_language} (checked {attempts} total)")

                    # Check pagination
                    page_info = result.get('pageInfo', {})
                    if not page_info.get('hasNextPage'):
                        break
                    cursor = page_info.get('endCursor')
                    pages_fetched += 1

                    time.sleep(1.5)  # Slightly longer delay between requests

                if attempts >= max_attempts_per_language:
                    break

            # Randomly sample if we got too many
            if len(language_repos) > repos_per_language:
                language_repos = random.sample(language_repos, repos_per_language)

            all_repos.extend(language_repos)
            repos_collected += len(language_repos)
            print(f"Total valid collected: {repos_collected}/{target_count}")

            # Save intermediate results
            if repos_collected % 1000 == 0 and repos_collected > 0:
                self.save_to_csv(all_repos, f'github_repos_intermediate_{repos_collected}.csv')

        # Final shuffle for randomness
        random.shuffle(all_repos)

        return all_repos[:target_count]

    def save_to_csv(self, repos, filename='github_repos.csv'):
        """Save repository data to CSV"""
        df = pd.DataFrame(repos)
        # Remove is_fork column from final output (used only for filtering)
        if 'is_fork' in df.columns:
            df = df.drop(columns=['is_fork'])
        df.to_csv(filename, index=False, encoding='utf-8')
        print(f"\nSaved {len(repos)} repositories to {filename}")
        return df


if __name__ == "__main__":
    scraper = GitHubScraper(GITHUB_TOKEN)

    # Scrape 10,000 repos (~1,000 per language)
    repos = scraper.scrape_repos(target_count=10000, repos_per_language=1000)

    # Save final results
    df = scraper.save_to_csv(repos, 'github_repos_final.csv')

    # Print summary statistics
    print("\n=== Summary Statistics ===")
    print(f"Total repositories: {len(df)}")
    print("\nRepositories per language:")
    print(df['language'].value_counts())
    print(f"\nAll have READMEs: {df['readme'].notna().all()}")
    print(f"All have >1 contributor: {(df['contributors'] > 1).all()}")
    print(f"Min contributors: {df['contributors'].min()}")
    print(f"Average contributors: {df['contributors'].mean():.2f}")
    print(f"Average stars: {df['stars'].mean():.2f}")
    print(f"Average forks: {df['forks'].mean():.2f}")
