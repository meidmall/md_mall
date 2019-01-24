from rest_framework import serializers

from areas.models import Area


class AreaSerializer(serializers.ModelSerializer):


    class Meta:
        model = Area
        fields = ['id','name']


# 市
class SubsAreaSerialzier(serializers.ModelSerializer):

    # area_set = AreaSerializer(many=True)
    subs = AreaSerializer(many=True)

    class Meta:
        model = Area
        # fields = ['area_set']
        fields = ['subs','id','name']