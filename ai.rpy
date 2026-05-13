# 存储玩家输入文本的变量
default player_input_text = ""

#存放对话历史
default conversation_history = []   # 存储 {"role": "user"/"assistant", "content": "..."}

# 定义各个表情的图片（放在 images/ 目录）
image eileen neutral = "images/eileen emoji/eileen_neutral.png"
image eileen neutral:
    "images/eileen emoji/eileen_neutral.png"
    zoom 0.8
    xalign 0.5
    yalign 0.5
    xpos 1050
    ypos 600

image eileen happy   = "images/eileen emoji/eileen_happy.png"
image eileen happy:
    "images/eileen emoji/eileen_happy.png"
    zoom 0.4
    xalign 0.5
    yalign 0.5
    xpos 1050
    ypos 700

image eileen sad = "images/eileen emoji/eileen_sad.png"
image eileen sad:
    "images/eileen emoji/eileen_sad.png"
    zoom 0.5
    xalign 0.5
    yalign 0.5
    xpos 1050
    ypos 700

image eileen angry = "images/eileen emoji/eileen_angry.png"
image eileen angry:
    "images/eileen emoji/eileen_angry.png"
    zoom 0.5
    xalign 0.5
    yalign 0.5
    xpos 1050
    ypos 700

image eileen surprised = "images/eileen emoji/eileen_surprised.png"
image eileen surprised:
    "images/eileen emoji/eileen emoji/eileen_surprised.png"
    zoom 0.5
    xalign 0.5
    yalign 0.5
    xpos 1050
    ypos 700

# 定义一个角色，使用中立表情为默认
define e = Character("艾琳", image="eileen neutral")

# ai_integration.rpy
init -1 python:
    import json
    import threading
    import os

    # DeepSeek 官方 API 地址
    DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"

    # 全局变量
    ai_response_text = ""
    ai_request_finished = False
    ai_request_error = ""
    
    # 用于存储对话历史（按时间顺序）
    conversation_history = []

    # 读取 API Key（从外部配置文件）
    def load_api_key():
        config_path = os.path.join(renpy.config.gamedir, "deepseek_config.json")
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
                return config.get("api_key", "")
        except Exception as e:
            return ""

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
            pages.append(text[:split_pos+1])
            text = text[split_pos+1:]
        if text:
            pages.append(text)
        return pages

    

    API_KEY = load_api_key()
    if not API_KEY:
        renpy.notify("警告：找不到 deepseek_config.json 或 API Key，请创建配置文件。")

    # 情绪关键词映射表
    emotion_map = {
        "happy": ["开心", "高兴", "喜欢", "爱", "棒", "好", "幸福", "笑"],
        "sad": ["难过", "伤心", "哭", "遗憾", "失望", "痛苦", "孤独"],
        "angry": ["生气", "愤怒", "恨", "讨厌", "可恶", "滚", "烦"],
        "surprised": ["惊讶", "居然", "天哪", "哇", "真的吗", "什么"],
    }
    default_emotion = "neutral"

    def analyze_emotion(text):
        happy_kw = ["开心", "高兴", "喜欢", "爱", "棒", "好", "幸福"]
        sad_kw = ["难过", "伤心", "哭", "遗憾", "失望", "痛苦"]
        angry_kw = ["生气", "愤怒", "恨", "讨厌", "可恶"]
        surprised_kw = ["惊讶", "居然", "天哪", "哇", "真的吗"]
        text_lower = text.lower()
        for kw in happy_kw:
            if kw in text_lower:
                return "happy"
        for kw in sad_kw:
            if kw in text_lower:
                return "sad"
        for kw in angry_kw:
            if kw in text_lower:
                return "angry"
        for kw in surprised_kw:
            if kw in text_lower:
                return "surprised"
        return "neutral"

    def ai_request_thread(user_message):
        global ai_response_text, ai_request_finished, ai_request_error
        try:
            # 把用户的新消息加入历史
            store.conversation_history.append({"role": "user", "content": user_message})

            # 构建完整的消息列表（可以加 system prompt，可选）
            messages = []

            messages.append({"role": "system", "content": "你是一个温柔的心理咨询师"}) #AI人格
            
            messages.extend(store.conversation_history)   # 直接使用全部历史

            # 可选：限制历史长度，防止 token 过多（保留最近 10 轮）
            max_turns = 10   # 轮数

            if len(messages) > max_turns * 2:
            # 保留 system 和最近的 MAX_TURNS 轮对话
                messages = messages[:1] + messages[-(max_turns * 2):] if messages[0]["role"] == "system" else messages[-max_turns * 2:]

            # 2. 构建请求体，在消息列表最开头插入系统提示词
            data = {
                "model": "deepseek-chat",
                "messages": messages,
                "temperature": 0.75,
                "max_tokens": 1000
            }
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {API_KEY}"
            }
            # 直接调用官方 API
            headers = {"Authorization": f"Bearer {API_KEY}"}
            response = renpy.fetch(
                DEEPSEEK_API_URL,
                json=data,
                headers=headers,
                timeout=30,
                result="json"
            )
            ai_content = response["choices"][0]["message"]["content"]
            ai_response_text = ai_content

            # 把 AI 的回复也加入历史
            store.conversation_history.append({"role": "assistant", "content": ai_content})
            ai_request_finished = True
        except Exception as e:
            ai_request_error = str(e)
            ai_response_text = f"[请求失败: {ai_request_error}]"
            ai_request_finished = True

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

#鼠标点击输入界面
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
    if len(conversation_history) == 0:
        e neutral "现在是连续聊天模式，输入“再见”结束。"
    $ chatting = True
    while chatting:
        $ player_input = renpy.input("和你说话：", length=200).strip()
        if player_input == "":
            e neutral "你什么也没说。"
            # 跳过本次循环，直接进入下一轮
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

#分页显示长文本
label show_paged_text(ai_reply):
    $ pages = split_text_into_pages(ai_reply)
    $ idx = 0
    while idx < len(pages):
        $ page_text = pages[idx]
        call screen paged_text_screen(page_text, idx+1, len(pages))
        # _return 是 True 表示点的是“下一页”，False 表示“结束”
        if _return:
            $ idx += 1
        else:
            # 不直接 break，而是把 idx 设到超出范围，循环自然结束
            $ idx = len(pages)
    return

screen paged_text_screen(t, current, total):
    frame:
        xalign 0.15
        yalign 1.0                 # 底部对齐
        yoffset -50                # 向上偏移50像素（可选，避免贴边）
        xsize 800
        background "#00000056"     # 半透明黑色背景，透出立绘
        padding (20, 20)
        vbox:
            text "[t]" size 26 color "#ffffff" xmaximum 760
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



