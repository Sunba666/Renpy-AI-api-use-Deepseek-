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
    from ai_core import (
        DEFAULT_MODEL,
        SYSTEM_PROMPT,
        VALID_EMOTIONS,
        build_request_data,
        escape_renpy_text_braces,
        extract_emotion_from_json,
        is_request_allowed,
        split_text_into_pages,
        trim_messages,
    )

    # DeepSeek 官方 API 地址
    DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"
    MAX_CHAT_TURNS = 10
    FETCH_TIMEOUT = 30

    # 全局变量
    ai_response_text = ""
    ai_request_finished = False
    ai_request_error = ""
    ai_request_in_progress = False

    # 读取 API Key（从外部配置文件）
    def load_api_key():
        config_path = os.path.join(renpy.config.gamedir, "deepseek_config.json")
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
                return config.get("api_key", "")
        except Exception:
            return ""

    def ai_request_thread(user_message):
        """仅在线程内做网络请求；对 store 与 UI 相关全局变量的写入一律回到主线程。"""
        err = None
        ai_content = None
        try:
            messages = [{"role": "system", "content": SYSTEM_PROMPT}]
            messages.extend(list(store.conversation_history))
            messages.append({"role": "user", "content": user_message})
            messages = trim_messages(messages, MAX_CHAT_TURNS)

            data = build_request_data(
                messages=messages,
                response_format={"type": "json_object"},
            )
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
            global ai_response_text, ai_request_finished, ai_request_error, ai_request_in_progress
            if err is None:
                store.conversation_history.append({"role": "user", "content": user_message})
                store.conversation_history.append({"role": "assistant", "content": ai_content})
                ai_response_text = ai_content
                ai_request_error = ""
            else:
                ai_request_error = err
                ai_response_text = "[请求失败: {}]".format(err)
            ai_request_finished = True
            ai_request_in_progress = False

        renpy.invoke_in_main_thread(_finish)

    def ask_ai_async(user_message):
        global ai_response_text, ai_request_finished, ai_request_error, ai_request_in_progress
        ai_response_text = ""
        ai_request_finished = False
        ai_request_error = ""
        ai_request_in_progress = True
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
            if not is_request_allowed(store.ai_request_in_progress):
                e neutral "AI 还在思考，请稍候..."
            else:
                show screen ai_thinking_screen
                $ ask_ai_async(player_input)
                while not is_ai_finished():
                    $ renpy.pause(0.1)
                hide screen ai_thinking_screen
                $ ai_text = get_ai_response()
                $ emo = extract_emotion_from_json(ai_text)
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
