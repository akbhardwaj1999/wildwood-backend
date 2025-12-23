from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from .models import NEW_WholesaleRequest, NEW_WholesaleUser

@receiver(post_save, sender=NEW_WholesaleRequest)
def create_wholesale_profile_on_approval(sender, instance, created, **kwargs):
    """
    Automatically create wholesale profile when request is approved
    This handles individual approval (not bulk action)
    """
    if not created and instance.status == 'approved':
        # Check if wholesale profile already exists
        try:
            wholesale_user = instance.user.wholesale_profile
            # Update existing profile
            wholesale_user.is_wholesale = True
            wholesale_user.approved_by = instance.reviewed_by
            wholesale_user.approved_at = instance.reviewed_at or timezone.now()
            wholesale_user.save()
        except NEW_WholesaleUser.DoesNotExist:
            # Create new profile
            wholesale_user = NEW_WholesaleUser.objects.create(
                user=instance.user,
                is_wholesale=True,
                approved_by=instance.reviewed_by,
                approved_at=instance.reviewed_at or timezone.now()
            )
