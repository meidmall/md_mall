import random
import re

from django.http import HttpResponse
from django.shortcuts import render

# Create your views here.
from django_redis import get_redis_connection
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.serializers import ForgetImagecodeSerializer, ForgetSmscodeserializer
from accounts.utils import dangerous, undangerous
from users.models import User


"""
  1.输入账号和图片验证码，发送请求到后端，以 get 方式，参数拼接在链接后面；
    2.后端对账号进行验证，调用之前的方法，可以同时判断手机号和账号名，查看有没有当前用户；
    3.使用序列化器对图片验证码进行验证，取出 text 和图片对应 id，从redis中进行查询出真实的图片
     text，判断 text 是否过期，对传过来的 text 和真实 text 进行对比，对比前需要进行转码和转小写，判断成功返回数据；
    4.根据 user 对象生成 access_token；
    5.将手机号的中间四位使用正则的 sub 方法替换成 * 号，防止手机号直接暴露出去；
    6.将修改过的手机号和生成的 token 返回给前端，token 中保存正确的手机号。
"""
class ForGetPasswordAPIView(APIView):

        def get(self, request, username):
            # username_count = User.objects.filter(username=username).count()
            # mobile_count = User.objects.filter(mobile=username).count()
            # if username_count == 0 or mobile_count == 0:
            #     return Response(status=status.HTTP_404_NOT_FOUND)

            try:
                if re.match(r'1[3-9]\d{9}', username):
                    user = User.objects.get(mobile=username)

                else:
                    user = User.objects.get(username=username)

            except User.DoseNotExist:
                user = None

            if user == None:
                return Response(status=status.HTTP_404_NOT_FOUND)

            # 1.接收参数
            params = request.query_params
            # 2.校验参数
            serializer = ForgetImagecodeSerializer(data=params)
            serializer.is_valid(raise_exception=True)

            mobile = user.mobile
            token = dangerous(mobile)

            # 6.返回相应
            return Response({
                'access_token':token,
                'mobile':mobile
            })


#ERROR basehttp 124 "GET /sms_codes/code/?access_token=eyJhbGciOiJIUzI1NiIsImV4cCI6MTU0ODQ3NjMyNSwiaWF0IjoxNTQ4NDc2MDI1fQ.eyJtb2JpbGUiOiIxNTg3Mjg1ODExNyJ9.kCN6pHBGCIpLn_fex_SuCYupRUp93jCBdCC0XVx64_c HTTP/1.1" 500 94302

class SmscodeAPIView(APIView):
    def get(self,request,):

        # 1.接收参数
        params = request.query_params
        #获取accress_token
        access_token = params['access_token']
        #通过isdangerous解码获取手机号,注意 因为undangoerous返回的是一个字典 我们需要获取字典中的mobile对应的值mobile
        token_dict_mobile = undangerous(access_token)
        mobile = token_dict_mobile['mobile']
        # # 2.校验参数
        # serializer = ForgetSmscodeserializer(data=params)
        # serializer.is_valid(raise_exception=True)
        # 3.生成短信
        sms_code = '%06d' % random.randint(0, 999999)
        # 4.将短信保存在redis中
        redis_conn = get_redis_connection('code')
        redis_conn.setex('sms_'+mobile, 2*60, sms_code)
        # 5.使用云通讯发送短信
        # CCP().send_template_sms(mobile, [sms_code, 5], 1)
        from celery_tasks.sms.tasks import send_sms_code
        # delay的参数和任务的参数对应
        # 必须调用delay方法
        send_sms_code.delay(mobile, sms_code)



        # 6.返回相应
        return Response({'msg': 'ok'})
#http://api.meiduo.site:8000/accounts/qwert/password/token/?sms_code=987271
class SmscodeVerification(APIView):
    def get(self,request,username):
        params = request.query_params.dict()
        params['username'] = username
        serializer = ForgetSmscodeserializer(data=params)
        serializer.is_valid(raise_exception=True)

        user = User.objects.get(username=username)

        token = dangerous(user.id)
        user_id = user.id
        return Response({
            'access_token':token,
            'user_id':user_id
        })

# class AuthenticationAPIView(APIView):
#
#     pass

