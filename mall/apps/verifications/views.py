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

"""
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

GET         /verifications/imagecodes/(?P<image_code_id>.+)/

GET         /verifications/imagecodes/?image_code_id=xxxxxx

"""
#APIView                        基类
#GenericAPIVIew                 对列表视图和详情视图做了通用支持,一般和mixin配合使用
#ListAPIVIew,RetriveAPIView     封装好了

class RegisterImageAPIView(APIView):

    def get(self,request,image_code_id):
        # 1.接收image_code_id
        # 2.生成图片和验证码
        text,image = captcha.generate_captcha()
        # 3.把验证码保存到redis中
        #3.1连接redis
        redis_conn = get_redis_connection('code')
        #3.2设置图片
        redis_conn.setex('img_'+image_code_id,60,text)
        # 4.返回图片相应

        # return HttpResponse(image)
        return HttpResponse(image,content_type='image/jpeg')
        # return Response()


"""
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

GET             /verifications/smscodes/(?P<mobile>1[345789]\d{9})/?text=xxxx & image_code_id=xxxx
一种是 路由  weather/beijing/2018/
另外一个是 查询字符串 weather/?place=beijing&year=2018
混合起来也是可以的
        weather/2018/?place=beijing
"""

#APIView                        基类
#GenericAPIVIew                 对列表视图和详情视图做了通用支持,一般和mixin配合使用
#ListAPIVIew,RetriveAPIView     封装好了

class RegisterSmscodeAPIView(APIView):

    def get(self,request,mobile):
        # 1.接收参数
        params = request.query_params
        # 2.校验参数  还需要验证码 用户输入的图片验证码和redis的保存 是否一致
        serializer = RegisterSmscodeSerializer(data=params)
        serializer.is_valid(raise_exception=True)
        # 3.生成短信
        sms_code = '%06d'%random.randint(0,999999)
        # 4.将短信保存在redis中
        redis_conn = get_redis_connection('code')


        redis_conn.setex('sms_'+mobile,5*60,sms_code)
        # 5.使用云通讯发送短信
        # CCP().send_template_sms(mobile,[sms_code,5],1)

        from clery_tasks.sms.tasks import send_sms_code
        # delay 的参数和 任务的参数对应
        # 必须调用 delay 方法
        send_sms_code.delay(mobile,sms_code)

        # 6.返回相应
        return Response({'msg':'ok'})

        """
        写信
        投递到邮箱

        """

