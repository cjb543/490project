import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

from completeness import struture_completeness

READMES = 3000
SHOW = 3


df: pd.DataFrame = pd.read_csv("raw_repos.csv")
df = df.sample(frac=1, random_state=42).reset_index(drop=True)

readmes = list(df["readme"].to_numpy())
test = struture_completeness(readmes)
test.compute(READMES)


for i in range(SHOW):
    print(df.iloc[i][["name", "owner"]])
    print(test.get_readme_completeness(readmes[i]))


for i in range(READMES):
    if (
        test.get_readme_completeness(readmes[i])["total"] == 0
        and df.iloc[i]["stars"] > 2000
    ):
        print(df.iloc[i][["name", "owner"]])

x = []
for i in range(READMES):
    x.append(test.get_readme_completeness(readmes[i])["total"])

y = df["stars"][:READMES]
data = {
        "section count": x,
        "stars": y
}

# plt.yticks(np.linspace(1, max(y), 15))
plt.figure(figsize=(15, 10))
sns.scatterplot(data=data, x="section count", y="stars")
# plt.ylabel("number of stars")
# plt.xlabel("number of sections")

plt.show()
