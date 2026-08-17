import zipfile
import json
import os
import csv
import beprint

rootpath = 'output'
result = {}

with open('translations_full.json', 'r', encoding='utf-8') as f:
    translations = json.load(f)

count = 0

for dirpath, dirnames, filenames in os.walk(rootpath):
    for filename in filenames:
        fullpath = os.path.join(dirpath, filename)
        if os.path.splitext(fullpath)[1] != '.sb3':
            continue
        with zipfile.ZipFile(fullpath) as zip:
            with zip.open('project.json', 'r') as f:
                content = f.read().decode()
                project = json.loads(content)
                project_result = {}
                for target in project['targets']:
                    for block in target['blocks'].values():
                        if isinstance(block, dict):
                            opcode = block['opcode']
                            project_result.setdefault(opcode, [0, 0])
                            # 数量/种类
                            project_result[opcode][0] += 1
                            project_result[opcode][1] = 1
                if sum(map(lambda x: x[0], project_result.values())) < 10:
                    continue
                for key, value in project_result.items():
                    result.setdefault(key, [0, 0])
                    result[key][0] += value[0]
                    result[key][1] += value[1]
                if len(project_result) >= 1:
                    count += 1
                    # 限制统计项目数量
                    # if count > 150:
                    #     break

total_blocks = sum(map(lambda x: x[0], result.values()))
print('积木总数' + str(total_blocks))

result_list = list(result.items())
result_list.sort(key=lambda x: x[1], reverse=True)

# CSV 输出（完整版，原始 opcode，无过滤）
with open('statistics.csv', 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(['rank', 'opcode', 'block_count', 'project_count', 'block_percent', 'project_percent'])
    for i, (key, value) in enumerate(result_list, 1):
        writer.writerow([
            i,
            key,
            value[0],
            value[1],
            round(value[0] / total_blocks * 100, 4),
            round(value[1] / count * 100, 1),
        ])
print('CSV 已保存至 statistics.csv')

# 人类可读表格（翻译 + 过滤无翻译项）
t = beprint.Table(['#', '积木名称', '使用 %/积木', '使用 %/项目'])
i = 0
for key, value in result_list:
    if key in translations:
        text = translations.get(key)
        i += 1
        t.add_row([str(i), text, format(value[0] / total_blocks * 100, '.4f'), format(value[1] / count * 100, '.1f')])
t.print(beprint.Chars(beprint.style_1), panel=beprint.Panel())
