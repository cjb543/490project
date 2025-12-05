import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

from completeness import struture_completeness
from get_contributors import contributors

N = 500

df = pd.read_csv("repo_data_numbers.csv")
df2 = pd.read_csv("raw_repos.csv")
df2.dropna()

readmes = df2["readme"].to_numpy()

# contributors series w/ <= 300 contributors
c = df2[df2["contributors"] <= 300]["contributors"]

# First from each tuple
idx = np.array([i[0] for i in list(c.items())])
print(idx[:5])


# df2.drop("contributors", axis=1, inplace=True)
# df2["contributors"] = contributors.get_contributors(df2)
# print(df2[["name", "owner", "contributors"]].head())

# Test
# fig, ax = plt.subplots(nrows=1, ncols=2)
# count, edges, bars = ax[0].hist(c)
# ax[0].bar_label(bars)
# plt.show()


x = readmes[idx]
X = []

sc = struture_completeness(x)
sc.compute(N)

for i in x:
    X.append("Yes" if sc.get_readme_completeness(i)["contribution"] else "No")


sns.set_theme(style="ticks", palette="pastel")
df3 = pd.DataFrame({"has contribution section": X[:N], "Number of contributors": c.to_numpy()[:N]})

sns.boxplot(data=df3, x="has contribution section", y="Number of contributors")
plt.tight_layout()
plt.show()


# Plot has contributor section against number of forks
