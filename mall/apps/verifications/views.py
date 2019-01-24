import random

from django.http import HttpResponse
from django.shortcuts import render

# Create your views here.
from rest_framework.response import Response
from rest_framework.views import APIView
from libs.captcha.captcha import captcha
from django_redis import get_redis_connection

from libs.yuntongxun.sms import CCP
from verifications.serializers import RegisterSmscodeSerializer

'''
1.分析需求 (到底要干什么)
2.把需要做的事情写下来(把思路梳理清楚)
3.请求方式 路由
4.确定视图
5.按照步骤实现功能

前端传递一个 uuid过来 ,我们后端生成一个图片

1.接收 image_code_id
2.生成图片和验证码
3.把验证码保存到redis中
4.返回图片相应
'''


class RegisterImageCodeView(APIView):

    def get(self, request, image_code_id):
        # 1.接受image_code_id
        # 2.生成图片和验证码
        text, image = captcha.generate_captcha()
        # 3.把验证码保存到redis中
        # 3.1连接redis
        redis_conn = get_redis_connection('code')
        # 3.2设置图片
        redis_conn.setex('img_'+image_code_id, 2*60, text)
        # 返回响应
        return HttpResponse(image, content_type='image/jpeg')

'''
1.分析需求 (到底要干什么)
2.把需要做的事情写下来(把思路梳理清楚)
3.请求方式 路由
4.确定视图
5.按照步骤实现功能

当用户点击 获取短信按钮的时候 前端应该将 手机号,图片验证码以及验证码id发送给后端

1.接收参数
2.校验参数
3.生成短信
4.将短信保存在redis中
5.使用云通讯发送短信
6.返回相应
'''

# APIView                        基类
# GenericAPIVIew                 对列表视图和详情视图做了通用支持,一般和mixin配合使用
# ListAPIVIew,RetriveAPIView     封装好了


class RegisterSmscodeView(APIView):

    def get(self, request, mobile):
        # 1.接收参数
        params = request.query_params
        # 2.校验参数
        serializer = RegisterSmscodeSerializer(data=params)
        serializer.is_valid(raise_exception=True)
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