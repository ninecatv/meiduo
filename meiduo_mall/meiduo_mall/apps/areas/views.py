from django.shortcuts import render
from rest_framework.viewsets import ReadOnlyModelViewSet
from rest_framework_extensions.cache.mixins import CacheResponseMixin

from .models import Areas
from .serializer import AreasSerializer, SubAreasSerializer
# Create your views here.


# GET areas/
class AreasViewSet(CacheResponseMixin, ReadOnlyModelViewSet):
    """省市区查询列表视图"""
    
    pagination_class = None  # 不使用分页

    def get_queryset(self):
        if self.action == 'list':
            return Areas.objects.filter(parent_id=None)
        else:
            return Areas.objects.all()

    def get_serializer_class(self):
        if self.action == 'list':
            return AreasSerializer
        else:
            return SubAreasSerializer



