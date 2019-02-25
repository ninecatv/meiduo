from django.conf.urls import url

from . import views

urlpatterns = [
    # qq登陆url
    url(r'^qq/authorization/$', views.OAuthUrlView.as_view()),

    # qq登陆的回调
    url(r'^qq/user/$', views.QQAuthUserView.as_view()),
]