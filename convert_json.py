import json
import os
import re
import sys
import time

import requests

try:
    from USER_AGENTS import get_user_agent
except:
    print("缺少依赖文件USER_AGENTS.py 文件 https://github.com/XgzK/JD_annex/blob/master/USER_AGENTS.py 下载")
    sys.exit(3)
"""
const $ = new Env("店铺签到转换为json格式")
Date: 2022/12/26 20:41
TG: https://t.me/InteIJ
cron: 1
export ShopToken="token2&token2"
代理 export ALL_PROXY="协议://IP:端口"
"""
JD_API_HOST = 'https://api.m.jd.com/api?appid=interCenter_shopSign'
# 使用数组保存减少后面其他CK请求时间
data = []
ALL_PROXY = os.environ.get("ALL_PROXY") if os.environ.get("ALL_PROXY") else None


def getvenderId(token):
    """
    获取店铺ID
    :param token:
    :return: [venderId]  or []
    """
    try:
        url = f'https://api.m.jd.com/api?appid=interCenter_shopSign&t={int(time.time())}' + '&loginType=2&functionId=interact_center_shopSign_getActivityInfo&body={"token":"' + token + '","venderId":""}&jsonp=jsonp1000'
        headers = {
            "accept": "*/*",
            "accept-encoding": "gzip, deflate, br",
            "accept-language": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7",
            "referer": 'https://h5.m.jd.com/',
            # "cookie": cookie,
            "User-Agent": get_user_agent()
        }
        pq_data = requests.get(url, headers=headers,
                               proxies={"https": ALL_PROXY})  # ALL_PROXY={"https":"socks5://127.0.0.1:9150"}
        if pq_data.status_code != 200:
            print(f'状态码: {pq_data.status_code}')
            return []
        code = re.findall('"code":(\d+)', pq_data.text)
        if code and int(code[0]) == 200:
            return [re.findall('"venderId":(\d+),', pq_data.text)[0]]
        elif code and int(code[0]) != 200:
            print(f"获取店铺获取失败,返回状态码: {code[0]}, 请删除tk: {token}")
        else:
            print(f'获取店铺获取失败,请删除tk: {token},没有返回状态码: {pq_data.text}')
        return []
    except Exception as e:
        print('获取店铺ID异常: ', e)
        return []


def getvenderName(venderId):
    """
    获取店铺名称
    :return: [店铺名称]
    """
    try:
        url = f"https://wq.jd.com/mshop/QueryShopMemberInfoJson?venderId={venderId}"
        headers = {
            "accept": "*/*",
            "accept-encoding": "gzip, deflate, br",
            "accept-language": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7",
            # "cookie": cookie,
            "User-Agent": get_user_agent()
        }
        pq_data = requests.get(url, headers=headers, proxies={"https": ALL_PROXY})
        if pq_data.status_code != 200:
            return []
        if 'shopName' in pq_data.json():
            return [pq_data.json()["shopName"]]
        return []
    except Exception as e:
        print('获取店铺名称异常: ', e)
        return []


def getActivityInfo(token, venderId):
    """
    获取店铺活动信息
    :param token:
    :param venderId:
    :return:
    """
    try:
        url = f'https://api.m.jd.com/api?appid=interCenter_shopSign&t={int(time.time())}' + '&loginType=2&functionId=interact_center_shopSign_getActivityInfo&body={"token":"' + f'{token}","venderId":{venderId}' + '}&jsonp=jsonp1005'
        headers = {
            "accept": "accept",
            "accept-encoding": "gzip, deflate",
            "accept-language": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7",
            # "cookie": cookie,
            "referer": f"https://h5.m.jd.com/babelDiy/Zeus/2PAAf74aG3D61qvfKUM5dxUssJQ9/index.html?token={token}&sceneval=2&jxsid=16105853541009626903&cu=true&utm_source=kong&utm_medium=jingfen&utm_campaign=t_1001280291_&utm_term=fa3f8f38c56f44e2b4bfc2f37bce9713",
            "User-Agent": get_user_agent()
        }
        pq_data = requests.get(url=url, headers=headers, proxies={"https": ALL_PROXY})
        if pq_data.status_code != 200:
            return []
        # print(pq_data.text)
        # 签到天和豆和预算份额
        level = re.findall('"level":(.*?),', pq_data.text)
        discount = re.findall('"discount":(\d+)', pq_data.text)
        budgetNum = re.findall('"budgetNum":(\d+)', pq_data.text)
        stday = ''
        levels = 0
        sun = len(level) if len(level) < len(discount) else len(discount)
        for i in range(sun):
            if int(level[i]) == 0:
                continue
            stday += f" {level[i]} 天 {discount[i]} 豆 {budgetNum[i]} 预算数"
            levels = level[i]
        startTime = time.strftime('%Y-%m-%d %H:%M:%S',
                                  time.localtime(int(re.findall('"startTime":(\d+),', pq_data.text)[0][0:10:])))
        endTime = time.strftime('%Y-%m-%d %H:%M:%S',
                                time.localtime(int(re.findall('"endTime":(\d+),', pq_data.text)[0][0:10:])))
        activityId = re.findall('"id":(\d+),', pq_data.text)[0]
        typeId = re.findall('"type":(\d+),', pq_data.text)
        # venderId, activityId  天数 对应奖励 开始时间 结束时间 活动份额
        data.append([token, venderId, activityId, int(typeId[0]) if typeId else 2, stday, levels, startTime, endTime,
                     int(re.findall('"endTime":(\d+),', pq_data.text)[0][0:10:])])
        return [200]
    except Exception as e:
        print("获取店铺活动信息异常: ", e)
        return []


