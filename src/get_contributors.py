# GraphQL cant get real contributor count, it gets "mentionableUsers", which apparently includes people watching
# and stuff and can be 1-3 orders of magnitude larger than real contributors

# Using the REST api which can actually fetch the real contributor count of a repository, but it's insanely slow.

import pandas as pd
from github import Auth, Github

class contributors:
    def __init__(self, api_token):
        self.__auth = Auth.Token(api_token)
        self.__g = Github(auth=self.__auth)


    def get_contributor_count(self, name: str) -> int:
        return self.__g.get_repo(name).get_contributors().totalCount


    def get_contributors(self, df: pd.DataFrame) -> list[int]:
        contributors = []
        for c, i in enumerate(df[["name", "owner"]].values):
            name = i[0]
            owner = i[1]
            repo_name = owner + "/" + name
            cnt = self.get_contributor_count(repo_name)
            print(f"repo {c}: {repo_name} has {cnt} contributors")
            contributors.append(cnt)
        return contributors

