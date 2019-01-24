from itsdangerous import TimedJSONWebSignatureSerializer as Serializer,BadSignature
from mall import settings


def generic_openid(openid):
    # 创建序列化器
    s = Serializer(secret_key=settings.SECRET_KEY, expires_in=60*60)
    # 组织数据
    data = {'openid': openid}
    # 对数据进处理
    token = s.dumps(data)
    # 返回
    return token.decode()


def check_access_token(access_token):
    s = Serializer(secret_key=settings.SECRET_KEY, expires_in=60*60)
    try:
        data = s.loads(access_token)
        '''
        data就是当时设置的字典
        data = {
                'openid':openid
                }
        '''
    except BadSignature:
        return None
    return data['openid']

