from django.contrib import admin
from django.db.models import Count

from cart.models import ShippingCost, Order, OrderItem, Payment, Address, Coupon


@admin.register(ShippingCost)
class ShippingCostAdmin(admin.ModelAdmin):
    list_display = [
        '__str__',
        'shipment_type',
        'parameter',
        'value_start',
        'value_end',
        'charges',
    ]
    list_filter = ['shipment_type', 'parameter']
    search_fields = ['shipment_type', 'parameter', 'charges']
    ordering = ['shipment_type']


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 1


class PaymentInline(admin.TabularInline):
    model = Payment
    extra = 1


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = [
        'reference_number',
        'user',
        'start_date',
        'ordered_date',
        'ordered',
        'status',
        'total_shipping_cost',
    ]
    list_filter = ['status', 'ordered']
    search_fields = ['reference_number', 'user', 'start_date', 'ordered_date', 'status']
    inlines = [
        OrderItemInline,
        PaymentInline
    ]

    def get_queryset(self, request):
        qs = super(OrderAdmin, self).get_queryset(request)
        return qs.annotate(null_position=Count('ordered_date')).order_by('-null_position', '-ordered_date')


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = [
        '__str__',
        'order',
        'variant',
        'quantity',
        'get_total_item_price',
    ]
    search_fields = ['order__reference_number', 'variant']
    ordering = ['-order__start_date']


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = [
        'email_address',
        'phone_number',
        'user',
        'first_name',
        'last_name',
        'address_line_1',
        'address_line_2',
        'country',
        'state',
        'city',
        'zip_code',
        'default',
    ]
    list_filter = [
        'default',
    ]
    search_fields = [
        'user__username',
        'first_name',
        'last_name',
        'email_address',
        'phone_number',
        'address_line_1',
        'address_line_2',
        'country',
        'state',
        'city',
        'zip_code',
    ]


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = [
        'reference_number',
        'order',
        'payment_method',
        'timestamp',
        'successful',
        'amount',
    ]
    list_filter = ['successful', 'payment_method']
    search_fields = ['order', 'timestamp', 'amount']


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = [
        'title',
        'description',
        'code',
        'discount',
        'discount_type',
        'minimum_order_amount',
        'single_use_per_user',
        'created_for_user',
        'active',
    ]
    list_filter = ['discount_type', 'active', 'single_use_per_user', 'created_for_user']
    search_fields = ['title', 'code', 'description']
