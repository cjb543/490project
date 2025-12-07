import mistune
import pandas as pd

from completeness import html_parser, struture_completeness

df = pd.read_csv('raw_repos.csv')
# print(df.isna().any())
# print(df[df.isna().any(axis=1)])
# print(df.shape[0])

# print(df.loc[2630])

# print(df.loc[747])
# sc = struture_completeness(df['readme'].tolist())
# sc.compute()

with open("rst_readme", 'r') as file:
    file_content = file.read()

parser = html_parser()
parser.feed('<html><head><title>Test</title></head>'
            '<body><h1>Parse me!</h1><h2>test</h2><p>dont show</p><h1><div>hello<p>hello2</p></div></h1><p>dont show again</p></body></html>')

# parser.feed("fjdskdjk")
# print(parser.heading_data)
if len(parser.start_tags) == 0:
    ...
    # print("Not html")

df[['owner', 'name', 'readme']].sample(5).to_csv('sample.csv', index=False)

readme_markdown = df[df['name'] == 'banditore']['readme'].iloc[0]
readme_html = df[df['name'] == 'sentry-testkit']['readme'].loc[1]

# markdown = mistune.create_markdown()
# print(markdown(readme_html))

html = mistune.html(file_content)
html_parser = html_parser()
html_parser.feed(html)
print(html)
print(html_parser.heading_data)
html_parser.clear()

# Markdown fence
code_block_test = """
# Hello
``` python print(\"hello\")```
hello
``` c++ hello ```
"""
html = mistune.html(code_block_test)
html_parser.feed(html)
print("Code BLOCKS", html_parser.code_blocks)
print(html_parser.start_tags)

print("--- INLINE CODE TEST ---")
inline_code = """
# Hello
## Installation
to install run `npm install gfx`
"""
html_parser.clear()
html = mistune.html(inline_code)
print(html)
html_parser.feed(html)
print(html_parser.code_blocks)  # 0
print(html_parser.inline_code_cnt)  # 1


with open("code_test", "r") as file:
    file_content = file.read()
html = mistune.html(file_content)
html_parser.clear()
html_parser.feed(html)
print(html_parser.code_blocks)
print(html_parser.inline_code_cnt)


# Image test
image_test = """
![CI](https://github.com/j0k3r/banditore/workflows/CI/badge.svg)
![CI](https://github.com/j0k3r/banditore/workflows/CI/badge.svg)
![CI](https://github.com/j0k3r/banditore/workflows/CI/badge.svg)
![CI](https://github.com/j0k3r/banditore/workflows/CI/badge.svg)
![CI](https://github.com/j0k3r/banditore/workflows/CI/badge.svg)
"""

html = mistune.html(image_test)
print(html)
html_parser.clear()
html_parser.feed(html)
print(html_parser.image_cnt)


with open("list_test", "r") as file:
    text = file.read()
print("--- LISTS ---")
html = mistune.html(text)
html_parser.clear()
html_parser.feed(html)
print(html_parser.list_item_cnt)
