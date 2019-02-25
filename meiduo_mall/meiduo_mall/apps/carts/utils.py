import pickle, base64
from django_redis import get_redis_connection


def merge_cart_cookie_to_redis(request, user, response):
    """购物车合并以cookie为准"""

    # 获取cookie购物车数据
    cart_str = request.COOKIES.get('carts')

    # 判断如果没有购物车数据以下代码不执行
    if cart_str is None:
        return

        # 将cart_str转成cart_dict
    cookie_cart_dict = pickle.loads(base64.b64decode(cart_str.encode()))
    # 创建redis链接对象
    redis_conn = get_redis_connection('cart')
    # 遍历cookie字典, 将sku_id和count直接加入到redis和hash中 如果cookie中的sku_id在hash中已存在,则会以cookie覆盖hash
    for sku_id in cookie_cart_dict:
        redis_conn.hset('cart_%d' % user.id, sku_id, cookie_cart_dict[sku_id]['count'])
        if cookie_cart_dict[sku_id]['selected']:
            redis_conn.sadd('selected_%d' % user.id, sku_id)

    # 将cookie中购物车数据清除
    response.delete_cookie('carts')
