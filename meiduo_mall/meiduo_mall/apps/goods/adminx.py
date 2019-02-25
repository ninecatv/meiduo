import xadmin
from xadmin import views

from goods import models
from orders import models


class BaseSetting(object):
    """xadmin的基本配置"""
    enable_themes = True  # 开启主题切换功能
    use_bootswatch = True


xadmin.site.register(views.BaseAdminView, BaseSetting)


class GlobalSettings(object):
    """xadmin的全局配置"""
    site_title = "美多商城运营管理系统"  # 设置站点标题
    site_footer = "美多商城集团有限公司"  # 设置站点的页脚
    menu_style = "accordion"  # 设置菜单折叠


class SKUAdmin(object):
    # 小图标
    model_icon = 'fa fa-gift'
    # 显示字段
    list_display = ['id', 'name', 'price', 'stock', 'sales', 'comments']
    # 通过id name进行搜索哦
    search_fields = ['id', 'name']
    # 分类
    list_filter = ['category']
    # 修改price stock
    list_editable = ['price', 'stock']
    # 查看商品详情信息
    show_detail_fields = ['name']
    # 书签
    show_bookmarks = True
    # 只读字段
    readonly_fields = ['sales', 'comments']


class OrderAdmin(object):
    list_display = ['order_id', 'create_time', 'total_amount', 'pay_method', 'status']
    refresh_times = [3, 5]  # 可选以支持按多长时间(秒)刷新页面

    data_charts = {
        "order_amount": {'title': '订单金额', "x-field": "create_time", "y-field": ('total_amount',),
                       "order": ('create_time',)},
        "order_count": {'title': '订单量', "x-field": "create_time", "y-field": ('total_count',),
                       "order": ('create_time',)},
    }


xadmin.site.register(models.SKU, SKUAdmin)
xadmin.site.register(views.CommAdminView, GlobalSettings)
xadmin.site.register(models.OrderInfo, OrderAdmin)