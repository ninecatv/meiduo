from django.conf.urls import url

from . import views

urlpatterns = [
    # 支付宝
    url(r'orders/(?P<order_id>\d+)/payment/', views.PaymentView.as_view()),

    # 支付完成
    url(r'^payment/status/$', views.PaymentStatusView.as_view())
]
