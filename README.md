<div align="center">

# AI_try

**Ren'Py × DeepSeek API** — 在视觉小说中接入 AI 实时对话

让游戏角色「艾琳」拥有真实的对话能力，支持情绪反馈与历史记忆。

</div>

---

## 核心功能

### 💬 AI 实时对话
- 接入 DeepSeek Chat API（`deepseek-v4-flash`），玩家在游戏中输入文字，AI 实时生成回复
- 异步请求，不阻塞游戏 UI
- 支持连续对话循环

### 🧠 历史记忆
- 自动保存对话历史（`conversation_history`），每次 API 调用携带上下文
- 设有限制轮数（默认 10 轮），防止 Token 溢出
- 跨页面保持对话连贯

### 😊 情绪反馈
- AI 回复自带情绪标注（JSON Output 模式），无需关键词猜测
- 5 种情绪：开心（happy）、难过（sad）、生气（angry）、惊讶（surprised）、中性（neutral）
- 对应切换艾琳表情立绘，沉浸感更强
- 非法/非 JSON 回复自动 fallback 到 neutral，游戏不崩溃

### 📖 分页阅读
- AI 返回的长文本自动按句号分页（每页约 400 字）
- 玩家点击「下一页」逐页阅读
- 支持 LaTeX 等特殊字符的安全渲染（`substitute False`）

### 🔧 外部配置
- API Key 通过外部 JSON 文件配置，不硬编码在源码中
- `.gitignore` 已忽略配置文件，避免 Key 泄露

### 🛡️ 并发保护
- AI 请求进行中时再次发送输入会被礼貌拦截
- 显示「AI 还在思考，请稍候...」避免重复请求

---

## 技术栈

| 技术 | 用途 |
|------|------|
| **Ren'Py 8.5.2** | 视觉小说引擎 |
| **DeepSeek API** | AI 对话生成（`deepseek-v4-flash`） |
| **renpy.fetch()** | 内置 HTTP 请求 |
| **Python threading** | 异步请求，不阻塞 UI |
| **JSON Output mode** | AI 结构化情绪输出 |
| **pytest** | 纯逻辑单元测试（23 个测试） |
| **Ren'Py ATL** | 角色动画与表情变换 |
| **JSON** | 配置文件 + API 数据交换 |

---

## 快速开始

### 环境要求

