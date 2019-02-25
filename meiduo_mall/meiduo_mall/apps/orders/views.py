from django.shortcuts import render
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import CreateAPIView
from rest_framework.permissions import IsAuthenticated
from django_redis import get_redis_connection
from decimal import Decimal

# Create your views here.
from goods.models import SKU
from .serializers import OrderSettlementSerializer, SaveOrderSerializer


class SaveOrderView(CreateAPIView):
    """保存订单"""

    permission_classes = [IsAuthenticated]  # 只有登陆用户才能访问该视图
    serializer_class = SaveOrderSerializer


class OrderSettlementView(APIView):
    """订单结算视图"""
    # 只有通过认证的用户才能访问该视图
    parser_classes = [IsAuthenticated]

    def get(self, request):
        """获取"""
        user = request.user

        # 从购物车中获取勾选要结算的商品
        # 创建redis连接对象
        redis_conn = get_redis_connection('cart')
        # 获取hash
        redis_cart = redis_conn.hgetall('cart_%s' % user.id)
        # 获取set
        cart_selected = redis_conn.smembers('selected_%s' % user.id)

        cart = {}
        for sku_id in cart_selected:
            cart[int(sku_id)] = int(redis_cart[sku_id])

        # 查询商品信息
        skus = SKU.objects.filter(id__in=cart.keys())

        for sku in skus:
            sku.count = cart[sku.id]

        freight = Decimal('10.00')

        serializer = OrderSettlementSerializer({'freight': freight, 'skus': skus})

        return Response(serializer.data)
