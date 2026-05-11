# 游戏的脚本可置于此文件中。

# 声明此游戏使用的角色。颜色参数可使角色姓名着色。

define e = Character("艾琳")


# 游戏在此开始。

label start:
    "你醒来，发现自己在一个陌生的房间。"
    menu:
        "你想做什么？"
        "找 AI 聊天":
            $ continue_chat = True
            while continue_chat:
                call ai_chat   # 进入连续对话界面
                menu:
                    "还想再聊点什么吗？"
                    "是的，继续":
                        pass
                    "不聊了":
                        $ continue_chat = False
                        "你和 AI 聊完了，回到现实。"
        "四处看看":
            pass
    return
    #$ continue_chat = True
    #while continue_chat:
        #call ai_chat
        #menu:
            #"还想再聊点什么吗？"
            #"是的，继续":
                #pass
            #"不聊了":
                #$ continue_chat = False
    #"下次再见。"