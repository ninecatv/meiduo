from django.conf.urls import url

from . import views

urlpatterns = [
    # 去结算
    url(r'^orders/settlement/$', views.OrderSettlementView.as_view()),

    # 订单

    url(r'^orders/$', views.SaveOrderView.as_view({'get': 'list', 'post': 'create'})),

    url(r'^orders/$', views.SaveOrderView.as_view()),

    # 商品评论
    # http://api.meiduo.site:8000/skus/1/comments/
    # 用户订单商品评论
    url(r'^orders/(?P<pk>\d+)/comments/$', views.UNCommentsView.as_view()),

    # orders/20190218071427000000001/uncommentgoods/
    url(r'^orders/(?P<pk>\d+)/uncommentgoods/$', views.UNCommentsView.as_view()),
    url(r'^skus/(?P<pk>\d+)/comments/$', views.SKUCommentsView.as_view()),

]