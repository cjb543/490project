
import pandas as pd
import requests

from config import GITHUB_TOKEN

endpoint = "https://api.github.com/graphql"
headers = {"Authorization": f"Bearer {GITHUB_TOKEN}"}
df = pd.read_csv('repo_data_numbers.csv')

query = """
query CheckReadmeExtensions(
  $owner: String!
  $name: String!
  $readmeMd: String!

  $readmemd: String!
  $readmeHtml: String!
  $readmeRst: String!
) {
  repository(owner: $owner, name: $name) {
    readmeMd: object(expression: $readmeMd) {
      ...fileData
    }
    readmemd: object(expression: $readmemd) {
      ...fileData
    }
    readmeHtml: object(expression: $readmeHtml) {

      ...fileData
    }
    readmeRst: object(expression: $readmeRst) {

      ...fileData
    }
  }
}

fragment fileData on GitObject {
  ... on Blob {

    byteSize

  }
}
"""


results_list = []


print(f"Starting query for {len(df)} repositories...")

for idx, row in df.iterrows():
    owner = row['owner']
    name = row['name']
    repo_slug = f"{owner}/{name}"

    variables = {

        "owner": owner,
        "name": name,

        "readmeMd": "HEAD:README.md",
        "readmemd": "HEAD:readme.md",
        "readmeHtml": "HEAD:README.html",

        "readmeRst": "HEAD:README.rst",
    }

    try:
        r = requests.post(endpoint, json={"query": query, "variables": variables}, headers=headers)
        r.raise_for_status()
        data = r.json()

        if "errors" in data:
            error_msg = data['errors'][0]['message'] if data['errors'] else "Unknown GraphQL error"
            print(f" GraphQL Error for {repo_slug}: {error_msg}")
            continue

        repo_data = data.get('data', {}).get('repository')
        if not repo_data:
            print(f"Warning: No repository data for {repo_slug}")
            continue

        extension = "Unknown"

        if repo_data.get('readmeMd') is not None:
            extension = ".md"
        elif repo_data.get('readmemd') is not None:
            extension = ".md"
        elif repo_data.get('readmeHtml') is not None:
            extension = ".html"

        elif repo_data.get('readmeRst') is not None:
            extension = ".rst"

        print(f"Readme: {idx} | {repo_slug} -> Extension: {extension}")

        results_list.append({
            "owner": owner,
            "name": name,
            "readme_extension": extension,
        })

    except requests.exceptions.RequestException as e:
        print(f"Network/Request Error for {repo_slug}: {e}")


results_df = pd.DataFrame(results_list)
results_df.to_csv("readme_extensions.csv", index=False)
