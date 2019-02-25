from itsdangerous import TimedJSONWebSignatureSerializer as Serializer, BadData
from django.conf import settings


def generate_save_user_token(openid):
    """对openid进行加密"""
    # 创建序列化器
    serializer = Serializer(settings.SECRET_KEY, 600)
    data = {'openid': openid}

    # 调用序列化器的dumps进行加密
    access_token_bytes = serializer.dumps(data)

    # 将加密后的data返回
    return access_token_bytes.decode()


def check_save_user_token(openid):
    """对加密的openid进行解密"""
    # 创建序列化器
    serializer = Serializer(settings.SECRET_KEY, 600)

    try:
        # 调用序列化器的loads进行解密
        data = serializer.loads(openid)
    except BadData:
        return None

    return data.get('openid')
