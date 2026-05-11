# 存储玩家输入文本的变量
default player_input_text = ""

#存放对话历史
default conversation_history = []   # 存储 {"role": "user"/"assistant", "content": "..."}

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

        """按最大字符数切分文本，尽量在句号、逗号处断开"""
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
        "【系统】现在是连续对话模式，你可以一直聊，输入“再见”结束。"
    $ chatting = True
    while chatting:
        $ player_input = renpy.input("和你说话：", length=200)
        $ player_input = player_input.strip()
        if player_input == "":
            "你什么也没说。"
        elif player_input == "再见":
            "你结束了对话。"
            $ chatting = False
        else:
            show screen ai_thinking_screen
            $ ask_ai_async(player_input)
            while not is_ai_finished():
                $ renpy.pause(0.1)
            hide screen ai_thinking_screen
            $ ai_response_text = get_ai_response()
            call show_paged_text(ai_response_text)
            $ renpy.pause(0.3)
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
        xalign 0.5 yalign 0.5
        xsize 800
        background "#000000dd"
        padding (20, 20)
        vbox:
            text "[t]" size 26 color "#fff" xmaximum 760
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



