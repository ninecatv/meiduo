from django.shortcuts import render
from QQLoginTool.QQtool import OAuthQQ
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.conf import settings
import logging
from rest_framework_jwt.settings import api_settings

from utils.weibo.weibotool import OAuthWeibo
from .models import QQAuthUser, OAuthSinaUser
from .utils import generate_save_user_token
from .serializer import QQAuthUserSerializer, SinaAuthUserSerializer
from carts.utils import merge_cart_cookie_to_redis
# Create your views here.

logger = logging.getLogger('django')


# url(r'^qq/user/$', views.QQAuthUserView.as_view()),
class QQAuthUserView(APIView):
    """用户扫码登陆回调处理"""

    def get(self, request):
        """
        https://graph.qq.com/oauth2.0/authorize?response_type=code&client_id=xxx&redirect_uri=xxx&state=xxx
        提取code请求参数
        使用code向qq服务器发送access_token请求
        使用access_token向qq服务器请求openid
        使用openid查询该qq号是否绑定过美多商城
        如果openid以绑定美多商城用户, 直接生成JWT token返回
        如果openid没有绑定美多商城用户, 创建用户并绑定openid
        """
        # 提取code请求参数
        code = request.query_params.get('code')
        if not code:
            return Response({'message': '缺少code'}, status=status.HTTP_400_BAD_REQUEST)

        # 创建OAuth对象
        oauthqq = OAuthQQ(
                client_id=settings.QQ_CLIENT_ID,
                client_secret=settings.QQ_CLIENT_SECRET,
                redirect_uri=settings.QQ_REDIRECT_URI,
                )

        try:
            # 通过code向qq服务器获取access_token
            access_token = oauthqq.get_access_token(code)

            # 通过access_token向qq服务器获取openid
            openid = oauthqq.get_open_id(access_token)
        except Exception as error:
            logger.info(error)
            return Response({'message': 'QQ服务器异常'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        # 查询openid是否绑定美多商城用户
        try:
            oauth_model = QQAuthUser.objects.get(openid=openid)
        except QQAuthUser.DoesNotExist:

            # 如果openid没有绑定过美多商城中的用户
            # 把openid进行加密安全处理,再响应给浏览器,让它先帮我们保存一会
            openid_sin = generate_save_user_token(openid)
            return Response({'access_token': openid_sin})

        else:
            # 如果openid已经绑定过美多商城中的用户(生成jwt token直接让它登录成功)
            # 手动生成token
            jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER  # 加载生成载荷函数
            jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER  # 加载生成token函数

            # 获取user对象
            user = oauth_model.user

            payload = jwt_payload_handler(user)  # 生成载荷
            token = jwt_encode_handler(payload)  # 根据载荷生成token

            response = Response({
                'token': token,
                'username': user.username,
                'user_id': user.id
            })
            # 合并购物车
            merge_cart_cookie_to_redis(request, user, response)

            return response

    def post(self, request):
        """openid绑定用户"""
        # 创建序列化器,进行反序列化
        serializer = QQAuthUserSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()  # save会接收到create和update的返回值

        # 手动生成token
        jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER  # 加载生成载荷函数
        jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER  # 加载生成token函数

        payload = jwt_payload_handler(user)  # 生成载荷
        token = jwt_encode_handler(payload)

        response = Response({
            'token': token,
            'username': user.username,
            'user_id': user.id
        })
        # 合并购物车
        merge_cart_cookie_to_redis(request, user, response)

        return response


class OAuthUrlView(APIView):
    """生成qq扫码登陆连接"""

    def get(self, request):
        # 1.获取next(从那里去到login界面)参数路径
        next = request.query_params.get('next')
        if not next:  # 如果没有指定来源将来登录成功就回到首页
            next = '/'

        # QQ登录参数
        """
        QQ_CLIENT_ID = '101514053'
        QQ_CLIENT_SECRET = '1075e75648566262ea35afa688073012'
        QQ_REDIRECT_URI = 'http://www.meiduo.site:8080/oauth_callback.html'
        oauthqq = OAuthQQ(client_id='101514053', 
                  client_secret='1075e75648566262ea35afa688073012', 
                  redirect_uri='http://www.meiduo.site:8080/oauth_callback.html',
                  state=next)
        """

        # 创建qq的登陆SDK对象
        oauth = OAuthQQ(
            client_id=settings.QQ_CLIENT_ID,
            client_secret=settings.QQ_CLIENT_SECRET,
            redirect_uri=settings.QQ_REDIRECT_URI,
            state=next
        )

        # 调用OAuth里面的get_qq_url生成qq登陆连接
        login_url = oauth.get_qq_url()

        # 把生成的qq登陆连接返回给前端
        return Response({'login_url': login_url})


class SinaAuthURLView(APIView):
    # http: // open.weibo.com / wiki / Oauth2 / authorize
    # 获取access_token接口：http: // open.weibo.com / wiki / Oauth2 / access_token
    def get(self, request):
        next = request.query_params.get('next')
        if not next:
            next = '/'
        oauthweibo = OAuthWeibo(client_id=settings.WEIBO_CLIENT_ID,
                        client_secret=settings.WEIBO_CLIENT_SECRET,
                        redirect_uri=settings.WEIBO_REDIRECT_URI,
                        state=next)
        login_url = oauthweibo.get_weibo_url()
        return Response({'login_url':login_url})


class SinaAuthUserView(APIView):
    """用户扫码登陆的回调处理"""
    def get(self, request):
        code = request.query_params.get('code')
        if not code:
            return Response({'message': '缺少code'}, status=status.HTTP_400_BAD_REQUEST)

        oauthweibo = OAuthWeibo(client_id=settings.WEIBO_CLIENT_ID,
                          client_secret=settings.WEIBO_CLIENT_SECRET,
                          redirect_uri=settings.WEIBO_REDIRECT_URI
                    )
        try:
            access_token = oauthweibo.get_access_token(code)
        except Exception as e:
            logger.info(e)
            return Response({'message': '微博服务器异常'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        try:
            # 使用access_token查询用户是否绑定
            oauthweibouser = OAuthSinaUser.objects.get(access_token=access_token)
        except OAuthSinaUser.DoesNotExist:
            # 把access_token进行加密安全处理,再响应给浏览器,让它先帮我们保存一会
            access_token = generate_save_user_token(access_token)
            return Response({'access_token': access_token})
        else:
            # 如果已经绑定,直接生成JWT token返回
            jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
            jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER

            # 获取oauth_user对象
            user = oauthweibouser.user
            payload = jwt_payload_handler(user)
            token = jwt_encode_handler(payload)

            response = Response({
                'token': token,
                'user_id': user.id,
                'username': user.username
            })
            # 合并购物车
            merge_cart_cookie_to_redis(request, response, user)
            return response

    def post(self, request):
        serializer = SinaAuthUserSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # ⽣成JWT token，并响应
        jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
        jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER
        payload = jwt_payload_handler(user)
        token = jwt_encode_handler(payload)
        response = Response({
            'token': token,
            'user_id': user.id,
            'username': user.username
        })

        merge_cart_cookie_to_redis(request, response, user)
        return response

