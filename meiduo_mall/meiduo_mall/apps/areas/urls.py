from rest_framework.routers import DefaultRouter

from . import views

urlpatterns = []


route = DefaultRouter()
route.register(r'areas', views.AreasViewSet, base_name='areas')
urlpatterns += route.urls

