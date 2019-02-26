from django.conf.urls import url

from . import views

urlpatterns = [
    # qq登陆url
    url(r'^qq/authorization/$', views.OAuthUrlView.as_view()),

    # qq登陆的回调
    url(r'^qq/user/$', views.QQAuthUserView.as_view()),

    # 微博登录url
    url(r'^weibo/authorization/$', views.SinaAuthURLView.as_view()),

    # 微博登录回调
    url(r'^sina/user/$', views.SinaAuthUserView.as_view()),
]
