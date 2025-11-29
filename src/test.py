from collections import defaultdict

import mistune
import pandas as pd

df: pd.DataFrame = pd.read_csv('github_repos_final.csv')
print(df.shape)

section_kws = dict()
section_kws['description'] = set(['describe', 'description', 'overview', 'about', 'summary', 'introduction', 'what is'])
section_kws['usage'] = set(['use', 'usage', 'quickstart', 'run', 'start document', 'docs example', 'demo', 'sample troubleshoot'])
section_kws['installation'] = set(['install', 'build', 'setup', 'download', 'compile'])
section_kws['licence'] = set(['license', 'licence', 'copyright'])
section_kws['credits'] = set(['credit', 'acknowledge', 'author'])
section_kws['table_of_contents'] = set(['content'])
section_kws['contribution'] = set(['contribute', 'contribution'])

c1, c2 = 0, 0
for readme in df['readme']:
    readme = readme.lower()
    if "## usage" in readme:
        c1 += 1
    elif "## how to use" in readme:
        c2 += 1
print("\"Usage\": ", c1)
print("\"How to use\": ", c2)


sm = set()
for readme in df['readme']:
    readme = readme.lower()
    for line in readme.splitlines():
        if line.startswith("##") and not line.startswith("###"):
            # print(readme)
            sm.add(line[3:])

lsm = sorted(list(sm))
# print(*(i + '\n' for i in lsm))

h2 = set()

mpp = defaultdict(lambda: {i: 0 for i in section_kws.keys()})

for readme in df['readme']:
    ast = mistune.create_markdown(renderer='ast')
    tree = ast(readme)
    for node in tree:
        if node.get('type') == 'heading' and node['attrs']['level'] == 2:
            for child in node['children']:
                if child.get('raw'):
                    raw = child['raw'].lower()
                    for i, j in section_kws.items():
                        for k in j:
                            if k in raw:
                                mpp[readme][i] = 1
                    h2.add(raw)
it1 = iter(mpp.keys())
it2 = iter(mpp.values())
for i in range(1):
    print(next(it1))
    print(next(it2))

# print(abs(len(h2) - len(lsm)))
# print(len(lsm), '\n', len(h2))
# print(h2)
