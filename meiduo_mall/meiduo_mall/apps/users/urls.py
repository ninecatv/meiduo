from django.conf.urls import url
from rest_framework_jwt.views import obtain_jwt_token
from rest_framework.routers import DefaultRouter

from . import views


urlpatterns = [
    # 用户注册路由
    url(r'^users/$', views.UserView.as_view()),

    # 验证用户名路由
    url(r'^usernames/(?P<username>\w{5,20})/count/$', views.UsernameCountView.as_view()),

    # 验证手机号码路由
    url(r'^mobiles/(?P<mobile>1[3-9]\d{9})/count/$', views.MobileCountView.as_view()),

    # JWT登陆路由
    url(r'^authorizations/$', views.UserAuthorizeView.as_view()),

    # 用户中心路由
    url(r'^user/$', views.UserDetailView.as_view()),

    # 邮件
    url(r'^email/$', views.EmailView.as_view()),

    # 激活邮箱
    url(r'^email/verification/$', views.EmailVerifyView.as_view()),

    # 浏览记录
    url(r'^browse_histories/$', views.UserBrowseHistoryView.as_view()),

]

route = DefaultRouter()
route.register(r'addresses', views.AddressViewSet, base_name='addresses')
urlpatterns += route.urls
# POST /addresses/ 新建  -> create
# PUT /addresses/<pk>/ 修改  -> update
# GET /addresses/  查询  -> list
# DELETE /addresses/<pk>/  删除 -> destroy
# PUT /addresses/<pk>/status/ 设置默认 -> status
# PUT /addresses/<pk>/title/  设置标题 -> title


