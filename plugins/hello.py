import random

import requests


def get_duration_str(seconds: float, like: str = "%02d:%02d:%02d"):
    """
    71  -> 01:11
    """
    m, s = divmod(float(seconds), 60)
    h, m = divmod(m, 60)
    # print(like % (h, m, s))
    if not seconds:
        return ""
    return like % (h, m, s)
def get_shipinghao(video_id,pass_ticket):

    url = "https://mp.weixin.qq.com/recweb/videolistapi?action=getvideoinfo&feed_id=finder_{video_id}&channelid=699001&pass_ticket={pass_ticket}".format(video_id=video_id,pass_ticket=pass_ticket)

    payload = {}
    headers = {
        'Host': 'mp.weixin.qq.com',
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/5{}.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36 NetType/WIFI MicroMessenger/6.8.0(0x16080000) MacWechat/3.8.5(0x13080510) XWEB/1100 Flue'.format(random.choice(range(10,90))),
        'x-requested-with': 'XMLHttpRequest',
        'accept': '*/*',
        'sec-fetch-site': 'same-origin',
        'sec-fetch-mode': 'cors',
        'sec-fetch-dest': 'empty',
        'accept-language': 'zh-CN,zh;q=0.9',
        'Cookie': 'pac_uid=0_42dfe723d711d'
    }

    response = requests.request("GET", url, headers=headers, data=payload)

    # print(response.text)
    inf = response.json()
    print(inf)
    description = inf.get("data", {}).get("description", "").replace("'","[").replace('"',"[").replace('“',"[").replace('”',"]")
    source = inf.get("data", {}).get("source", "")
    if inf.get("data", {}).get("resolution_list", []):
        play_url = inf.get("data", {}).get("resolution_list", [])[0]["url"]
        print(play_url)
        duration = get_duration_str(inf.get("data", {}).get("resolution_list", [])[0]["duration"]/1000)
    else:
        play_url = "该视频无法获取播放地址"
        duration = ""
    wx_url = "https://mp.weixin.qq.com/recweb/clientjump?feed_id=finder_{video_id}&tag=getvideolist&channelid=699001".format(video_id=video_id)
    return description, source, play_url, duration,wx_url

s1="14404630107220351100"
s2="%252BAOHOlDaxg4K%252BtGZui0izKDfd9iX4NBrMTAaCNJ3ijWtdZl%252FnRzOxgINGu0Cipqj6kj5%252FmQKTap2LV2NUBhygg%253D%253D"
s4 = get_shipinghao(s1,s2)