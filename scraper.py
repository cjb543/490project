import requests
import time
import json
from datetime import datetime, timedelta
import base64
from config import GITHUB_TOKEN

# Configuration
HEADERS = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Content-Type": "application/json"
}

def get_graphql_query():
    """Return the GraphQL query"""
    return """
    query($cursor: String, $searchQuery: String!) {
      search(
        query: $searchQuery
        type: REPOSITORY
        first: 100
        after: $cursor
      ) {
        pageInfo {
          hasNextPage
          endCursor
        }
        nodes {
          ... on Repository {
            nameWithOwner
            stargazerCount
            forkCount
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
          }
        }
      }
    }
    """

def get_readme_rest(owner, repo):
    """Fallback: Fetch README using REST API if GraphQL fails"""
    url = f"https://api.github.com/repos/{owner}/{repo}/readme"
    response = requests.get(url, headers=HEADERS)
    
    if response.status_code == 200:
        content = response.json().get('content', '')
        return base64.b64decode(content).decode('utf-8')
    return None

def fetch_repos_for_date_range(start_date, end_date, max_repos=1000):
    """Fetch repositories for a specific date range"""
    repos_data = []
    cursor = None
    
    # Use indexed-at for better distribution, no star sorting
    search_query = f"created:{start_date}..{end_date}"
    
    print(f"Fetching repos from {start_date} to {end_date}...")
    
    while len(repos_data) < max_repos:
        variables = {"cursor": cursor, "searchQuery": search_query}
        
        for attempt in range(3):
            response = requests.post(
                "https://api.github.com/graphql",
                headers=HEADERS,
                json={"query": get_graphql_query(), "variables": variables},
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                break
            elif response.status_code in [502, 503, 504]:
                wait_time = 2 ** attempt
                print(f"Server error {response.status_code}, retrying in {wait_time}s...")
                time.sleep(wait_time)
            else:
                print(f"Error: {response.status_code}")
                return repos_data
        else:
            print("Failed after retries")
            return repos_data
        
        if not result or 'data' not in result:
            break
        
        search_data = result['data']['search']
        
        for node in search_data['nodes']:
            if len(repos_data) >= max_repos:
                break
            
            # Extract README
            readme_content = None
            if node.get('object') and node['object'].get('text'):
                readme_content = node['object']['text']
            else:
                owner, repo = node['nameWithOwner'].split('/')
                readme_content = get_readme_rest(owner, repo)
            
            # Extract commit count
            commit_count = 0
            if node.get('defaultBranchRef') and node['defaultBranchRef'].get('target'):
                commit_count = node['defaultBranchRef']['target']['history']['totalCount']
            
            repo_data = {
                "name": node['nameWithOwner'],
                "stars": node['stargazerCount'],
                "forks": node['forkCount'],
                "commits": commit_count,
                "readme": readme_content
            }
            
            repos_data.append(repo_data)
            print(f"  [{start_date} to {end_date}] Collected {len(repos_data)}/{max_repos}")
        
        if search_data['pageInfo']['hasNextPage']:
            cursor = search_data['pageInfo']['endCursor']
            time.sleep(0.1)
        else:
            break
    
    return repos_data

def extract_repositories(target_count=5000):
    """Extract repository data using multiple date ranges"""
    all_repos = []
    
    # Calculate date ranges (split 1 year into chunks)
    end_date = datetime.now()
    num_ranges = (target_count // 900) + 1  # ~900 repos per range to account for some gaps
    days_per_range = 365 // num_ranges
    
    date_ranges = []
    for i in range(num_ranges):
        range_end = end_date - timedelta(days=days_per_range * i)
        range_start = end_date - timedelta(days=days_per_range * (i + 1))
        date_ranges.append((
            range_start.strftime("%Y-%m-%d"),
            range_end.strftime("%Y-%m-%d")
        ))
    
    print(f"Will fetch from {num_ranges} date ranges to get {target_count} repos")
    print(f"Repos per range: ~{target_count // num_ranges}\n")
    
    repos_per_range = target_count // num_ranges
    
    for start, end in date_ranges:
        if len(all_repos) >= target_count:
            break
        
        repos = fetch_repos_for_date_range(start, end, repos_per_range)
        all_repos.extend(repos)
        print(f"Total collected so far: {len(all_repos)}/{target_count}\n")
    
    return all_repos[:target_count]

def save_to_json(data, filename="github_repos_data.json"):
    """Save collected data to JSON file"""
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"Data saved to {filename}")

def main():
    print("Starting GitHub repository data extraction...")
    repos = extract_repositories(5000)
    print(f"\nTotal repositories collected: {len(repos)}")
    save_to_json(repos)
    
    # Summary statistics
    total_stars = sum(r['stars'] for r in repos)
    total_forks = sum(r['forks'] for r in repos)
    total_commits = sum(r['commits'] for r in repos)
    
    print(f"\nSummary:")
    print(f"Total stars: {total_stars}")
    print(f"Total forks: {total_forks}")
    print(f"Total commits: {total_commits}")
    print(f"Repositories with README: {sum(1 for r in repos if r['readme'])}")

if __name__ == "__main__":
    main()
