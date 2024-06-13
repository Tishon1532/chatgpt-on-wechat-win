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
            ContextType.TEXT,
            ContextType.JOIN_GROUP,
            ContextType.PATPAT,
            ContextType.QUOTE
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
        if content == "帮助" or content == "功能":
            # 完整的功能指南
            features_guide = (
"""🌟 🌟🌟功能列表 🌟🌟🌟
--------------------------------
“早报”：每天更新国内外大事
“签到”：每日获取积分
“摸鱼日历”：摸鱼专用
“我的积分”：查看积分余额
“肯德基”：疯狂星期四文案
“看手相”：凭手相推论运势
“看面相”：凭面相推论运势
“写文案”：生成小红书文案
“地震查询”：查询地震信息
“开启OCR”：提取图片文字
“总结群聊”：总结当日聊天
“群聊统计”：看群聊榜单信息
“github热榜”：查看热门项目
“周报生成器”：快速撰写周报
“搜索+内容”：调用AI搜索
“画+提示词”：调用AI绘画
“写歌+描述”：调用AI写歌
“滤镜+美妆”：调用AI P图
“滤镜+动漫”：调用AI动漫化
“配音+文本”：调用AI配音
“角色名”：查看配音角色
“关键词+图片”：搜索图片
“点歌+歌名”：QQ音乐点歌
“城市+天气”：查该城市天气
“抖音+内容”：搜索相关视频
“城市+地铁”：查当地地铁图
“解析+链接”：解析短视频
“找+资源名”：搜索影视资源
“下载+链接”：下载外链资源
“快递+单号”：查询快递信息
“题库搜索+内容”：查题
“律师+内容”：法律咨询
“微博搜索+内容”：搜微博
“写文书+描述”：起诉状生成
“短链+url”:长链接转短链接
“ping+域名   ping+IP”
“机票查询示例：\n 2024.2.24 北京到上海的机票”
“火车票查询示例：\n 2024.2.24 北京到上海的火车票”
------------------------------
转发微信文章会自动总结
发送文件会自动上传总结
转发视频号会自动解析链接
@AI 发淘宝链接查历史价格
拍一拍 可以获得美团优惠券
-------------------------------
@ai +内容：调用kimi对话
ai +内容：调用kimi对话
gpt +内容：调用GPT4对话
-------------------------------
还有更多隐藏功能等你探索
"""
                    )
            _set_reply_text(features_guide, e_context, level=ReplyType.TEXT)
            return
        else:
            """丢到下一步"""
            e_context.action = EventAction.CONTINUE

    def get_help_text(self, **kwargs):
        help_text = "开启管理员模式，其他人无权提问"
        return help_text


