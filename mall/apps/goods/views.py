from django.shortcuts import render

# Create your views here.
from goods.models import SKU
from goods.serializers import HostSKUListSerializer

"""
页面静态化  -- 提升用户体验,SEO
其实就是我们现把数据查询出来,查询出来之后,将数据填充到模板中
将html写入到指定的文件,当用户访问的时候,直接访问静态html
"""
"""
列表数据
热销数据
分类数据

热销数据:应该是到哪个分类去获取哪个分类的热销数据

1.获取分类ID
2.根据ID获取数据  [sku,sku]
3.将数据转换为字典或者json数据
4.返回响应

GET   /goods/categories/(?P<category_id>\d+)/hotskus/
"""
from rest_framework.generics import ListAPIView


class HostSKUListAPIView(ListAPIView):

    pagination_class = None

    serializer_class = HostSKUListSerializer

    def get_queryset(self):
        category_id = self.kwargs['category_id']
        return SKU.objects.filter(category_id=category_id).order_by('-sales')[:2]

'''
列表数据的获取
当用户选择一个分类的时候,我们需要对分类数据进行排序,进行分页处理
简化需求,一步一步的实现
现获取所有分类数据,再排序,再分页

现获取所有分类数据
1.先获取所有数据
2.将对象列表转换为字典
3.返回响应

GET    /goods/categories/(?P<category_id>\d+)/skus/
'''
from rest_framework.filters import OrderingFilter


class SKUListAPIView(ListAPIView):
    # 排序
    filter_backends = [OrderingFilter]
    ordering_fields = ['create_time', 'sales', 'price']
    serializer_class = HostSKUListSerializer

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

