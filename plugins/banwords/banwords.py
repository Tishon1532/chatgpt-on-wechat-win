# encoding:utf-8

import json
import os

import plugins
from bridge.context import ContextType
from bridge.reply import Reply, ReplyType
from common.log import logger
from plugins import *

from .lib.WordsSearch import WordsSearch


@plugins.register(
    name="Banwords",
    desire_priority=998,
    hidden=True,
    desc="判断消息中是否有敏感词、决定是否回复。",
    version="1.0",
    author="Francis",
)
class Banwords(Plugin):
    def __init__(self):
        super().__init__()
        try:
            # load config
            curdir = os.path.dirname(__file__)
            self.config_path = os.path.join(os.path.dirname(__file__), "config.json")
            with open(self.config_path, 'r', encoding='utf-8') as f:
                    conf = json.load(f)

            self.searchr = WordsSearch()
            self.action = conf["action"]
            banwords_path = os.path.join(curdir, "banwords.txt")
            with open(banwords_path, "r", encoding="utf-8") as f:
                words = []
                for line in f:
                    word = line.strip()
                    if word:
                        words.append(word)
            self.searchr.SetKeywords(words)
            self.handlers[Event.ON_HANDLE_CONTEXT] = self.on_handle_context
            if conf.get("reply_filter", True):
                self.handlers[Event.ON_DECORATE_REPLY] = self.on_decorate_reply
                self.reply_action = conf.get("reply_action", "ignore")
            self.conf = conf
            logger.info("[Banwords] inited")
        except Exception as e:
            logger.warn("[Banwords] init failed.")
            raise e

    def on_handle_context(self, e_context: EventContext):
        if e_context["context"].type not in [
            ContextType.TEXT,
            ContextType.IMAGE_CREATE,
        ]:
            return
        context = e_context['context']
        user_id = e_context['context']['msg'].from_user_id
        content = e_context["context"].content
        isgroup = context.get("isgroup", False)
        user_nickname = e_context['context']['msg'].actual_user_nickname if isgroup else e_context['context']['msg'].from_user_nickname
        logger.debug("[Banwords] on_handle_context. content: %s" % content)
        users = self.conf.get("users", {})
        user_record = users.get(str(user_id), {"nickname": user_nickname, "violations": 0})
        if user_record and user_record["violations"] >= 3:
            reply = Reply(ReplyType.ERROR, "您已被拉黑")
            e_context["reply"] = reply
            e_context.action = EventAction.BREAK_PASS
        if self.action == "ignore":
            f = self.searchr.FindFirst(content)
            if self.action == "ignore":
                f = self.searchr.FindFirst(content)
                if f:
                    logger.info("[Banwords] %s in message" % f["Keyword"])
                    e_context.action = EventAction.BREAK_PASS
                    return
        elif self.action == "replace":
            if self.searchr.ContainsAny(content):
                user_record["violations"] += 1
                users[str(user_id)] = user_record
                self.conf["users"] = users  # 确保用户记录被更新到conf中
                # 写回配置文件
                if user_record["violations"] >= 3:
                    # 用户违规次数超过3次，则拉黑
                    reply = Reply(ReplyType.ERROR, "您已被拉黑")
                    e_context["reply"] = reply
                    e_context.action = EventAction.BREAK_PASS
                else:
                    try:
                        logger.info("[Banwords] Writing to config_path: %s" % self.config_path)
                        with open(self.config_path, "w", encoding="utf-8") as f:
                            json.dump(self.conf, f, indent=4,ensure_ascii=False)
                    except Exception as e:
                        logger.error("[Banwords] Error occurred: %s" % str(e))
                    reply = Reply(ReplyType.INFO, "发言中包含敏感词\n累计违规三次将自动拉入黑名单")
                    e_context["reply"] = reply
                    e_context.action = EventAction.BREAK_PASS
                    return

    def on_decorate_reply(self, e_context: EventContext):
        if e_context["reply"].type not in [ReplyType.TEXT]:
            return

        reply = e_context["reply"]
        content = reply.content
        if self.reply_action == "ignore":
            f = self.searchr.FindFirst(content)
            if f:
                logger.info("[Banwords] %s in reply" % f["Keyword"])
                e_context["reply"] = None
                e_context.action = EventAction.BREAK_PASS
                return
        elif self.reply_action == "replace":
            if self.searchr.ContainsAny(content):
                reply = Reply(ReplyType.TEXT, "已替换回复中的敏感词: \n" + self.searchr.Replace(content))
                e_context["reply"] = reply
                e_context.action = EventAction.CONTINUE
                return

    def get_help_text(self, **kwargs):
        return "过滤消息中的敏感词,拉黑多次发送的用户。"
