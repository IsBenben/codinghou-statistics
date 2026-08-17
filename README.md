# SB3 统计

自动下载 Scratch (sb3) 项目并统计积木使用频率的工具。

## 功能

- **get_codinghou.py** - 从编程侯平台批量下载 sb3 项目，自动解密混淆文件，支持断点续传
- **statistics.py** - 解析 output 目录下所有 sb3 文件，统计各类积木的使用数量和占比

## 使用方法

```bash
# 1. 安装依赖
pip install requests
pip install beprint

# 2. 复制配置文件并填入你的 Token
cp config.py  # 编辑 config.py 填入 TOKEN

# 3. 下载项目
python get_codinghou.py

# 4. 统计积木
python statistics.py
```

## 实现细节

### sb3 文件结构

sb3 本质是 ZIP 压缩包，内含 `project.json` 描述项目全部积木和脚本数据。编程猴平台对下载的 sb3 文件做了混淆处理（逐字节 XOR 0xFF + 9 字节魔数头），需解密后才能正常解析。

### get_codinghou.py 工作流程

1. **加载配置** - 从 `config.py` 读取 TOKEN、API 地址、请求间隔等配置
2. **分页获取作品列表** - 调用 `pubworkInfoPage` API，按收藏数排序，每页 10 条
3. **获取下载地址** - 调用 `workInfoDetail` API 拿到 `fileUrl`
4. **流式下载** - 32KB 分块下载，实时显示进度百分比
5. **解密** - 先尝试直接作为 ZIP 打开；若失败则逐字节取反，再检测并移除 9 字节混淆头部（匹配两种已知 pattern）
6. **断点续传** - 进度保存在 `progress.json`（页码 + 页内索引），中断后可从上次位置继续
7. **去重跳过** - 文件名格式 `{work_id} {sanitized_name}.sb3`，已存在则跳过

### statistics.py 工作流程

1. **遍历 sb3** - 递归扫描 `output/` 下所有 `.sb3` 文件
2. **解析 project.json** - 读取 `targets[].blocks`，提取每个 block 的 `opcode`
3. **聚合统计** - 维护两个维度：积木总数量、出现该积木的项目数
4. **过滤** - 积木总数 < 10 的项目视为无效，跳过
5. **翻译** - 通过 `zh-cn.json` 将 opcode 转为中文积木名称
6. **输出表格** - 使用 `beprint` 库渲染，包含两列百分比：占总积木数 / 占总项目数

### 依赖

- `requests` - HTTP 请求
- `beprint` - 表格格式化输出
- 标准库：`zipfile`, `json`, `os`, `re`, `time`, `sys`, `io`

## License

MIT Modified License

附加条款：

1. 本工具包含网络爬虫功能，使用时应控制请求频率（默认 10 秒/次），避免对目标服务器造成过大负担。请遵守目标网站的 robots.txt 及使用条款。
2. `output/` 目录下载的 sb3 文件为第三方用户作品，版权归原作者所有。**严禁将 output 目录下的文件公开发布或用于商业用途**，仅供本地统计分析使用。

