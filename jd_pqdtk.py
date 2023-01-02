#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
File: jd_pqdtk.py(店铺签到简化版)
Date: 2022/12/19 23:17
Channel: https://t.me/InteTU
Group: https://t.me/InteIJ
cron: 0 0 * * *
new Env('店铺签到简化版');
店铺签到简化版是根据开源的js店铺签到优化而来,优化程序运行的时长，让你在更短的时间内完成签到任务
代理 export ALL_PROXY="协议://IP:端口"
"""
import json
import os
import re
import sys
import time
from datetime import datetime

import requests
from requests.exceptions import ProxyError
from urllib3 import HTTPSConnectionPool

try:
    from jdCookie import get_cookies
    from USER_AGENTS import get_user_agent
    from sendNotify import send

    getCk = get_cookies()
    if type(getCk) != list:
        getCk = []
except Exception as e:
    print("缺少文件可能缺少其中一个，jdCookie.py sendNotify.py USER_AGENTS.py", e)
    sys.exit(3)
msg = ''
JD_API_HOST = 'https://api.m.jd.com/api?appid=interCenter_shopSign'
lis = []
ALL_PROXY = os.environ.get("ALL_PROXY") if os.environ.get("ALL_PROXY") else None


def signCollectGift(cookie, token, venderId, activityId, typeId):
    """
    店铺签到
    :param cookie:
    :param token:
    :param venderId:
    :param activityId:
    :return: []发生未知问题 [200] 签到成功 [-1] 签到上限 [-2] 需要重试
    """
    global msg
    try:
        url = f'{JD_API_HOST}&t={int(time.time())}&loginType=2&functionId=interact_center_shopSign_signCollectGift&body=' + '{"token":"' + f'{token}","venderId":{venderId},"activityId":{activityId},"type":{typeId},"actionType":' + '7}&jsonp=jsonp1004'
        headers = {
            "accept": "accept",
            "accept-encoding": "gzip, deflate",
            "accept-language": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7",
            "cookie": cookie,
            "referer": f"https://h5.m.jd.com/babelDiy/Zeus/2PAAf74aG3D61qvfKUM5dxUssJQ9/index.html?token=${token}&sceneval=2&jxsid=16105853541009626903&cu=true&utm_source=kong&utm_medium=jingfen&utm_campaign=t_1001280291_&utm_term=fa3f8f38c56f44e2b4bfc2f37bce9713",
            "User-Agent": get_user_agent()
        }
        pq_data = requests.get(url, headers=headers, timeout=10, proxies={"https": ALL_PROXY})
        # 筛选所有非200问题
        if pq_data.status_code != 200:
            print(f'失败token: : {token} 失败状态码: {pq_data.status_code}')
            return []
        codata = re.findall('"code":(\d+)', pq_data.text)
        if codata:
            if int(codata[0]) == 200:
                print(f'店铺 {token} 签到成功')
                return [200]
            else:
                codata1 = re.findall('"msg":"(.*?)",', pq_data.text)
                if codata1:
                    print(f'失败token1: {token} 失败返回值: {codata1[0]}')
                    if codata1[0] == "用户达到签到上限":
                        return [-1]
                    elif codata1[0] == "当前不存在有效的活动!":
                        lis.append(token)
                        print(f'删除非正常店铺: {token}')
                    return []
                msg += f"失败token2: {token} 失败返回值: {codata[0]}\n"
                print(f'失败token2: {token} 失败返回值: {codata[0]}')
                return []
        return []
    except ProxyError:
        print(f"店铺: {token} 发生 ProxyError 代理异常,进行重试")
        return [-2]
    except HTTPSConnectionPool:
        print(f"店铺: {token} 发生 HTTPSConnectionPool 异常,进行重试")
        return [-2]
    except Exception as e:
        print(f'失败token: {token} 签到异常: {e}')
        return []


def taskUrl(cookie, token, venderId, activityId, maximum, typeId, maxtime):
    """
    店铺获取签到信息
    :param cookie:
    :param token:
    :param venderId:
    :param activityId:
    :param maximum: 最大签到天数
    :param typeId:
    :param maxtime: 最大签到天数的秒
    :return: []发生未知问题 [200] 签到成功 [-1] 记录签到零天 [-2] 需要重试
    """
    global msg
    try:
        url = f'{JD_API_HOST}&t={int(time.time())}&loginType=2&functionId=interact_center_shopSign_getSignRecord&body=' + '{"token":"' + f'{token}","venderId":{venderId},"activityId":{activityId},"type":{typeId}' + '}&jsonp=jsonp1006'
        headers = {
            "accept": "application/json",
            "accept-encoding": "gzip, deflate, br",
            "accept-language": "zh-CN,zh;q=0.9",
            "cookie": cookie,
            "referer": "https://h5.m.jd.com/",
            "User-Agent": get_user_agent()
        }
        # 店铺获取签到
        pq_data = requests.get(url, headers=headers, timeout=10, proxies={"https": ALL_PROXY})
        # 筛选所有非200问题
        if pq_data.status_code == 403:
            print("触发403异常停止一分钟")
            time.sleep(60)
            return []
        elif pq_data.status_code != 200:
            print(f"触发状态码 {pq_data.status_code} 将删除店铺 {token}")
            msg += f"触发状态码 {pq_data.status_code} 将删除店铺 {token}\n"
            lis.append(token)
            return []
        days = re.findall('"days":(\d+)', pq_data.text)[0]
        print(f'店铺 {token} 已经签到 {days} 天')
        if int(days) >= int(maximum):
            print(f'达到签到天数自动删除: {token}')
            msg += f'达到签到天数自动删除: {token}\n'
            # 删除签到满的店铺签到
            lis.append(token)
        elif int(days) < 2 and int(time.time()) + (86164 * (int(maximum) - 1)) > maxtime:
            print(f'检测到店铺 {token} 现在签到无法达到最大签到天数将自动删除本店铺')
            msg += f'检测到店铺 {token} 现在签到无法达到最大签到天数将自动删除本店铺\n'
            lis.append(token)
        if int(days) == 0:
            return [-1]
        return [200]
    except ProxyError:
        print(f"店铺: {token} 发生 ProxyError 代理异常,进行重试")
        return [-2]
    except HTTPSConnectionPool:
        print(f"店铺: {token} 发生 HTTPSConnectionPool 异常,进行重试")
        return [-2]
    except Exception as e:
        print(f'店铺 {token} 获取签到信息异常: ', e)
        return []


def fo(cookie, token, venderId, activityId, typeId):
    """
    解决一些异常的
    :return:
    """
    aa = 0
    while True:
        res = signCollectGift(cookie, token, venderId, activityId, typeId)
        if aa == 3:
            return res
        # 结束本次循环
        if res and res[0] == -1:
            return res
        elif res and res[0] == -2:
            aa += 1
        else:
            return res


def fotask(cookie, token, venderId, activityId, maximum, typeId, maxtime):
    aa = 0
    while True:
        ta = taskUrl(cookie, token, venderId, activityId, maximum, typeId, maxtime)
        if aa == 3:
            return ta
        if ta and ta[0] == -1:
            return ta
        elif ta and ta[0] == -2:
            aa += 1
        else:
            return ta


if __name__ == '__main__':
    filename = 'pqdtk.json'
    if os.path.exists(filename) is False:
        print('没有检测到同目录下有pqdtk.json存在')
        sys.exit(3)
    with open(filename, mode='r', encoding='utf-8') as f:
        js = json.load(f)
    su2 = 0
    for ck in getCk:
        print(f'现在执行签到天数的是CK{su2}')
        for token in js.keys():
            try:
                # 如果超过日期自动跳过
                if int(time.time()) > js[token]['time']:
                    if su2 == 0:
                        lis.append(token)
                    continue
                res = fo(ck, str(token), js[token]['venderId'], js[token]['activityId'],
                         js[token]['typeId'])
                # 结束本次循环
                if res and res[0] == -1:
                    break
            except:
                pass
        su2 += 1
    su2 = 0
    for ck in getCk:
        print(f'现在获取签到天数的是CK{su2}')
        su = 0
        for token in js.keys():
            try:
                if int(time.time()) > js[token]['time']:
                    continue
                su3 = fotask(ck, token, js[token]['venderId'], js[token]['activityId'], js[token]['maximum'],
                             js[token]['typeId'], js[token]['time'])
                if su3 and su3[0] == -1:
                    su += 1
                    if su > 5:
                        print(f'CK{su2}连续获取五次零签到天数执行下一个CK')
                        break
            except Exception as e:
                print(e)
        su2 += 1
    for i in lis:
        try:
            js.pop(i) if i in js else ""
        except:
            pass
    # 把失败的删除,重新添加
    with open(filename, mode='w', encoding='utf-8') as f:
        json.dump(js, f, ensure_ascii=False, indent=4, sort_keys=True)
    title = "🗣消息提醒：店铺签到简化版"
    msg = f"⏰{str(datetime.now())[:19]}\n" + msg
    send(title, msg)
