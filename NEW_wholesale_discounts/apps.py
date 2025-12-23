from django.apps import AppConfig


class NewWholesaleDiscountsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'NEW_wholesale_discounts'
    
    def ready(self):
        import NEW_wholesale_discounts.signals