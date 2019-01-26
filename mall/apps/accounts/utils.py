from itsdangerous import TimedJSONWebSignatureSerializer as Serializer, BadData
from django.conf import settings
def dangerous(mobile):


    # serializer = Serializer(秘钥, 有效期秒)
    serializer = Serializer(settings.SECRET_KEY, 300)
    # serializer.dumps(数据), 返回bytes类型
    token = serializer.dumps({'mobile': mobile})
    token = token.decode()
    return token

def undangerous(token):
    # 检验token
    # 验证失败，会抛出itsdangerous.BadData异常
    serializer = Serializer(settings.SECRET_KEY, 300)
    try:
        data = serializer.loads(token)
    except BadData:
        return None
    return data