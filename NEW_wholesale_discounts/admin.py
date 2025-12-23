from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from .models import NEW_WholesaleDiscountConfig, NEW_WholesaleUser, NEW_WholesaleDiscount, NEW_WholesaleRequest

@admin.register(NEW_WholesaleDiscountConfig)
class NEW_WholesaleDiscountConfigAdmin(admin.ModelAdmin):
    """NEW: Admin interface for wholesale discount configuration"""
    list_display = [
        'name', 'threshold_1', 'discount_1', 'threshold_2', 'discount_2',
        'threshold_3', 'discount_3', 'threshold_4', 'discount_4', 'is_active'
    ]
    list_filter = ['is_active', 'created_at']
    search_fields = ['name']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Configuration Info', {
            'fields': ('name', 'is_active')
        }),
        ('Discount Tier 1', {
            'fields': ('threshold_1', 'discount_1'),
            'description': 'First discount tier (e.g., Above $500 → 10% off)'
        }),
        ('Discount Tier 2', {
            'fields': ('threshold_2', 'discount_2'),
            'description': 'Second discount tier (e.g., Above $1000 → 15% off)'
        }),
        ('Discount Tier 3', {
            'fields': ('threshold_3', 'discount_3'),
            'description': 'Third discount tier (e.g., Above $2000 → 20% off)'
        }),
        ('Discount Tier 4', {
            'fields': ('threshold_4', 'discount_4'),
            'description': 'Fourth discount tier (e.g., Above $2500 → 25% off)'
        }),
    )
    
    actions = ['activate_config', 'deactivate_config']
    
    def activate_config(self, request, queryset):
        """Activate selected configurations"""
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} configurations activated.')
    activate_config.short_description = 'Activate selected configurations'
    
    def deactivate_config(self, request, queryset):
        """Deactivate selected configurations"""
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} configurations deactivated.')
    deactivate_config.short_description = 'Deactivate selected configurations'

