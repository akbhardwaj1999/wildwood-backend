from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import (
    NEW_WholesaleRequest, 
    NEW_WholesaleUser, 
    NEW_WholesaleDiscountConfig,
    NEW_WholesaleDiscount
)
from .utils import (
    NEW_is_user_wholesale,
    NEW_get_discount_summary,
    NEW_calculate_wholesale_discount,
    NEW_get_next_discount_threshold
)

User = get_user_model()


class WholesaleRequestSerializer(serializers.ModelSerializer):
    """Serializer for wholesale account requests"""
    business_type_display = serializers.SerializerMethodField()
    status_display = serializers.SerializerMethodField()
    documents_url = serializers.SerializerMethodField()
    
    class Meta:
        model = NEW_WholesaleRequest
        fields = [
            'id', 'business_name', 'business_type', 'business_type_display',
            'tax_id', 'website', 'expected_monthly_volume', 'reason',
            'documents', 'documents_url', 'status', 'status_display',
            'reviewed_by', 'reviewed_at', 'admin_notes', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'status', 'reviewed_by', 'reviewed_at', 'admin_notes',
            'created_at', 'updated_at'
        ]
    
    def get_business_type_display(self, obj):
        """Get business type display name"""
        return obj.get_business_type_display()
    
    def get_status_display(self, obj):
        """Get status display name"""
        return obj.get_status_display()
    
    def get_documents_url(self, obj):
        """Return absolute URL for documents if available"""
        if obj.documents:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.documents.url)
            return obj.documents.url
        return None


class WholesaleRequestCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating wholesale requests"""
    
    class Meta:
        model = NEW_WholesaleRequest
        fields = [
            'business_name', 'business_type', 'tax_id', 'website',
            'expected_monthly_volume', 'reason', 'documents'
        ]
    
    def validate(self, data):
        """Validate that user doesn't have pending or approved request"""
        user = self.context['request'].user
        
        existing_request = NEW_WholesaleRequest.objects.filter(
            user=user,
            status__in=['pending', 'approved']
        ).first()
        
        if existing_request:
            if existing_request.status == 'pending':
                raise serializers.ValidationError(
                    'You already have a pending wholesale request.'
                )
            else:
                raise serializers.ValidationError(
                    'You already have an approved wholesale account.'
                )
        
        return data
    
    def create(self, validated_data):
        """Create wholesale request for current user"""
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class WholesaleUserSerializer(serializers.ModelSerializer):
    """Serializer for wholesale user profile"""
    user_username = serializers.CharField(source='user.username', read_only=True)
    user_email = serializers.CharField(source='user.email', read_only=True)
    
    class Meta:
        model = NEW_WholesaleUser
        fields = [
            'id', 'user', 'user_username', 'user_email', 'is_wholesale',
            'approved_by', 'approved_at', 'notes', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'user', 'approved_by', 'approved_at', 'created_at', 'updated_at'
        ]


class WholesaleDiscountConfigSerializer(serializers.ModelSerializer):
    """Serializer for wholesale discount configuration"""
    tiers = serializers.SerializerMethodField()
    
    class Meta:
        model = NEW_WholesaleDiscountConfig
        fields = [
            'id', 'name', 'threshold_1', 'discount_1', 'threshold_2', 'discount_2',
            'threshold_3', 'discount_3', 'threshold_4', 'discount_4',
            'is_active', 'tiers', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_tiers(self, obj):
        """Return tiers in a structured format"""
        return [
            {
                'name': f'Above ${obj.threshold_1}',
                'min_order_amount': float(obj.threshold_1),
                'discount_percentage': float(obj.discount_1),
                'description': f'Get {obj.discount_1}% off orders above ${obj.threshold_1}'
            },
            {
                'name': f'Above ${obj.threshold_2}',
                'min_order_amount': float(obj.threshold_2),
                'discount_percentage': float(obj.discount_2),
                'description': f'Get {obj.discount_2}% off orders above ${obj.threshold_2}'
            },
            {
                'name': f'Above ${obj.threshold_3}',
                'min_order_amount': float(obj.threshold_3),
                'discount_percentage': float(obj.discount_3),
                'description': f'Get {obj.discount_3}% off orders above ${obj.threshold_3}'
            },
            {
                'name': f'Above ${obj.threshold_4}',
                'min_order_amount': float(obj.threshold_4),
                'discount_percentage': float(obj.discount_4),
                'description': f'Get {obj.discount_4}% off orders above ${obj.threshold_4}'
            }
        ]


class WholesaleStatusSerializer(serializers.Serializer):
    """Serializer for wholesale status response"""
    is_wholesale = serializers.BooleanField()
    has_pending_request = serializers.BooleanField()
    has_approved_request = serializers.BooleanField()
    wholesale_profile = WholesaleUserSerializer(required=False, allow_null=True)
    recent_requests = WholesaleRequestSerializer(many=True, required=False)
    discount_tiers = serializers.ListField(required=False, allow_null=True)


class WholesaleDiscountCalculateSerializer(serializers.Serializer):
    """Serializer for discount calculation request"""
    amount = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=0)
    
    def validate_amount(self, value):
        """Validate amount is positive"""
        if value <= 0:
            raise serializers.ValidationError('Amount must be greater than 0.')
        return value


class WholesaleDiscountResponseSerializer(serializers.Serializer):
    """Serializer for discount calculation response"""
    success = serializers.BooleanField()
    is_wholesale = serializers.BooleanField()
    discount_amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    discount_percentage = serializers.DecimalField(max_digits=5, decimal_places=2, required=False, allow_null=True)
    discount_tiers = serializers.ListField(required=False, allow_null=True)
    next_threshold = serializers.DictField(required=False, allow_null=True)

