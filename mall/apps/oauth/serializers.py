import re

from django_redis import get_redis_connection
from itsdangerous import Serializer
from rest_framework import serializers

from mall import settings
from oauth.models import OAuthQQUser, OAuthWeiboUser
from oauth.utils import check_access_token
from users.models import User
from verifications.views import RegisterSmscodeView

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

class WeiboOauthSerializers(serializers.ModelSerializer):
    """微博验证序列化器"""

    # 指名模型类中没有的字段
    mobile = serializers.CharField(max_length=11)
    sms_code = serializers.CharField(max_length=6, min_length=6, write_only=True)
    access_token = serializers.CharField(write_only=True)  # 反序列化输入

    token = serializers.CharField(read_only=True)
    user_id = serializers.IntegerField(read_only=True)  # 序列化输出

    class Meta:
        model = User
        fields = ('password', 'mobile', 'username', 'sms_code', 'token', 'access_token', 'user_id')

        extra_kwargs = {
            'username': {
                'read_only': True
            },
            'password': {
                'write_only': True
            }
        }

    def validated_mobile(self, value):
        """
        验证手机号
        :param value:
        :return:
        """
        if not re.match(r"1[3-9]\d{9}$", value):
            raise serializers.ValidationError("手机号格式错误")
        return value

    def validate(self, attrs):
        """
        验证access_token
        :param attrs:
        :return:
        """
        tjs = Serializer(settings.SECRET_KEY, 300)
        try:
            data = tjs.loads(attrs["access_token"])  # 解析token
        except:
            raise serializers.ValidationError("无效的token")

        # 获取weibotoken
        weibotoken = data.get("weibotoken")
        # attrs中添加weibotoken
        attrs["weibotoken"] = weibotoken
        # 验证短信验证码:
        rel_sms_code = RegisterSmscodeView.checkSMSCode(attrs["mobile"])
        if not rel_sms_code:
            raise serializers.ValidationError('短信验证码失效')
            # 3、比对用户输入的短信和redis中真实短信
        if attrs['sms_code'] != rel_sms_code:
            raise serializers.ValidationError('短信验证不一致')
        # 验证手机号是否被注册过
        try:
            user = User.objects.get(mobile=attrs['mobile'])
        except:
            # 未注册过，注册为新用户
            return attrs
        else:
            # 注册过 查询用户进行绑定
            # 判断密码
            if not user.check_password(attrs['password']):
                raise serializers.ValidationError('密码错误')
            attrs['user'] = user
            return attrs

    def create(self, validated_data):
        """
        保存用户
        :param self:
        :param validated_data:
        :return:
        """
        # 判断用户
        user = validated_data.get('user', None)
        if user is None:
            # 创建用户
            user = User.objects.create_user(username=validated_data['mobile'],
                                            password=validated_data['password'],
                                            mobile=validated_data['mobile'])
        # 绑定操作
        OAuthWeiboUser.objects.create(user=user, weibotoken=validated_data["weibotoken"])
        # user_id=user.id
        # 生成加密后的token数据
        from rest_framework_jwt.settings import api_settings
        jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
        jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER

        payload = jwt_payload_handler(user)  # 生成载荷部分
        token = jwt_encode_handler(payload)  # 生成token

        # user添加token属性
        user.token = token
        user.user_id = user.id

        return user
