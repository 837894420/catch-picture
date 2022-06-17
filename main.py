import os
import threading
import time
from datetime import datetime

import numpy as np
import requests as rs
from PIL import Image
from io import BytesIO
from queue import Queue

# 原先的print函数和主线程的锁
_print = print
mutex = threading.Lock()


# 定义新的print函数
def print(text, *args, **kw):#加锁并重写print方法防止多线程输出错乱
    '''
    使输出有序进行，不出现多线程同一时间输出导致错乱的问题。
    '''
    with mutex:
        _print(text, *args, **kw)


#收集的随机图片接口，爬取简单方便,对不同网址肯定有一点爬取差别的，需要自己调参数
#url ='https://api.ghser.com/random/pc.php'#三秋，文档https://api.ghser.com/acg.html
#url = 'https://www.dmoe.cc/random.php'#樱花，文档http://www.dmoe.cc/
#url = 'https://api.ixiaowai.cn/api/api.php'#小歪，文档https://api.ixiaowai.cn/
#url = 'https://api.vvhan.com/dongman.html'#韩小韩，该网址返回图片链接固定格式，可直接对重定向后的网址改变参数获取，文档https://api.vvhan.com/dongman.html
#url = 'https://api.r10086.com/img-api.php?type=动漫综合1' #樱道，文档https://img.r10086.com/
#url = 'https://api.yimian.xyz/img?type=moe' #EEE.DOG,文档https://www.eee.dog/tech/rand-pic-api.html
#url = 'https://acg.toubiec.cn/random.php' #晓晴博客，文档https://www.toubiec.cn/318.html
#url = 'https://cdn.seovx.com/d/?mom=302' #夏沫，文档https://cdn.seovx.com/
#url = 'https://api.mtyqx.cn/tapi/random.php' #墨天逸，文档https://api.mtyqx.cn/
#url = 'https://api.btstu.cn/sjbz/api.php?lx=dongman' #搏天，文档https://api.btstu.cn/doc/sjbz.php
#url = 'https://api.isoyu.com/aipc_animation.php' #姬长信，有点慢好像服务器不在国内，文档https://api.isoyu.com/
#url = 'https://api.paugram.com/wallpaper/' #保罗，图片不适合当壁纸，大量留白，文档https://api.paugram.com/help/wallpaper

#不是重定向的网址，可以直接用catchContext()爬取，多线程没弄
#url = 'https://img.xjh.me/random_img.php'+'?type=bg&ctype=age/nature'#岁月小驻，文档文档http://img.xjh.me/，可设定参数返回背景图，默认为头像图
#url = 'https://acg.yanwz.cn/api.php'#汐岑，文档https://acg.yanwz.cn/



# 多线程使用，放入链接，对每个链接开启一个线程进行处理，最多放入n(可设置)个线程，记住，每个链接应该是返回一个只有图片的页面
urls = ['https://api.ghser.com/random/pc.php','https://www.dmoe.cc/random.php',
        'https://api.ixiaowai.cn/api/api.php','https://api.yimian.xyz/img?type=moe',
        'https://acg.toubiec.cn/random.php','https://cdn.seovx.com/d/?mom=302',
        'https://api.mtyqx.cn/tapi/random.php','https://api.btstu.cn/sjbz/api.php?lx=dongman']
#单线程使用
url = 'https://api.ghser.com/random/pc.php'

#全局设置，可修改
threadNum = 4 #开启的最大线程数
pictureNum = 10 #每个线程获取的图片数
ctime = 2 #设定爬取每个网址的间隔时间，一个单位代表一秒
file = "image"#文件地址，该相对路径为当前文件的父文件地址，会自动生成

# 重构请求头，默认请求头容易被防止反爬虫拦截，请在访问前使用开发者模式查看你的浏览器下的访问该网址的请求头内容，找到对应的值填入这里
headers = {#一般只用改User-Agent，还不行的话就全复制下来，还不行换地址
'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36 Edg/100.0.1185.50',
}

