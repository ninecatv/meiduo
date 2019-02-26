from decimal import Decimal
from django.db import transaction
from django_redis import get_redis_connection
from django.utils import timezone
from rest_framework import serializers

from goods.models import SKU
from users.models import User
from .models import OrderInfo, OrderGoods


class SaveOrderSerializer(serializers.ModelSerializer):
    """保存订单序列化器"""

    class Meta:
        model = OrderInfo
        fields = ('order_id', 'address', 'pay_method')
        read_only_fields = ('order_id',)
        extra_kwargs = {
            'address': {
                'write_only': True,
                'required': True,
            },
            'pay_method': {
                'write_only': True,
                'required': True
            }
        }

    def create(self, validated_data):
        """重写序列化器的create方法进行存储订单表/订单商品"""
        # 订单基本信息表 订单商品表  sku   spu 四个表要么一起成功 要么一起失败
        # 获取当前下单用户
        user = self.context['request'].user
        # 生成订单编号 当前时间 + user_id  20190215100800000000001
        order_id = timezone.now().strftime('%Y%m%d%H%M%S') + '%09d' % user.id
        # 获取用户收获地址
        address = validated_data['address']
        # 获取用户选择的支付方式
        pay_method = validated_data['pay_method']

        # 订单状态 如果选择的是货到付款,则是待发货, 如果选择的是支付宝支付的话就是待付款
        # status = '待支付'  if 如果用户选择的支付方式 == 支付宝支付 else '待发货'
        status = (OrderInfo.ORDER_STATUS_ENUM['UNPAID']
                  if OrderInfo.PAY_METHODS_ENUM['ALIPAY'] == pay_method
                  else OrderInfo.ORDER_STATUS_ENUM['UNSEND'])

        # 开启一个事物
        with transaction.atomic():
            # 创建一个事物保存点
            save_id = transaction.savepoint()

            try:

                # 保存订单基本信息数据 OrderInfo
                order = OrderInfo.objects.create(
                    order_id=order_id,
                    user=user,
                    address=address,
                    total_count=0,
                    total_amount=Decimal('0.00'),
                    freight=Decimal('10.00'),
                    pay_method=pay_method,
                    status=status
                )
                # 从redis中获取购物车结算商品数据
                # 创建redis连接对像
                redis_conn = get_redis_connection('cart')
                # 获取hash
                cart_redis_dict = redis_conn.hgetall('cart_%d' % user.id)
                # 获取set 要购买的商品
                cart_selected_ids = redis_conn.smembers('selected_%d' % user.id)

                # 使用一个中间表
                cart_selected_dict = {}
                for sku_id_bytes in cart_selected_ids:
                    cart_selected_dict[int(sku_id_bytes)] = int(cart_redis_dict[sku_id_bytes])

                # 查询所有商品数据
                # skus = SKU.objects.filter(id__in=cart_selected_dict.keys())
                # 判断商品库存是否充足
                for sku_id in cart_selected_dict:
                    while True:
                        # 获取sku对象
                        sku = SKU.objects.get(id=sku_id)
                        # 获取当前sku商品要购买的数量
                        sku_count = cart_selected_dict[sku_id]

                        # 获取查询出来的库存和销量
                        origin_stock = sku.stock  # 原始库存
                        origin_sales = sku.sales  # 原始销量

                        # 判断用户要购买的商品数量是否有库存
                        if sku_count > origin_stock:
                            raise serializers.ValidationError('库存不足')

                        # 计算新库存和销量
                        # 减少商品库存，增加商品销量
                        new_stock = origin_stock - sku_count  # 减少库存
                        new_sales = origin_sales + sku_count  # 增加销量

                        # 减少库存增加销量, sku 使用乐观锁
                        result = SKU.objects.filter(id=sku_id, stock=origin_stock).update(stock=new_stock,
                                                                                          sales=new_sales)

                        if result == 0:
                            continue  # 跳出本次循环,进入下一次循环

                        # 修改spu销量
                        spu = sku.goods
                        spu.sales += sku_count
                        spu.save()
                        # 保存订单商品数据
                        OrderGoods.objects.create(
                            order=order,
                            sku=sku,
                            count=sku_count,
                            price=sku.price
                        )

                        # 累计计算总数量和总价格
                        order.total_count += sku_count
                        order.total_amount += (sku.price * sku_count)
                        break

                # 总价格加上邮费
                order.total_amount += order.freight
                order.save()
            except Exception:
                # 无论中间出现什么问题都回滚 要么一起成功要么一起失败
                transaction.savepoint_rollback(save_id)
                raise
            else:
                # 如果中间没有出现异常 就提交事物
                transaction.savepoint_commit(save_id)
        # 在redis购物车中删除已计算商品数据
        pl = redis_conn.pipeline()
        pl.hdel('cart_%d' % user.id, *cart_selected_ids)
        pl.srem('selected_%d' % user.id, *cart_selected_ids)
        pl.execute()
        return order


class CartSKUSerializer(serializers.ModelSerializer):
    """订单序列化器"""

    count = serializers.IntegerField(label='数量')

    class Meta:
        model = SKU
        fields = ['id', 'name', 'default_image_url', 'price', 'count']


class OrderSettlementSerializer(serializers.Serializer):
    """
    订单结算数据序列化器
    """
    # float 1.23 ==> 123 * 10 ^ -2  --> 1.299999999
    # Decimal  1.23    1    23
    # max_digits 一共多少位；decimal_places：小数点保留几位
    freight = serializers.DecimalField(label='运费', max_digits=10, decimal_places=2)
    skus = CartSKUSerializer(many=True)


class SKUCommentSerializers(serializers.ModelSerializer):
    """商品评论信息"""

    class Meta:
        model = SKU
        fields = ['id', 'name', 'price', 'default_image_url']


class GoodsCommentSerializer(serializers.ModelSerializer):
    """订单商品评论"""
    sku = SKUCommentSerializers()

    class Meta:
        model = OrderGoods
        fields = ['id', 'sku', 'price', 'comment', 'score', 'is_anonymous']


class UpdateCommentSerializer(serializers.Serializer):
    """用户订单评论序列化器"""

    comment = serializers.CharField(label='评论内容')
    score = serializers.IntegerField(label='评分', default=5)
    is_anonymous = serializers.BooleanField(label='是否匿名')

    def update(self, instance, validated_data):
        instance.comment = validated_data.get('comment')
        instance.score = validated_data.get('score')
        instance.is_anonymous = validated_data.get('is_anonymous')
        instance.is_commented = True
        instance.save()

        sku = instance.sku
        sku.comments += 1
        sku.save()
        return validated_data
