from django.shortcuts import render

# Create your views here.
from rest_framework.response import Response
from rest_framework.views import APIView
from QQLoginTool.QQtool import OAuthQQ
from mall import settings
from rest_framework import status

from oauth.models import OAuthQQUser
from oauth.serializers import OAuthQQUserSerializer
from oauth.utils import generic_open_id

"""
当用户点击qq按钮的时候,会发送一个请求,
我们后端返回给它一个 url (URL是根据文档来拼接出来的)
GET     /oauth/qq/statues/

"""

class OAuthQQURLAPIView(APIView):

    def get(self,request):


        # auth_url = 'https://graph.qq.com/oauth2.0/authorize?response_type=code&client_id=101474184&redirect_uri=http://www.meiduo.site:8080/oauth_callback.html&state=test'
        #成功之后 回调到哪里去
        state = '/'
        #1.创建oauthqq的实例对象
        oauth = OAuthQQ(client_id=settings.QQ_CLIENT_ID,
                        client_secret=settings.QQ_CLIENT_SECRET,
                        redirect_uri=settings.QQ_REDIRECT_URI,
                        state=state)

        #2. 获取跳转的url
        auth_url = oauth.get_qq_url()

        return Response({'auth_url':auth_url})

"""
1. 用户同意授权登陆,这个时候 会返回一个 code
2. 我们用code 换取 token
3. 有了token,我们再获取 openid
"""

"""
1.分析需求 (到底要干什么)
2.把需要做的事情写下来(把思路梳理清楚)
3.路由和请求方式
4.确定视图
5.按照步骤实现功能


前端会接收到 用户同意之后的, code 前端应该将这个code 发送给后端

1. 接收这个数据
2. 用code换token
3. 用token换openid

GET     /oauth/qq/users/?code=xxxxxx
"""

class OAuthQQUserAPIView(APIView):

    def get(self,request):
        # 1. 接收这个数据
        params = request.query_params
        code = params.get('code')
        if code is None:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        # 2. 用code换token
        oauth = OAuthQQ(client_id=settings.QQ_CLIENT_ID,
                        client_secret=settings.QQ_CLIENT_SECRET,
                        redirect_uri=settings.QQ_REDIRECT_URI)
        token = oauth.get_access_token(code)
        # '336DAF004732E4FB403B7C0FBE9C33DE'
        # 3. 用token换openid
        openid = oauth.get_open_id(token)

        #openid是此网站上唯一对应用户身份的标识，网站可将此ID进行存储便于用户下次登录时辨识其身份
        # 获取的openid有两种情况:
        # 1. 用户之前绑定过
        # 2. 用户之前没有绑定过

        # 根据openid查询数据
        try:
            qquser = OAuthQQUser.objects.get(openid=openid)
        except OAuthQQUser.DoesNotExist:
            #不存在

            # openid 很重要 ,所以我们需要对openid进行一个处理
            # 绑定也应该有一个时效

            """
            为什么要抽取和封装?
            1. 为了解耦
            2. 为了方便复用

            封装和抽取的原则是什么呢?
            1. 如果第二次出现的代码 就进行封装
            2. 实现了一个小功能

            封装和抽取的步骤
            1. 定义一个函数
            2. 将要抽取的代码 复制过来 哪里有问题改哪里 没有的变量定义为参数
            3. 验证

            """

            # s = Serializer(secret_key=settings.SECRET_KEY, expires_in=3600)
            #
            # # 2. 组织数据
            # data = {
            #     'openid': openid
            # }
            #
            # # 3. 让序列化器对数据进行处理
            # token = s.dumps(data)

            token = generic_open_id(openid)

            return  Response({'access_token':token})

        else:
            # 存在,应该让用户登陆

            from rest_framework_jwt.settings import api_settings

            jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
            jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER

            payload = jwt_payload_handler(qquser.user)
            token = jwt_encode_handler(payload)

            return Response({
                'token':token,
                'username':qquser.user.username,
                'user_id':qquser.user.id
            })

        # finally:
        #     pass

    """
    当用户点击绑定的时候 ,我们需要将 手机号,密码,短信验证码和加密的openid 传递过来

    1. 接收数据
    2. 对数据进行校验
    3. 保存数据
    4. 返回相应


    POST    /oauth/qq/users/

    """
    def post(self,request):
        # 1. 接收数据
        data = request.data
        # 2. 对数据进行校验
        serializer = OAuthQQUserSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        # 3. 保存数据
        qquser = serializer.save()
        # 4. 返回相应, 应该有token数据

        from rest_framework_jwt.settings import api_settings

        jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
        jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER

        payload = jwt_payload_handler(qquser.user)
        token = jwt_encode_handler(payload)

        return Response({
            'token': token,
            'username': qquser.user.username,
            'user_id': qquser.user.id
        })






from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from mall import settings
from itsdangerous import BadSignature,SignatureExpired

#1. 创建一个序列化器
#  secret_key,   秘钥
# expires_in=None  过期时间 单位是:秒
s = Serializer(secret_key=settings.SECRET_KEY,expires_in=3600)

#2. 组织数据
data = {
    'openid':'1234567890'
}

#3. 让序列化器对数据进行处理
token = s.dumps(data)

#eyJpYXQiOjE1NDcwODkwODAsImV4cCI6MTU0NzA5MjY4MCwiYWxnIjoiSFMyNTYifQ.
# eyJvcGVuaWQiOiIxMjM0NTY3ODkwIn0.
# OGyy5mJ5s4fNvH9gmREyJoC8raeEQPU40LpThD-lIl8


# 4. 获取数据对数据进行 解密
s.loads(token)





s = Serializer(secret_key=settings.SECRET_KEY,expires_in=1)

#2. 组织数据
data = {
    'openid':'1234567890'
}

#3. 让序列化器对数据进行处理
token = s.dumps(data)