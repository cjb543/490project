from collections import defaultdict

import mistune
import pandas as pd

df: pd.DataFrame = pd.read_csv('github_repos_final.csv')

class struture_completess:

    def __init__(self, readmes: list[str]):
        self.section_kws = dict()
        self.__section_kws['description'] = ['describe', 'description', 'overview', 'about', 'summary', 'introduction', 'what is']
        self.__section_kws['usage'] = ['use', 'usage', 'quickstart', 'run', 'start document', 'docs example', 'demo', 'sample troubleshoot']
        self.__section_kws['installation'] = ['install', 'build', 'setup', 'download', 'compile']
        self.__section_kws['licence'] = ['license', 'licence', 'copyright']
        self.__section_kws['credits'] = ['credit', 'acknowledge', 'author']
        self.__section_kws['table_of_contents'] = ['content']
        self.__section_kws['contribution'] = ['contribute', 'contribution']

        self.__completeness: defaultdict[str, dict[str, int]] = defaultdict(lambda: {**{i: 0 for i in self.section_kws.keys()}, "total": 0})
        self.__readmes = readmes

    def __collect_children(self, children: list[dict]) -> list[str]:
        res: list[str] = []
        for child in children:
            res.append(child['raw'].lower()) if child.get('raw') else ...
        return res

    def __is_section(self, heading: str) -> str | None:
        for section, kws in self.section_kws.items():
            if any([kw in heading for kw in kws]):
                return section
        return None

    def get_readme_completeness(self, readme: str) -> dict[str, int]:
        return self.completeness[readme]

    def compute(self):
        for readme in self.readmes:
            ast = mistune.create_markdown(renderer='ast')
            tree = ast(readme)

            for node in tree:
                if node.get('type') == 'heading' and node['attrs']['level'] == 2:
                    headings: list[str] = self.collect_children(node['children'])
                    for h in headings:
                        section: str | None = self.is_section(h)
                        if section:
                            self.completeness[readme][section] = 1
                            self.completeness[readme]['total'] += 1
