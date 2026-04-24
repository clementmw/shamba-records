from rest_framework import serializers
from .models import *



class FieldManagementSerializer(serializers.ModelSerializer):
    class Meta:
        model = FieldManagement
        fields = '__all__'
    

class FieldUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = FieldManagement
        fields = ['name', 'planting_date', 'size', 'crop_type','current_stage','field_status','review','review_at']
    
    def update(self, instance, validated_data):
        instance.field_name = validated_data.get('name', instance.field_name)
        instance.size = validated_data.get('size', instance.size)
        instance.crop_type = validated_data.get('crop_type', instance.crop_type)
        instance.current_stage = validated_data.get('current_stage', instance.current_stage)
        instance.field_status = validated_data.get('field_status', instance.field_status)
        instance.review = validated_data.get('review', instance.review)
        instance.review_at = validated_data.get('review_at', instance.review_at)
        instance.save()
        return instance

