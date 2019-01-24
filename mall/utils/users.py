import re

from users.models import User


def jwt_response_payload_handler(token, user=None, request=None):
    # token,   jwt生成的token
    # user=None,   jwt验证成功之后的user
    # request=None    请求
    return {
        'token': token,
        'username': user.username,
        'user_id': user.id
    }


from django.contrib.auth.backends import ModelBackend
'''
1.定义一个方法
2.把要抽取的代码复制过去,哪里有问题改哪里,没有的变量定义为参数
3.验证
'''


def get_user_by_account(username):
    try:
        if re.match(r'1[3-9]\d{9}', username):
            user = User.objects.get(mobile=username)
        else:
            user = User.objects.get(username=username)
    except User.DoseNotExist:
        user = None
    return user


class UsernameMobileModelBackend(ModelBackend):

    def authenticate(self, request, username=None, password=None, **kwargs):

        # 1.根据用户名确认用户输入的是手机号还是用户名
        # try:
        #     if re.match(r'1[3-9]\d{9}', username):
        #         user = User.objects.get(mobile = username)
        #     else:
        #         user = User.objects.get(username = username)
        # except User.DoseNotExist:
        #     user = None
        user = get_user_by_account(username)
        # 2.验证密码
        if user is not None and user.check_password(password):
            return user
        return None


class MyBackend(object):
    def authenticate(self, request, username=None, password=None):
        user = get_user_by_account(username)
        # 2.验证密码
        if user is not None and user.check_password(password):
            return user
        return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None