# coding=utf-8
import json
import requests
import math
from config import global_config
from requests_toolbelt import MultipartEncoder
from requests.packages.urllib3.exceptions import InsecureRequestWarning

import _thread
import time

# 加载js
import execjs
# 播放音频文件
from playsound import playsound
# 定时任务
import schedule

import os


# 登陆
def login():
    params = MultipartEncoder(
        fields={'username': global_config.getRaw('login', 'username'),
                'password': global_config.getRaw('login', 'password')}
    )
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36',
        'Content-Type': params.content_type
    }
    url = 'https://e-gw.giant.com.cn/index.php/login/login'
    requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
    response = requests.post(url=url, headers=headers,
                            data=params, verify=False)  # verify=Fasle去掉https验证
    page_json = response.json()
    if (page_json['status'] == 1):
        global_config.reWriteConfigFile(
            'login', 'token', page_json['data']['token'])
        # 登陆成功10s后开始搜索
        time.sleep(10)
        search()
    else:
        print('login 失败')


# 退出当前登陆账号
def loginOut():
    params = MultipartEncoder(
        fields={'token': global_config.getRaw('login', 'token')}
    )
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36',
        'Content-Type': params.content_type
    }
    url = 'https://e-gw.giant.com.cn/index.php/login/logout'
    requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
    response = requests.post(url=url, headers=headers,
                            data=params, verify=False)  # verify=Fasle去掉https验证
    page_json = response.json()
    if (page_json['status'] == 1):
        global_config.reWriteConfigFile('login', 'token', '')
    else:
        print('loginOut 失败')


# 库存查询
def is_stock(code):
    params = {
        'sku': global_config.getRaw('goods', 'sku'),
        'shopno': code,
        'user_id': global_config.getRaw('login', 'token')
    }
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36'
    }
    url = 'https://e-gw.giant.com.cn/index.php/api/sku_stock'
    requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
    response = requests.post(url=url, headers=headers,
                            data=params, verify=False)
    page_json = response.json()
    if (page_json['status'] == 1):
        rest = decryptStock(page_json['data'])
        return rest
    else:
        _thread.exit()


# 设置为服务门店
def doStore(code):
    params = {
        'code': code,
        'user_id': global_config.getRaw('login', 'token')
    }
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36'
    }
    url = 'https://e-gw.giant.com.cn/index.php/api/do_store'
    requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
    response = requests.post(url=url, headers=headers,
                            data=params, verify=False)
    if (response.status_code == 200):
        return True


def loopRequest(threadName, deplay, page, per_page):
    url = 'https://e-gw.giant.com.cn/index.php/api/store_list'
    headers = {
        'server': 'nginx',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.5005.61 Safari/537.36'
    }
    requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
    loop = False
    while (loop != True):
        page = page + 1
        params = {
            'per_page': per_page, 'page': page, 'province': global_config.getRaw(
                'goods', 'province'), 'city': global_config.getRaw('goods', 'city')
        }
        # time.sleep(deplay * 5)
        print('page: ', page)
        response = requests.post(
            url=url, headers=headers, data=params, verify=False)
        if response.status_code != 503:
            res_json = response.json()
            hasSotreLsit = len(res_json['data'])
            if (hasSotreLsit > 0):
                for ls in res_json['data']:
                    # 遍历门店
                    code = (ls['code'])
                    setStore = doStore(code)
                    if (setStore):
                        store_name = ls['name']
                        stock_num = is_stock(code)
                        if stock_num > 0:
                            txt1 = [time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
                                    store_name, '库存:', str(stock_num), ' 位置:', ls['addr1']]
                            x1 = ''.join(txt1)
                            # playAudio()
                            logRest(x1)
            else:
                loop = True
                # _thread.exit()


# 处理返回字符串截取方法
def dealStrSub(val):
    numA = math.ceil(len(val)/2)
    str1 = val[numA:len(val)]
    str2 = val[0:numA]
    str3 = str1[1:3]
    str3_1 = str1[1:2]
    str4 = str1[4:6]
    str4_1 = str1[4:5]
    if (str3_1 == '0'):
        str3 = str1[2:3]
    if (str4_1 == '0'):
        str4 = str1[5:6]
    str7 = str1[6:len(str1)]
    str5 = str2+str7
    a = len(str5)
    b = int(str3)
    data = a - b
    str6 = str5[int(str4):int(data)]
    return str6


# 库存余量解密
def decryptStock(stockStr):
    # stockStr 这个是查询库存返回的值
    key = dealStrSub(stockStr)
    node = execjs.get()
    path = filePath('\js\main.js')
    fp = open(path, encoding="utf-8")
    ctx = node.compile(fp.read())
    result = ctx.call(
        'decrypt', key, 'nKB6qnkQimMG5Pv1CCPfz205YgQurfcZs1kZuuDtyim8EXmR', True)
    data = json.loads(result)
    return data['stock']


def logRest(str):
    with open("log.txt", "a", encoding="utf-8") as file:
        file.write(str)
        file.write('\n')


def search():
    loopRequest('a', 1, 0, 10)
    # 创建30个多线程,每页100个数据
    # for tr_num in range(1, 10):
    #     _thread.start_new_thread(
    #         loopRequest, ('线程: ' + str(tr_num), 1, tr_num, 10))  # 50
    # 爬取20s后 存库操作
    # _thread.exit()


def playAudio():
    # path = os.getcwd() + '\sound\sound.wav'
    playsound('sound.wav')


def filePath(str):
    path = os.getcwd()+str
    return path


schedule.every(int(global_config.getRaw('config', 'looptime'))).minutes.do(login)

if __name__ == '__main__':
    login()
    while True:
        schedule.run_pending()   # 运行所有可以运行的任务
        time.sleep(1)

