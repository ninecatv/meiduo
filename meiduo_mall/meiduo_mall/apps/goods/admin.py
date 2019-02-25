from django.contrib import admin

from . import models
from celery_tasks.html.tasks import generate_static_list_search_html, generate_static_sku_detail_html
# Register your models here.


class GoodsCategoryAdmin(admin.ModelAdmin):
    """
    模型站点管理类,不光可以控制admin的页面展示样式,还可以监听它里面的数据变化
    """
    def save_model(self, request, obj, form, change):
        """
        监听运营人员在admin界面点击了商品分类保存事件
        :param request: 本次保存的请求对象
        :param obj: 本次保存的模型对象
        :param form: 要进行修改的表单数据
        :param change: 是否要进行修改 True或False
        """
        obj.save()
        generate_static_list_search_html.delay()

    def delete_model(self, request, obj):
        """
        监听运营人员在admin界面点击商品分类删除事件
        :param request: 本次删除的请求对象
        :param obj: 本次要删除的模型对象
        """
        obj.delete()
        generate_static_list_search_html.delay()


class SKUAdmin(admin.ModelAdmin):
    """sku商品"""
    def save_model(self, request, obj, form, change):
        obj.save()
        generate_static_sku_detail_html.delay(obj.id)


class SKUImageAdmin(admin.ModelAdmin):
    """sku图片"""

    def save_model(self, request, obj, form, change):
        obj.save()

        # 获取sku
        sku = obj.sku  # 获取sku所对应的图片
        if not sku.default_image_url:  # 如果sku没有默认图片
            sku.default_image_url = obj.image.url  # 把当前的图片路径设置到sku中

        generate_static_sku_detail_html.delay(sku.id)

    def delete_model(self, request, obj):
        obj.delete()
        generate_static_sku_detail_html.delay(obj.sku.id)


admin.site.register(models.GoodsCategory, GoodsCategoryAdmin)
admin.site.register(models.GoodsChannel)
admin.site.register(models.Goods)
admin.site.register(models.Brand)
admin.site.register(models.GoodsSpecification)
admin.site.register(models.SpecificationOption)
admin.site.register(models.SKU, SKUAdmin)
admin.site.register(models.SKUSpecification)
admin.site.register(models.SKUImage, SKUImageAdmin)