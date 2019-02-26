from django.shortcuts import render
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.mixins import CreateModelMixin, ListModelMixin
from rest_framework.permissions import IsAuthenticated
from django_redis import get_redis_connection
from decimal import Decimal

# Create your views here.
from goods.models import SKU
from rest_framework.viewsets import GenericViewSet
from .serializers import OrderSettlementSerializer, SaveOrderSerializer, OrderListSerializer, UpdateCommentSerializer, \
    GoodsCommentSerializer
from orders.models import OrderGoods, OrderInfo


# /skus/16/comments/
class SKUCommentsView(APIView):
    """获取商品所有评论"""

    def get(self, request, pk):
        # 根据pk获取所有已评论的sku评论信息
        order_comments = OrderGoods.objects.filter(sku_id=pk, is_commented=True).all()
        data = []
        # 遍历所有订单的评论信息并组织返回数据
        for order_good in order_comments:
            user_comment = {
                'comment': order_good.comment,
                'score': order_good.score,
                'username': OrderInfo.objects.get(order_id=order_good.order_id).user.username
            }
            data.append(user_comment)

        return Response(data)


class UNCommentsView(APIView):
    """用户订单商品评论"""
    # 只有登录用户才能访该视图
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        # 根据pk查询订单所有评论
        order_goods_comments = OrderGoods.objects.filter(order_id=pk, is_commented=False).all()
        # 如果没有获取到订单中商品评论,就说明评论完成了,把订单状态改成已完成
        if not order_goods_comments:
            try:
                order_info = OrderInfo.objects.get(order_id=pk)
                order_info.status = OrderInfo.ORDER_STATUS_ENUM['FINISHED']
                order_info.save()
            except OrderInfo.DoesNotExist:
                return Response({'message': '订单异常'}, status=status.HTTP_400_BAD_REQUEST)

        # 创建序列化器
        serializer = GoodsCommentSerializer(order_goods_comments, many=True)

        return Response(serializer.data)

    def post(self, request, pk):
        """
        comment: 评论内容
        is_anonymous: True匿名评论反之False
        order: 订单编号
        score: 评分
        sku: 商品id
        """
        sku_id = request.data.get('sku')
        try:
            order_good = OrderGoods.objects.get(order_id=pk, sku_id=sku_id)
        except OrderInfo.DoesNotExist:
            return Response({'message': '订单商品不存在'}, status=status.HTTP_400_BAD_REQUEST)
        # 创建序列化器
        serializer = UpdateCommentSerializer(instance=order_good, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response({'message': '评论成功'})


class SaveOrderView(CreateModelMixin, ListModelMixin, GenericViewSet):
    """提交订单/订单列表"""
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if self.action == 'list':
            return OrderInfo.objects.filter(user=self.request.user).order_by('-create_time')
        else:
            return None

    def get_serializer_class(self):
        """根据action不同选择不同的序列化器"""
        if self.action == 'list':
            return OrderListSerializer
        else:
            return SaveOrderSerializer

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        count = queryset.count()
        return Response({'count': count, 'results': serializer.data})


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
