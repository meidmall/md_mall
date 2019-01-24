import re

from rest_framework import serializers

from mall import settings
from users.models import User, Address
from django_redis import get_redis_connection


# serializers.ModelSerializer
# serializers.Serializer
from users.utils import generic_verify_url


class  RegiserUserSerializer(serializers.ModelSerializer):
    """
    手机号,用户名,密码,短信验证码,确认密码,是否同意协议
    """

    # 自己定字段就可以了
    """
    write_only: 只是在 反序列化(将JSON转换为模型)的时候 使用 , 在序列化(将对象转换为字典,JSON)的时候不使用该字段
    read_only: 在序列化(将对象转换为字典,JSON)的时候,

    """
    sms_code=serializers.CharField(label='短信验证码',max_length=6,min_length=6,write_only=True,required=True,allow_blank=False)
    allow=serializers.CharField(label='是否同意协议',required=True,allow_null=False,write_only=True)
    password2=serializers.CharField(label='确认密码',required=True,allow_null=False,write_only=True)

    token = serializers.CharField(label='token',read_only=True)
    """
    ModelSerializer 自动生成字段的过程
    会对 fields 进行遍历, 先去 model中查看是否有相应的字段
    如果有 则自动生成
    如果没有 则查看当前类 是否有定义
    """
    class Meta:
        model = User
        fields = ['id','token','mobile','username','password','sms_code','allow','password2']

        extra_kwargs = {
            'id': {'read_only': True},
            'username': {
                'min_length': 5,
                'max_length': 20,
                'error_messages': {
                    'min_length': '仅允许5-20个字符的用户名',
                    'max_length': '仅允许5-20个字符的用户名',
                }
            },
            'password': {
                'write_only': True,
                'min_length': 8,
                'max_length': 20,
                'error_messages': {
                    'min_length': '仅允许8-20个字符的密码',
                    'max_length': '仅允许8-20个字符的密码',
                }
            }
        }



    """
    校验数据
    1. 字段类型
    2. 字段选项
    3. 单个字段
    4. 多个字段

    mobile: 符合手机号规则
    allow: 是否同意协议

    两次密码需要一致
    短信

    """
    #单个字段
    def validate_mobile(self,value):

        if not re.match(r'1[3-9]\d{9}',value):
            raise serializers.ValidationError('手机号不符合规则')

        return value

    def validate_allow(self,value):

        if value != 'true':
            raise serializers.ValidationError('没有同意协议')

        return value


    #多个字段
    def validate(self, attrs):

        #1两次密码需要一致
        password = attrs['password']
        password2 = attrs['password2']

        if password!=password2:
            raise serializers.ValidationError('密码不一致')

        #2短信
        # 2.1 获取用户提交的
        mobile = attrs.get('mobile')
        sms_code = attrs['sms_code']
        # 2.2 获取 redis
        redis_conn = get_redis_connection('code')

        redis_code = redis_conn.get('sms_'+mobile)

        if redis_code is None:
            raise serializers.ValidationError('短信验证码已过期')

        # 最好删除短信
        redis_conn.delete('sms_'+mobile)
        #2.3 比对
        if redis_code.decode() != sms_code:
            raise serializers.ValidationError('验证码不一致')


        return attrs


    def create(self, validated_data):
        # print(validated_data)

        del validated_data['sms_code']
        del validated_data['allow']
        del validated_data['password2']

        #1. 自己把数据入库
        # user = User.objects.create(**validated_data)

        #2. 现在的数据 满足要求了 ,可以让父类去执行
        user = super().create(validated_data)

        #3. 密码还是明文
        # 我们需要加密
        user.set_password(validated_data['password'])
        user.save()

        # 用户入库之后,我们生成token
        from rest_framework_jwt.settings import api_settings

        #4.1 需要使用 jwt的2个方法
        jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
        jwt_encode_handler=api_settings.JWT_ENCODE_HANDLER

        #4.2 让payload(载荷 )盛放一些用户信息
        payload = jwt_payload_handler(user)
        token = jwt_encode_handler(payload)

        user.token=token

        return user


class Person(object):
    name='itcast'



# p = Person()
# p.name
#
# p.age = 12
# print(p.age)
#
# p2 = Person()
# print(p2.age)


# serializers.Serializer
# serializers.ModelSerializer

class UserCenterInfoSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = ('id', 'username', 'mobile', 'email','email_active')


# serializers.Serializer
# serializers.ModelSerializer

class UserEmailInfoSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = ('id', 'email')
        extra_kwargs = {
            'email': {
                'required': True
            }
        }


    def update(self, instance, validated_data):

        # 先把数据 更新一下
        email = validated_data.get('email')

        instance.email=email
        instance.save()

        # super().update(instance,validate_data)

        # 再发送邮件
        from django.core.mail import send_mail

        #subject, message, from_email, recipient_list,
        #subject            主题
        subject = '美多商场激活邮件'
        # message,          内容
        message=''
        # from_email,       谁发送的
        from_email=settings.EMAIL_FROM
        # recipient_list,   收件人列表
        recipient_list = [email]

        # user_id = 8
        verify_url = generic_verify_url(instance.id)

        # html_message = '<p>尊敬的用户您好！</p>' \
        #                '<p>感谢您使用美多商城。</p>' \
        #                '<p>您的邮箱为：%s 。请点击此链接激活您的邮箱：</p>' \
        #                '<p><a href="%s">%s<a></p>' % (email, verify_url, verify_url)
        #
        #
        # send_mail(subject=subject,
        #           message=message,
        #           from_email=from_email,
        #           recipient_list=recipient_list,
        #           html_message=html_message)

        from clery_tasks.mail.tasks import send_celery_email
        send_celery_email.delay(subject,
                  message,
                  from_email,
                  email,
                  verify_url,
                  recipient_list)

        return instance


#
# class AddressSerializer(serializers.ModelSerializer):
#
#     province = serializers.StringRelatedField(read_only=True)
#     city = serializers.StringRelatedField(read_only=True)
#     district = serializers.StringRelatedField(read_only=True)
#     province_id = serializers.IntegerField(label='省ID', required=True)
#     city_id = serializers.IntegerField(label='市ID', required=True)
#     district_id = serializers.IntegerField(label='区ID', required=True)
#     mobile = serializers.RegexField(label='手机号', regex=r'^1[3-9]\d{9}$')
#
#     class Meta:
#         model = Address
#         exclude = ('user', 'is_deleted', 'create_time', 'update_time')
#
#     def create(self, validated_data):
#
#
#         # validated_data 缺少user_id
#         validated_data['user']=self.context['request'].user
#
#         # return Address.objects.create(**validated_data)
#         return super().create(validated_data)

class AddressSerializer(serializers.ModelSerializer):

    province = serializers.StringRelatedField(read_only=True)
    city = serializers.StringRelatedField(read_only=True)
    district = serializers.StringRelatedField(read_only=True)
    province_id = serializers.IntegerField(label='省ID', required=True)
    city_id = serializers.IntegerField(label='市ID', required=True)
    district_id = serializers.IntegerField(label='区ID', required=True)
    mobile = serializers.RegexField(label='手机号', regex=r'^1[3-9]\d{9}$')

    class Meta:
        model = Address
        exclude = ('user', 'is_deleted', 'create_time', 'update_time')


    def create(self, validated_data):
        #Address模型类中有user属性,将user对象添加到模型类的创建参数中
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)

class AddressTitleSerializer(serializers.ModelSerializer):
    """
    地址标题
    """
    class Meta:
        model = Address
        fields = ('title',)


from goods.models import SKU
from django_redis import get_redis_connection

class AddUserBrowsingHistorySerializer(serializers.Serializer):
    """
    添加用户浏览记录序列化器
    """
    sku_id = serializers.IntegerField(label='商品编号',min_value=1,required=True)

    def validate_sku_id(self,value):
        """
        检查商品是否存在
        """
        try:
            SKU.objects.get(pk=value)
        except SKU.DoesNotExist:
            raise serializers.ValidationError('商品不存在')

        return value


    def create(self, validated_data):
        sku_id = validated_data['sku_id']

        user = self.context['request'].user

        # 把数据保存到redis中
        #1. 连接redis
        redis_conn = get_redis_connection('history')
        #2. 先把 sku_id 删除
        # 列表用户的key 不能重复
        #  history_3
        redis_conn.lrem('history_%s'%user.id,0,sku_id)
        #3. 再添加到左边
        redis_conn.lpush('history_%s'%user.id,sku_id)

        #4. redis列表中只保留5条记录
        redis_conn.ltrim('history_%s'%user.id,0,4)

        return validated_data

class SKUSerializer(serializers.ModelSerializer):

    class Meta:
        model = SKU
        fields = ('id', 'name', 'price', 'default_image_url', 'comments')


