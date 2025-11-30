import pandas as pd

from completeness import struture_completeness

df: pd.DataFrame = pd.read_csv('github_repos_final.csv')
readmes = list(df['readme'].to_numpy())
test = struture_completeness(readmes)
test.compute(3)

for i in range(3):
    print(df.iloc[i][['name', 'owner']])
    print(test.get_readme_completeness(readmes[i]))
