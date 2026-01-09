from django.apps import AppConfig


class CartConfig(AppConfig):
    name = 'cart'
    
    def ready(self):
        """
        Start the APScheduler when Django is ready (ONLY for development)
        For production (PythonAnywhere), use scheduled task instead:
        - Go to PythonAnywhere → Tasks tab
        - Add: python /home/username/wildwood-backend/manage.py send_abandoned_cart_emails
        - Set to run every 2 minutes (or desired interval)
        """
        import os
        import sys
        
        # Skip during migrations, shell, test commands, etc.
        if any(command in sys.argv for command in ['migrate', 'makemigrations', 'shell', 'test', 'collectstatic']):
            return
        
        # ONLY start scheduler in development (runserver mode)
        # For production (WSGI/PythonAnywhere), use scheduled task instead
        if 'runserver' in sys.argv:
            # For Windows: RUN_MAIN is set after first reload
            # Start scheduler only in the reloader process (not the initial process)
            if os.environ.get('RUN_MAIN') == 'true':
                from .scheduler import start_scheduler
                try:
                    start_scheduler()
                    self._scheduler_started = True
                except Exception as e:
                    import traceback
                    traceback.print_exc()