import mistune
import pandas as pd

from completeness import html_parser

with open('sample_readme', 'r') as file:
    text = file.read()

df = pd.read_csv('raw_repos.csv')
text = df.loc[0]['readme']

html = mistune.html(text)
# print(html)

html_parser = html_parser()
html_parser.feed(html)
print(html_parser.text_data)
print("\n\n", " ".join(html_parser.text_data))
