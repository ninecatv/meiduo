# Create your views here.
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from django_redis import get_redis_connection
from random import randint
import logging

from . import constants
from celery_tasks.sms.tasks import send_sms_code

logger = logging.getLogger('django')  # 创建日志输出器


# 请求地址 GET  sms_codes/(?P<mobile>1[3-9]\d{9})/
class SMSCodeView(APIView):
    """发送短信验证码接口"""

    def get(self, request, mobile):

        # GET  sms_codes/(?P<mobile>1[3-9]\d{9})/
        # 创建redis数据库对象
        redis_conn = get_redis_connection('verify_codes')

        # 从redis中读取flag
        send_flag = redis_conn.get('SMS_flag_%s' % mobile)
        # 如果取到有值,说明该手机号一分钟之内已经发送过验证码
        if send_flag:
            return Response({'message': '频繁发送短信验证码'}, status=status.HTTP_400_BAD_REQUEST)

        # 生成短信验证码
        sms_code = '%06d' % randint(0, 999999)
        logger.info(sms_code)

        # 创建管道
        pl = redis_conn.pipeline()

        # 将生成的验证码保存到redis数据库
        # setex('key', '过期时长', 'value')
        # redis_conn.setex('SMS_%s' % mobile, constants.SMS_CODE_REDIS_EXPIRES, sms_code)
        # 使用管道
        pl.setex('sms_%s' % mobile, constants.SMS_CODE_REDIS_EXPIRES, sms_code)

        # 记录用户一分钟之内只能发送一次标记
        # redis_conn.setex('SMS_flag_%s' % mobile, constants.SEND_SMS_CODE_INTERVAL, 1)
        pl.setex('SMS_flag_%s' % mobile, constants.SEND_SMS_CODE_INTERVAL, 1)

        # 执行管道
        pl.execute()

        # 发送短信验证码
        # CCP().send_template_sms(mobile, [sms_code, constants.SMS_CODE_REDIS_EXPIRES // 60], 1)
        send_sms_code.delay(mobile, sms_code)

        # 返回
        return Response({'message': "OK"})
