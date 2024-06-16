# encoding:utf-8

import plugins
from bridge import context
from bridge.context import ContextType
from bridge.reply import Reply, ReplyType
from channel.chat_message import ChatMessage
from common.log import logger
from plugins import *
from config import conf
def open_admin_mode():
    curdir = os.path.dirname(__file__)
    config_path = os.path.join(curdir, "config.json")
    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)
    config['switch'] = True
    with open(config_path, 'w',encoding="utf-8") as f:
        json.dump(config, f,ensure_ascii=False, indent=4)
    return "管理员模式已开启\n仅管理员可以触发bot"
def close_admin_mode():
    curdir = os.path.dirname(__file__)
    config_path = os.path.join(curdir, "config.json")
    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)
    config['switch'] = False  # 将work_mode的值修改为5
    with open(config_path, 'w',encoding="utf-8") as f:
        json.dump(config, f,ensure_ascii=False, indent=4)
    return "管理员模式已关闭，所有人可触发bot"

def _set_reply_text(content: str, e_context: EventContext, level: ReplyType = ReplyType.ERROR):
    reply = Reply(level, content)
    e_context["reply"] = reply
    e_context.action = EventAction.BREAK_PASS
@plugins.register(
    name="admin",
    desire_priority=999,
    hidden=True,
    desc="管理员模式",
    version="0.1",
    author="francis",
)
class Admin(Plugin):

    def __init__(self):
        super().__init__()
        try:
            self.handlers[Event.ON_HANDLE_CONTEXT] = self.on_handle_context
        except Exception as e:
            logger.error(f"[Admin]初始化异常：{e}")
            raise "[Admin] init failed, ignore "

    def on_handle_context(self, e_context: EventContext):
        if e_context["context"].type not in [
            ContextType.TEXT,ContextType.IMAGE_CREATE,
            ContextType.PATPAT,ContextType.QUOTE
        ]:
            return
        user_id = e_context['context']['msg'].from_user_id
        context = e_context["context"]
        isgroup = context.get("isgroup", False)
        content = context.content
        curdir = os.path.dirname(__file__)
        config_path = os.path.join(curdir, "config.json")
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
            # print(config)
        admin_id = config.get("admin_id", )
        switch = config.get("switch", False)

        if switch:#管理员开启，只回复管理员信息
            if user_id == admin_id:
                e_context.action = EventAction.CONTINUE
            else:
                logger.info(f"[Admin] user_id：{user_id}  已被屏蔽")
                e_context.action = EventAction.BREAK_PASS
       
        else:
            """丢到下一步"""
            e_context.action = EventAction.CONTINUE

    def get_help_text(self, **kwargs):
        help_text = "开启管理员模式，其他人无权提问"
        return help_text