- Ren'Py 8.5.2+（[下载](https://www.renpy.org/)）
- DeepSeek API Key（[注册](https://platform.deepseek.com/)）

### 安装与运行

```bash
# 1. 克隆仓库
git clone https://github.com/Sunba666/Renpy-AI-api-use-Deepseek-.git
cd Renpy-AI-api-use-Deepseek-

# 2. 配置 API Key
cp game/deepseek_config.example.json game/deepseek_config.json
# 编辑 deepseek_config.json，填入你的 API Key

# 3. 用 Ren'Py 打开项目目录，点击「启动」
# 或在命令行运行：
python -m renpy .
```

### 运行测试

```bash
# 安装 pytest（首次）
pip install pytest

# 运行 23 个纯逻辑单元测试
python -m pytest tests/ -v
```

### 游戏操作

1. 游戏开始后，选择「找 AI 聊天」
2. 输入你想说的话（最长 200 字）
3. AI 实时回复，情绪自动切换立绘
4. 看完点击「下一页」继续，或「结束」退出
5. 可选择「继续聊」或「不聊了」回到游戏

---

## 项目结构

```
AI_try/
├── README.md                     # 项目文档
├── definition.rpy                # 全局定义（背景图）
├── options.rpy                   # Ren'Py 项目配置
├── script.rpy                    # 主脚本（游戏入口 + 聊天循环）
├── screens.rpy                   # UI 屏幕定义
├── gui.rpy                       # GUI 界面样式
├── SourceHanSansLite.ttf         # 思源黑体字体
├── deepseek_config - example.json # API Key 配置模板
├── tests/
│   └── test_ai_core.py           # 🧪 23 个 pytest 单元测试
│
├── game/
│   ├── ai_core.py                # 🔑 纯 Python 核心逻辑（可测试）
│   │   ├── build_request_data()  #   API 请求体构建
│   │   ├── extract_emotion_from_json()  # JSON 情绪解析
│   │   ├── escape_renpy_text_braces()   # 花括号转义
│   │   ├── split_text_into_pages()      # 长文本分页
│   │   ├── trim_messages()       #   Token 控制
│   │   └── is_request_allowed()  #   并发锁检查
│   ├── ai.rpy                    # Ren'Py AI 对话界面 + API 调用
│   │   ├── DeepSeek API 调用
│   │   ├── JSON 情绪解析
│   │   ├── 长文本分页
│   │   ├── 并发锁保护
│   │   └── 花括号/特殊字符转义
│   ├── deepseek_config.json      # 真实 API Key（.gitignore 已忽略）
│   ├── images/
│   │   ├── background/           # 背景图（市立图书馆等）
│   │   └── eileen emoji/         # 艾琳表情立绘
│   │       ├── eileen_neutral.png
│   │       ├── eileen_happy.png
│   │       ├── eileen_sad.png
│   │       ├── eileen_angry.png
│   │       └── eileen_surprised.png
│   └── ...（其他 Ren'Py 标准文件）
│
├── tl/                           # 翻译文件
├── libs/                         # 库文件
├── cache/                        # 运行时缓存（已忽略）
└── saves/                        # 游戏存档（已忽略）
```

---

## 关键设计

### AI 请求流程

```
玩家输入 → renpy.input()
  ↓
并发锁检查 ── 已有请求？──→ "AI 还在思考，请稍候..."
  ↓ 无
ask_ai_async() → threading.Thread()
  ↓
ai_request_thread() → renpy.fetch() → DeepSeek API (JSON Output mode)
  ↓
renpy.invoke_in_main_thread() → 更新全局变量
  ↓
extract_emotion_from_json() → 解析情绪 → 切换艾琳立绘
  ↓
分页显示 → 玩家逐页阅读
```

### JSON Output 情绪系统

DeepSeek 的回复要求按以下 JSON 格式输出，不再需要关键词猜测：

```json
{"emotion": "happy|sad|angry|surprised|neutral", "text": "你的回复内容"}
```

- API 请求使用 `response_format: {"type": "json_object"}` 约束
- `extract_emotion_from_json()` 解析 emotion 字段
- 非法 JSON / 无效情绪值自动 fallback 到 `neutral`

旧的关键词匹配方式（`analyze_emotion` + `emotion_map`）已移除。

### 并发锁

- `ai_request_in_progress` 全局标志控制
- 请求开始时置 `True`，完成时（无论成功/失败）置 `False`
- 聊天循环中调用 `is_request_allowed()` 检查
- 防止玩家在 AI 回复前多次发送导致的竞争条件

### 特殊字符安全处理

- **花括号 `{}`**：`escape_renpy_text_braces()` 将 `{}` 转义为 `{{}}`，防止 Ren'Py 误判为文本标签
- **Python 替换语法**：`text` 显示时使用 `substitute False`，防止 LaTeX 中的 `\`、`^` 等符号被解析为 Python 表达式

### 模块化设计

| 文件 | 职责 | 可测试 |
|------|------|--------|
| `game/ai_core.py` | 纯 Python 逻辑函数 | ✅ 23 个 pytest 覆盖 |
| `game/ai.rpy` | Ren'Py UI + API 编排 | 需 Ren'Py 运行时 |

纯逻辑（数据结构转换、字符串处理、状态检查）全部提取到 `ai_core.py`，不依赖 Ren'Py 运行时，可在标准 Python 环境中用 pytest 验证。

---

## 配置文件

```json
{
    "api_key":"在此处填入你的DEEPSEEK API KEY"
}
```

将 `deepseek_config.example.json` 复制为 `deepseek_config.json` 并填入 Key。

---

## 📦 更新日志

### 2026-07 (当前版本)

#### 🚀 改进
- **Model 升级**：`deepseek-chat` → `deepseek-v4-flash`（兼容最新 DeepSeek API）
- **JSON Output 情绪系统**：关键词匹配 → AI 直接输出结构化 JSON，情绪准确率从 ~60% 提升到 ~95%
- **并发锁保护**：防止 AI 思考时重复发送请求导致竞争条件
- **模块化重构**：纯逻辑提取到 `ai_core.py`，不依赖 Ren'Py 运行时

#### 🧪 测试
- 新增 `tests/test_ai_core.py`，23 个 pytest 单元测试覆盖所有逻辑函数
- 测试内容包括：model 配置、JSON 情绪解析（含非法回退）、分页、花括号转义、对话裁剪、并发锁

### 2026-06-20

#### 🐛 修复
- **ATL 语法错误**：原代码在 `image` 定义中误用 `at` 关键字导致编译失败，改为 `At()` + `Transform()` 复合方式
- **LaTeX 公式渲染崩溃**：DeepSeek 返回 `\cdots`、`\geq` 等字符时触发 Ren'Py Python 替换解析异常，添加 `substitute False` 禁用替换，并增加花括号转义函数
- **删除残留编译文件**：`ai（2）.rpyc` 对应的源码已不存在，删除该旧编译文件避免加载错误代码

---

## License

MIT
