from rest_framework import status, generics, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from django.shortcuts import get_object_or_404
from django.utils import timezone
from decimal import Decimal

from .models import (
    NEW_WholesaleRequest,
    NEW_WholesaleUser,
    NEW_WholesaleDiscountConfig,
    NEW_WholesaleDiscount
)
from .serializers import (
    WholesaleRequestSerializer,
    WholesaleRequestCreateSerializer,
    WholesaleUserSerializer,
    WholesaleDiscountConfigSerializer,
    WholesaleStatusSerializer,
    WholesaleDiscountCalculateSerializer,
    WholesaleDiscountResponseSerializer
)
from .utils import (
    NEW_is_user_wholesale,
    NEW_get_discount_summary,
    NEW_calculate_wholesale_discount,
    NEW_get_next_discount_threshold
)


class WholesaleStatusView(generics.RetrieveAPIView):
    """
    Get current user's wholesale status
    GET /api/wholesale/status/
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = WholesaleStatusSerializer
    
    def get_object(self):
        user = self.request.user
        is_wholesale = NEW_is_user_wholesale(user)
        
        # Get wholesale profile if exists
        try:
            wholesale_profile = user.wholesale_profile
        except NEW_WholesaleUser.DoesNotExist:
            wholesale_profile = None
        
        # Check for pending/approved requests
        pending_request = NEW_WholesaleRequest.objects.filter(
            user=user,
            status='pending'
        ).first()
        
        approved_request = NEW_WholesaleRequest.objects.filter(
            user=user,
            status='approved'
        ).first()
        
        # Get recent requests
        recent_requests = NEW_WholesaleRequest.objects.filter(
            user=user
        ).order_by('-created_at')[:5]
        
        # Get discount summary if wholesale
        discount_summary = NEW_get_discount_summary(user) if is_wholesale else None
        
        return {
            'is_wholesale': is_wholesale,
            'has_pending_request': pending_request is not None,
            'has_approved_request': approved_request is not None,
            'wholesale_profile': wholesale_profile,
            'recent_requests': recent_requests,
            'discount_tiers': discount_summary['discount_tiers'] if discount_summary else None
        }


class WholesaleRequestCreateView(generics.CreateAPIView):
    """
    Create a new wholesale account request
    POST /api/wholesale/request/
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = WholesaleRequestCreateSerializer
    parser_classes = [MultiPartParser, FormParser]
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context


class WholesaleRequestListView(generics.ListAPIView):
    """
    List user's wholesale requests
    GET /api/wholesale/requests/
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = WholesaleRequestSerializer
    
    def get_queryset(self):
        return NEW_WholesaleRequest.objects.filter(
            user=self.request.user
        ).order_by('-created_at')
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context


class WholesaleRequestDetailView(generics.RetrieveAPIView):
    """
    Get details of a specific wholesale request
    GET /api/wholesale/requests/{id}/
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = WholesaleRequestSerializer
    
    def get_queryset(self):
        return NEW_WholesaleRequest.objects.filter(user=self.request.user)
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context


class WholesaleTiersView(generics.ListAPIView):
    """
    Get available wholesale discount tiers
    GET /api/wholesale/tiers/
    """
    permission_classes = [permissions.AllowAny]  # Public endpoint
    serializer_class = WholesaleDiscountConfigSerializer
    
    def get_queryset(self):
        return NEW_WholesaleDiscountConfig.objects.filter(is_active=True)
    
    def list(self, request, *args, **kwargs):
        """Return active config with tiers"""
        config = NEW_WholesaleDiscountConfig.objects.filter(is_active=True).first()
        
        if not config:
            return Response({
                'message': 'No wholesale pricing tiers available.',
                'tiers': []
            }, status=status.HTTP_200_OK)
        
        serializer = self.get_serializer(config)
        return Response({
            'message': 'Wholesale pricing tiers',
            'config': serializer.data
        }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def calculate_wholesale_discount(request):
    """
    Calculate wholesale discount for a given order amount
    POST /api/wholesale/discount/calculate/
    Body: {"amount": 1500.00}
    """
    serializer = WholesaleDiscountCalculateSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    order_amount = Decimal(str(serializer.validated_data['amount']))
    user = request.user
    
    # Check if user is wholesale
    is_wholesale = NEW_is_user_wholesale(user)
    
    if not is_wholesale:
        return Response({
            'success': True,
            'is_wholesale': False,
            'discount_amount': 0.00,
            'discount_percentage': None,
            'discount_tiers': None,
            'next_threshold': None,
            'message': 'You need wholesale access to get discounts.'
        }, status=status.HTTP_200_OK)
    
    # Calculate discount
    discount_amount = NEW_calculate_wholesale_discount(order_amount, user)
    
    # Get discount summary
    discount_summary = NEW_get_discount_summary(user)
    
    # Get next threshold
    next_threshold = NEW_get_next_discount_threshold(order_amount)
    
    # Get discount percentage
    config = NEW_WholesaleDiscountConfig.objects.filter(is_active=True).first()
    discount_percentage = None
    if config:
        discount_percentage = config.get_discount_for_amount(order_amount)
    
    return Response({
        'success': True,
        'is_wholesale': True,
        'discount_amount': float(discount_amount),
        'discount_percentage': float(discount_percentage) if discount_percentage else None,
        'discount_tiers': discount_summary['discount_tiers'] if discount_summary else None,
        'next_threshold': next_threshold
    }, status=status.HTTP_200_OK)


# Admin Views
class AdminWholesaleRequestListView(generics.ListAPIView):
    """
    List all wholesale requests (Admin only)
    GET /api/wholesale/admin/requests/
    """
    permission_classes = [permissions.IsAdminUser]
    serializer_class = WholesaleRequestSerializer
    
    def get_queryset(self):
        status_filter = self.request.query_params.get('status', None)
        queryset = NEW_WholesaleRequest.objects.all().order_by('-created_at')
        
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        return queryset
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context


class AdminWholesaleRequestDetailView(generics.RetrieveUpdateAPIView):
    """
    Get or update wholesale request (Admin only)
    GET /api/wholesale/admin/requests/{id}/
    PATCH /api/wholesale/admin/requests/{id}/
    """
    permission_classes = [permissions.IsAdminUser]
    serializer_class = WholesaleRequestSerializer
    queryset = NEW_WholesaleRequest.objects.all()
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context
    
    def update(self, request, *args, **kwargs):
        """Update request status and create/update wholesale user if approved"""
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        
        old_status = instance.status
        new_status = serializer.validated_data.get('status', old_status)
        
        # If status changed to approved, create/update wholesale user
        if old_status != 'approved' and new_status == 'approved':
            wholesale_user, created = NEW_WholesaleUser.objects.get_or_create(
                user=instance.user,
                defaults={
                    'is_wholesale': True,
                    'approved_by': request.user,
                    'approved_at': timezone.now()
                }
            )
            
            if not created:
                wholesale_user.is_wholesale = True
                wholesale_user.approved_by = request.user
                wholesale_user.approved_at = timezone.now()
                wholesale_user.save()
        
        # If status changed from approved to rejected, remove wholesale access
        elif old_status == 'approved' and new_status == 'rejected':
            try:
                wholesale_user = instance.user.wholesale_profile
                wholesale_user.is_wholesale = False
                wholesale_user.save()
            except NEW_WholesaleUser.DoesNotExist:
                pass
        
        # Update reviewed_by and reviewed_at
        if 'status' in serializer.validated_data:
            serializer.validated_data['reviewed_by'] = request.user
            serializer.validated_data['reviewed_at'] = timezone.now()
        
        self.perform_update(serializer)
        
        return Response(serializer.data)

