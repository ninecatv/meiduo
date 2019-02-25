from django.shortcuts import render
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.generics import CreateAPIView, RetrieveAPIView, UpdateAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import GenericViewSet
from rest_framework.mixins import CreateModelMixin, UpdateModelMixin
from django_redis import get_redis_connection
from rest_framework_jwt.views import ObtainJSONWebToken

# Create your views here.
from goods.models import SKU
from goods.serializer import SKUSerializer
from .serializer import UserAddressSerializer, AddressTitleSerializer, EmailSerializer, UserDetailSerializer, \
    CreateUserSerializer, AddUserBrowsingHistorySerializer
from .models import User, Address
from . import constants
from carts.utils import merge_cart_cookie_to_redis



class UserAuthorizeView(ObtainJSONWebToken):
    """重写账号密码登录视图"""

    def post(self, request, *args, **kwargs):
        response = super(UserAuthorizeView, self).post(request, *args, **kwargs)
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            user = serializer.object.get('user') or request.user
            # 合并购物车
            merge_cart_cookie_to_redis(request, user, response)

        return response


class UserBrowseHistoryView(CreateAPIView):
    """用户浏览记录"""
    serializer_class = AddUserBrowsingHistorySerializer
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """读取用户浏览记录"""
        # 创建redis连接对象
        redis_conn = get_redis_connection('history')

        # 查询用户在redis数据库中的浏览记录[b'1', b'2', b'3']
        sku_ids = redis_conn.lrange('history_%s' % request.user.id, 0, -1)

        # 把sku_id从对应的模型中取出来
        sku_list = []
        for sku_id in sku_ids:
            sku = SKU.objects.get(id=sku_id)
            sku_list.append(sku)

        # 序列化器
        serializer = SKUSerializer(sku_list, many=True)

        return Response(serializer.data)


class AddressViewSet(UpdateModelMixin, CreateModelMixin, GenericViewSet):
    """用户地址"""
    # 只有本网站登陆的用户才能访问此接口
    permission_classes = [IsAuthenticated]

    serializer_class = UserAddressSerializer

    def create(self, request, *args, **kwargs):
        """用户新增地址"""
        # 判断用户地址数量是否上限
        address_count = request.user.addresses.count()
        if address_count > constants.USER_ADDRESS_COUNTS_LIMIT:
            return Response({'message': '地址数量上限'}, status=status.HTTP_400_BAD_REQUEST)
        # 创建序列化器给data参数传值(反序列化)
        # serializer = UserAddressSerializer(data=request.data, context={'request': request})
        # # 调用序列化器的is_valid方法
        # serializer.is_valid(raise_exception=True)
        # # 调用序列化器的save
        # serializer.save()
        # # 响应
        # return Response(serializer.data, status=status.HTTP_201_CREATED)
        return super(AddressViewSet, self).create(request, *args, **kwargs)

    def get_queryset(self):
        return self.request.user.addresses.filter(is_deleted=False)

    # GET /addresses/
    def list(self, request, *args, **kwargs):
        """
        用户地址列表数据
        """
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        user = self.request.user
        return Response({
            'user_id': user.id,
            'default_address_id': user.default_address_id,
            'limit': constants.USER_ADDRESS_COUNTS_LIMIT,
            'addresses': serializer.data,
        })

        # delete /addresses/<pk>/

    def destroy(self, request, *args, **kwargs):
        """
        处理删除
        """
        address = self.get_object()

        # 进行逻辑删除
        address.is_deleted = True
        address.save()

        return Response(status=status.HTTP_204_NO_CONTENT)

        # put /addresses/pk/status/

    @action(methods=['put'], detail=True)
    def status(self, request, pk=None):
        """
        设置默认地址
        """
        address = self.get_object()
        request.user.default_address = address
        request.user.save()
        return Response({'message': 'OK'}, status=status.HTTP_200_OK)

    # put /addresses/pk/title/
    # 需要请求体参数 title
    @action(methods=['put'], detail=True)
    def title(self, request, pk=None):
        """
        修改标题
        """
        address = self.get_object()
        serializer = AddressTitleSerializer(instance=address, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


# GET email/verification
class EmailVerifyView(APIView):
    """激活邮箱"""

    def get(self, request):

        # 1. 获取token查询参数
        token = request.query_params.get('token')
        if not token:
            return Response({'message': '缺少token'}, status=status.HTTP_400_BAD_REQUEST)

        # 2. 对token进行解密并返回查询到的user
        user = User.check_verify_email_token(token)
        if not user:
            return Response({'message': '无效的token'}, status=status.HTTP_400_BAD_REQUEST)

        # 3. 修改user的email_active字段, 并保存
        user.email_active = True
        user.save()

        return Response({'message': 'ok'})


# PUT email/
class EmailView(UpdateAPIView):
    """保存用户邮箱"""

    permission_classes = [IsAuthenticated]
    serializer_class = EmailSerializer

    def get_object(self):
        return self.request.user


# url(r'^user/$', views.UserDetailSerializer),
class UserDetailView(RetrieveAPIView):
    """用户个人中心"""
    # 指定序列化器
    serializer_class = UserDetailSerializer
    # 只有登陆的用户才能访问当前视图
    permission_classes = [IsAuthenticated]

    def get_object(self):
        """返回当前用户信息"""
        return self.request.user


# url(r'^authorizations/$', obtain_jwt_token)
class UserView(CreateAPIView):
    """注册视图"""
    serializer_class = CreateUserSerializer


# url(r'^usernames/(?P<username>\w{5,20})/count/$', views.UsernameCountView.as_view()),
class UsernameCountView(APIView):
    """验证用户名是否已存在"""

    def get(self, request, username):
        # 查询用户是否已存在
        count = User.objects.filter(username=username).count()
        # 构造响应数据
        data = {
            'count': count,
            'username': username
        }

        return Response(data)


# url(r'^mobiles/(?P<mobile>1[3-9]\d{9})/count/$', views.MobileCountView.as_view()),
class MobileCountView(APIView):
    """验证手机号码是否已注册"""

    def get(self, request, mobile):
        # 查询手机号
        count = User.objects.filter(mobile=mobile).count()
        # 构造响应数据
        data = {
            'count': count,
            'username': mobile
        }

        return Response(data)
