from django.shortcuts import render

# Create your views here.
from rest_framework.views import APIView

from goods.models import SKU
from goods.serializers import HotSKUListSerializer

"""
表的设计 思想:
    1. 根据产品给的原型 尽量多的分析表的字段 (不要分析表和表之间的关系)
    2. 在一个安静的没有人打扰的环境中 分析表和表之间的关系(2个表和2个表去分析)
"""


class HomeAPIView(APIView):
    pass


"""
页面静态化  -- 提升用户体验 ,SEO

其实就是我们先把数据 查询出来,查询出来之后,将数据填充到模板中,
形式了html,将html写入到指定的文件

当用户访问的时候 ,直接访问 静态html


"""


"""
列表数据

一个是热销数据
列表数据

热销数据: 应该是到哪个分类去 获取哪个分类的热销数据

1. 获取分类id
2. 根据id获取数据  [SKU,SKU,SKU]
3. 将数据转化为字典(JSON数据)
4. 返回相应

GET      /goods/categories/(?P<category_id>\d+)/hotskus/

"""
from rest_framework.generics import ListAPIView
class HotSKUListAPIView(ListAPIView):

    pagination_class = None

    # queryset = SKU.objects.filter(category_id=category_id).order_by('-sales')[:2]
    # queryset = SKU.objects.all()
    def get_queryset(self):
        category_id = self.kwargs['category_id']
        return SKU.objects.filter(category_id=category_id).order_by('-sales')[:2]



    serializer_class = HotSKUListSerializer







"""
列表数据的获取

当用户选择一个分类的时候,我们需要对分类数据进行 排序,进行分页处理

简化需求,一步一步的实现

先获取所有分类数据,再排序,再分页


先获取所有分类数据
1.先获取所有数据  [SKU,SKU,SKU]
2.将对象列表转换位字典(JSON)
3. 返回相应

GET     /goods/categories/(?P<category_id>\d+)/skus/

"""
from rest_framework.generics import ListAPIView
from rest_framework.filters import OrderingFilter
from rest_framework.pagination import LimitOffsetPagination,PageNumberPagination
from rest_framework.generics import GenericAPIView

class SKUListAPIView(ListAPIView):

    # 添加排序
    filter_backends = [OrderingFilter]
    ordering_fields = ['create_time','sales','price']

    #分页
    # pagination_class =

    serializer_class = HotSKUListSerializer

    # queryset = SKU.objects.filter(category=category_id)
    def get_queryset(self):

        category_id = self.kwargs['category_id']

        return SKU.objects.filter(category=category_id)



from .serializers import SKUIndexSerializer
from drf_haystack.viewsets import HaystackViewSet

class SKUSearchViewSet(HaystackViewSet):
    """
    SKU搜索
    """
    index_models = [SKU]

    serializer_class = SKUIndexSerializer