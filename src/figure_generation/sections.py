import matplotlib.pyplot as plt
import pandas as pd

df = pd.read_csv("../../data/repo_data_numbers.csv")
total_sections = [0, 1, 2, 3, 4, 5, 6, 7]
counts = [0] * 8
for _, row in df.iterrows():
    total = int(row["total_sections"])
    counts[total] += 1
bars = plt.bar(total_sections, counts,color="#54487A")
plt.bar_label(bars)
plt.xlabel("Amount of Sections in README")
plt.ylabel("Amount of Repositories")
plt.show()
