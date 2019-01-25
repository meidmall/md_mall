from django.http import HttpResponse
from django.shortcuts import render

# Create your views here.
from rest_framework import status
from rest_framework.response import Response

from rest_framework.views import APIView

from goods.models import SKU
from libs.captcha import captcha
from users.models import User, Address
from users.serializers import RegisterUserSerializer, UserCenterInfoSerializer, UserEmailInfoSerializer, \
    AddressSerializer, AddUserBrowsingHistorySerializer, SKUSerializer
from users.utils import check_token

'''
1. 前段发送用户名给后端,后端判断用户名是否存在
请求方式:
GET    /users/usernames/(?P<username>\w{5,20})/count/


'''


class RegisterUsernameAPIView(APIView):

    def get(self, request, username):
        count = User.objects.filter(username=username).count()

        return Response({'count': count,
                        'username': username})
'''
接收前段发过来的手机号
GET   /users/mobile/(?P<mobile>1[3-9]\d{9})/count
'''


class RegisterMobileAPIView(APIView):

    def get(self, request, mobile):
        count = User.objects.filter(mobile=mobile).count()

        return Response({'mobile': mobile,
                        'count': count})

'''
当用户点击注册按钮的时候,前端需要收集手机号,用户名,密码,短信验证码,确认密码,是否同意协议

1.接收数据
2.校验数据
3.数据入库
4.返回响应

请求方式:POST   /users/register/
'''


class RegisterUserAPIView(APIView):

    def post(self, request):
        # 1.接收数据
        data = request.data
        # 2.校验数据
        serializer = RegisterUserSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        # 3.数据入库
        serializer.save()
        # 4.返回响应
        # 序列化:将模型转换为json
        # 如何序列化的呢?我们的序列化器是根据字段来查询模型中对应的字段,如果序列化器中有,模型中没有就会报错
        # 如果字段设置为write_only,则会在序列化中忽略此字段
        return Response(serializer.data)

'''
当用户注册成功之后自动登陆
自动登陆的功能是要求用户注册成功之后,返回数据的时候需要额外添加一个token

1.序列化的时候添加一个token
2.这个token怎么生成
'''

'''
个人中心的信息展示
必须是登陆用户才可以访问
1.让前端传递用户信息
2.我们根据用户信息获取user
3.将对象转换为json(字典)数据

GET  /users/infos/
'''
from rest_framework.permissions import IsAuthenticated
# class UserCenterInfoAPIView(APIView):
#     # 添加权限   必须是登陆用户才可以访问
#     permission_classes = [IsAuthenticated]
#
#     def get(self, request):
#
#         # 1.获取用户信息
#         user = request.user
#         # 2.将模型转换为字典(Json)
#         serializer = UserCenterInfoSerializer(user)
#         return Response(serializer.data)
from rest_framework.generics import RetrieveAPIView


class UserCenterInfoAPIView(RetrieveAPIView):
    # 添加权限   必须是登陆用户才可以访问
    permission_classes = [IsAuthenticated]

    serializer_class = UserCenterInfoSerializer

    def get_object(self):

        return self.request.user

"""
当用户输入邮箱之后点击保存的时候
我们需要将邮箱内容发送给后端,后端需要更新指定用户的email字段
同时后端需要给这个邮箱发送一个激活链接
当用户点击激活链接的时候,改变email_avtive的状态

1.接收数据
2.校验
3.保存数据
4.返回响应

PUT  users/emails/
"""


# class UserEmailInfoAPIView(APIView):
#
#     permission_classes = [IsAuthenticated]
#
#     def put(self, request):
#         data = request.data
#         serializer = UserEmailInfoSerializer(instance=request.user, data=data)
#         serializer.is_valid(raise_exception=True)
#         serializer.save()
#         return Response(serializer.data)

from rest_framework.generics import UpdateAPIView


class UserEmailInfoAPIView(UpdateAPIView):

    permission_classes = [IsAuthenticated]

    serializer_class = UserEmailInfoSerializer

    def get_object(self):

        return self.request.user


"""
激活需求
当用户点击激活链接的时候,需要让前端接收到token信息
然后让前端发送一个请求,这个请求包含token信息

1.接收token信息
2.对token信息进行解析
3.解析获取user_id之后进行查询
4.修改状态
5.返回响应

GET    /emails/verification/
"""


class UserEmailVerificationAPIView(APIView):

    def get(self, request):
        # 1.接收token信息
        token = request.query_params.get('token')
        if token is None:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        # 2.对token信息进行解析
        user_id = check_token(token)
        if user_id is None:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        # 3.解析获取user_id之后进行查询
        user = User.objects.get(pk=user_id)
        # 4.修改状态
        user.email_active = True
        user.save()
        # 5.返回响应
        return Response({'msg': 'ok'})

"""
1.分析需求 (到底要干什么)
2.把需要做的事情写下来(把思路梳理清楚)
3.路由和请求方式
4.确定视图
5.按照步骤实现功能

新增地址

1. 后端接收数据
2. 对数据进行校验
3. 数据入库
4. 返回相应

POST        /users/addresses/

"""
from rest_framework.generics import CreateAPIView, ListAPIView