lock = threading.RLock()#线程锁
errorNum = 0  #错误线程数
errorUrls = [] #错误线程值
globalTotal = 0 #统计开线程后的爬取总数

#测试爬取图片
def catchContext(url):
    for n in range(pictureNum):
        n = n + 1
        r = rs.get(url, headers=headers)#若出现SSL证书验证问题，可以在请求中设置verify=False
        print(r.headers)
        for i in r.request.headers.items():
            print(i)
        print(r.status_code)
        code = r.status_code
        img = r.content#图片文件内容
        name = r.url#重定向链接
        print(name + "    " + str(n))
        img = Image.open(BytesIO(r.content))
        r = name.split('/')[-1]  # 获取图片名称
        p = r.split('.')[-1]
        print(p)
        if p != 'png' and p != 'jpg':#不是重定向的结果需要自己命名了
            now_time = datetime.now()
            str1 = datetime.strftime(now_time, '%Y%m%d%H%M%S')
            img.save(file + '/' + str1 + ".png")
            print(str1 +"保存成功")
            time.sleep(1)
        else:#重定向的结果不需要自己命名
            img.save(file + '/' + r)
            print(r + "保存成功")
            time.sleep(1)

#单线程爬取，可直接调用
def catch(url):
    total = 0  # 统计下载的图片数量
    for n in range(pictureNum):#获取图片数量
        n = n + 1
        r = rs.get(url, headers=headers)
        img = r.content  #图片文件内容
        name = r.url#重定向链接
        print(" ")
        print("url：" + name)
        code = r.status_code#返回的状态码
        #imgsize = Image.open(BytesIO(r.content))
        #print(imgsize.size)#图片大小
        r = name.split('/')[-1]#获取图片名称
        print("获取第" + str(n) + "张")
        print(r)
        #存文件
        if not os.path.exists(file):
            print("文件不存在，已创建！")
            os.mkdir(file)
        else:
            print("开始下载图片")
        if code == 200:
            if not os.path.exists(file + r):
                with open(file + "/" + r, mode="wb") as f:
                    # 开始下载
                    f.write(img)
                    print("保存第" + str(n) + "张成功")
                    total = total + 1
            else:
                print("第" + str(n) + "张存在，不重复获取")
        else:
            print("第" + str(n) + "张状态码不正常，文件无法访问")#如果同一地址下出现该问题过多，建议换地址
        time.sleep(0.01)
    print("---------" + url + ": 完成爬取过程，一共下载了" + str(total) + "张图片-----------")



#多线程爬取，注意参数修改
def ThreadCatch(url, eEvent):
    print("-------------------------------" + "----------------------------------------")
    print(url + "开起线程")
    print("线程" + threading.current_thread().getName())
    total = 0  # 统计下载的图片数量
    global globalTotal
    global errorNum
    try:
        for n in range(pictureNum):#获取图片数量
            n = n + 1
            r = rs.get(url, headers=headers)
            img = r.content  #图片文件内容
            name = r.url#重定向链接
            print(" ")
            print(threading.current_thread().getName())
            print("url：" + name)
            code = r.status_code#返回的状态码
            #imgsize = Image.open(BytesIO(r.content))
            #print(imgsize.size)#图片大小
            r = name.split('/')[-1]#获取图片名称
            print("获取第" + str(n) + "张")
            print(r)
            #存文件
            if not os.path.exists(file):
                print("文件不存在，已创建！")
                os.mkdir(file)
            else:
                print("开始下载图片")
            if code == 200:
                if not os.path.exists(file + r):
                    with open(file + "/" + r, mode="wb") as f:
                        # 开始下载
                        f.write(img)
                        print("保存第" + str(n) + "张成功" )
                        total = total + 1
                        lock.acquire()#对全局统计数量上锁
                        globalTotal = globalTotal + 1
                        lock.release()#解锁
                else:
                    print("第" + str(n) + "张存在，不重复获取")
            else:
                print("第" + str(n) + "张状态码不正常，文件无法访问")
            time.sleep(ctime)
        print("---------" + url + ": 完成爬取过程，一共下载了" + str(total) + "张图片-----------")
        print(threading.current_thread().getName() + "线程结束")
        print("eEvent.is_set: " + str(eEvent.is_set()))
    except ConnectionError:
        print("[ERROR]:链接错误，结束线程：" + threading.current_thread().getName())
        errorNum = errorNum + 1
        errorUrls.append(threading.current_thread().getName())
    except OSError:
        print("[ERROR]:文件下载错误，可能文件命名原因，结束线程：" + threading.current_thread().getName())
        errorNum = errorNum + 1
        errorUrls.append(threading.current_thread().getName())
    finally:
        eEvent.set()  # 唤醒等待线程


