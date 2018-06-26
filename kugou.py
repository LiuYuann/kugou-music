from selenium import webdriver
from pyquery import PyQuery as pq
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.chrome.options import Options
import re
import requests
import os
import random
import pymysql

chrome_options = Options()
chrome_options.add_argument('--headless')
browser = webdriver.Chrome(chrome_options=chrome_options)
browser.get('http://www.kugou.com/yy/singer/index/2-all-1.html')
wait = WebDriverWait(browser, 10)
db = pymysql.connect("localhost", "root", "", port=3306, db='ttt', charset='utf8')
cursor = db.cursor()
table = 'web_singer'


def findhref():
    html = browser.page_source
    doc = pq(html)
    li = doc.remove('.pic').find('.r ul li a').items()
    for i in li:
        yield i.attr('href')


def parsedata(d):
    for i in findhref():
        print(i)
        html = requests.get(i).text
        doc = pq(html)
        title = doc('body > div.wrap.clear_fix > div.sng_ins_1 > div.top > div > div > strong').text()
        discription = doc('body > div.wrap.clear_fix > div.sng_ins_1 > div.top > div > p').text()
        img_url = doc('body > div.wrap.clear_fix > div.sng_ins_1 > div.top > img').attr('_src')
        data = {
            'singername': title,
            'singerjieshao': discription,
            'img_url': img_url,
            'singerImages': '',
            'tabsiID': random.randint(1, 10),
            'is_re_singer': random.randint(0, 1)
        }
        d.append(data)


def download_image(url):
    file_path = None
    try:
        response = requests.get(url)
        if response.status_code == 200:
            file_path = re.search('(\d+).jpg$', url).group(1) + '.jpg'
            if not os.path.exists(file_path):
                with open(file_path, 'wb')as f:
                    f.write(response.content)
            else:
                print('Already downloaded!!!')
            return file_path
    except requests.ConnectionError:
        print("Downloading failed!!!")


def savetoMysql(data):
    keys = ','.join(data.keys())
    values = ','.join(['%s'] * len(data))
    sql2 = 'INSERT INTO {table}({keys}) values ({values})'.format(table=table, keys=keys, values=values)
    try:
        if cursor.execute(sql2, tuple(data.values())):
            print('success')
            db.commit()
    except Exception as e:
        print('erro', repr(e))
        db.rollback()


def savedata(d):
    for i in d:
        filepath = download_image(i.pop('img_url'))
        if(filepath):
            i['singerImages']=filepath
            savetoMysql(i)


if __name__ == '__main__':
    d = []
    if not os.path.exists('img'):
        os.mkdir('img')
    os.chdir('img')
    parsedata(d)
    savedata(d)
