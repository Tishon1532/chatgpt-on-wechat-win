# 简介

> **bridge_room**，<u>为[WeChat-AIChatbot-WinOnly](https://github.com/chazzjimel/WeChat-AIChatbot-WinOnly)</u>的ntchat通道版插件 微信群有500人上限的限制，建立多个群的话又有信息无法互通的不便，通过本插件自动将消息转发到同一个同步组内的所有群，消除这一不便性，间接达成扩大群成员数的目的。
为了丰富使用场景，新增多种转发模式。


## 特别提醒
> 使用机器人有被封禁微信账号的风险，请尽量使用小号来运行，本人对因使用本插件造成账号封禁带来的损失不负责任。

# **详细功能列表：**

- [x] 桥接模式 管理员 ：此模式只有管理员的消息在主群和副群互通
- [x] 桥接模式 单向   ：此模式将同步主群所有群员消息到副群，副群的消息不会同步到主群
- [x] 桥接模式 双向   ：此模式主群和副群所有群员消息可以互通，双方可以实现跨群交流

![1](https://github.com/Tishon1532/bridge_room/blob/main/img/1.jpg?raw=true)


>
# config.json文件内容示例
```bash
'''
{
  "admin_wxid": ["YOUR_WXID", "OTHER_WXID"]                                  # 填入上面管理员的id，可以是自己也可以是其他人(被转发者），在模式管理员时，只有这个wxid账号发的内容会自动转发
  "room_wxid": "3450948946@chatroom",                         # romm_wxid代表主群的ID
  "member_list": [
            "4497090431@chatroom",
            "3463120559@chatroom"
        ]                                                     # member_list代表副群的群id，可以是多个
  "work_mode": 1                                              # 工作模式，即1代表管理员、2代表单向、3代表双向
 }
```
>**如何找群id** 在主项目运行日志里：'room_wxid'即代表每个群的ID。把这个ID填在config.json的room_wxid就代表是主群，填在member_list就代表是副群。

## 实现原理
> 因为要实现监听所有群的任何消息和发送内容，依靠插件的优先级实现不了，本插件实现原理为修改原框架，写成插件目的只是为了方便使用godcmd开启和关闭。通过识别插件的开关来判断是否开启框架的调用,为了尽可能减少因修改框架对每个人装的各种各样的其他插件的影响，目前本项目只提供文字消息类转发。

**## ntchat_channel和Godcmd 修改：**

ntchat_channel需要在def handle_group(self, cmsg: ChatMessage)下修改代码。完整代码如下：

```bash
    def handle_group(self, cmsg: ChatMessage):
        root_dir=os.path.abspath(os.path.join(os.path.dirname(__file__),"..\.."))
        base_dir = root_dir+'\plugins\plugins.json'
        with open(base_dir, "r", encoding="utf-8") as f:
            config = json.load(f)
            if config["plugins"]["bridge_room"]["enabled"] == False:
                pass
            else:
                from plugins.bridge_room.main import send_message_synv
                try:
                    send_message_synv(cmsg)
                except Exception as e:
                    print(e)
        if cmsg.ctype == ContextType.VOICE:
            if not conf().get("speech_recognition"):
                return
            logger.debug("[WX]receive voice for group msg: {}".format(cmsg.content))
        elif cmsg.ctype == ContextType.IMAGE:
            logger.debug("[WX]receive image for group msg: {}".format(cmsg.content))
        elif cmsg.ctype in [ContextType.JOIN_GROUP, ContextType.PATPAT]:
            logger.debug("[WX]receive note msg: {}".format(cmsg.content))
        elif cmsg.ctype == ContextType.TEXT:
            pass
        else:
            logger.debug("[WX]receive group msg: {}".format(cmsg.content))
        context = self._compose_context(cmsg.ctype, cmsg.content, isgroup=True, msg=cmsg)
        if context:
            self.produce(context)
```

Godcmd需要添加功能开启的口令：
```bash
ADMIN_COMMANDS = {
    "bridge_room": {
        "alias": ["bridge_room", "桥接模式"],
        "args": ["参数名"],
        "desc": "群聊通道调试",
    }
}
```
Godcmd需要添加功能切换的口令：
```bash
elif any(cmd in info["alias"] for info in ADMIN_COMMANDS.values()):
                if isadmin:
```

                        elif cmd == "bridge_room":
                            from plugins.bridge_room.main import change_work_mode
                            if args[0] == "管理员":
                                # 管理员模式，work_mode置为1
                                ok, result = True, change_work_mode(1)

                            elif args[0] == "单向":
                                # work_mode置为2
                                ok, result = True, change_work_mode(2)
                            elif args[0] == "双向":
                                # work_mode置为3
                                ok, result = True, change_work_mode(3)
```
```
