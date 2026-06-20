<div align="center">

# AI_try

**Ren'Py × DeepSeek API** — 在视觉小说中接入 AI 实时对话

让游戏角色「艾琳」拥有真实的对话能力，支持情绪反馈与历史记忆。

</div>

---

## 核心功能

### 💬 AI 实时对话
- 接入 DeepSeek Chat API，玩家在游戏中输入文字，AI 实时生成回复
- 异步请求，不阻塞游戏 UI
- 支持连续对话循环

### 🧠 历史记忆
- 自动保存对话历史（`conversation_history`），每次 API 调用携带上下文
- 设有限制轮数（默认 10 轮），防止 Token 溢出
- 跨页面保持对话连贯

### 😊 情绪反馈
- 自动分析 AI 回复中的情绪关键词
- 4 种情绪映射：开心（happy）、难过（sad）、生气（angry）、惊讶（surprised）
- 对应切换艾琳表情立绘，沉浸感更强

### 📖 分页阅读
- AI 返回的长文本自动按句号分页（每页约 400 字）
- 玩家点击「下一页」逐页阅读
- 支持 LaTeX 等特殊字符的安全渲染（`substitute False`）

### 🔧 外部配置
- API Key 通过外部 JSON 文件配置，不硬编码在源码中
- `.gitignore` 已忽略配置文件，避免 Key 泄露

---

## 技术栈

| 技术 | 用途 |
|------|------|
| **Ren'Py 8.5.2** | 视觉小说引擎 |
| **DeepSeek API** | AI 对话生成 |
| **renpy.fetch()** | 内置 HTTP 请求 |
| **Python threading** | 异步请求，不阻塞 UI |
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

### 游戏操作

1. 游戏开始后，选择「找 AI 聊天」
2. 输入你想说的话（最长 200 字）
3. AI 实时回复，情绪自动切换立绘
4. 看完点击「下一页」继续，或「结束」退出
5. 可以选择「继续聊」或「不聊了」回到游戏

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
│
├── game/
│   ├── ai.rpy                    # 🔑 AI 对话核心逻辑
│   │   ├── DeepSeek API 调用
│   │   ├── 情绪关键词分析
│   │   ├── 长文本分页
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
ask_ai_async() → threading.Thread()
  ↓
ai_request_thread() → renpy.fetch() → DeepSeek API
  ↓
renpy.invoke_in_main_thread() → 更新全局变量
  ↓
情绪分析 → 切换艾琳立绘
  ↓
分页显示 → 玩家逐页阅读
```

### 特殊字符安全处理

- **花括号 `{}`**：`escape_renpy_text_braces()` 将 `{}` 转义为 `{{}}`，防止 Ren'Py 误判为文本标签
- **Python 替换语法**：`text` 显示时使用 `substitute False`，防止 LaTeX 中的 `\`、`^` 等符号被解析为 Python 表达式

### 情绪映射表

| 情绪 | 触发关键词（部分） |
|------|-------------------|
| 🟢 happy | 开心、高兴、喜欢、爱、幸福 |
| 🔵 sad | 难过、伤心、哭、失望、孤独 |
| 🔴 angry | 生气、愤怒、讨厌、滚 |
| 🟡 surprised | 惊讶、天哪、哇、真的吗 |

---

## 配置文件

```json
{
    "api_key":"在此处填入你的DEEPSEEK API KEY"
}
```

将 `deepseek_config.example.json` 复制为 `deepseek_config.json` 并填入 Key。

---

## 📦 本次更新（2026-06-20）

### 🐛 修复
- **ATL 语法错误**：原代码在 `image` 定义中误用 `at` 关键字导致编译失败，改为 `At()` + `Transform()` 复合方式
- **LaTeX 公式渲染崩溃**：DeepSeek 返回 `\cdots`、`\geq` 等字符时触发 Ren'Py Python 替换解析异常，添加 `substitute False` 禁用替换，并增加花括号转义函数
- **删除残留编译文件**：`ai（2）.rpyc` 对应的源码已不存在，删除该旧编译文件避免加载错误代码

### 📝 文档
- 创建了完整的 README.md，包含核心功能、技术栈、快速开始、项目结构、关键设计说明

---

## License

MIT