#线程测试
def text(url, eEvent):
    print("-------------------------------"+"----------------------------------------")
    print(url+":测试开始")
    print("线程"+threading.current_thread().getName())
    global globalTotal
    time.sleep(1)
    lock.acquire()  # 对全局统计数量上锁
    try:
        globalTotal = globalTotal + 1
    finally:
        lock.release()  # 解锁
    print("--------------------------" + url + ":测试结束,唤醒等待线程" + "----------------")
    eEvent.set()  # 唤醒等待线程




def runThread():
    print("--------开起线程执行数据-----------")
    # 创建event事件
    eEvent = threading.Event()
    global urls
    queue = Queue()#等待队列
    size = len(urls)
    n = 0
    li = []
    if size <= threadNum & size > 0:#开启线程最大数
        for t in urls:
            n = n + 1
            th = threading.Thread(target=ThreadCatch, name="Thread-" + str(n), args=(t, eEvent))
            #th = threading.Thread(target=text, name="Thread-" + str(n), args=(t, ))#测试多线程方法
            th.start()
            li.append(th)
        for l in li:
            l.join()#等待所有子线程完成后主线程才结束

    elif size > threadNum:#线程池模拟，生成等待队列，队列中存储数值（url和线程使用状态，0未使用，1使用），简单线程池模拟实现，好难搞啊
        print("始终只同时执行"+str(threadNum)+"个线程")
        for u in urls:
            queue.put(u) #构建等待队列
        while not queue.empty():
            print("当前存活线程数"+ str(threading.active_count())+"存活数包括主线程")
            if threading.active_count() >= threadNum + 1:#判断线程是否为最大最大值，是就进入等待
                eEvent.clear()
                print("eEvent.is_set: " + str(eEvent.is_set()))
                print("主线程等待")
                eEvent.wait()
                print("主线程等待结束,创建新线程")
            d = queue.get()
            print(d)
            n = n + 1
            th = threading.Thread(target=ThreadCatch, name="Thread-" + str(n), args=(d, eEvent))
            #th = threading.Thread(target=text, name="Thread-" + str(n), args=[d, eEvent])#测试多线程方法
            print("尝试开启线程")
            th.start()
            if queue.empty():
                print("所有任务都添加到线程里，主线程等待所有线程执行完毕")
                x = True
                y = 1
                while x == True:#当存活的线程只剩下主线程或超过10分钟后主线程自动结束
                    time.sleep(60)
                    y = y + 1
                    if threading.active_count() == 1 or y >= 10:
                        break
    else:
        print("无线程开启，链接数组中无数据")

# class myThread (threading.Thread):
#     def __init__(self, name, url):
#         threading.Thread.__init__(self)
#         self.name = name
#         self.url = url
#     def run(self):
#         print ("开始线程：" + self.name)
#         catch(self.url)
#         print ("退出线程：" + self.name)

# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    #三个方法都应该单独使用
    #catchContext(url)#单线程爬取测试，可爬取非重定向网址，修改url
    #catch(url)#单线程爬取，修改url
    runThread()#调用多线程爬取，修改urls
    print("---------" + "多线程下的统计： 完成爬取过程，一共下载了" + str(globalTotal) + "张图片-----------")
    print("有" + str(errorNum) +"个线程出现错误导致该线程提前结束")
    if errorNum > 0:
        print("错误线程名：" + str(errorUrls))
    print("----------------------------主线程结束-----------------------------------------")
