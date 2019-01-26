from django.shortcuts import render

# Create your views here.
from itsdangerous import Serializer
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from QQLoginTool.QQtool import OAuthQQ

from libs.weibo.weibo import OAuthWeibo
from mall import settings
from oauth.models import OAuthQQUser, OAuthWeiboUser
from oauth.serializers import OAuthQQUserSerializer
from oauth.utils import generic_openid

"""
当用户点击QQ按钮的时候会发送一个请求
我们后端返回给他一个url(这个url是根据文档来拼接出来的)

GET   oauth/qq/statues/
"""


class OAuthQQURLAPIView(APIView):

    def get(self, request):

        state = '/'
        # 1.创建OAuthQQ的实例对象
        oauth = OAuthQQ(client_id=settings.QQ_CLIENT_ID,
                        client_secret=settings.QQ_CLIENT_SECRET,
                        redirect_uri=settings.QQ_REDIRECT_URI,
                        state=state)
        # 2.获取跳转的url
        auth_url = oauth.get_qq_url()

        return Response({'auth_url': auth_url})

"""
1.用户同意授权登陆,这时候会返回一个code
2.我们用code换取token
3.有token我们再获取openid
"""
"""
前段会接收到用户同意后的code,前端应该把这个code发送给后端
1.接收这个数据
2.用code换取token
3.用token换取openid

GET  oauth/qq/users/?code=xxxxx
"""


class OAuthQQUserAPIView(APIView):

    def get(self, request):
        # 1.接收这个数据
        params = request.query_params
        code = params.get('code')
        if code is None:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        # 2.用code换取token
        oauth = OAuthQQ(client_id=settings.QQ_CLIENT_ID,
                        client_secret=settings.QQ_CLIENT_SECRET,
                        redirect_uri=settings.QQ_REDIRECT_URI,)
        token = oauth.get_access_token(code)
        # 3.用token换取openid
        openid = oauth.get_open_id(token)

        # openid是此网站上唯一对应用户身份的标识，网站可将此ID进行存储便于用户下次登录时辨识其身份
        # 获取的openid有两种情况:
        # 1.用户之前绑定过
        # 2.用户之前没有绑定过
        try:
            qquser = OAuthQQUser.objects.get(openid=openid)
        except OAuthQQUser.DoesNotExist:
            # openid很重要,所以我对openid有一个处理
            # 绑定也应该有一个时效

            """
            为什么要抽取和封装?
            1.为了解耦
            2.方便复用
            封装和抽取的原则是什么呢?
            1.如果第二次出现的代码,就进行一个封装
            2.实现一个小功能
            封装和抽取的步骤:
            1.定义一个函数
            2.将要抽取的代码复制过来,哪里有问题改哪里,没有的变量定义为参数
            3.验证
            """
            # s = Serializer(secret_key=settings.SECRET_KEY, expires_in=3600)
            # # 2.组织数据
            # data = {
            #     'openid': openid
            # }
            # # 3.让序列化器对数据进行处理
            # token = s.dumps(data)
            token = generic_openid(openid)
            return Response({'access_token': token})
        else:
            from rest_framework_jwt.settings import api_settings
            # 需要使用jwt的两个方法
            jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
            jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER
            # 让payload(载荷)盛放用户信息
            payload = jwt_payload_handler(qquser.user)
            token = jwt_encode_handler(payload)

            return Response({
                'token': token,
                'username': qquser.user.username,
                'user_id': qquser.user.id
            })

    """
    当用户点击绑定的时候,我们需要将手机号,密码,短信验证码和openid传递过来

    1.接收数据
    2.对数据进行校验
    3.保存数据
    4.返回响应

    POST
    """
    def post(self,request):
        # 1.接收数据
        data = request.data
        # 2.对数据进行校验
        serializer = OAuthQQUserSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        # 3.保存数据
        qquser = serializer.save()
        # 4.返回响应 应该有token
        from rest_framework_jwt.settings import api_settings
        # 需要使用jwt的两个方法
        jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
        jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER
        # 让payload(载荷)盛放用户信息
        payload = jwt_payload_handler(qquser.user)
        token = jwt_encode_handler(payload)

        return Response({
            'token': token,
            'username': qquser.user.username,
            'user_id': qquser.user.id
        })



# from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
# # 1.创建一个序列化器
# # 参数secret_key,  秘钥
# # 参数expires_in    有效期,单位:秒
# s = Serializer(secret_key=settings.SECRET_KEY, expires_in=3600)
# # 2.组织数据
# data = {
#     'openid': '1234567890'
# }
# # 3.让序列化器对数据进行处理
# token = s.dumps(data)
# # 4.获取数据,对数据进行解密
# s.loads(token)

class WeiboAuthURLView(APIView):
    """定义微博第三方登录的视图类"""
    def get(self, request):
        """
        获取微博登录的链接
        oauth/weibo/authorization/?next=/
        :param request:
        :return:
        """
        # 1.通过查询字符串
        # next = request.query_params.get('state')
        # if not next:
        #     next = "/"
        # state = '/'

        # 获取微博登录网页
        oauth = OAuthWeibo(client_id=settings.WEIBO_CLIENT_ID,
                        # client_secret=settings.WEIBO_CLIENT_SECRET,
                        redirect_uri=settings.WEIBO_REDIRECT_URI,
                        # state=next
                           )


        login_url = oauth.get_weibo_url()
        return Response({'login_url': login_url})

class WeiboOauthView(APIView):
    """验证微博登录"""
    def get(self, request):
        """
        第三方登录检查
        oauth/sina/user/
        ?code=0e67548e9e075577630cc983ff79fa6a
        :param request:
        :return:
        """
        # 1.获取code值
        code = request.query_params.get("code")

        # 2.检查参数
        if not code:
            return Response({'errors': '缺少code值'}, status=400)

        # 3.获取token值
        next = "/"

        # 获取微博登录网页
        weiboauth = OAuthWeibo(client_id=settings.WEIBO_CLIENT_ID,
                        client_secret=settings.WEIBO_CLIENT_SECRET,
                        redirect_uri=settings.WEIBO_REDIRECT_URI,
                        state=next)
        weibotoken = weiboauth.get_access_token(code=code)
        print(weibotoken)

        # 5.判断是否绑定过美多账号
        try:
            weibo_user = OAuthWeiboUser.objects.get(weibotoken=weibotoken)
        except:
            # 6.未绑定,进入绑定页面,完成绑定
            tjs = Serializer(settings.SECRET_KEY, 300)
            weibotoken = tjs.dumps({'weibotoken': weibotoken}).decode()

            return Response({'access_token': weibotoken})
        else:
            # 7.绑定过,则登录成功
            # 生成jwt-token值
            from rest_framework_jwt.settings import api_settings
            user = weibo_user.user
            jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
            jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER

            payload = jwt_payload_handler(user)  # 生成载荷部分
            token = jwt_encode_handler(payload)  # 生成token

            response = Response(
                {
                    'token': token,
                    'username': user.username,
                    'user_id': user.id
                }
            )

        return response

