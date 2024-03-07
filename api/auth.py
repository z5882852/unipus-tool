import base64
import json
import time
import requests
from requests import Session
from PIL import Image


class UAuth:
    def __init__(self, session: Session, username, password):
        self.session = session
        self.username = username
        self.password = password
        # self.session = session

    def login_api(self, captcha="", encodeCaptha=None):
        """
        登录

        captha: 验证码
        encodeCaptha: 验证码标识
        """
        url = "https://sso.unipus.cn/sso/0.1/sso/login"
        data = {
            "service": "https://u.unipus.cn/user/comm/login?school_id=",
            "username": self.username,
            "password": self.password,
            "captcha": captcha,
            "rememberMe": "on",
            "captchaCode": captcha,
        }
        if encodeCaptha is not None:
            data.update({'encodeCaptha': encodeCaptha})
        data = json.dumps(data, separators=(',', ':'))
        response = self.session.post(url, data=data)
        if response.status_code != 200:
            return 1, f"登录失败，status_code:{response.status_code}", None
        data = response.json()
        if data.get("code") == "1502":
            return 3, f"登录失败，{data.get('msg', '未知错误')}", None
        elif data.get("code") == "0":
            return 0, f"登录成功！用户名: {data.get('rs', {}).get('nickname', '未知')}", data.get('rs', None)
        return 4, f"{data.get('msg', '未知错误')}", None

    def get_captcha_img(self):
        url = "https://sso.unipus.cn/sso/4.0/sso/image_captcha2"
        response = self.session.post(url)
        if response.status_code != 200:
            return 1, f"获取验证码失败，status_code:{response.status_code}", None
        data = response.json()
        if data.get("code") == "0" and data.get('rs', None) is not None:
            return 0, f"成功", data.get('rs', None)
        return 2, f"{data.get('msg', '未知错误')}", None

    def show_captcha_img(self, base64_data):
        with open('./data/captcha/captcha.jpg', 'wb') as file:
            image = base64.b64decode(base64_data)
            file.write(image)
        img = Image.open('./data/captcha/captcha.jpg')
        img.show()

    def get_captcha(self):
        code, mes, data = self.get_captcha_img()
        if code != 0 and data is not None:
            print(mes)
        img_data = data.get("image")
        encodeCaptha = data.get("encodeCaptha")
        self.show_captcha_img(img_data)
        captcha_code = input("请输入验证码: ")
        return captcha_code, encodeCaptha

    def login(self):
        code, mes, data = self.login_api()
        if code == 0:
            return data
        if mes != "需要图片或者滑块验证码":
            raise Exception(f"登录失败, {mes}")
        while True:
            captcha_code, encodeCaptha = self.get_captcha()
            code, mes, data = self.login_api(captcha_code, encodeCaptha)
            print(mes)
            if code == 0:
                return data
            raise Exception(f"登录失败, {mes}")

    def login_ticket(self, school_id, ticket):
        url = "https://u.unipus.cn/user/comm/login"
        params = {
            "school_id": school_id,
            "ticket": ticket
        }
        self.session.get(url, params=params)

    def repeat_login(self):
        url = "https://u.unipus.cn/repeatLogin"
        response = self.session.get(url)
        print(response.text)
        print(response)

    def print_user_info(self, openId):
        url = "https://ucamapi.unipus.cn/rpc/api/user-info"
        params = {
            "openId": openId,
            "source": "0",
            "callback": "jsonp_0000000000"
        }
        response = self.session.get(url, params=params)
        if response.status_code != 200:
            print(f"获取用户信息失败，status_code:{response.status_code}")
        try:
            text = response.text[17:-1]

            data = json.loads(text)
            print(f'用户名: {data["result"]["user"]["username"]}')
            print(f'昵称: {data["result"]["user"]["nickname"]}')
            print(f'真实姓名: {data["result"]["user"]["name"]}')
            print(f'学号: {data["result"]["user"]["num"]}')
            print(f'学校名: {data["result"]["user"]["schoolName"]}')
        except Exception as e:
            print(f"获取用户信息失败, Exception: {e}")
            raise Exception(e)
        return data

    def set_token(self):
        """
        在headers设置X-Annotator-Auth-Token:
        """
        url = "https://u.unipus.cn/user/data/getToken"
        params = {
            "_": int(time.time() * 1000)
        }
        response = self.session.get(url, params=params)
        if response.status_code != 200:
            print("获取token失败")
            return None
        data = response.json()
        token = data.get("token")
        headers = self.session.headers
        headers.update({"X-Annotator-Auth-Token": token})
        self.session.headers = headers
        print("获取token成功")
        return token
