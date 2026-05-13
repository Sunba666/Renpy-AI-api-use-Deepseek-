# 存储玩家输入文本的变量
default player_input_text = ""

# 存放对话历史
default conversation_history = []  # 存储 {"role": "user"/"assistant", "content": "..."}

# 定义各个表情的图片（放在 images/ 目录）— 共用布局，按表情只改 zoom / ypos
transform eileen_slot(slot_y=700):
    xalign 0.5
    yalign 0.5
    xpos 1050
    ypos slot_y

image eileen neutral = At(
    Transform("images/eileen emoji/eileen_neutral.png", zoom=0.8),
    eileen_slot(600),
)

image eileen happy = At(
    Transform("images/eileen emoji/eileen_happy.png", zoom=0.4),
    eileen_slot(),
)

image eileen sad = At(
    Transform("images/eileen emoji/eileen_sad.png", zoom=0.5),
    eileen_slot(),
)

image eileen angry = At(
    Transform("images/eileen emoji/eileen_angry.png", zoom=0.5),
    eileen_slot(),
)

image eileen surprised = At(
    Transform("images/eileen emoji/eileen_surprised.png", zoom=0.5),
    eileen_slot(),
)

# 定义一个角色，使用中立表情为默认
define e = Character("艾琳", image="eileen neutral")

# DeepSeek API 与工具函数（init python）
init -1 python:
    import json
    import threading
    import os

    # DeepSeek 官方 API 地址
    DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"
    SYSTEM_PROMPT = "你是一个温柔的心理咨询师"
    MAX_CHAT_TURNS = 10
    FETCH_TIMEOUT = 30

    # 全局变量
    ai_response_text = ""
    ai_request_finished = False
    ai_request_error = ""

    # 读取 API Key（从外部配置文件）
    def load_api_key():
        config_path = os.path.join(renpy.config.gamedir, "deepseek_config.json")
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
                return config.get("api_key", "")
        except Exception:
            return ""

    def escape_renpy_text_braces(s):
        """将字符串中的花括号转义，避免 Ren'Py text 把 LaTeX 等里的 {...} 当成文本标签。"""
        if not isinstance(s, str):
            s = str(s)
        return s.replace("{", "{{").replace("}", "}}")

    # 分页函数
    def split_text_into_pages(text, max_chars_per_page=400):
        if not isinstance(text, str):
            text = str(text)
        if not text:
            return ["(没有内容)"]
        pages = []
        while len(text) > max_chars_per_page:
            split_pos = text.rfind('。', 0, max_chars_per_page)
            if split_pos == -1:
                split_pos = text.rfind('，', 0, max_chars_per_page)
            if split_pos == -1:
                split_pos = max_chars_per_page
            pages.append(text[:split_pos + 1])
            text = text[split_pos + 1:]
        if text:
            pages.append(text)
        return pages

    API_KEY = load_api_key()
    if not API_KEY:
        renpy.notify("警告：找不到 deepseek_config.json 或 API Key，请创建配置文件。")

    # 情绪关键词映射表（按优先级：先匹配到的情绪生效）
    emotion_map = {
        "happy": ["开心", "高兴", "喜欢", "爱", "棒", "好", "幸福", "笑"],
        "sad": ["难过", "伤心", "哭", "遗憾", "失望", "痛苦", "孤独"],
        "angry": ["生气", "愤怒", "恨", "讨厌", "可恶", "滚", "烦"],
        "surprised": ["惊讶", "居然", "天哪", "哇", "真的吗", "什么"],
    }
    default_emotion = "neutral"
    _EMOTION_ORDER = ("happy", "sad", "angry", "surprised")

    def analyze_emotion(text):
        if not text:
            return default_emotion
        for emotion in _EMOTION_ORDER:
            for kw in emotion_map[emotion]:
                if kw in text:
                    return emotion
        return default_emotion

    def _trim_messages(messages):
        """限制历史长度，防止 token 过多（保留最近 MAX_CHAT_TURNS 轮对话）。"""
        max_msgs = 1 + MAX_CHAT_TURNS * 2
        if len(messages) <= max_msgs:
            return messages
        if messages and messages[0]["role"] == "system":
            return messages[:1] + messages[-(MAX_CHAT_TURNS * 2):]
        return messages[-(MAX_CHAT_TURNS * 2):]

    def ai_request_thread(user_message):
        """仅在线程内做网络请求；对 store 与 UI 相关全局变量的写入一律回到主线程。"""
        err = None
        ai_content = None
        try:
            messages = [{"role": "system", "content": SYSTEM_PROMPT}]
            messages.extend(list(store.conversation_history))
            messages.append({"role": "user", "content": user_message})
            messages = _trim_messages(messages)

            data = {
                "model": "deepseek-chat",
                "messages": messages,
                "temperature": 0.75,
                "max_tokens": 1000,
            }
            headers = {
                "Content-Type": "application/json",
                "Authorization": "Bearer " + API_KEY,
            }
            response = renpy.fetch(
                DEEPSEEK_API_URL,
                json=data,
                headers=headers,
                timeout=FETCH_TIMEOUT,
                result="json",
            )
            ai_content = response["choices"][0]["message"]["content"]
        except Exception as ex:
            err = str(ex)

        def _finish():
            global ai_response_text, ai_request_finished, ai_request_error
            if err is None:
                store.conversation_history.append({"role": "user", "content": user_message})
                store.conversation_history.append({"role": "assistant", "content": ai_content})
                ai_response_text = ai_content
                ai_request_error = ""
            else:
                ai_request_error = err
                ai_response_text = "[请求失败: {}]".format(err)
            ai_request_finished = True

        renpy.invoke_in_main_thread(_finish)

    def ask_ai_async(user_message):
        global ai_response_text, ai_request_finished, ai_request_error
        ai_response_text = ""
        ai_request_finished = False
        ai_request_error = ""
        threading.Thread(target=ai_request_thread, args=(user_message,), daemon=True).start()

    def is_ai_finished():
        return ai_request_finished

    def get_ai_response():
        return ai_response_text

