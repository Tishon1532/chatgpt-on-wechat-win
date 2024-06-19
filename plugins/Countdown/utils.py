# encoding:utf-8

from datetime import datetime, date
from common.log import logger
from lunarcalendar import Converter, Solar, Lunar
from random import randint
import os
import json


class Model(object):
    # 任务数据格式：
    # 0：任务ID
    # 1：时间信息 - 格式为：%Y-%m-%d    例如:2023-12-1
    # 2：备注内容
    # 3：自定义消息内容 - 使用“x”占位，如“距离考试还有x天”
    def __init__(self, taskInfo, use_random_id=True):
        super().__init__()

        # ID - 根据情况生成任务ID
        if use_random_id:
            self.taskId = self.get_short_id()
        else:
            self.taskId = taskInfo[0]

        # 时间信息
        timeValue = taskInfo[1]
        try:
            # 判断时间格式是否正确
            datetime.strptime(timeValue, "%Y-%m-%d")
            self.dateStr = timeValue
            logger.debug(timeValue)
        except:
            logger.info("时间格式错误")
            raise ValueError("时间格式错误")

        # 消息内容
        self.custom_message = taskInfo[2]

        # 备注内容
        self.remark = taskInfo[3]

    # 生成随机任务ID
    def get_short_id(self):
        short_id = randint(100, 999)

        # 检查ID是否重复
        tasks = JsonOP().readJson()
        if str(short_id) in tasks:
            short_id = self.get_short_id()

        return short_id


class TaskManager(object):
    def __init__(self):
        super().__init__()
        logger.debug("[TimeTaskTool] TaskManager")

    # 读取任务
    def readTask(self):
        task_dict = JsonOP().readJson()
        return task_dict

    # 添加任务
    def addTask(self, taskModel: Model):
        task_dict = JsonOP().readJson()
        task_dict[taskModel.taskId] = (
            taskModel.taskId,
            taskModel.dateStr,
            taskModel.custom_message,
            taskModel.remark,
        )

        JsonOP().saveJson(task_dict)
        return task_dict[taskModel.taskId]

    # 删除任务
    def rmTask(self, taskId):
        task_dict = JsonOP().readJson()
        if taskId in task_dict:
            taskinfo = task_dict.pop(taskId)
            JsonOP().saveJson(task_dict)
            return taskinfo
        return None

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

    def lunar_to_solar(self, year, month, day):
        lunar_date = Lunar(year, month, day, isleap=False)
        solar_date = Converter.Lunar2Solar(lunar_date)
        # 确保返回的是 datetime.date 类型
        return date(solar_date.year, solar_date.month, solar_date.day)


# Json文件读写
class JsonOP(object):
    __file_name = "CountdownTask.json"

    def __init__(self):
        super().__init__()
        self.__file_path = os.path.join(os.path.dirname(__file__), self.__file_name)
        if not os.path.exists(self.__file_path):
            self.saveJson({})
            logger.info(f"创建任务文件{self.__file_path}")

    def readJson(self):
        try:
            with open(self.__file_path, "r", encoding="utf-8") as file:
                tasks = json.load(file)
                return tasks
        except:
            return self.resetJson()

    def saveJson(self, tasks: dict = {}):
        try:
            with open(self.__file_path, "w", encoding="utf-8") as file:
                json.dump(tasks, file, ensure_ascii=False, indent=4)
        except:
            self.resetJson()

    def resetJson(self):
        with open(self.__file_path, "r", encoding="utf-8") as file:
            deleted_file = file.read()
            # 出错重置
            self.saveJson({})
            logger.info("任务文件因出错重置，原文件内容为")
            logger.info(deleted_file)
            return {}