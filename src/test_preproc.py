import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

from completeness import struture_completeness
from get_contributors import contributors

df = pd.read_csv("repo_data_numbers.csv")

fig, ax = plt.subplots(nrows=3, ncols=3, figsize=(12, 12))
_, _, bars = ax[0][0].hist(df['contributors'])
ax[0][0].bar_label(bars)
ax[0][0].set_title("contributor counts vs number of repos")
ax[0][0].set_xlabel("Number of contributors")
ax[0][0].set_ylabel("Number of Repositories")


c = df["contributors"].to_numpy()
X = df['has_contributing'].to_numpy()


tmp = pd.DataFrame({"has contribution section": X, "Number of contributors": c})
cutoff = tmp["Number of contributors"].quantile(0.90)
print("90 percent less than", cutoff)
df_filtered = tmp[tmp["Number of contributors"] <= cutoff]

print(df_filtered.value_counts())
print(df_filtered.groupby('has contribution section')['Number of contributors'].describe())

sns.boxplot(data=df_filtered, x="has contribution section", y="Number of contributors", ax=ax[0][1])

# ax[0][1].set_ylim(0, 100)
plt.show()


# forks = df2['forks'].to_numpy()
# df4 = pd.DataFrame({"has contribution section": x, "Number of Forks": forks})
# sns.boxplot(data=df4, x="has contribution section", y="Number of Forks", ax=ax[1])
# plt.tight_layout()
# plt.show()


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
