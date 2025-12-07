from collections import defaultdict
from html.parser import HTMLParser


class html_parser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.headings: set[str] = set(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])

        self.start_tags: list[str] = []
        self.heading_tags: list[str] = []

        self.at_heading: bool = False
        self.at_pre: bool = False
        self.at_code: bool = False
        self.at_table: bool = False

        self.code_blocks: int = 0
        self.inline_code_cnt: int = 0
        self.heading_data: list[str] = []
        self.image_cnt: int = 0
        self.list_item_cnt: int = 0
        self.text_data: list[str] = []

    def handle_starttag(self, tag, attrs) -> None:
        self.start_tags.append(tag)

        if tag == "pre":
            self.at_pre = True
        elif tag == "code":
            self.at_code = True
            if self.at_pre:
                self.code_blocks += 1
            else:
                self.inline_code_cnt += 1
        elif tag == 'img':
            self.image_cnt += 1
        elif tag == 'li':
            self.list_item_cnt += 1
        elif tag == 'table':
            self.at_table = True
        elif tag in self.headings:
            self.heading_tags.append(tag)
            self.at_heading = True

    def handle_endtag(self, tag: str) -> None:
        if tag in self.headings:
            self.at_heading = False
        elif tag == 'pre':
            self.at_pre = False
        elif tag == 'code':
            self.at_code = False
        elif tag == 'table':
            self.at_table = False

    def handle_data(self, data: str) -> None:
        data = data.strip()
        if data == "":
            return
        if self.at_heading:
            self.heading_data.append(data)
        elif not self.at_code and not self.at_table:
            self.text_data.append(data)

    def clear(self):
        self.reset()
        self.start_tags = []
        self.heading_tags = []
        self.at_heading = False
        self.at_code = False
        self.at_pre = False
        self.at_table = False
        self.code_blocks = 0
        self.inline_code_cnt = 0
        self.image_cnt = 0
        self.heading_data = []
        self.list_item_cnt = 0
        self.text_data = []


class struture_completeness:

    def __init__(self, html_readmes: list[str]):
        self.__section_kws = dict()
        self.__section_kws['description'] = ['describe', 'description', 'overview', 'about', 'summary', 'introduction', 'what is']
        self.__section_kws['usage'] = ['use', 'usage', 'quickstart', 'run', 'start document', 'docs example', 'demo', 'sample troubleshoot']
        self.__section_kws['installation'] = ['install', 'build', 'setup', 'download', 'compile', 'installation']
        self.__section_kws['license'] = ['license', 'licence', 'copyright']
        self.__section_kws['credits'] = ['credit', 'acknowledge', 'author']
        self.__section_kws['table_of_contents'] = ['content']
        self.__section_kws['contribution'] = ['contribute', 'contribution', 'contributing']

        self.__completeness: defaultdict[str, dict[str, int]] = defaultdict(lambda: {**{i: 0 for i in self.__section_kws.keys()}, "total": 0, "heading_cnt": 0, "code_block_cnt": 0, "inline_code_cnt": 0, "image_cnt": 0, "list_item_cnt": 0})
        self.__readmes = html_readmes

    def __is_section(self, heading: str) -> str | None:
        for section, kws in self.__section_kws.items():
            if any([kw in heading for kw in kws]):
                return section
        return None

    def __process_heading(self, readme: str, heading: str) -> None:
        section: str | None = self.__is_section(heading)
        if section:
            self.__completeness[readme]['total'] += 1 if self.__completeness[readme][section] == 0 else 0
            self.__completeness[readme][section] = 1

    def __parse_html(self, readme: str) -> None:
        parser = html_parser()
        parser.feed(readme)

        self.__completeness[readme]['heading_cnt'] = len(parser.heading_data)
        self.__completeness[readme]['code_block_cnt'] = parser.code_blocks
        self.__completeness[readme]['inline_code_nnt'] = parser.inline_code_cnt
        self.__completeness[readme]['image_cnt'] = parser.image_cnt
        self.__completeness[readme]['list_item_cnt'] = parser.list_item_cnt

        for h in parser.heading_data:
            self.__process_heading(readme, h.lower())

    def get_readme_completeness(self, readme: str) -> dict[str, int]:
        return self.__completeness[readme]

    def compute(self, n=-1):
        if n < 0:
            n = len(self.__readmes) if n == -1 else 0
        for i in range(min(n, len(self.__readmes))):
            readme = self.__readmes[i]
            self.__parse_html(readme)
