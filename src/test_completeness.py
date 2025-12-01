import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from completeness import struture_completeness

READMES = 3000
SHOW = 3


df: pd.DataFrame = pd.read_csv('raw_repos.csv')
df = df.sample(frac=1, random_state=42).reset_index(drop=True)

readmes = list(df['readme'].to_numpy())
test = struture_completeness(readmes)
test.compute(READMES)


for i in range(SHOW):
    print(df.iloc[i][['name', 'owner']])
    print(test.get_readme_completeness(readmes[i]))


for i in range(READMES):
    if test.get_readme_completeness(readmes[i])['total'] == 0 and df.iloc[i]['stars'] > 1000:
        print(df.iloc[i][['name', 'owner']])

x = []
for i in range(READMES):
    x.append(test.get_readme_completeness(readmes[i])['total'])
print(x)
y = df['stars'][:READMES]

plt.figure(figsize=(15, 10))
plt.yticks(np.linspace(1, max(y), 15))
plt.scatter(x, y)
plt.xlabel('number of sections')
plt.ylabel('number of stars')

plt.show()
