import zipfile
import json
import os
import beprint

rootpath = 'output'
result = {}

with open('zh-cn.json', 'r', encoding='utf-8') as f:
    translations = json.load(f)
translations.update({
    'PROCEDURES_CALL': '自制积木调用',
    'CONTROL_IF_ELSE': '如果 () 那么 ... 否则',
    'OPERATOR_LETTER_OF': '() 的第 () 个字符',
    'CONTROL_CREATE_CLONE_OF': '克隆 ()',
    'CONTROL_START_AS_CLONE': '当作为克隆体启动时',
    'CONTROL_WAIT_UNTIL': '等待 ()',
    'CONTROL_REPEAT_UNTIL': '重复执行直到 ()',
    'CONTROL_DELETE_THIS_CLONE': '删除此克隆体',
    'ARGUMENT_REPORTER_BOOLEAN': '自制积木布尔参数',
    'PEN_STAMP': '图章',
    'PEN_PENDOWN': '落笔',
    'PEN_PENUP': '抬笔',
    'PEN_SETPENCOLORTOCOLOR': '将笔的颜色设为 ()',
    'PEN_CLEAR': '全部擦除',
    'PEN_SETPENCOLORPARAMTO': '将笔的 () 设为 ()',
    'PEN_SETSIZETO': '将笔的粗细设为 ()',
    'PEN_CHANGEPENCOLORPARAMBY': '将笔的 () 增加 ()',
    'MUSIC_PLAYNOTEFORBEATS': '演奏音符 () () 拍',
})

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

t = beprint.Table(['#', '积木名称', '使用 %/积木', '使用 %/项目'])

total_blocks = sum(map(lambda x: x[0], result.values()))
print('积木总数' + str(total_blocks))

result_list = list(result.items())
result_list.sort(key=lambda x: x[1], reverse=True)
i = 0
for key, value in result_list:
    translate_key = key.replace('operator', 'operators').upper()
    if translate_key in translations:
        text = translations.get(translate_key, translate_key.replace('_', ' ').title()) \
            .replace('%1', '()').replace('%2', '()').replace('%3', '()')
        i += 1
        t.add_row([str(i), beprint.align_left(text, 30), format(value[0] / total_blocks * 100, '.4f'), format(value[1] / count * 100, '.1f')])
t.print(beprint.Chars(beprint.style_1))
