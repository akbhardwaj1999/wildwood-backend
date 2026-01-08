# Generated migration for adding created_for_user field to Coupon model

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('cart', '0003_alter_address_address_type'),
    ]

    operations = [
        migrations.AddField(
            model_name='coupon',
            name='created_for_user',
            field=models.ForeignKey(
                blank=True,
                help_text='If set, only this user can use this coupon',
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='coupons',
                to=settings.AUTH_USER_MODEL
            ),
        ),
    ]

