import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from completeness import struture_completeness
from config import GITHUB_TOKEN
from get_contributors import contributors

N = 500

df = pd.read_csv("repo_data_numbers.csv")

df2 = pd.read_csv("raw_repos.csv")
df2.dropna()
df2.drop("contributors", axis=1, inplace=True)

readmes = list(df2["readme"])

A = []
for c in df["contributors"]:
    if c <= 100:
        A.append(c)

# Get contributors
contributors = contributors(GITHUB_TOKEN)
df2["contributors"] = contributors.get_contributors(df2)

print(df2[["name", "owner", "contributors"]].head())

# Test
fig, ax = plt.subplots(nrows=1, ncols=2)

count, edges, bars = ax[0].hist(A)
ax[0].bar_label(bars)
plt.show()

# sc = struture_completeness(readmes)
# sc.compute(N)
#
# x = []
# for i in range(N):
#     readme = readmes[i]
#     d: dict[str, int] = sc.get_readme_completeness(readme)
#     x.append(d["contribution"])
#
# df3 = pd.DataFrame({"x": x, "y": list(df["contributors"][:N])})
# print(df.info())
#
# sns.set_theme(style="ticks", palette="pastel")
# fig, axes = plt.subplots(nrows=1, ncols=2, figsize=(10, 5))
#
# sns.boxplot(data=df3, x="x", y="y", ax=axes[0])
# axes[0].set_xlabel("Has contribution section")
# axes[0].set_ylabel("Number of contributors")
#
# plt.tight_layout()
# plt.show()
