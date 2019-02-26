import json
from urllib.parse import urlencode, parse_qs

import requests


class OAuthWeibo(object):
    """微博认证辅助工具"""
    def __init__(self, client_id=None, client_secret=None, redirect_uri=None, state=None):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.state = state  # 用于保存登录成功后的跳转页面路径

    def get_weibo_url(self):
        # 微博登陆url参数组建
        data_dict = {
            'client_id': self.client_id,
            'response_type': 'code',
            'redirect_uri': self.redirect_uri,
            'client_secret': self.client_secret,
            'state': self.state,
        }

        # 构建url
        weibo_url = 'https://api.weibo.com/oauth2/authorize?' + urlencode(data_dict)
        return weibo_url

    # 获取access_token值
    def get_access_token(self, code):
        # 构建参数数据
        data_dict = {
            'grant_type': 'authorization_code',
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'redirect_uri': self.redirect_uri,
            'code': code
        }

        # 构建url
        access_url = 'https://api.weibo.com/oauth2/access_token?' + urlencode(data_dict)

        # 发送请求
        try:
            response = requests.post(access_url)
            data = response.text
            data = json.loads(data)
        except:
            raise Exception('微博请求失败')

        # 提取access_token
        access_token = data.get('access_token', None)

        if not access_token:
            raise Exception('access_token获取失败')

        return access_token

