from django.contrib.auth.backends import ModelBackend
import re

from .models import User


def jwt_response_payload_handler(token, user=None, request=None):
    """自定义JWT登陆成功返回数据"""

    return {
        'token': token,
        'username': user.username,
        'user_id': user.id
    }


def get_user_by_account(account):
    """
    通过手机号或者用户名动态获取user
    :param account: 手机号或者用户名
    """

    # # 判断account是不是手机号
    # if re.match(r'1[3-9]\d{9}', account):
    #     # 表示是手机号登录
    #     try:
    #         user = User.objects.get(mobile=account)
    #     except User.DoesNotExist:
    #         return None
    #
    # else:
    #     # 用户名登录
    #     try:
    #         user = User.objects.get(username=account)
    #     except User.DoesNotExist:
    #         return None

    # zx15312345678  # 如果想要实现多账号登录用户名必须不能以数字
    # 13981234567

    try:
        if re.match(r'1[3-9]\d{9}', account):
            user = User.objects.get(mobile=account)
        else:
            user = User.objects.get(username=account)
    except User.DoesNotExist:
        return None

    return user


class UsernameMobileAuthBackend(ModelBackend):
    """自定django认证后端"""

    def authenticate(self, request, username=None, password=None, **kwargs):
        """
        重写认证方法,实现多账号登陆
        :param request: 本次登陆的用户对象
        :param username: 手机号&用户名
        :param password: 密码
        :return: user或者None
        """
        # 通过传入的username 获取到user对象(通过手机号或用户名动态查询user)
        user = get_user_by_account(username)
        # 判断用户user的密码
        if user and user.check_password(password):
            # 验证通过返回user
            return user