# 鼠标点击输入界面
screen ai_input_screen():
    frame:
        xalign 0.5 yalign 0.5
        xsize 600
        background "#000000dd"
        padding (20, 20)
        vbox:
            text "你想说什么？" size 28
            null height 10
            input:
                value VariableInputValue("player_input_text")
            textbutton "发送" action Return(True)

# 游戏内对话
label ai_chat:
    if not conversation_history:
        e neutral "现在是连续聊天模式，输入“再见”结束。"
    $ chatting = True
    while chatting:
        $ player_input = renpy.input("和你说话：", length=200).strip()
        if player_input == "":
            e neutral "你什么也没说。"
        elif player_input == "再见":
            e neutral "那下次再聊吧。"
            $ chatting = False
        else:
            show screen ai_thinking_screen
            $ ask_ai_async(player_input)
            while not is_ai_finished():
                $ renpy.pause(0.1)
            hide screen ai_thinking_screen
            $ ai_text = get_ai_response()
            $ emo = analyze_emotion(ai_text)
            $ renpy.show("eileen " + emo)
            call show_paged_text(ai_text)
            $ renpy.pause(0.2)
    return

# 分页显示长文本
label show_paged_text(ai_reply):
    $ pages = split_text_into_pages(escape_renpy_text_braces(ai_reply))
    $ idx = 0
    while idx < len(pages):
        $ page_text = pages[idx]
        call screen paged_text_screen(page_text, idx + 1, len(pages))
        if _return:
            $ idx += 1
        else:
            $ idx = len(pages)
    return

screen paged_text_screen(t, current, total):
    frame:
        xalign 0.15
        yalign 1.0
        yoffset -50
        xsize 800
        background "#00000056"
        padding (20, 20)
        vbox:
            text t size 26 color "#ffffff" xmaximum 760 substitute False
            null height 20
            hbox:
                xalign 1.0
                spacing 20
                if current < total:
                    textbutton "下一页" action Return(True)
                else:
                    textbutton "结束" action Return(False)

screen ai_thinking_screen:
    zorder 100
    vbox:
        xalign 0.5
        yalign 0.5
        text "AI 正在思考..." size 30 color "#FFFFFF" outlines [(1, "#000000", 0, 0)]
        text "." size 40 color "#FFD966" at thinking_animation

transform thinking_animation:
    alpha 1.0
    linear 0.5 alpha 0.2
    linear 0.5 alpha 1.0
    repeat
