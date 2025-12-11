import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

df = pd.read_csv("../../data/repo_data_numbers.csv")

sns.histplot(df["token_count"], bins=100)
plt.ylabel('Number of Repositories')
plt.xlim(0, 3000)
plt.show()
