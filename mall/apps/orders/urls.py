from django.conf.urls import url
from . import views

urlpatterns = [
    # /orders/places/
    url(r'^places/$', views.PlaceOrderAPIView.as_view(), name='placeorder'),
    url(r'^$', views.OrderAPIView.as_view(), name='order'),
    url(r'^skus/(?P<pk>\d+)/comments/$', views.CommentShowAPIView.as_view(), name='comment'),
    # url(r'^(?P<sku_id>\w+)/comments/$', views.CommentAPIView.as_view(), name='comments'),

]