def signCollectGift(cookie, token, venderId, activityId):
    """
    店铺签到
    :param cookie:
    :param token:
    :param venderId:
    :param activityId:
    :return:
    """
    try:
        url = f'{JD_API_HOST}&t={int(time.time())}&loginType=2&functionId=interact_center_shopSign_signCollectGift&body=' + '{"token":"' + f'{token}","venderId":{venderId},"activityId":{activityId},"type":2,"actionType":' + '7}&jsonp=jsonp1004'
        headers = {
            "accept": "accept",
            "accept-encoding": "gzip, deflate",
            "accept-language": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7",
            "cookie": cookie,
            "referer": f"https://h5.m.jd.com/babelDiy/Zeus/2PAAf74aG3D61qvfKUM5dxUssJQ9/index.html?token=${token}&sceneval=2&jxsid=16105853541009626903&cu=true&utm_source=kong&utm_medium=jingfen&utm_campaign=t_1001280291_&utm_term=fa3f8f38c56f44e2b4bfc2f37bce9713",
            "User-Agent": get_user_agent()
        }
        pq_data = requests.get(url, headers=headers)
        # 筛选所有非200问题
        if pq_data.status_code != 200:
            return []
        codata = re.findall('"code":(\d+)', pq_data.text)
        if codata:
            if int(codata[0]) == 200:
                print('签到成功')
                return [200]
            else:
                codata1 = re.findall('"msg":"(.*?)",', pq_data.text)
                if codata1:
                    print(f'签到失败信息: {codata1[0]}')
                    return []
                print(f'签到失败返回值: {codata[0]}')
                return []
        return []
    except Exception as e:
        print('店铺签到异常: ', e)
        return []


def taskUrl(cookie, token, venderId, activityId):
    """
    店铺获取签到信息
    :param cookie:
    :param token:
    :param venderId:
    :param activityId:
    :return:
    """
    global msg
    try:
        url = f'{JD_API_HOST}&t={int(time.time())}&loginType=2&functionId=interact_center_shopSign_getSignRecord&body=' + '{"token":"' + f'{token}","venderId":{venderId},"activityId":{activityId},"type":2' + '}&jsonp=jsonp1006'
        headers = {
            "accept": "application/json",
            "accept-encoding": "gzip, deflate, br",
            "accept-language": "zh-CN,zh;q=0.9",
            "cookie": cookie,
            "referer": "https://h5.m.jd.com/",
            "User-Agent": get_user_agent()
        }
        # 店铺获取签到
        pq_data = requests.get(url, headers=headers)
        # 筛选所有非200问题
        if pq_data.status_code != 200:
            return []
        days = re.findall('"days":(\d+)', pq_data.text)[0]
        # print(pq_data.text)
        print(f'已经签到 {days} 天')
        msg += f'已经签到 {days} 天\n'
        return [200]
    except Exception as e:
        print('店铺获取签到信息异常: ', e)
        return []


def forCK(token: list):
    """
    执行任务
    :return:
    """
    # 遍历所有店铺
    for i in range(len(token)):
        time.sleep(1)
        venderId = getvenderId(token[i])
        if venderId:
            print(venderId)
            getActivityInfo(token[i], venderId[0])
        # shopName = getvenderName(venderId)
        # if shopName is None:
        #     continue

    # cookie = get_cookies()
    # for i in cookie:
    #     signCollectGift(cookie, token)
    #     taskUrl(cookie, token)


if __name__ == '__main__':
    filename = 'pqdtk.json'
    if os.environ.get("ShopToken"):
        ShopToken = os.environ.get("ShopToken")
    else:
        print('请设置变量格式\nexport ShopToken="token2&token2"')
        sys.exit(3)
    try:
        with open(filename, mode='r', encoding='utf-8') as f:
            js = json.load(f)
    except FileNotFoundError:
        # 如果文件不存在创建并写入{} js = {}
        print(f"没有检测到{filename}存在开始创建")
        fp = open(filename, 'w+', encoding='utf-8')
        json.dump({}, fp, ensure_ascii=False, indent=4, sort_keys=True)
        fp.close()
        js = {}
    except Exception as e:
        print(f"发生异常事件: {e}")
        sys.exit(3)
    forCK(list(ShopToken.split('&')))
    for i in range(len(data)):
        if int(time.time()) + (86164 * int(data[i][5])) > data[i][8]:
            print(f"店铺 {data[i][0]} 无法达到最大签到天跳过添加")
            continue
        js.setdefault(data[i][0], {
            "venderId": data[i][1],
            "activityId": data[i][2],
            "typeId": data[i][3],
            "stday": data[i][4],
            "maximum": data[i][5],
            "startTime": data[i][6],
            "EndTime": data[i][7],
            "time": data[i][8]
        })
    with open(filename, mode='w+', encoding='utf-8') as f:
        json.dump(js, f, ensure_ascii=False, indent=4, sort_keys=True)
    print(f'店铺签到转换成功，请去脚本所在目录查看{filename}')
