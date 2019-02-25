from django.shortcuts import render
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
import base64, pickle
from django_redis import get_redis_connection

from goods.models import SKU
from .serializers import CartSerializer, CartSKUSerializer, CartDeleteSerializer, CartSelectSerializer


# Create your views here.


class CartsView(APIView):
    """购物车视图"""

    def perform_authentication(self, request):
        """禁用验证/延后验证"""
        pass

    def post(self, request):
        """添加购物车"""
        serializer = CartSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        sku_id = serializer.validated_data.get('sku_id')
        count = serializer.validated_data.get('count')
        selected = serializer.validated_data.get('selected')

        # 创建响应对象
        response = Response(serializer.data, status=status.HTTP_201_CREATED)

        try:
            # 获取登陆用户 首次获取还会认证
            user = request.user
            # 如果代码还能继续往下走说明时登陆用户存储到redis数据库

            # 创建redis连接对象
            redis_conn = get_redis_connection('cart')
            pl = redis_conn.pipeline()
            pl.hincrby('cart_%d' % user.id, sku_id, count)
            if selected:  # 判断当前商品是否勾选, 把勾选的商品sku_id添加到set集合中
                pl.sadd('selected_%d' % user.id, sku_id)
            pl.execute()

        except:
            # 没有登陆存储到cookie中
            # 获取cookie中购物车数据
            cart_cookie = request.COOKIES.get('carts')
            # 判断是否有购物车数据
            if cart_cookie:
                # 把字符传转换成bytes类型字符串
                cart_cookie_bytes = cart_cookie.encode()
                # 把bytes类型字符串转换成bytes类型ascii马
                cart_ascii_bytes = base64.b64decode(cart_cookie_bytes)
                # 把bytes类型ascii马转python字典
                cart_dict = pickle.loads(cart_ascii_bytes)

            else:
                # 没有cookie购物车数据
                cart_dict = {}
            # 判断本次添加的商品是否在购物车中,如果在需要做增量计算
            if sku_id in cart_dict:
                origin_count = cart_dict[sku_id]['count']
                count += origin_count

            cart_dict[sku_id] = {
                'count': count,
                'selected': selected
            }
            # 把python字典转换成字符串
            cart_ascii_bytes = pickle.dumps(cart_dict)
            cart_cookie_bytes = base64.b64encode(cart_ascii_bytes)
            cart_str = cart_cookie_bytes.decode()

            response.set_cookie('carts', cart_str)

        return response

    def get(self, request):
        """查询购物车"""
        try:
            user = request.user
            # 如果获取到user说明是已登录用户（操作redis数据库）

        except:
            # 如果获取不到user说明是未登录用户(获取cookie购物车数据)
            user = None

        else:
            # 如果获取到user说明是已经登录的用户(操作redis数据库)
            # 创建redis链接对象
            redis_conn = get_redis_connection('cart')
            # 获取hash数据{sku_id_16:1, sku_id_10:2}
            cart_redis_dict = redis_conn.hgetall('cart_%d' % user.id)
            # 获取set数据
            cart_selected_ids = redis_conn.smembers('selected_%d' % user.id)
            # 把redis的购物车数据转成cookie购物车数据格式一样
            # 定义一个用来转换数据格式的大字典
            cart_dict = {}
            for sku_id_bytes in cart_redis_dict:
                cart_dict[int(sku_id_bytes)] = {
                    'count': int(cart_redis_dict[sku_id_bytes]),
                    'selected': sku_id_bytes in cart_selected_ids
                }
        if not user:
            # 如果没有获取到user说明当前是未登录用户在操作(cookie购物车数据)
            cart_cookie = request.COOKIES.get('carts')
            # 判断是否有cookie购物车数据
            if cart_cookie:
                # 把cookie转成python字典
                cart_dict = pickle.loads(base64.b64decode(cart_cookie.encode()))
            else:
                cart_dict = {}

        # 以下代码无论是否登录还是未登录都会执行
        # 获取购物车中的所有sku模型
        skus = SKU.objects.filter(id__in=cart_dict.keys())
        # 遍历skus查询集, 给每个模型追加两个属性
        for sku in skus:
            sku.count = cart_dict[sku.id]['count']
            sku.selected = cart_dict[sku.id]['selected']

        # 创建序列化器　进行序列化操作
        serializer = CartSKUSerializer(skus, many=True)

        return Response(serializer.data)

    def put(self, request):
        """修改购物车"""
        serializer = CartSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        sku_id = serializer.validated_data.get('sku_id')
        count = serializer.validated_data.get('count')
        selected = serializer.validated_data.get('selected')

        response = Response(serializer.data)
        try:
            user = request.user
        except:
            user = None
        else:
            # 如果获取到user说明是登陆用户(操作redis数据库)
            # 创建redis连接对象
            redis_conn = get_redis_connection('cart')
            # 创建管道
            pl = redis_conn.pipeline()
            # 修改hash字典{sku_id_16:2, sku_id_2:1}
            # 勾选状态set集合{sku_id_16, sku_id_2}
            # 修改指定购买数据时,把hash字典中指定的sku_id的value覆盖掉
            pl.hset('cart_%d' % user.id, sku_id, count)
            # 修改商品勾选状态
            if selected:
                pl.sadd('selected_%d' % user.id, sku_id)
            else:
                pl.srem('selected_%d' % user.id, sku_id)
            # 执行管道
            pl.execute()

        if not user:
            # 如果没有获取到user说明是未登录用户(cookie购物车数据)
            cart_str = request.COOKIES.get('carts')

            # 判断是否有cookie购物车数据
            if cart_str:
                # 未登录用户操作cookie购物车数据
                cart_dict = pickle.loads(base64.b64decode(cart_str.encode()))
                # 判断当前修改的sku_id是否在cart_dict字典中存在
                if sku_id in cart_dict:
                    # 直接覆盖商品的数据及勾选状态
                    cart_dict[sku_id] = {
                        'count': count,
                        'selected': selected
                    }
                # 讲python字典转成cookie数据格式
                cart_str = base64.b64encode(pickle.dumps(cart_dict)).decode()
                # 设置cookie
                response.set_cookie('carts', cart_str)

        return response

    def delete(self, request):
        """删除购物车"""
        serializer = CartDeleteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        sku_id = serializer.validated_data.get('sku_id')

        response = Response(serializer.data, status.HTTP_204_NO_CONTENT)

        try:
            user = request.user
        except:
            user = None
        else:
            # 获取到user说明是登录用户操作redis 数据库
            # 创建链接对象
            redis_conn = get_redis_connection('cart')
            # 创建管道
            pl = redis_conn.pipeline()
            # 删除hash字典中指定的sku_id的键值对
            pl.hdel('cart_%d', user.id, sku_id)
            # 删除set集合中指定的sku_id的元素
            pl.srem('selected_%d', user.id, sku_id)
            # 执行管道
            pl.execute()

        if not user:
            # 没有获取到user说明是未登录用户
            # 获取cookie
            cart_str = request.COOKIES.get('carts')
            if cart_str:
                # 将cart_str 转成 cart_dict
                cart_dict = pickle.loads(base64.b64decode(cart_str.encode()))
            # 将cart_dict中指定的sku_id移除
                if sku_id in cart_dict:
                    del cart_dict[sku_id]
                if len(cart_dict.keys()):  # 如果if成立说明购物车中还有商品
                    # 将cart_dict 转成 cart_str
                    cart_str = base64.b64encode(pickle.dumps(cart_dict)).decode()
                    # 设置cookie
                    response.set_cookie('carts', cart_str)
                else:
                    # 如果全部商品都删除了,则把cookie删除
                    response.delete_cookie('carts')

        return response


