from rest_framework import serializers
from django_redis import get_redis_connection

from .utils import check_save_user_token
from users.models import User
from .models import QQAuthUser, OAuthSinaUser


class QQAuthUserSerializer(serializers.Serializer):
        """绑定用户的序列化器"""

        access_token = serializers.CharField(label='操作凭证', write_only=True)
        mobile = serializers.RegexField(label='⼿手机号', regex=r'^1[3-9]\d{9}$')
        password = serializers.CharField(label='密码', max_length=20, min_length=8, write_only=True)
        sms_code = serializers.CharField(label='短信验证码')

        def validate(self, attrs):

            # 获取加密的openid
            access_token = attrs.get('access_token')
            # 将获取到的openid进行解密
            openid = check_save_user_token(access_token)
            if not openid:
                raise serializers.ValidationError('openid无效')

            # 把解密后的openid保存到反序列化的大字典中,以备后期绑定用户使用
            attrs['access_token'] = openid

            # 验证短信验证码是否正确, 创建redis连接对象
            redis_conn = get_redis_connection('verify_codes')
            # 获取当前用户的手机号码并从redis数据库中获取对应的验证码 !: bytes类型
            mobile = attrs.get('mobile')
            real_sms_code = redis_conn.get('sms_%s' % mobile)
            # 获取前端传过来的验证码
            sms_code = attrs.get('sms_code')
            if real_sms_code.decode() != sms_code:
                raise serializers.ValidationError('验证码错误')

            try:
                # 判断手机号是否以存在用户还是新用户
                user = User.objects.get(mobile=mobile)

            except User.DoesNotExist:
                # 如果出现异常说明是新用户
                pass
            else:
                # 表示该手机号是以注册用户
                if not user.check_password(attrs.get('password')):
                    raise serializers.ValidationError('密码错误')

                # 将认证后的用户放到反序例化的大字典中
                attrs['user'] = user

            return attrs

        def create(self, validated_data):
            """将openid跟用户绑定"""

            # 获取当前用户
            user = validated_data.get('user')

            if not user:
                # 如果用户不存在,则新增一个用户
                user = User(
                    username=validated_data.get('mobile'),
                    mobile=validated_data.get('mobile')
                )
                user.set_password(validated_data.get('password'))  # 对密码进行加密处理
                user.save()

            # 让user跟openid绑定
            QQAuthUser.objects.create(
                user=user,
                openid=validated_data.get('access_token')
            )

            return user


class SinaAuthUserSerializer(serializers.Serializer):
    """微博用户注册序列化器"""
    mobile = serializers.RegexField(label='手机号', regex=r'1[3-9]\d{9}$')
    access_token = serializers.CharField(label='操作凭证')
    password = serializers.CharField(label='密码', max_length=20, min_length=8)
    sms_code = serializers.CharField(label='短信验证码')

    def validate(self, data):
        """校验参数"""
        # 获取access_token
        access_token = check_save_user_token(data['access_token'])
        if not access_token:
            raise serializers.ValidationError('access_token无效')

        data['access_token'] = access_token
        # 检验短信验证码
        mobile = data['mobile']
        sms_code = data['sms_code']
        redis_conn = get_redis_connection('verify_codes')
        real_sms_code = redis_conn.get('sms_%s' % mobile)
        if real_sms_code.decode() != sms_code:  # 存进redis数据库是字符串类型,取出来是bytes类型
            raise serializers.ValidationError('短信验证码错误')

        # 检验密码
        try:
            user = User.objects.get(mobile=mobile)
        except User.DoesNotExist:
            # 取不出来user说明是新用户
            pass
        else:
            password = data['password']
            if not user.check_password(password):
                raise serializers.ValidationError('密码错误')
            data['user'] = user

        return data

    def create(self, validated_data):
        # 检验用户是否存在
        user = validated_data.get('user')
        if not user:
            user = User(
                username=validated_data.get('username'),
                mobile=validated_data.get('mobile'),
                password=validated_data.get('password')
            )
            user.set_password(validated_data.get('password'))
            user.save()

        OAuthSinaUser.objects.create(
                access_token=validated_data.get('access_token'),
                user=user
            )
        return user