class UserAddressAPIView(CreateAPIView, ListAPIView):

    serializer_class = AddressSerializer
    queryset = Address.objects.all()

    def get(self, request, *args, **kwargs):
        data = self.get_queryset()
        serializer = self.get_serializer(data, many=True)
        user = self.request.user

        return Response({
            'user_id': user.id,
            'default_address_id': user.default_address_id,
            'limit': 20,
            'addresses': serializer.data,
        })


"""
1.分析需求 (到底要干什么)
2.把需要做的事情写下来(把思路梳理清楚)
3.路由和请求方式
4.确定视图
5.按照步骤实现功能

最近浏览记录
1.必须是登陆用户的我们才记录浏览记录
2.在详情页面中添加,添加商品Id和用户id
3.把数据保存在数据库中是没问题的
4.我们把数据保存在redis的列表中回顾redis

添加浏览记录的业务逻辑
1.接收商品id
2.校验数据
3.保存到redis中
4.返回响应

POST   users/histories
"""
from rest_framework.mixins import CreateModelMixin
from django_redis import get_redis_connection


class UserHistoryAPIView(CreateAPIView):

    permission_classes = [IsAuthenticated]

    serializer_class = AddUserBrowsingHistorySerializer
    '''
    获取浏览记录数据
    1.从redis中获取数据   [1,2,3]
    2.根据id查询数据     [sku,sku,sku]
    3.使用序列化器转换数据
    4.返回响应
    '''
    def get(self, request):

        # 1.获取用户信息
        user_id = request.user.id
        # 2.连接redis
        redis_conn = get_redis_connection('history')
        # 3.获取redis中的数据
        redis_sku_id = redis_conn.lrange('history_%s' % user_id, 0, 5)
        skus = []
        for sku_id in redis_sku_id:
            sku = SKU.objects.get(pk=sku_id)
            skus.append(sku)
        # 序列化
        serializer = SKUSerializer(skus, many=True)
        return Response(serializer.data)

from rest_framework_jwt.views import ObtainJSONWebToken
from carts.utils import merge_cookie_to_redis


class MergeLoginAPIView(ObtainJSONWebToken):

    def post(self, request, *args, **kwargs):
        # 调用jwt扩展的方法，对用户登录的数据进行验证
        response = super().post(request)

        # 如果用户登录成功，进行购物车数据合并
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            # 表示用户登录成功
            user = serializer.validated_data.get("user")
            # 合并购物车
            # merge_cart_cookie_to_redis(request, user, response)
            response = merge_cookie_to_redis(request, user, response)

        return response


# 忘记密码重置密码
"""

总体思路：
    找回密码
    找回密码步骤
    输入账号用户名与图片验证码来获取用户手机号，以便对操作人进行身份认证
    发送短信验证码，完成身份认证
    填写两次新密码，并提交
    完成密码重置



第一步——这一步主要是判断用户的账号是否存在：
    1.输入账号和图片验证码，发送请求到后端，以 get 方式，参数拼接在链接后面；
    2.后端对账号进行验证，调用之前的方法，可以同时判断手机号和账号名，查看有没有当前用户；
    3.使用序列化器对图片验证码进行验证，取出 text 和图片对应 id，从redis中进行查询出真实的图片
     text，判断 text 是否过期，对传过来的 text 和真实 text 进行对比，对比前需要进行转码和转小写，判断成功返回数据；
    4.根据 user 对象生成 access_token；
    5.将手机号的中间四位使用正则的 sub 方法替换成 * 号，防止手机号直接暴露出去；
    6.将修改过的手机号和生成的 token 返回给前端，token 中保存正确的手机号。

    技术点：
        使用 itsdangerous 生成凭据 access_token，使用 TimedJSONWebSignatureSerializer 可以生成带有有效期的 token。
        JWT 和 itsdangerous 生成的token区别是，JWT 生成的 token 用来保持登录状态使用，
        而 其他需要验证的 token 都使用由 itsdangerous 生成的。

第二步——这一步主要是验证用户的手机号：
    前端发送请求，带上上一步生成的 access_token；
    在模型类中定义验证 token 的方法，使用 itdangerous 提供的方法进行反验证，
    取出存在 token 中的手机号，进行判断是否在 60s 内，防止重复发送；
    生成短信验证码，存入 redis，使用异步 celery 发送短信；
    返回成功消息；

第三步——返回用于设置密码的接口调用凭据 access_token:
    用户收到短信并填写短信验证码；
    发送请求到后端，带上 account 和 sms_code;
    后端编写序列化器对参数进行校验；
    生成用于修改密码的 token，将 user_id 保存进去，返回 user_id 和 token

第四步——进行密码的重置：
    进入到这一步，用户的身份已经被确认，进行密码的重置即可，
    为了防止被别人拿着 access_token 去对别人的用户进行设置，
    所以也需要对 user_id 和 access_token 中保存的 user_id 进行比较，确认了身份在进行修改。

    在模型类中实现检验修改密码 token 的方法，取出 data，判断 user_id 是否一样；
    定义重置密码序列化器，判断两次密码是否一样，判断是否是当前用户，返回数据；
    调用 updata 方法更新密码；
    返回重置密码成功信息。
"""
