from rest_framework import serializers
from api.models import User, Catering, VariantCaterings, Order
from django.db import transaction
from django.core.exceptions import ValidationError

class UserSerializer(serializers.ModelSerializer):
    total_order = serializers.IntegerField(read_only=True)
    class Meta:
        model = User
        fields = ('username',
                  'id',
                  'role',
                  'store_name',
                  'total_order')
    
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation.pop('password', None)
        return representation

        
class VariantCateringSerializer(serializers.ModelSerializer):
    class Meta:
        model = VariantCaterings
        fields = (
            'id',
            'variant_name',
            'additional_price',
        )

class CateringSerializer(serializers.ModelSerializer):
    catering_variants = VariantCateringSerializer(many=True)
    class Meta:
        model = Catering
        fields = (
            'id',
            'title',
            'imageLink',
            'price',
            'is_closed',
            'stock',
            'date',
            'created_at',
            'created_by',
            'catering_variants',
        )
    
    def create(self, validated_data):
        variants = validated_data.pop('catering_variants')
        catering = Catering.objects.create(**validated_data)
        for variant in variants :
            VariantCaterings.objects.create(catering=catering, **variant)
        return catering


class OrderCateringSerializer(serializers.ModelSerializer):
    class Meta:
        model = Catering
        fields = (
            'id',
            'date',
            'title',
            'price',
            'imageLink',
        )

class OrderUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            'id',
            'username',
        )


class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = (
            'id',
            'ordered_by',
            'ordered_at',
            'is_paid',
            'catering',
            'notes',
            'variant'
        )
        extra_kwargs = {
            'variant': {'required': False, 'allow_null': True},
        }


class OrderCateringViewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Catering
        fields = (
            'id',
            'title',
            'price',
            'date'
        )

class OrderViewSerializer(serializers.ModelSerializer):
    ordered_by = OrderUserSerializer()
    variant = VariantCateringSerializer()
    catering = OrderCateringViewSerializer()
    class Meta:
        model = Order
        fields = (
            'id',
            'ordered_by',
            'ordered_at',
            'is_paid',
            'catering',
            'notes',
            'variant'
        )
        extra_kwargs = {
            'variant': {'required': False, 'allow_null': True},
        }


class CateringViewSerializer(serializers.ModelSerializer):
    order_count = serializers.IntegerField(read_only=True)
    catering_variants = VariantCateringSerializer(many=True)
    created_by = UserSerializer()
    class Meta:
        model = Catering
        fields = (
            'id',
            'title',
            'price',
            'date',
            'imageLink',
            'created_at',
            'created_by',
            'catering_variants',
            'is_closed',
            'stock',
            'order_count'
        )