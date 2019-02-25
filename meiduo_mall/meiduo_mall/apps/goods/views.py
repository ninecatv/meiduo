from django.shortcuts import render
from rest_framework.generics import GenericAPIView, ListAPIView
from rest_framework.response import Response
from rest_framework.filters import OrderingFilter
from drf_haystack.viewsets import HaystackViewSet

from .models import SKU
from .serializer import SKUSerializer,SKUIndexSerializer
# Create your views here.


class SKUSearchViewSet(HaystackViewSet):
    """
    SKU搜索
    """
    index_models = [SKU]

    serializer_class = SKUIndexSerializer


# class CategoryView(GenericAPIView
#                    ):
#     """
#     商品列表页面包屑导航
#     """
#     queryset = GoodsCategory.objects.all()
#
#     def get(self, request, pk=None):
#         ret = dict(
#             cat1='',
#             cat2='',
#             cat3=''
#         )
#         category = self.get_object()
#         if category.parent is None:
#             # 当前类别为一级类别
#             ret['cat1'] = ChannelSerializer(category.goodschannel_set.all()[0]).data
#         elif category.goodscategory_set.count() == 0:
#             # 当前类别为三级
#             ret['cat3'] = CategorySerializer(category).data
#             cat2 = category.parent
#             ret['cat2'] = CategorySerializer(cat2).data
#             ret['cat1'] = ChannelSerializer(cat2.parent.goodschannel_set.all()[0]).data
#         else:
#             # 当前类别为二级
#             ret['cat2'] = CategorySerializer(category).data
#             ret['cat1'] = ChannelSerializer(category.parent.goodschannel_set.all()[0]).data
#
#         return Response(ret)


# /categories/(?P<category_id>\d+)/skus?page=xxx&page_size=xxx&ordering=xxx
class SKUListView(ListAPIView):
    """商品列表视图"""
    # 指定查询集:因为要展示的商品列列表需要明确的指定分类，所以重写获取查询集⽅方法
    # queryset = SKU.objects.all()

    # 指定序列化器
    serializer_class = SKUSerializer
    # 指定过滤后端为排序
    filter_backends = [OrderingFilter]
    # 指定排序要的字段
    ordering_fields = ['create_time', 'price', 'sales']
    # 指定查询集
    # queryset = SKU.objects.filter(is_launched=True, category_id=category_id)

    def get_queryset(self):
        category_id = self.kwargs['category_id']
        return SKU.objects.filter(is_launched=True, category_id=category_id)
