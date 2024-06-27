import datetime
import json
import os
import re
import time
import xml.etree.ElementTree as ET
from bridge.context import ContextType
from channel.chat_message import ChatMessage
from channel.wechatnt.nt_run import wechatnt
from channel.wechatnt.WechatImageDecoder import WechatImageDecoder
from common.log import logger
import urllib.request

def process_payment_info(text):
    # 将文本按行分割，以便处理
    lines = text.split('\n')
    # 检查文本行数是否足够
    if len(lines) >= 3:
        # 选取前两行
        result_lines = lines[:2]
        # 检查第二行是否包含特定关键字
        if "付款方备注" in result_lines[1]:
            # 只返回前两行
            return '\n'.join(result_lines)
        elif "来自" in result_lines[1]:
            # 返回前三行
            return '\n'.join(lines[:3])
    # 如果文本行数不符合要求，返回原始文本
    return text
def get_emoji_file(xmlContent):
    root = ET.XML(xmlContent)
    emoji = root.find("emoji")
    url = emoji.get("cdnurl")
    filename = emoji.get("md5")
    if url is None or filename is None:
        path = "发送了一张本地图片"
    else:
        root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..\.."))
        # 将表情下载到emoji文件夹下
        path =  root_dir+"\\image\\"+filename
        if not os.path.exists(path):
            urllib.request.urlretrieve(url, path)
            exist = False
        else:
            exist = True

    return path

def ensure_file_ready(file_path, timeout=10, interval=0.5):
    """确保文件可读。

    :param file_path: 文件路径。
    :param timeout: 超时时间，单位为秒。
    :param interval: 检查间隔，单位为秒。
    :return: 文件是否可读。
    """
    start_time = time.time()
    while True:
        if os.path.exists(file_path) and os.access(file_path, os.R_OK):
            return True
        elif time.time() - start_time > timeout:
            return False
        else:
            time.sleep(interval)


def get_nickname(contacts, wxid):
    for contact in contacts:
        if contact['wxid'] == wxid:
            return contact['nickname']
    return None  # 如果没有找到对应的wxid，则返回None


def get_display_name_or_nickname(room_members, group_wxid, wxid):
    if group_wxid in room_members:
        for member in room_members[group_wxid]['member_list']:
            if member['wxid'] == wxid:
                return member['display_name'] if member['display_name'] else member['nickname']
    return None  # 如果没有找到对应的group_wxid或wxid，则返回None


