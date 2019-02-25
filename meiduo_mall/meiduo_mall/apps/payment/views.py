from django.shortcuts import render
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from alipay import AliPay
import os
from django.conf import settings

# Create your views here.
from orders.models import OrderInfo
from .models import Payment


class PaymentView(APIView):
    """支付宝"""

    permission_classes = [IsAuthenticated]

    def get(self, request, order_id):
        """获取支付宝支付url"""
        # 获取当前登录⽤用户
        user = request.user
        # 接受并校验order_id
        try:
            order = OrderInfo.objects.get(order_id=order_id, user=user, status=OrderInfo.ORDER_STATUS_ENUM['UNPAID'])
        except OrderInfo.DoesNotExist:
            raise Response({'message': '订单信息异常'}, status=status.HTTP_400_BAD_REQUEST)
        # 创建⽀付宝支付对象
        alipay = AliPay(
            appid=settings.ALIPAY_APPID,
            app_notify_url=None,  # 默认回调url
            app_private_key_path=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'keys/app_private_key.pem'),
            # 支付宝的公钥，验证支付宝回传消息使用，不是你自己的公钥,
            alipay_public_key_path=os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                'keys/alipay_public_key.pem'),
            sign_type="RSA2",  # RSA 或者 RSA2
            debug=settings.ALIPAY_DEBUG  # 默认False
        )
        # ⽣成登录⽀付宝连接
        # 电脑网站支付，需要跳转到https://openapi.alipay.com/gateway.do? + order_string
        order_string = alipay.api_alipay_trade_page_pay(
            out_trade_no=order_id,  # 订单编号
            total_amount=str(order.total_amount),  # 注意: 一定要把总价转换成字符串类型,不然会报错
            subject="美多商城%s" % order_id,  # 注意:如果变量是字条串类型必须用%s占位,如果变量是int类型可以用%d也可以用%s占位
            return_url='http://www.meiduo.site/pay_success.html',  # 支付成功后的回调
        )
        # 响应登录⽀付宝连接
        alipay_url = settings.ALIPAY_URL + '?' + order_string

        return Response({'alipay_url': alipay_url})


# 支付成功后验证和修改订单状态
class PaymentStatusView(APIView):
    """修改订单状态"""

    def put(self, request):
        # 获取查询参数中的所有参数 query_params  /django  GET
        query_dict = request.query_params
        # 把query_dict类型对象转换成python字典
        data = query_dict.dict()
        # 把查询参数中的sing签名部分参数提取出来
        sign = data.pop('sign')
        # 创建alipay支付对象
        alipay = AliPay(
            appid=settings.ALIPAY_APPID,
            app_notify_url=None,  # 默认回调url
            app_private_key_path=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'keys/app_private_key.pem'),
            # 支付宝的公钥，验证支付宝回传消息使用，不是你自己的公钥,
            alipay_public_key_path=os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                'keys/alipay_public_key.pem'),
            sign_type="RSA2",  # RSA 或者 RSA2
            debug=settings.ALIPAY_DEBUG  # 默认False
        )
        # 使用alipay支付对象调用verify方法进行验证
        success = alipay.verify(data, sign)  # 如果返回True表示支付成功,如果False表示支付中信息有错误
        if success:
            # 获取美多商城订单编号
            order_id = data.get('out_trade_no')
            # 获取支付宝流水号
            trade_id = data.get('trade_no')
            # 把交易号跟支付宝流水号进行绑定
            Payment.objects.create(
                order_id=order_id,
                trade_id=trade_id
            )

            # 修改订单状态
            OrderInfo.objects.filter(order_id=order_id, status=OrderInfo.ORDER_STATUS_ENUM['UNPAID']).update(status=OrderInfo.ORDER_STATUS_ENUM['UNSEND'])

            return Response({'trade_id': trade_id})
        else:
            return Response({'message': '非法请求'}, status=status.HTTP_403_FORBIDDEN)
