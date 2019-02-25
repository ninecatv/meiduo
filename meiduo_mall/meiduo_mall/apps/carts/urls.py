from django.conf.urls import url

from . import views

urlpatterns = [
    # 购物车路由
    url(r'^carts/$', views.CartsView.as_view()),

    # 购物车全选
    url(r'^carts/selection/$', views.CartSelectedView.as_view()),
]