class NtchatMessage(ChatMessage):
    def __init__(self, wechat, wechat_msg, is_group=False):
        try:
            super().__init__(wechat_msg)
            self.msg_id = wechat_msg['data'].get('from_wxid', wechat_msg['data'].get("room_wxid"))
            self.create_time = wechat_msg['data'].get("timestamp")
            self.is_group = is_group
            self.wechat = wechat

            # 获取一些可能多次使用的值
            current_dir = os.getcwd()
            login_info = self.wechat.get_login_info()
            nickname = login_info['nickname']
            user_id = login_info['wxid']

            # 从文件读取数据，并构建以 wxid 为键的字典
            with open(os.path.join(current_dir, "tmp", 'wx_contacts.json'), 'r', encoding='utf-8') as f:
                contacts = {contact['wxid']: contact['nickname'] for contact in json.load(f)}
            with open(os.path.join(current_dir, "tmp", 'wx_rooms.json'), 'r', encoding='utf-8') as f:
                rooms = {room['wxid']: room['nickname'] for room in json.load(f)}
            data = wechat_msg['data']
            self.from_user_id = data.get('from_wxid', data.get("room_wxid"))
            self.from_user_nickname = contacts.get(self.from_user_id)
            self.to_user_id = user_id
            self.to_user_nickname = nickname
            self.other_user_nickname = self.from_user_nickname
            self.other_user_id = self.from_user_id
            # print(wechat_msg)  ##重要，检查type数字类型，查看xml内容参数时用
            if wechat_msg["type"] == 11046:  # 文本消息类型
                if "gh_" in self.other_user_id :
                    self.ctype = ContextType.MP
                    self.content = data['msg']
                else:
                    self.ctype = ContextType.TEXT
                    self.content = data['msg']
            elif wechat_msg["type"] == 11047:  # 需要缓存文件的消息类型
                image_path = data.get('image').replace('\\', '/')
                if ensure_file_ready(image_path):
                    decoder = WechatImageDecoder(image_path)
                    self.ctype = ContextType.IMAGE
                    self.content = decoder.decode()
                    self._prepare_fn = lambda: None
                else:
                    logger.error(f"Image file {image_path} is not ready.")
            elif wechat_msg["type"] == 11048:  # 需要缓存文件的消息类型
                self.ctype = ContextType.VOICE
                self.content = data.get('mp3_file')
                self._prepare_fn = lambda: None
            elif wechat_msg["type"] == 11050:  #需要缓存的微信名片消息类型
                raw_msg = data['raw_msg']
                self.ctype = ContextType.CARD
                self.content = raw_msg
            elif wechat_msg["type"] == 11051:  # 需要缓存文件的消息类型
                self.ctype = ContextType.VIDEO
                self.content = data.get('video')
            elif wechat_msg["type"] == 11052:  # 需要缓存文件的消息类型---表情图片
                self.ctype = ContextType.EMOJI
                emoji_path=get_emoji_file(data["raw_msg"])
                self.content = emoji_path
                self._prepare_fn = lambda: None
                if self.is_group:
                    directory = os.path.join(os.getcwd(), "tmp")
                    file_path = os.path.join(directory, "wx_room_members.json")
                    with open(file_path, 'r', encoding='utf-8') as file:
                        room_members = json.load(file)
                    self.from_user_nickname = get_display_name_or_nickname(room_members, data.get('room_wxid'),
                                                                           self.from_user_id)
            elif wechat_msg["type"] == 11054:  # 分享链接消息类型
                xmlContent = data["raw_msg"]
                from_wxid = data["from_wxid"]
                root = ET.XML(xmlContent)
                appmsg = root.find("appmsg")
                msg = appmsg.find("des")
                type = appmsg.find("type")
                name = root.find(".//mmreader/category/name")
                name_text = name.text if name is not None else None
                if "gh_"in from_wxid and name_text != "微信支付" :
                    self.ctype = ContextType.MP_LINK #关注的公众号主动推送的文章链接类型
                    self.content = xmlContent
                elif name_text == "微信支付":
                    self.content = process_payment_info(msg.text)
                    self.ctype = ContextType.WCPAY
                else:
                    self.ctype = ContextType.LINK #用户转发分享的文章链接类型
                    self.content = xmlContent
            elif wechat_msg["type"] == 11055:  # 需要缓存文件的消息类型
                self.ctype = ContextType.FILE
                self.content = data.get('file')
            elif wechat_msg["type"] == 11056:  #小程序类型
                raw_msg = data['raw_msg']
                self.ctype = ContextType.MINIAPP
                self.content = raw_msg
            elif wechat_msg["type"] == 11058 : #系统消息类型
                if "拍了拍" in data.get('raw_msg'):
                    self.ctype = ContextType.PATPAT
                    self.content = data.get('raw_msg')
                    if self.is_group:
                        directory = os.path.join(os.getcwd(), "tmp")
                        file_path = os.path.join(directory, "wx_room_members.json")
                        with open(file_path, 'r', encoding='utf-8') as file:
                            room_members = json.load(file)
                        self.actual_user_nickname = get_display_name_or_nickname(room_members, data.get('room_wxid'),
                                                                                 self.from_user_id)
                else:
                    self.content = data.get('raw_msg')
                    if "移出了群聊" in self.content:
                        pattern = r'"(.*?)"'
                        match = re.search(pattern, data["raw_msg"])
                        if match:
                            nickname = match.group(1)
                        else:
                            nickname = "None"
                        self.content = f"{nickname} 因违反群内规则，已被踢出群聊！"
                        self.ctype = ContextType.EXIT_GROUP
                    else:
                        self.ctype = ContextType.SYSTEM
            elif wechat_msg["type"] == 11060:  #未知消息类型
                raw_msg = data['raw_msg']
                self.ctype = ContextType.SYSTEM
                self.content = raw_msg
            elif wechat_msg["type"] == 11061:  # 引用消息,视频号视频,QQ音乐,聊天记录,APP小程序,表情,微信直播,微信服务号
                xmlContent = data["raw_msg"]
                root = ET.XML(xmlContent)
                appmsg = root.find("appmsg")
                msg = appmsg.find("title")
                type = appmsg.find("type")
                if type.text == "51":    #视频号视频
                    self.content = xmlContent
                    self.ctype = ContextType.WECHAT_VIDEO
                elif type.text == "3":     #QQ音乐
                    self.content = xmlContent
                    pass
                elif type.text == "19" or type.text == "40":     #聊天记录
                    pass
                elif type.text == "36" :     #APP小程序
                    pass
                elif type.text == "8":     #表情
                    pass
                elif type.text == "63":     #微信直播
                    self.content = xmlContent
                    self.ctype = ContextType.SYSTEM
                elif type.text == "21":     #未知
                    pass
                else:
                    #引用消息类型
                    refermsg = appmsg.find("refermsg")
                    refwxid = refermsg.find("chatusr")
                    refwxid_text = refwxid.text
                    refname = refermsg.find("displayname")
                    refname_text = refname.text

                    if refermsg is not None:
                        if self.is_group:
                            directory = os.path.join(os.getcwd(), "tmp")
                            file_path = os.path.join(directory, "wx_room_members.json")
                            with open(file_path, 'r', encoding='utf-8') as file:
                                room_members = json.load(file)
                            self.actual_user_nickname = get_display_name_or_nickname(room_members, data.get('room_wxid'),
                                                                                     self.from_user_id)
                            self.content = msg.text
                            self.to_user_id = refwxid.text
                            self.ctype = ContextType.QUOTE
                            self.to_user_nickname =refname_text
                            if self.to_user_id is None:
                                self.to_user_id =self.from_user_id
                            print(
                                f"【{self.actual_user_nickname}】 ID:{self.from_user_id}  引用了 【{self.to_user_nickname}】 ID:{self.to_user_id} 的信息并回复 【{self.content}】")

                    else:
                        pass

            elif wechat_msg["type"] == 11098:    #  加入群聊
                self.ctype = ContextType.JOIN_GROUP
                self.actual_user_nickname = data['member_list'][0]['nickname']
                self.content = f"{self.actual_user_nickname}加入了群聊！"
                directory = os.path.join(os.getcwd(), "tmp")
                result = {}
                for room_wxid in rooms.keys():
                    room_members = wechatnt.get_room_members(room_wxid)
                    result[room_wxid] = room_members
                with open(os.path.join(directory, 'wx_room_members.json'), 'w', encoding='utf-8') as f:
                    json.dump(result, f, ensure_ascii=False, indent=4)
            elif wechat_msg["type"] == 11099:    #  退群通知
                self.ctype = ContextType.LEAVE_GROUP
                self.actual_user_nickname = data['member_list'][0]['nickname']
                self.content = f"{self.actual_user_nickname}退出了群聊！"

            else:
                raise NotImplementedError(
                    "Unsupported message type: Type:{} MsgType:{}".format(wechat_msg["type"], wechat_msg["type"]))

            if self.is_group:
                directory = os.path.join(os.getcwd(), "tmp")
                file_path = os.path.join(directory, "wx_room_members.json")
                with open(file_path, 'r', encoding='utf-8') as file:
                    room_members = json.load(file)
                self.other_user_nickname = rooms.get(data.get('room_wxid'))
                self.other_user_id = data.get('room_wxid')
                if self.from_user_id:
                    at_list = data.get('at_user_list', [])
                    self.is_at = user_id in at_list
                    content = data.get('msg', '')
                    pattern = f"@{re.escape(nickname)}(\u2005|\u0020)"
                    self.is_at |= bool(re.search(pattern, content))
                    self.actual_user_id = self.from_user_id
                    if not self.actual_user_nickname:
                        self.actual_user_nickname = get_display_name_or_nickname(room_members, data.get('room_wxid'),
                                                                                 self.from_user_id)

                else:
                    logger.error("群聊消息中没有找到 conversation_id 或 room_wxid")

            logger.debug(f"WechatMessage has be en successfully instantiated with message id: {self.msg_id}")
        except Exception as e:
            logger.error(f"在 WechatMessage 的初始化过程中出现错误：{e}")
            raise e
