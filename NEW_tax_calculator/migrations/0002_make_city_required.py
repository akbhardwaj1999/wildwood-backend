# Generated manually to make city field required

from django.db import migrations, models
import smart_selects.db_fields


def delete_tax_rates_without_city(apps, schema_editor):
    """Delete tax rates that don't have a city (city is now required)"""
    NEW_TaxRate = apps.get_model('NEW_tax_calculator', 'NEW_TaxRate')
    deleted_count = NEW_TaxRate.objects.filter(city__isnull=True).delete()[0]
    print(f'Deleted {deleted_count} tax rates without city (city is now required)')


def reverse_delete(apps, schema_editor):
    """Reverse migration - nothing to do"""
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('NEW_tax_calculator', '0001_initial'),
    ]

    operations = [
        # First, delete any tax rates without city
        migrations.RunPython(delete_tax_rates_without_city, reverse_delete),
        
        # Then make city field required
        migrations.AlterField(
            model_name='new_taxrate',
            name='city',
            field=smart_selects.db_fields.ChainedForeignKey(
                auto_choose=True,
                chained_field='state',
                chained_model_field='state',
                on_delete=models.CASCADE,
                related_name='tax_rates',
                to='NEW_tax_calculator.city',
                blank=False,
                null=False,
            ),
        ),
    ]

