from django_redis import get_redis_connection
from rest_framework import serializers

from users.models import User


class ForgetImagecodeSerializer(serializers.Serializer):

    text = serializers.CharField(max_length=4, min_length=4, required=True)
    image_code_id = serializers.UUIDField(required=True)

    def validate(self, attrs):
        # 1.获取用户提交的验证码
        text = attrs['text']
        # 2. 获取redis的验证码
        # 2.1连接redis
        redis_conn = get_redis_connection('code')
        # 2.2 获取数据
        image_id = attrs.get('image_code_id')
        redis_text = redis_conn.get('img_'+str(image_id))
        # 2.3 redis的数据有时效
        if redis_text is None:
            raise serializers.ValidationError('图片验证码过期')
        # 3. 比对
        # 3.1. redis的数据是bytes类型
        # 3.2  大小写的问题
        if redis_text.decode().lower() != text.lower():
            raise serializers.ValidationError('验证码错误')

        return attrs

class ForgetSmscodeserializer(serializers.Serializer):

    sms_code = serializers.CharField(label='短信验证码', max_length=6,
                                     min_length=6, required=True,
                                     allow_blank=False, write_only=True)
    def validate(self, attrs):
        # 2.1获取用户提交的短信
        sms_code = attrs['sms_code']
        #self.initail_data里有username
        username = self.initial_data['username']

        user = User.objects.get(username=username)
        mobile = user.mobile


        # 2.2获取redis中的短信
        redis_conn = get_redis_connection('code')
        redis_code = redis_conn.get('sms_'+mobile)
        # 是否过期
        if redis_code is None:
            raise serializers.ValidationError('验证码过期')
        redis_conn.delete('sms_' + mobile)
        # 2.3比对
        if sms_code != redis_code.decode():
            raise serializers.ValidationError('验证码错误')
        return attrs
