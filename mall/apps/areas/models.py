from django.db import models

#一个省: n个市

# 省
class Area(models.Model):
    name = models.CharField(max_length=20, verbose_name='名称')
    parent = models.ForeignKey('self', on_delete=models.SET_NULL,related_name='subs', null=True, blank=True, verbose_name='上级行政区划')
    # area_set = [Area,Area,Area]  市
    # subs = [Area,Area,Area]  市
    class Meta:
        db_table = 'tb_areas'
        verbose_name = '行政区划'
        verbose_name_plural = '行政区划'
    def __str__(self):
        return self.name
# 省
# class Area(models.Model):
#     name = models.CharField(max_length=20, verbose_name='名称')
#     parent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, verbose_name='上级行政区划')
#      #市
#     # area_set = [Area,Area,]
#     class Meta:
#         db_table = 'tb_areas'
#         verbose_name = '行政区划'
#         verbose_name_plural = '行政区划'
#
#     def __str__(self):
#         return self.name


# 人物  1
#  bookinfo_set

# 书籍  n