# encoding:utf-8
import json
import os
# import langid
from bridge.bridge import Bridge
from bridge.context import ContextType
from bridge.reply import Reply, ReplyType
from config import conf
import plugins
from plugins import *
from common.log import logger
# import replicate
from common.expired_dict import ExpiredDict
import time
import re
import requests
import random
import threading
import io
from PIL import Image
from channel.wechatnt.nt_run import *

def change_work_mode(content):
    curdir = os.path.dirname(__file__)
    config_path = os.path.join(curdir, "config.json")
    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)
    for item in config:
        item['work_mode'] = content  # 将work_mode的值修改为1-3
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=4)
    return "微信群聊模式已改变。"
def send_message_synv(cmsg):
    other_user_nickname = cmsg.other_user_nickname
    from_wxid = cmsg.from_user_id
    from_wxid_nickname = cmsg.from_user_nickname
    room_wxid = cmsg.other_user_id
    content = cmsg.content
    my_wxid=wechatnt.get_self_info()["wxid"]

    curdir = os.path.dirname(__file__)
    config_path = os.path.join(curdir, "config.json")
    content = f"{other_user_nickname}-{from_wxid_nickname}:\n----------\n{content}\n"
    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)

    if from_wxid != my_wxid:
        for group in config:
            # 管理员模式 只转发管理员信息。
            if group["work_mode"] == 1:
                if group["room_wxid"] == room_wxid:
                    if from_wxid in group["admin_wxid"]:
                        for member in group["member_list"]:
                            time.sleep(random.randint(0, 5))
                            wechatnt.send_text(member, content)

                elif room_wxid in group["member_list"]:
                    if from_wxid in group["admin_wxid"]:
                        for member in group["member_list"]:
                            if member != room_wxid:
                                time.sleep(random.randint(0, 5))
                                wechatnt.send_text(member, content)

                        time.sleep(random.randint(0, 5))
                        wechatnt.send_text(group["room_wxid"], content)


            # 单向模式 只是主群发送到其他群副群。
            elif group["work_mode"] == 2:

                if group["room_wxid"] == room_wxid:
                    for member in group["member_list"]:
                        time.sleep(random.randint(0, 5))
                        wechatnt.send_text(member, content)

            # 双向模式 主群副群双向发送。
            elif group["work_mode"] == 3:
                if group["room_wxid"] == room_wxid:
                    for member in group["member_list"]:
                        time.sleep(random.randint(0, 5))
                        wechatnt.send_text(member, content)

                elif room_wxid in group["member_list"]:
                    for member in group["member_list"]:
                        if member != room_wxid:
                            time.sleep(random.randint(0, 5))
                            wechatnt.send_text(member, content)

                    time.sleep(random.randint(0, 5))
                    wechatnt.send_text(group["room_wxid"], content)


@plugins.register(name="bridge_room", desc="转发指定群内消息", desire_priority=-999, version="0.1",
                  author="Yinzhoujun")
class Forward_Message(Plugin):
    def __init__(self):
        super().__init__()
        curdir = os.path.dirname(__file__)
        self.config_path = os.path.join(curdir, "config.json")

        if not os.path.exists(self.config_path):
            logger.info('[RP] 配置文件不存在，将使用config-template.json模板')
            config_path = os.path.join(curdir, "config.json.template")
        try:

            self.handlers[Event.ON_HANDLE_CONTEXT] = self.on_handle_context
            logger.info("[bridge_room] inited")
        except Exception as e:
            if isinstance(e, FileNotFoundError):
                logger.warn(f"[bridge_room] init failed, config.json not found.")
            else:
                logger.warn("[bridge_room] init failed." + str(e))
            raise e

    def on_handle_context(self, e_context: EventContext):

        if e_context['context'].type not in [ContextType.TEXT]:
            return

        e_context.action = EventAction.CONTINUE  # 事件继续，交付给下个插件或默认逻辑



    def get_help_text(self, verbose=False, **kwargs):
        help_text = "利用bot桥接群聊\n实现多群信息互通，跨群梦幻联动\n"
        if not verbose:
            return help_text

        help_text = "插件需由管理员开启\n----\n在插件目录下的config.json\n需要配置如下信息\nadmin_wxid代表管理员的ID\nroom_wxid代表主群ID\nmember_list代表副群ID\n注：副群可以填写多个ID\n----------------\n触发口令：\n#桥接模式 管理员\n此模式只有管理员的消息在主群和副群互通\n\n#桥接模式 单向\n此模式将同步主群所有群员消息到副群，副群的消息无法同步到主群\n\n#桥接模式 双向\n此模式主群和副群所有群员消息可以互通，都可以实现跨群交流"
        return help_text
