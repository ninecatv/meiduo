from drf_haystack.serializers import HaystackSerializer
from rest_framework import serializers

from goods.search_indexes import SKUIndex
from .models import SKU


class SKUSerializer(serializers.ModelSerializer):
    """SKU商品列表序列化器"""

    class Meta:
        model = SKU
        fields = ['id', 'name', 'price', 'default_image_url', 'sales', 'comments']


class SKUIndexSerializer(HaystackSerializer):
    """
    SKU索引结果数据序列化器
    """
    object = SKUSerializer(read_only=True)

    class Meta:
        index_classes = [SKUIndex]
        fields = ('text', 'object')
