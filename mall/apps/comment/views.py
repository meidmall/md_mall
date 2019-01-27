# from django.shortcuts import render
#
# # Create your views here.
# from rest_framework.generics import ListAPIView
#
# from comment.serializers import CommentShowSerializer
# from orders.models import OrderGoods
#
#
# class CommentShowAPIView(ListAPIView):
#
#     serializer_class = CommentShowSerializer
#
#     def get_queryset(self):
#         sku_id = self.kwargs['pk']
#         return OrderGoods.objects.filter(sku_id=sku_id)