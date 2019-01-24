from itsdangerous import TimedJSONWebSignatureSerializer as Serializer, BadSignature

from mall import settings


def generic_verify_url(user_id):
    # 创建序列化器
    s = Serializer(secret_key=settings.SECRET_KEY, expires_in=3600)
    # 组织数据
    data = {
        'id': user_id
    }
    # 对数据加密
    token = s.dumps(data)

    return 'http://www.meiduo.site:8080/success_verify_email.html?token=' + token.decode()


def check_token(token):
    # 1.创建序列化器
    s = Serializer(secret_key=settings.SECRET_KEY, expires_in=3600)
    # 2.解析数据
    try:
        result = s.loads(token)
    except BadSignature:
        return None
    return result.get('id')