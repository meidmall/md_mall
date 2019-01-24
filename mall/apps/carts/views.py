import base64
import pickle

from django.shortcuts import render

# Create your views here.
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from carts.serializers import CartSerializer, CartSKUSerializer, CartDeleteSerializer
from django_redis import get_redis_connection

from goods.models import SKU

'''
1.未登录用户的数据是保存在cookie中
    登录用户的数据是保存在redis中

2.cookie数据,我们需要保存商品id,个数,选中状态
    redis数据,我们需要保存商品id,个数,选中状态
3.组织cookie的数据结构
{
    sku_id:{count:3,selected:True}
}

    redis保存在内存中,redis的数据设置原则:占用最少的空间,满足我们的需求
4.判断用户是否登陆
request.user
如果用户的token过期了/伪造的,我们需要重写perform_authentication 方法
让试图现不要进行身份认证,当我们需要的时候再来认证
'''


class CartAPIView(APIView):
    # 重写perform_authentication 方法
    # 这样就可以直接进入到我们的添加购物车的逻辑中来了
    # 当我们需要验证的时候,再去验证

    def perform_authentication(self, request):
        pass
    '''
    我们的token过期了或者被篡改了就不能添加到购物车了
    正确的业务逻辑是现让用户添加到购物车
    token过期了,或者被篡改了,我们就认为是未登陆用户
    如果我们要让用户加入到购物车,就不应该先验证用户的token
    '''
    def post(self, request):
        # 添加购物车的业务逻辑是:
        # 用户点击添加购物车按钮的时候,前端需要收集数据:
        # 商品ID,个数,选中的状态默认为True,用户信息
        # 1.接收数据
        data = request.data
        # 2.校验数据(商品是否存在,商品的个数是否充足)
        serializer = CartSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        # 3.获取校验之后的数据
        count = serializer.validated_data['count']
        sku_id = serializer.validated_data['sku_id']
        selected = serializer.validated_data['selected']
        # 4.获取用户信息
        try:
            user = request.user
        except Exception as e:
            user = None
        # 5.根据用户的信息进行判断用户是否登陆
        if user is not None and user.is_authenticated:
            # 6.登陆用户保存在redis中
            # 6.1连接redis
            redis_conn = get_redis_connection('cart')
            # 6.2将数据保存在redis中的hash和set中
            # redis_conn.hset('cart_%s' % user.id, sku_id, count)
            # 管道1:创建管道
            pl = redis_conn.pipeline()
            # 管道2:将指令添加到管道
            pl.hincrby('cart_%s' % user.id, sku_id, count)
            if selected:
                pl.sadd('cart_selected_%s' % user.id, sku_id)
            # 管道3:执行管道
            pl.execute()
            # 6.3返回响应
            return Response(serializer.data)

        # 7.未登陆用户保存在cookie中
        else:
            # 7.1先获取cookie数据
            cookie_str = request.COOKIES.get('cart')
            # 7.2判断是否存在cookie数据
            if cookie_str is not None:
                decode = base64.b64decode(cookie_str)
                cookie_cart = pickle.loads(decode)
            else:
                cookie_cart = {}
            # 7.3如果添加的购物车商品id存在 则进行商品数量的累加
            if sku_id in cookie_cart:
                origin_count = cookie_cart[sku_id]['count']
                count += origin_count
            # 7.4如果添加的购物车商品id不存在,则直接添加商品信息
            cookie_cart[sku_id] = {
                'count': count,
                'selected': selected
            }
            # 7.5对字典进行处理
            # 7.5.1 将字典转换为二进制
            dumps = pickle.dumps(cookie_cart)
            # 7.5.2 进行base64的编码
            encode = base64.b64encode(dumps)
            # 7.5.3 将bytes类型转换为str
            value = encode.decode()
            # 7.6返回响应
            response = Response(serializer.data)
            response.set_cookie('cart', value)
            return response

    '''
    当用户点击购物车列表的时候,前端需要发送一个get请求
    get请求的书籍需要将用户信息传递过来

    '''
    def get(self, request):
        # 1.接收用户信息
        try:
            user = request.user
        except Exception as e:
            user = None
        # 2.根据用户信息进行判断
        if user is not None and user.is_authenticated:
            # 3.登陆用户从redis中获取数据
            # 3.1 连接redis
            redis_conn = get_redis_connection('cart')
            # 3.2 hash    cart_userid:  {sku_id:count}
            redis_cart = redis_conn.hgetall('cart_%s' % user.id)
            #      set
            redis_selected = redis_conn.smembers('cart_selected_%s' % user.id)
        #         获取hash的所有数据
            cart = {}
            for sku_id, count in redis_cart.items():
                cart[int(sku_id)] = {
                    'count': int(count),
                    'selected': sku_id in redis_selected
                }
        #     3.3 根据商品id获取商品的详细信息
        #     3.4 返回响应
        # 4.未登陆用户从cookie中获取数据
        else:
            # 4.1 先从cookie中获取数据
            cart_str = request.COOKIES.get('cart')
            # 4.2 判断是否存在购物车数据
            if cart_str is not None:
                decode = base64.b64decode(cart_str)
                cart = pickle.loads(decode)
            else:
                cart = {}
            # 4.3 根据商品id,获取商品的详细信息
            # 4.4 返回响应
        # 5.根据商品id,获取商品的详细信息
        skus = SKU.objects.filter(id__in=cart.keys())
        for sku in skus:
            sku.count = cart[sku.id]['count']
            sku.selected = cart[sku.id]['selected']
        serializer = CartSKUSerializer(skus, many=True)
        # 6.返回响应
        return Response(serializer.data)

    def put(self, request):
        """
        前端需要将商品id,count(个数是采用的最终数据提交给后端),selected提交给后端
        """
        # 1.接收数据
        data = request.data
        # 2.校验数据
        serializer = CartSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        # 3.获取验证之后的数据
        count = serializer.validated_data['count']
        selected = serializer.validated_data['selected']
        sku_id = serializer.validated_data['sku_id']
        # 4.获取用户信息
        try:
            user = request.user
        except Exception as e:
            user = None
        # 5.根据用户的信息进行判断用户是否登陆
        if user is not None and user.is_authenticated:
            # 6.登陆用户redis
            # 6.1 连接redis
            redis_conn = get_redis_connection('cart')
            # 6.2更新数据
            # hash
            redis_conn.hset('cart_%s' % user.id, sku_id, count)
            # set
            if selected:
                # 选中,添加进去
                redis_conn.sadd('cart_selected_%s' % user.id, sku_id)
            else:
                # 取消选中,移除出去
                redis_conn.srem('cart_selected_%s' % user.id, sku_id)
            # 6.3返回响应
            # 因为前端是将个数的最终值传递过来的,所以我们要返回回去
            return Response(serializer.data)
        else:
            # 7.未登陆用户用cookie
            # 7.1获取cookie数据
            cookie_str = request.COOKIES.get('cart')
            # 7.2判断cart数据是否存在
            if cookie_str is not None:
                cookie_cart = pickle.loads(base64.b64decode(cookie_str))
            else:
                cookie_cart = {}
            # 7.3更新数据
            if sku_id in cookie_cart:
                cookie_cart[int(sku_id)] = {
                    'count': int(count),
                    'selected': selected
                }
            # 7.4返回响应
            response = Response(serializer.data)
            value = base64.b64encode(pickle.dumps(cookie_cart)).decode()
            response.set_cookie('cart', value)
            return response

    def delete(self, request):
        """
        用户在删除购物车数据的时候只需要将商品的id传递给我们
        """
        # 1. 后端接收数据
        data = request.data
        # 2.校验数据
        serializer = CartDeleteSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        # 3.获取校验之后的数据
        sku_id = serializer.validated_data.get('sku_id')
        # 4.获取用户信息
        try:
            user = request.user
        except Exception as e:
            user = None
        # 5.根据用户信息进行判断
        if user is not None and user.is_authenticated:
            # 6.登陆用户redis
            # 6.1 连接redis
            redis_conn = get_redis_connection('cart')
            # 6.2 删除数据
            pl = redis_conn.pipeline()
            pl.hdel('cart_%s' % user.id, sku_id)
            pl.srem('cart_selected_%s' % user.id, sku_id)
            pl.execute()
            # 6.3 返回响应
            return Response(status=status.HTTP_204_NO_CONTENT)
        else:
            # 7.未登陆用户cookie
            # 7.1 获取cookie数据
            cookie_str = request.COOKIES.get('cart')
            # 7.2判断cart数据是否存在
            if cookie_str is not None:
                cookie_cart = pickle.loads(base64.b64decode(cookie_str))
            else:
                cookie_cart = {}
            # 7.3删除指定数据
            if sku_id in cookie_cart:
                del cookie_cart[sku_id]
            # 7.4返回响应
            response = Response(status=status.HTTP_204_NO_CONTENT)
            value = base64.b64encode(pickle.dumps(cookie_cart)).decode()
            response.set_cookie('cart', value)
            return response

