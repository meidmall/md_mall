from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^qq/statues/$', views.OAuthQQURLAPIView.as_view()),
    url(r'^qq/users/$', views.OAuthQQUserAPIView.as_view()),
    url(r'^weibo/statues/$', views.WeiboAuthURLView.as_view()),
    url(r'^weibo/users/$', views.OAuthQQUserAPIView.as_view()),
]