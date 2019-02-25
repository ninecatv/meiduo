from django.conf.urls import url

from . import views

urlpatterns = [
    # 去结算
    url(r'^orders/settlement/$', views.OrderSettlementView.as_view()),

    # 订单
    url(r'^orders/$', views.SaveOrderView.as_view()),
]