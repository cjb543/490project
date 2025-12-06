from collections import defaultdict

import mistune
import pandas as pd


class struture_completeness:

    def __init__(self, readmes: list[str]):
        self.__section_kws = dict()
        self.__section_kws['description'] = ['describe', 'description', 'overview', 'about', 'summary', 'introduction', 'what is']
        self.__section_kws['usage'] = ['use', 'usage', 'quickstart', 'run', 'start document', 'docs example', 'demo', 'sample troubleshoot']
        self.__section_kws['installation'] = ['install', 'build', 'setup', 'download', 'compile']
        self.__section_kws['license'] = ['license', 'licence', 'copyright']
        self.__section_kws['credits'] = ['credit', 'acknowledge', 'author']
        self.__section_kws['table_of_contents'] = ['content']
        self.__section_kws['contribution'] = ['contribute', 'contribution', 'contributing']

        self.__completeness: defaultdict[str, dict[str, int]] = defaultdict(lambda: {**{i: 0 for i in self.__section_kws.keys()}, "total": 0})
        self.__readmes = readmes

    def __collect_children(self, children: list[dict]) -> list[str]:
        res: list[str] = []
        for child in children:
            res.append(child['raw'].lower()) if child.get('raw') else ...
        return res

    def __is_section(self, heading: str) -> str | None:
        for section, kws in self.__section_kws.items():
            if any([kw in heading for kw in kws]):
                return section
        return None

    def get_readme_completeness(self, readme: str) -> dict[str, int]:
        return self.__completeness[readme]

    def compute(self, n=-1):
        if n < 0:
            n = len(self.__readmes) if n == -1 else 0

        for i in range(min(n, len(self.__readmes))):
            readme = self.__readmes[i]
            ast = mistune.create_markdown(renderer='ast')
            tree = ast(readme)

            for node in tree:
                if node.get('type') == 'heading' and node['attrs']['level'] < 4:
                    headings: list[str] = self.__collect_children(node['children'])
                    for h in headings:
                        section: str | None = self.__is_section(h)
                        if section:
                            self.__completeness[readme]['total'] += 1 if self.__completeness[readme][section] == 0 else 0
                            self.__completeness[readme][section] = 1
