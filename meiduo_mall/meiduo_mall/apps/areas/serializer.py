from rest_framework import serializers

from .models import Areas


class AreasSerializer(serializers.ModelSerializer):
    """如果是查询所有的省的就用此序列器"""

    class Meta:
        model = Areas
        fields = ['id', 'name']


class SubAreasSerializer(serializers.ModelSerializer):
    """如果是查询单一省或者市的话就用此序列化器"""
    # 子集样式跟AreaSerializer⼀样
    subs = AreasSerializer(many=True)

    class Meta:
        model = Areas
        fields = ['id', 'name', 'subs']
