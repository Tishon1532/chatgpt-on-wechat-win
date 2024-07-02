# encoding:utf-8
import datetime
import threading
import time
from datetime import datetime
import plugins
from bridge.context import ContextType
from bridge.reply import Reply, ReplyType
from channel.chat_message import ChatMessage
import plugins.lcard.app_card as fun
from plugins import *
import requests

@plugins.register(
    name="lcard",
    desire_priority=100,
    namecn="lcard",
    desc="发送卡片式链接和小程序",
    version="0.2.2",
    author="Francis",
)
class lcard(Plugin):
    def __init__(self):
        super().__init__()
        self.json_path = os.path.join(os.path.dirname(__file__), 'config.json')
        self.handlers[Event.ON_HANDLE_CONTEXT] = self.on_handle_context
        logger.info("[lcard] inited")

    def on_handle_context(self, e_context: EventContext):
        if e_context["context"].type not in [
            ContextType.TEXT
        ]:
            return
        context = e_context["context"]
        isgroup = context.get("isgroup", False)
        content = context.content
        _user_id = e_context['context']['msg'].from_user_id
        to_user_id = e_context['context']['msg'].to_user_id
        logger.debug("[Francis] on_handle_context. content: %s" % content)
        #发送各种榜单
        trending_pinyin = {
            "百度热榜": "baidu",
            "今日热榜": "top",
            "今日热文": "top",
            "热门新闻": "top",
            "今日热门新闻": "top",
            "今日的热门新闻": "top",
            "知乎热榜": "zhihu",
            "抖音热榜": "douyin",
            "掘金热榜": "juejin",
            "吾爱热榜": "52pojie",
            "网易热榜": "ne-news",
            "豆瓣热榜": "douban-media",
            "今日头条":"toutiao",
            "github热榜":"github",
            "澎湃新闻":"thepaper",
            "小红书":"xiaohongshu",
            "微博热榜": "weibo",
            "b站热榜": "bilibili",
        }
        content = content.strip()

        if content in trending_pinyin:
            trending = trending_pinyin[content]
            url = f"https://rebang.today/home?tab={trending}"
            gh_id="gh_7d739cf5e919"
            username="Francis"
            title = "今日热榜-全站榜单 🏆\n🅰🅸 ℝ𝕖𝕓𝕒𝕟𝕘.𝕋𝕠𝕕𝕒𝕪"
            desc ="涵盖：今日头条、抖音、Github、吾爱、掘金、bilibili、百度、知乎、网易、微博...\n追踪全网热点、简单高效阅读。"
            image_url="https://mmbiz.qpic.cn/sz_mmbiz_jpg/RiacFDBX14xAWVSLByXwA4pg6jickFZQT09smokU52wziaZhibhtkSIBll5wKiawKrDmXWwf1YYGq4ZiaJYGfViaDZDrw/300?wxtype=jpeg&amp;wxfrom=401"
            xml_link = fun.get_xml(to_user_id,url, gh_id, username, title, desc, image_url)
            _set_reply_text(xml_link, e_context, level=ReplyType.LINK)
            return
        elif content == "新闻直播间":
            video_mp = fun.cctv13_live_xml(to_user_id)
            _set_reply_text(video_mp, e_context, level=ReplyType.LINK)
            return
        elif content.startswith("点歌"):
            keyword = content[2:].replace(" ", "").strip()
            url = f"http://api.xtaoa.com/api/musicjx.php?id={keyword}&type=search&media=tencent"
            resp1 = requests.get(url)
            data = resp1.json()
            music_parse = data[0]
            song_id = music_parse["song_id"]
            singer=music_parse["author"]
            song=music_parse["name"]
            picture=music_parse["cover"]
            if song_id :
                #以下是xml示例，替换相关参数
                card_app = f"""<msg>
<fromusername>{to_user_id}</fromusername>
<scene>0</scene>
<commenturl></commenturl>
<appmsg appid="wx5aa333606550dfd5" sdkver="0">
<title>{song}</title>
<des>{singer}</des>
    <action>view</action>
    <type>3</type>
    <showtype>0</showtype>
    <content></content>
    <url>http://c.y.qq.com/v8/playsong.html?songmid={song_id}</url>
    <dataurl>http://wx.music.tc.qq.com/C4000015IWzW2NC8oN.m4a?guid=2000000280&amp;vkey=D42EDA8187C9697F31ED99CD9B3635DFBD3DAE29E4E8CF0EA549F2F247464072D17D5516DBBA34BB26D906D69E5E28239E0D557EEC5311BC&amp;uin=0&amp;fromtag=30280&amp;trace=772d0804e4366763</dataurl>
    <lowurl></lowurl>
    <lowdataurl></lowdataurl>
    <recorditem></recorditem>
    <thumburl>{picture}</thumburl>
    <messageaction></messageaction>
    <md5>fe75b445564bdf938ea28b455f0ccf43</md5>
    <extinfo></extinfo>
    <sourceusername></sourceusername>
    <sourcedisplayname></sourcedisplayname>
    <commenturl></commenturl>
    <appattach>
        <totallen>0</totallen>
        <attachid></attachid>
        <emoticonmd5></emoticonmd5>
        <fileext></fileext>
        <cdnthumburl>{picture}</cdnthumburl>
        <aeskey></aeskey>
        <cdnthumbaeskey></cdnthumbaeskey>
        <encryver>1</encryver>
        <cdnthumblength>24237</cdnthumblength>
        <cdnthumbheight>500</cdnthumbheight>
        <cdnthumbwidth>500</cdnthumbwidth>
    </appattach>
    <weappinfo>
        <pagepath></pagepath>
        <username></username>
        <appid></appid>
        <appservicetype>0</appservicetype>
    </weappinfo>
    <websearch />
</appmsg>
<appinfo>
    <version>1</version>
    <appname>QQ音乐</appname>
</appinfo>
</msg>"""
                _set_reply_text(card_app, e_context, level=ReplyType.LINK)
                return
            else:
                _set_reply_text("未找到该歌曲", e_context, level=ReplyType.TEXT)
                return
        #发送天气链接卡片，数据链接msn天气
        elif content.endswith("天气"):
            import  re
            weather_match = re.search(r"(.+?)(的)?天气", content)
            city_name = weather_match.group(1) if weather_match else "成都"
            url = f"https://api.pearktrue.cn/api/weather/?city={city_name}&id=1"
            response = requests.get(url)
            if response.status_code == 200:
                datas = json.loads(response.text)["data"]
                print(datas)
                if all(isinstance(data, dict) for data in datas):
                    first_data_weather = datas[0]['weather']
                    second_data_weather = datas[1]['weather']
                    first_data_temperature = datas[0]['temperature']
                    second_data_temperature = datas[1]['temperature']
                    gh_id = "gh_7d739cf5e919"
                    username = "Francis"
                    title = f"{city_name}今天\n天气：{first_data_weather}  气温：{first_data_temperature}"
                    desc = f"\n明天：{second_data_weather}  \n气温：{second_data_temperature}"
                    weather_url = "https://www.msn.cn/zh-cn/weather/"
                    image_url = "https://mmbiz.qpic.cn/mmbiz_jpg/xuic5bNARavt67O3KvoXqjJJanKwRkfIiaJT6Oiavia0icVgC9DWInofCKA655AuicqgdBukd36nFXTqHBUUvfc0uCCQ/300?wxtype=jpeg&amp;wxfrom=401"
                    xml_link = fun.get_xml(to_user_id,weather_url, gh_id, username, title, desc, image_url)
                    _set_reply_text(xml_link, e_context, level=ReplyType.LINK)
                    return
                else:
                    _set_reply_text("请按格式输入：城市+天气\n例如：北京天气", e_context, level=ReplyType.TEXT)
                    return


        elif content.startswith("我要吃") or content.startswith("我想吃")  :
            keyword = content[3:].strip()
            xml_app = fun.woyaochi_app(to_user_id,keyword)
            _set_reply_text(xml_app, e_context, level=ReplyType.MINIAPP)
            return
        elif content.endswith("怎么做"):
            global dish_name
            if content.endswith("怎么做"):
                dish_name = content[:-3].strip()
            url = f"https://m.xiachufang.com/search/?keyword={dish_name}"
            gh_id = "gh_fbfa5dacde93"
            username = "美食教程"
            title = "                美食教程"
            desc = f"\n🔍️ {dish_name}\n\n\n                    xiachufang.com"
            image_url = "https://mmbiz.qpic.cn/mmbiz_jpg/Uc03FJicJseLq0yQ4JqqiaIIlDB7KuiaNY7ia14ZGCfDeVXktfI9kU6ZGu4659Y3n9CVhP5oKEIYkvXJgDg9WRia5Ng/300?wx_fmt=jpeg&amp;wxfrom=1"
            xml_link = fun.get_xml(to_user_id,url, gh_id, username, title, desc, image_url)
            _set_reply_text(xml_link, e_context, level=ReplyType.LINK)
            return
        elif content == "美团外卖":
            xml_app = fun.meituan(to_user_id)
            _set_reply_text(xml_app, e_context, level=ReplyType.MINIAPP)
            return

        huoche_keywords = ["火车票", "高铁票", "动车票"]
        # 用于匹配以火车票关键词结尾的正则表达式
        pattern = r"(\d{4}\.\d{1,2}\.\d{1,2})?\s*(.+)\s*到\s*(.+?)(?:的)?\s*(" + '|'.join(huoche_keywords) + ")$"

        import re
        match = re.search(pattern, content)

        if match:
            date, departure, arrival, ticket_type = match.groups()
            departure = departure.strip()  # 去除可能存在的多余空格
            arrival = arrival.strip()  # 去除可能存在的多余空格
            if date:
                date = datetime.strptime(date, "%Y.%m.%d").strftime("%Y-%m-%d")
            else:
                date = datetime.now().strftime("%Y-%m-%d")
            # 假设以下是调用查询火车票的函数，返回查询结果
            card_app = fun.huochepiao_app(to_user_id,content,departure, arrival, date)  # 你需要用正确的函数替换这里
            # 假设以下代码设置用于回复用户的信息
            _set_reply_text(card_app, e_context, level=ReplyType.MINIAPP)
            return
        pattern = r"(\d{4}\.\d{1,2}\.\d{1,2})?\s*(.+)\s*到\s*(.+?)(?:的)?\s*机票$"
        match = re.search(pattern, content)
        if match:
            # 提取日期、出发城市和到达城市
            date, departure, arrival = match.groups()
            departure = departure.strip()  # 去除可能存在的多余空格
            arrival = arrival.strip()  # 去除可能存在的多余空格
            # 转换日期格式
            if date:
                date = datetime.strptime(date, "%Y.%m.%d").strftime("%Y-%m-%d")
            else:
                date = datetime.now().strftime("%Y-%m-%d")
            with open(self.json_path, encoding='utf-8') as f:
                config = json.load(f)
            station_list = config.get("station_list", [])
            departure_code = None
            arrival_code = None
            for station in station_list:
                print(f"Checking station: {station['name']}")  # 输出正在检查的站点名称
                if station["name"] == departure:
                    departure_code = station["code"]
                    print(f"Found departure code: {departure_code}")  # 确认找到出发地代码
                if station["name"] == arrival:
                    arrival_code = station["code"]
                    print(f"Found arrival code: {arrival_code}")  # 确认找到目的地代码
            if departure_code and arrival_code:
                card_app = fun.air_tickets_app(to_user_id,content, departure_code, departure, arrival_code, arrival, date)
                _set_reply_text(card_app, e_context, level=ReplyType.MINIAPP)
                return
            else:
                _set_reply_text("未查到该行程机票信息", e_context, level=ReplyType.TEXT)
                return

    def get_help_text(self, verbose=False, **kwargs):
        help_text = "发送卡片式链接和小程序"
        if not verbose:
            return help_text
        help_text = "发送卡片式链接和小程序,可以实现卡片天气，卡片点歌，火车飞机票查询"
        return help_text
def _set_reply_text(content: str, e_context: EventContext, level: ReplyType = ReplyType.ERROR):
    reply = Reply(level, content)
    e_context["reply"] = reply
    e_context.action = EventAction.BREAK_PASS