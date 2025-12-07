import matplotlib.pyplot as plt
import mistune
import pandas as pd
import seaborn as sns

from completeness import html_parser, struture_completeness

df = pd.read_csv('repo_data_numbers.csv')
# df2 = pd.read_csv('raw_repos.csv')

totals_sections = [0, 1, 2, 3, 4, 5, 6, 7]
counts = [0] * 8
html_parser = html_parser()
with open('sample_readme', 'r') as file:
    text = file.read()

text = mistune.html(text)
print(text)
html_parser.feed(text)
print(" ".join(html_parser.text_data))

for index, row in df.iterrows():
    total = int(row['total_sections'])
    counts[total] += 1
bars = plt.bar(totals_sections, counts)
plt.bar_label(bars)
plt.show()

plt.scatter(x=df['completeness_score'], y=df['log_stars'])
plt.show()


# text = df2.loc[0]['readme']
# text = mistune.html(text)

# x = []
# x.append(text)
# sc = struture_completeness(x)
# sc.compute()
# print("SC:", sc.get_readme_completeness(text))


# readmes = df2['readme'].tolist()
# reades = [mistune.html(readme) for readme in readmes]
# sc = struture_completeness(reades)
# sc.compute()
#
# totals_sections1 = [0, 1, 2, 3, 4, 5, 6, 7]
# counts1 = [0] * 8
#
# for readme in reades:
#     d = sc.get_readme_completeness(readme)
#     total = d['total']
#     counts1[total] += 1
#
