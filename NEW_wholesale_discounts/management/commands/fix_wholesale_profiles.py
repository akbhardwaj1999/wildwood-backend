from django.core.management.base import BaseCommand
from django.utils import timezone
from NEW_wholesale_discounts.models import NEW_WholesaleRequest, NEW_WholesaleUser, NEW_WholesaleTier
from django.contrib.auth.models import User

class Command(BaseCommand):
    help = 'Fix wholesale profiles for approved requests that are missing profiles'

    def handle(self, *args, **options):
        # Find approved requests without wholesale profiles
        approved_requests = NEW_WholesaleRequest.objects.filter(
            status='approved'
        ).select_related('user')
        
        fixed_count = 0
        
        for request in approved_requests:
            try:
                # Check if wholesale profile exists
                wholesale_user = request.user.wholesale_profile
                self.stdout.write(
                    self.style.WARNING(f'Profile already exists for {request.user.username}')
                )
            except NEW_WholesaleUser.DoesNotExist:
                # Create missing profile
                wholesale_user = NEW_WholesaleUser.objects.create(
                    user=request.user,
                    is_wholesale=True,
                    approved_by=request.reviewed_by,
                    approved_at=request.reviewed_at or timezone.now()
                )
                
                # Assign default tier
                default_tier = NEW_WholesaleTier.objects.filter(
                    is_active=True
                ).order_by('min_order_amount').first()
                
                if default_tier:
                    wholesale_user.wholesale_tier = default_tier
                    wholesale_user.save()
                
                fixed_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Created wholesale profile for {request.user.username}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(f'Fixed {fixed_count} wholesale profiles')
        )
