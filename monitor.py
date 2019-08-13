import time

import itchat
import json
import requests
import sys

from click._compat import raw_input


class monitor ():

    def __init__(self, ):
        self.session = requests.session ()
        # 请求头
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:54.0) Gecko/20100101 Firefox/54.0',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Referer': 'https://passport.weibo.cn/signin/login',
            'Connection': 'close',
            'Accept-Language': 'zh-CN,zh;q=0.8,en-US;q=0.5,en;q=0.3'
        }

    def login(self, username, password):
        """
        登录新浪
        :param username:
        :param password:
        :return:
        """
        # 登录URL
        login_url = 'https://passport.weibo.cn/sso/login'

        # 请求数据
        data = {
            'username': username,
            'password': password,
            'savestate': 1,
            'entry': 'mweibo',
            'mainpageflag': 1
        }
        try:
            r = self.session.post (login_url, data=data, headers=self.headers)
            if r.status_code == 200 and json.loads (r.text)['retcode'] == 20000000:
                self.echoMsg ('Info', '登录成功! UserId:' + json.loads (r.text)['data']['uid'])
            else:
                self.echoMsg ('Error', '登录失败')
                sys.exit ()
        except Exception as e:
            self.echoMsg ('Error', e)
            sys.exit ()

    def get_wb_info(self, wb_user_id):
        # 获取containerid
        global containerid
        user_info = 'https://m.weibo.cn/api/container/getIndex?uid=%s&type=uid&value=%s' % (wb_user_id, wb_user_id)
        try:
            r = self.session.get (user_info, headers=self.headers)
            for i in r.json ()['data']['tabsInfo']['tabs']:
                if i['tab_type'] == 'weibo':
                    containerid = i['containerid']
        except Exception as e:
            self.echoMsg ('Error', e)
            sys.exit ()
        # 获取发文信息
        self.weibo_info = 'https://m.weibo.cn/api/container/getIndex?uid=%s&type=uid&value=%s&containerid=%s' % (
            wb_user_id, wb_user_id, containerid)
        try:
            r = self.session.get (self.weibo_info, headers=self.headers)
            self.itemIds = []
            for i in r.json ()['data']['cards']:
                if i['card_type'] == 9:
                    self.itemIds.append (i['mblog']['id'])
            self.echoMsg ('Info', '成功获取微博发文信息')
            self.echoMsg ('Info', '有 %d 篇文章' % len (self.itemIds))
        except Exception as e:
            self.echoMsg ('Error', e)
            sys.exit ()

    @property
    def start_monitor(self, ):
        wb_dict = {}
        try:
            r = self.session.get (self.weibo_info, headers=self.headers)
            for i in r.json ()['data']['cards']:
                if i['card_type'] == 9:
                    if str (i['mblog']['id']) not in self.itemIds:
                        self.itemIds.append (i['mblog']['id'])
                        self.echoMsg ('Info', '发布新的文章啦！！！')
                        wb_dict['created_at'] = i['mblog']['created_at']
                        wb_dict['text'] = i['mblog']['text']
                        wb_dict['source'] = i['mblog']['source']
                        wb_dict['nick_name'] = i['mblog']['user']['screen_name']
                        wb_dict['url'] = i['scheme']
                        # 如果包含图片
                        if 'pics' in i['mblog']:
                            wb_dict['pic_urls'] = []
                            for j in i['mblog']['pics']:
                                wb_dict['pic_urls'].append (j['url'])
                        return wb_dict
            self.echoMsg ('Info', '有 %d 篇文章' % len (self.itemIds))
        except Exception as e:
            self.echoMsg ('Error', e)
            sys.exit ()

    def echoMsg(self, level, msg):
        if level == 'Info':
            print ('[Info] %s' % msg)
        elif level == 'Error':
            print ('[Error] %s' % msg)


def start(username, password, wb_user_id, wx_user_id):
    """
    :param username:微博用户名
    :param password:微博用户密码
    :param wb_user_id:微博被监听用户userid
    :param wx_user_id:微信接收消息userid
    :return:
    """
    m = monitor ()
    m.login (username, password)
    m.get_wb_info (wb_user_id)
    while 1:
        new_wb = m.start_monitor
        if new_wb is not None:
            print (new_wb)
            itchat.send (new_wb['text'] + "\n" + new_wb['url'], wx_user_id)
        time.sleep (60)


def wechat_login():
    itchat.auto_login (hotReload=True)
    user_info = itchat.search_friends ("元大头")
    return user_info[0]["UserName"]


if __name__ == '__main__':
    wx_user_id=wechat_login ()
    wb_user_id = '2492465520'
    username = '15029903732'
    password = raw_input ('请输入微博登陆密码: ')
    start (username, password, wb_user_id, wx_user_id)