@admin.register(NEW_WholesaleUser)
class NEW_WholesaleUserAdmin(admin.ModelAdmin):
    """NEW: Admin interface for wholesale users"""
    list_display = [
        'user', 'is_wholesale', 'approved_by', 'approved_at', 'created_at'
    ]
    list_filter = ['is_wholesale', 'approved_at', 'created_at']
    search_fields = ['user__username', 'user__email', 'notes']
    ordering = ['-created_at']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('User Information', {
            'fields': ('user',)
        }),
        ('Wholesale Status', {
            'fields': ('is_wholesale',)
        }),
        ('Approval Information', {
            'fields': ('approved_by', 'approved_at'),
            'classes': ('collapse',)
        }),
        ('Notes', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['approve_wholesale', 'revoke_wholesale']
    
    def approve_wholesale(self, request, queryset):
        """Approve wholesale status"""
        updated = queryset.update(
            is_wholesale=True,
            approved_by=request.user,
            approved_at=timezone.now()
        )
        self.message_user(request, f'{updated} users approved for wholesale.')
    approve_wholesale.short_description = 'Approve wholesale status'
    
    def revoke_wholesale(self, request, queryset):
        """Revoke wholesale status"""
        updated = queryset.update(
            is_wholesale=False,
            approved_by=request.user,
            approved_at=timezone.now()
        )
        self.message_user(request, f'{updated} users revoked from wholesale.')
    revoke_wholesale.short_description = 'Revoke wholesale status'

@admin.register(NEW_WholesaleDiscount)
class NEW_WholesaleDiscountAdmin(admin.ModelAdmin):
    """NEW: Admin interface for wholesale discounts"""
    list_display = [
        'order_link', 'wholesale_user', 'discount_type', 'discount_value',
        'discount_amount', 'order_amount', 'applied_at'
    ]
    list_filter = ['discount_type', 'applied_at']
    search_fields = ['order__id', 'wholesale_user__user__username']
    ordering = ['-applied_at']
    date_hierarchy = 'applied_at'
    readonly_fields = ['applied_at']
    
    fieldsets = (
        ('Order Information', {
            'fields': ('order',)
        }),
        ('Wholesale Information', {
            'fields': ('wholesale_user',)
        }),
        ('Discount Details', {
            'fields': ('discount_type', 'discount_value', 'discount_amount', 'order_amount')
        }),
        ('Application Info', {
            'fields': ('applied_at',),
            'classes': ('collapse',)
        }),
    )
    
    def order_link(self, obj):
        """Link to order admin"""
        url = reverse('admin:cart_order_change', args=[obj.order.id])
        return format_html('<a href="{}">Order #{}</a>', url, obj.order.id)
    order_link.short_description = 'Order'
    order_link.admin_order_field = 'order__id'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('order', 'wholesale_user')

@admin.register(NEW_WholesaleRequest)
class NEW_WholesaleRequestAdmin(admin.ModelAdmin):
    """NEW: Admin interface for wholesale requests"""
    list_display = [
        'id', 'user_link', 'business_name', 'business_type_display', 
        'status_badge', 'created_at', 'reviewed_by', 'action_buttons'
    ]
    list_filter = ['status', 'business_type', 'created_at', 'reviewed_at']
    search_fields = ['user__username', 'user__email', 'business_name', 'tax_id']
    ordering = ['-created_at']
    date_hierarchy = 'created_at'
    readonly_fields = ['created_at', 'updated_at', 'user', 'documents_link']
    list_per_page = 25
    
    def get_queryset(self, request):
        """Optimize queryset with select_related"""
        return super().get_queryset(request).select_related('user', 'reviewed_by')
    
    fieldsets = (
        ('User Information', {
            'fields': ('user', 'created_at', 'updated_at')
        }),
        ('Business Information', {
            'fields': ('business_name', 'business_type', 'tax_id', 'website')
        }),
        ('Request Details', {
            'fields': ('expected_monthly_volume', 'reason', 'documents_link')
        }),
        ('Review Information', {
            'fields': ('status', 'reviewed_by', 'reviewed_at', 'admin_notes'),
        }),
    )
    
    def user_link(self, obj):
        """Link to user admin"""
        if obj.user:
            url = reverse('admin:auth_user_change', args=[obj.user.id])
            return format_html('<a href="{}">{}</a>', url, obj.user.username)
        return '-'
    user_link.short_description = 'User'
    user_link.admin_order_field = 'user__username'
    
    def business_type_display(self, obj):
        """Display business type"""
        return obj.get_business_type_display()
    business_type_display.short_description = 'Business Type'
    business_type_display.admin_order_field = 'business_type'
    
    def status_badge(self, obj):
        """Display status with color coding"""
        colors = {
            'pending': 'orange',
            'approved': 'green',
            'rejected': 'red'
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    status_badge.admin_order_field = 'status'
    
    def documents_link(self, obj):
        """Link to download documents"""
        if obj.documents:
            return format_html(
                '<a href="{}" target="_blank" style="color: blue; text-decoration: underline;">📄 View Document</a>',
                obj.documents.url
            )
        return 'No documents uploaded'
    documents_link.short_description = 'Supporting Documents'
    
    def action_buttons(self, obj):
        """Quick action buttons"""
        if obj.status == 'pending':
            change_url = reverse('admin:NEW_wholesale_discounts_new_wholesalerequest_change', args=[obj.id])
            return format_html(
                '<a href="{}" style="background-color: green; color: white; padding: 4px 8px; border-radius: 3px; text-decoration: none; margin-right: 5px;">✓ Review</a>',
                change_url
            )
        elif obj.status == 'approved':
            return format_html('<span style="color: green;">✓ Approved</span>')
        elif obj.status == 'rejected':
            return format_html('<span style="color: red;">✗ Rejected</span>')
        return '-'
    action_buttons.short_description = 'Actions'
    
    actions = ['approve_requests', 'reject_requests']
    
    def approve_requests(self, request, queryset):
        """Approve selected requests"""
        updated = 0
        for req in queryset:
            req.status = 'approved'
            req.reviewed_by = request.user
            req.reviewed_at = timezone.now()
            req.save()
            
            # Create wholesale user profile
            wholesale_user, created = NEW_WholesaleUser.objects.get_or_create(
                user=req.user,
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
            
            updated += 1
        
        self.message_user(request, f'{updated} requests approved.')
    approve_requests.short_description = 'Approve selected requests'
    
    def reject_requests(self, request, queryset):
        """Reject selected requests"""
        updated = queryset.update(
            status='rejected',
            reviewed_by=request.user,
            reviewed_at=timezone.now()
        )
        self.message_user(request, f'{updated} requests rejected.')
    reject_requests.short_description = 'Reject selected requests'