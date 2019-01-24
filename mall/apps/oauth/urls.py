from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^qq/statues/$', views.OAuthQQURLAPIView.as_view()),
    url(r'^qq/users/$', views.OAuthQQUserAPIView.as_view())
]