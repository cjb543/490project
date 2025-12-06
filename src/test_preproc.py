import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

from completeness import struture_completeness
from get_contributors import contributors

df = pd.read_csv("repo_data_numbers.csv")
print(df[df.isna().any(axis=1)])
# contributors series w/ <= 300 contributors
c = df[df["contributors"] <= 300]["contributors"]

idx = np.array([i[0] for i in list(c.items())])
X: np.ndarray[np.int32] = df.loc[idx]['has_contributing'].to_numpy()
print(X)

fig, ax = plt.subplots(nrows=1, ncols=2)
sns.set_theme(style="ticks", palette="pastel")

# Only looking at <= 300 contributors. Repos over 300 are treated as outliers.
df3 = pd.DataFrame({"has contribution section": X, "Number of contributors": c.to_numpy()})
sns.boxplot(data=df3, x="has contribution section", y="Number of contributors", ax=ax[0])

# forks = df2['forks'].to_numpy()
# df4 = pd.DataFrame({"has contribution section": x, "Number of Forks": forks})
# sns.boxplot(data=df4, x="has contribution section", y="Number of Forks", ax=ax[1])
plt.tight_layout()
plt.show()


# Section completeness score vs stars
# scores: list[int] = []
# for readme in readmes:
#     comp: dict[str, int] = sc.get_readme_completeness(readme)
#     scores.append(comp['total'])
#
# stars = df2['stars']
# sns.scatterplot(data=pd.Dataframe({'section completeness score': scores, 'stars': np.log(stars)}), x='section completeness score', y='stars')
# plt.plot()

# all individual sections vs stars
# fig, ax = plt.subplots(nrows=3, ncols=3)


# df2.drop("contributors", axis=1, inplace=True)
# df2["contributors"] = contributors.get_contributors(df2)
# print(df2[["name", "owner", "contributors"]].head())

# Test
# fig, ax = plt.subplots(nrows=1, ncols=2)
# count, edges, bars = ax[0].hist(c)
# ax[0].bar_label(bars)
# plt.show()
