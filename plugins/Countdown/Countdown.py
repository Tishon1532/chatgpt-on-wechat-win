# encoding:utf-8
import re

import plugins
from plugins.Countdown.utils import *
from bridge.context import ContextType
from bridge.reply import Reply, ReplyType
from common.log import logger
from plugins import *
from datetime import datetime, timedelta


def format_day_to_y_m_d(start_date, end_date):
    years = end_date.year - start_date.year
    months = end_date.month - start_date.month
    days = end_date.day - start_date.day

    if days < 0:  # 如果天数小于零，表示还不到这个月
        months -= 1
        # 计算上一个月有多少天，并加入当前天数
        prev_month = (end_date.replace(day=1) - timedelta(days=1)).day
        days += prev_month

    if months < 0:  # 如果月份小于零，表示还不到这一年
        years -= 1
        months += 12

    result = ""
    if years == 0 and months == 0:
        result = f"{abs(days)}"  # 确保只有天时不输出多余字符
    elif years == 0:
        result = f"{abs(months)}个月{abs(days)}"
    else:
        result = f"{abs(years)}年{abs(months)}个月{abs(days)}"
    return result
@plugins.register(
    name="Countdown",
    desire_priority=100,
    namecn="Countdown",
    desc="纪念日，节假日倒计时，可搭配timetask",
    version="0.7",
    author="Francis",
)
class Countdown(Plugin):
    command_prefix = ""

    def __init__(self):
        super().__init__()
        self.handlers[Event.ON_HANDLE_CONTEXT] = self.on_handle_context
        logger.info("[Countdown] inited")
        self.taskManager = TaskManager()
        self.damin_id = "wwwwwwoooooooooooo" #管理员ID，需要自行修改
        #这个列表添加的日期会倒计时解说会自动更新,下一年也无需手动设置,这个列表可以自行增减
        self.default_tasks = [
            ("001", "2024-01-01", "元旦节", "距离元旦节还有x天"),
            ("002", "2024-02-14", "情人节", "距离情人节还有x天"),
            ("003", "2024-03-08", "妇女节", "距离妇女节还有x天"),
            ("004", "2024-03-11", "龙抬头", "距离龙抬头还有x天"),
            ("005", "2024-03-12", "植树节", "距离植树节还有x天"),
            ("006", "2024-03-15", "315", "距离消费者权益日还有x天"),
            ("007", "2024-04-01", "愚人节", "距离愚人节还有x天"),
            ("008", "2024-05-12", "母亲节", "距离母亲节还有x天"),
            ("009", "2024-05-20", "520", "距离520还有x天"),
            ("010", "2024-06-01", "儿童节", "距离儿童节还有x天"),
            ("011", "2024-06-16", "父亲节", "距离父亲节还有x天"),
            ("012", "2024-06-18", "618", "距离618购物节还有x天"),
            ("013", "2024-07-01", "建党节", "距离建党节还有x天"),
            ("014", "2024-08-01", "建军节", "距离建军节还有x天"),
            ("015", "2024-09-10", "教师节", "距离教师节还有x天"),
            ("016", "2024-09-18", "九一八", "距离九一八事变纪念日还有x天"),
            ("017", "2024-10-01", "国庆节", "距离国庆节还有x天"),
            ("018", "2024-11-01", "万圣节", "距离万圣节还有x天"),
            ("019", "2024-11-11", "双11", "距离双11购物节还有x天"),
            ("020", "2024-11-21", "感恩节", "距离感恩节还有x天"),
            ("020", "2024-12-12", "双12", "距离双12购物节还有x天"),
            ("021", "2024-12-13", "国家公祭日", "距离国家公祭日还有x天"),
            ("022", "2024-12-24", "平安夜", "距离平安夜还有x天"),
            ("023", "2024-12-25", "圣诞节", "距离圣诞节还有x天"),
            ("024", "2024-06-07", "高考", "距离普通高等学校招生全国统一考试还有x天")

            # 你可以根据需求增加更多节日
            ]
        self.lunar_tasks = [
            ("097", (1, 1), "春节", "距离春节还有x天"),
            ("098", (1, 10), "雨水", "距离雨水还有x天"),
            ("099", (1, 25), "惊蛰", "距离惊蛰还有x天"),
            ("100", (1, 15), "元宵节", "距离元宵节还有x天"),
            ("101", (2, 11), "春分", "距离春分还有x天"),
            ("102", (2, 26), "清明节", "距离清明节还有x天"),
            ("103", (3, 11), "谷雨", "距离谷雨还有x天"),
            ("104", (3, 27), "立夏", "距离立夏还有x天"),
            ("105", (4, 13), "小满", "距离小满还有x天"),
            ("106", (4, 29), "芒种", "距离芒种还有x天"),
            ("107", (5, 5), "端午节", "距端午节还有x天"),
            ("108", (5, 16), "夏至", "距离夏至还有x天"),
            ("109", (6, 1), "小暑", "距离小暑还有x天"),
            ("110", (6, 17), "大暑", "距离大暑还有x天"),
            ("111", (7, 4), "立秋", "距离立秋还有x天"),
            ("112", (7, 15), "中元节", "距离中元节还有x天"),
            ("113", (7, 19), "处暑", "距离处暑还有x天"),
            ("114", (8, 5), "白露", "距离白露还有x天"),
            ("115", (8, 15), "中秋节", "距离中秋节还有x天"),
            ("116", (9, 6), "寒露", "距离寒露还有x天"),
            ("117", (9, 9), "重阳节", "距离重阳节还有x天"),
            ("118", (9, 21), "霜降", "距离霜降还有x天"),
            ("119", (10, 7), "立冬", "距离立冬还有x天"),
            ("120", (10, 22), "小雪", "距离小雪还有x天"),
            ("121", (11, 6), "大雪", "距离大雪还有x天"),
            ("122", (11, 21), "冬至", "距离冬至还有x天"),
            ("123", (11, 25), "小寒", "距离小寒还有x天"),
            ("124", (12, 8), "腊八节", "距离腊八节还有x天"),
            ("125", (12, 10), "大寒", "距离大寒还有x天"),
            ("126", (12, 25), "立春", "距离立春还有x天"),
            ("128", (12, 29), "除夕", "距离除夕还有x天"),
            ("127", (7, 7), "七夕节", "距离七夕节还有x天"),
        ]
        self.taskManager.update_default_tasks(self.default_tasks, self.lunar_tasks)
        self.update_task_date_if_needed()  # 添加检查日期更新函数

    def update_task_date_if_needed(self):
        tasks = self.taskManager.readTask()
        today = datetime.today().date()
        is_updated = False

        for task_id, task_info in tasks.items():
            # 检查是否在default_tasks中
            if any(task_id == default_task[0] for default_task in self.default_tasks):
                task_date = datetime.strptime(task_info[1], "%Y-%m-%d").date()
                if task_date < today:
                    task_date = task_date.replace(year=today.year + 1)
                    updated_task = (task_info[0], task_date.strftime("%Y-%m-%d"), task_info[2], task_info[3])
                    tasks[task_id] = updated_task
                    is_updated = True
            # 检查是否在lunar_tasks中
            elif any(task_id == lunar_task[0] for lunar_task in self.lunar_tasks):
                lunar_date_tuple = next(lunar_task[1] for lunar_task in self.lunar_tasks if lunar_task[0] == task_id)
                solar_date = self.taskManager.lunar_to_solar(today.year, *lunar_date_tuple)
                if solar_date < today:
                    solar_date = self.taskManager.lunar_to_solar(today.year + 1, *lunar_date_tuple)
                updated_task = (task_info[0], solar_date.strftime("%Y-%m-%d"), task_info[2], task_info[3])
                tasks[task_id] = updated_task
                is_updated = True

        if is_updated:
            JsonOP().saveJson(tasks)  # 确保保存更新后的任务
    def update_default_tasks(self, default_tasks, lunar_tasks):
        current_year = datetime.now().year
        updated_tasks = []
        for task_id, date_str, remark, message in default_tasks:
            date_obj = datetime.strptime(date_str, "%Y-%m-%d")
            if date_obj < datetime.now():
                date_obj = date_obj.replace(year=current_year + 1)
            new_date_str = date_obj.strftime("%Y-%m-%d")
            updated_tasks.append((task_id, new_date_str, remark, message))

        task_dict = self.readTask()
        for task_id, date_str, remark, message in updated_tasks:
            if task_id not in task_dict:
                task_info = (task_id, date_str, remark, message)
                task_model = Model(task_info, use_random_id=False)
                self.addTask(task_model)

        for task_id, (lunar_month, lunar_day), remark, message in lunar_tasks:
            solar_date = self.lunar_to_solar(current_year, lunar_month, lunar_day)
            if solar_date < date.today():
                solar_date = self.lunar_to_solar(current_year + 1, lunar_month, lunar_day)
            new_date_str = solar_date.strftime("%Y-%m-%d")
            if task_id not in task_dict:
                task_info = (task_id, new_date_str, remark, message)
                task_model = Model(task_info, use_random_id=False)
                self.addTask(task_model)
    def on_handle_context(self, e_context: EventContext):
            if e_context["context"].type not in [ContextType.TEXT]:
                return
            content = e_context["context"].content
            _user_id = e_context['context']['msg'].from_user_id
            logger.debug("[Countdown] on_handle_context. content: %s" % content)

            if content.startswith("run")  :
                self.runTask(content, e_context)
            elif content.startswith("add"):
                if _user_id != self.damin_id:
                    reply = Reply(type=ReplyType.TEXT, content="管理员功能，您无权添加")
                    e_context["reply"] = reply
                    e_context.action = EventAction.BREAK_PASS
                else:
                    self.addTask(content, e_context)
            elif content.startswith("rm"):
                if _user_id != self.damin_id:
                    reply = Reply(type=ReplyType.TEXT, content="管理员功能，您无权删除")
                    e_context["reply"] = reply
                    e_context.action = EventAction.BREAK_PASS
                else:
                    self.rmTask(content, e_context)
            elif content.startswith("ls"):
                if _user_id != self.damin_id:
                    reply = Reply(type=ReplyType.TEXT, content="管理员功能，您暂无查看权限")
                    e_context["reply"] = reply
                    e_context.action = EventAction.BREAK_PASS
                else:
                    self.lsTask(content, e_context)
            else:
                e_context.action = EventAction.CONTINUE

    def runTask(self, content, e_context: EventContext):
        # 获取任务标识，这里可能是任务编号，也可能是备注
        task_flag = content.split(" ")[1]

        task_dict = self.taskManager.readTask()

        # 使用任务标识查找任务，
        # 首先尝试使用任务标识作为编号查找任务
        if task_flag in task_dict:
            taskInfo = task_dict[task_flag]
        # 如果使用编号没有找到任务，则尝试使用任务标识作为备注查找任务
        else:
            taskInfo = self.find_task_by_remark(task_flag, task_dict)

        # 判断任务是否存在
        if taskInfo:
            self.execute_task(taskInfo, e_context)
        # 未找到任务
        else:
            reply_text = f"执行任务失败，未知任务编号或备注"
            self.reply(reply_text, e_context)

    # 定义一个函数，使用备注查找任务
    def find_task_by_remark(self, remark, task_dict):
        for taskInfo in task_dict.values():
            if taskInfo[2] == remark:
                return taskInfo
        return None

    def execute_task(self, taskInfo, e_context):
        logger.info(f"{taskInfo}")
        logger.debug(f"执行任务{taskInfo[0]}")

        dateStr = taskInfo[1]
        date = datetime.strptime(dateStr, "%Y-%m-%d").date()
        remark = taskInfo[2]
        message = taskInfo[3]

        today = datetime.today().date()
        diff = date - today
        day = diff.days

        if message != "":
            if day >= 0:
                message = message.replace("x", "{}", 1)
                reply_text = message.format(abs(day))
            else:
                start_date = datetime.strptime(taskInfo[1], "%Y-%m-%d").date()
                today = datetime.today().date()
                formatted_day = format_day_to_y_m_d(start_date, today)
                message = message.replace("还有", "已经过去了", 1)
                message = message.replace("x", "{}", 1)
                reply_text = message.format(formatted_day)
        else:
            if day >= 0:
                reply_text = f"距离目标日{dateStr}还有{day}天"
            else:
                reply_text = f"目标日{dateStr}已经过去{-day}天了"

        self.reply(reply_text, e_context)

    def addTask(self, content, e_context: EventContext):
        # 时间信息
        dateStr = ""
        # 备注内容
        remark = ""
        # 自定义消息内容
        custom_message = ""

        logger.info(content)
        wordsArray = content.split(" ")
        logger.info(wordsArray)

        if len(wordsArray) >= 2:
            dateStr = wordsArray[1]
            dateStr = self.convert_date_format(dateStr)
        if len(wordsArray) >= 3:
            remark = wordsArray[2]

        if len(wordsArray) == 4:
            custom_message = wordsArray[3]

        if len(wordsArray) > 4:
            reply_text = "指令格式有误，请检查\n#help Countdown查看帮助信息"
            self.reply(reply_text, e_context)
            return

        taskInfo = ("", dateStr, remark, custom_message)
        try:
            taskModel = Model(taskInfo)
            taskInfo = self.taskManager.addTask(taskModel)
            reply_text = f"添加任务成功\n" + self.outputTask({taskInfo})

        except:
            logger.info(dateStr)
            reply_text = "指令格式有误，请检查\n#help Countdown查看帮助信息"

        self.reply(reply_text, e_context)

    def convert_date_format(self, date_str):
        # 尝试匹配两种不同的日期格式
        match1 = re.match(r'^\d{4}-\d{1,2}-\d{1,2}$', date_str)
        match2 = re.match(r'^\d{4}\.\d{1,2}\.\d{1,2}$', date_str)
        if match1:
            return date_str  # "YYYY-MM-DD" 格式，不需要转换
        elif match2:
            return date_str.replace('.', '-')  # 将 "YYYY.MM.DD" 格式转换为 "YYYY-MM-DD"
        elif re.match(r'^\d{4}年\d{1,2}月\d{1,2}日$', date_str):
            return re.sub(r'[年月日]', '-', date_str).strip('-')  # 将 "YYYY年MM月DD日" 格式转换为 "YYYY-MM-DD"
        else:
            # raise ValueError("日期格式不正确，请使用 'YYYY-MM-DD' 或 'YYYY.MM.DD' 格式")
            return None
    def rmTask(self, content, e_context: EventContext):
        taskId = content.split(" ")[1]

        taskInfo = self.taskManager.rmTask(taskId)
        if taskInfo:
            reply_text = f"删除任务成功\n"
        else:
            reply_text = f"删除任务失败，未知任务编号{taskId}\n"

        self.reply(reply_text, e_context)

    def lsTask(self, content, e_context: EventContext):
        task_dict = self.taskManager.readTask()
        logger.info(task_dict)
        reply_text = "任务列表\n" + self.outputTask(task_dict.values())
        self.reply(reply_text, e_context)

    def outputTask(self, task_dict: dict):
        content = ""
        for taskinfo in task_dict:
            tmp = f"【{taskinfo[0]}】{taskinfo[1]} {taskinfo[2]} {taskinfo[3]}\n"
            content = content + tmp
        str1 = "\n使用提示\n"
        str2 = f"【添加任务】{self.command_prefix} add <时间> [备注] [消息]\n"
        str3 = f"【删除任务】{self.command_prefix} rm <任务编号>\n"
        str4 = f"【执行任务】{self.command_prefix} run <任务编号或备注>\n"
        str5 = f"【任务列表】{self.command_prefix} ls\n"
        content = content + str1 + str2 + str3 + str4 + str5
        return content

    def reply(self, reply_message, e_context: EventContext):
        reply = Reply()
        reply.type = ReplyType.TEXT
        reply.content = reply_message
        e_context["reply"] = reply
        e_context.action = EventAction.BREAK_PASS

    def get_help_text(self, verbose=False, **kwargs):
        help_text = "搭配timetask，实现倒计时，纪念日提醒"
        if not verbose:
            return help_text
        str1 = f"【添加任务】\n{self.command_prefix} add <时间> [备注] [消息]\n"
        str2 = f"   时间 必选 格式为“年-月-日”\n"
        str3 = f"   备注 可选 该任务的备注\n"
        str4 = f"   消息 可选 使用“x”占位\n"
        str5 = f"   例:{self.command_prefix} add 2023.6.7 高考 距离全国高考还有x天\n\n"
        text1 = str1 + str2 + str3 + str4 + str5

        str1 = f"【删除任务】{self.command_prefix} rm <编号>\n"
        str2 = f"   例:{self.command_prefix} rm 001\n\n"
        text2 = str1 + str2

        str1 = f"【执行任务】{self.command_prefix} run <编号>\n"
        str2 = f"   例:{self.command_prefix} run 001     run 备注\n\n"
        text3 = str1 + str2

        str1 = f"【任务列表】{self.command_prefix} ls\n"
        text4 = str1

        help_text = "Countdown倒计时插件使用帮助\n\n" + text1 + text2 + text3 + text4
        return help_text
