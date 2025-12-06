import requests
import pandas as pd
from config import GITHUB_TOKEN

endpoint = "https://api.github.com/graphql"
headers = {"Authorization": f"Bearer {GITHUB_TOKEN}"}

query = """
{
        repository(owner:"nodejs", name:"node") {
            name
            owner {
                login
            }
        }
}
"""

r = requests.post(endpoint, json={"query": query}, headers=headers)
data = r.json()
print(data)

df = pd.read_csv("raw_repos.csv")
print(df[df['owner'] == 'nodejs'])
