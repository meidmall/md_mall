from django_redis import get_redis_connection
from rest_framework import serializers

from oauth.models import OAuthQQUser
from oauth.utils import check_access_token
from users.models import User

"""
加密的openid,手机号,密码,短信验证码, 对这些数据进行校验
校验没有问题,保存数据的时候是保存user和openid
"""


class OAuthQQUserSerializer(serializers.Serializer):
    """
       QQ登录创建用户序列化器
       """
    access_token = serializers.CharField(label='操作凭证')
    mobile = serializers.RegexField(label='手机号', regex=r'^1[3-9]\d{9}$')
    password = serializers.CharField(label='密码', max_length=20, min_length=8)
    sms_code = serializers.CharField(label='短信验证码')

    def validate(self, attrs):
        # 1.对openid进行验证处理
        access_token = attrs.get('access_token')
        openid = check_access_token(access_token)
        # 通过attrs来传递数据
        attrs['openid'] = openid
        if openid is None:
            return serializers.ValidationError('openid错误')
        # 2.需要对短信进行验证
        # 2.1获取用户提交的短信
        sms_code = attrs['sms_code']
        mobile = attrs.get('mobile')
        # 2.2获取redis中的短信
        redis_conn = get_redis_connection('code')
        redis_code = redis_conn.get('sms_' + mobile)
        # 是否过期
        if redis_code is None:
            raise serializers.ValidationError('验证码过期')
        redis_conn.delete('sms_' + mobile)
        # 2.3比对
        if sms_code != redis_code.decode():
            raise serializers.ValidationError('验证码错误')
        # 3.需要对手机号进行判断
        try:
            user = User.objects.get(mobile=mobile)
        except User.DoesNotExist:
            # 没有用户就创建用户,在create方法中创建
            pass
        else:
            # 有用户就验证密码
            if not user.check_password(attrs['password']):
                raise serializers.ValidationError('密码错误')
            attrs['user'] = user
        return attrs

    def create(self, validated_data):

        user = validated_data.get('user')
        if user is None:
            user = User.objects.create(
                mobile=validated_data['mobile'],
                username=validated_data['mobile'],
                password=validated_data['password']
            )
            user.set_password(validated_data['password'])
            user.save()
        qquser = OAuthQQUser.objects.create(
            user=user,
            openid=validated_data['openid']
        )
        return qquser