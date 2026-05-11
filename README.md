# Renpy api use

这是一个使用 DeepSeek API 的 Ren'Py 引入式代码块，能与AI交流（能实现日常交流和历史消息同步）

## 配置 API 密钥

1. 注册 [DeepSeek 开放平台](https://platform.deepseek.com/) 获取 API Key。
2. 在 `game/` 文件夹下复制 `deepseek_config.example.json` 并重命名为 `deepseek_config.json`。
3. 将你的 API Key 填入 `deepseek_config.json` 中。
4. 运行游戏即可使用 AI 对话功能。

### 其他
1.目前仍在优化中，打算之后引入多个AI模型
2.目前仅支持聊天功能，为游戏内部玩法设定