class CartSelectedView(APIView):
    """购物车全选视图"""
    def perform_authentication(self, request):
        """延后认证"""
        pass

    def put(self, request):
        """全选/取消全选"""
        serializer = CartSelectSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        selected = serializer.validated_data.get('selected')

        response = Response(serializer.data)
        try:
            user = request.user
        except:
            user = None
        else:
            # 获取到user是登录用户操作redis
            # 创建redis链接对象
            redis_conn = get_redis_connection('cart')
            # 获取redis中的hash字典
            cart_dict = redis_conn.hgetall('cart_%d' % user.id)
            # 判断是全选还是取消全选
            if selected:
                # 如果全选就把sku_id全部添加到set集合中
                redis_conn.sadd('selected_%d' % user.id, *cart_dict.keys())
            else:
                # 如果取消全选就把sku_id从set集合中全部移除
                redis_conn.srem('selected_%d' % user.id, *cart_dict.keys())

        if not user:
            # 没有获取到user是未登录用户操作cookie购物车数据
            # 获取cookie购物车数据
            cart_str = request.COOKIES.get('carts')
            if cart_str:
                # 将cart_str 转成 cart_dict
                cart_dict = pickle.loads(base64.b64decode(cart_str.encode()))
                # 遍历cart_dict将selected全部设置为用户传入的selected
                for sku_id in cart_dict:
                    # 取出每个sku_id对应的小字典
                    sku_id_dict = cart_dict[sku_id]
                    # 全选是把selected全部改为True否则改为False
                    sku_id_dict['selected'] = selected
                # 将cart_dict 转成 cart_str
                cart_str = base64.b64encode(pickle.dumps(cart_dict)).decode()
                # 设置cookie
                response.set_cookie('carts', cart_str)

        return response
