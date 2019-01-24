from django.conf.urls import url
from .views import OAuthQQURLAPIView,OAuthQQUserAPIView
urlpatterns =[
    url(r'^qq/statues/$',OAuthQQURLAPIView.as_view()),

    url(r'^qq/users/$',OAuthQQUserAPIView.as_view()),
]