import mistune
import pandas as pd

from completeness import html_parser


def has_html(readme: str) -> bool:
    parser.clear()
    parser.feed(readme)
    tags = []
    tags.append(len(parser.heading_data))
    tags.append(parser.image_cnt)
    tags.append(parser.list_item_cnt)
    tags.append(parser.code_blocks)
    tags.append(parser.inline_code_cnt)
    return any(i for i in tags)


df = pd.read_csv('filtered_readmes.csv,')

readmes = df['readme'].tolist()

html_count = 0
parser = html_parser()
for readme in readmes:
    html_count += has_html(readme)
print(html_count)
