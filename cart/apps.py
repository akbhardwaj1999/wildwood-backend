from django.apps import AppConfig


class CartConfig(AppConfig):
    name = 'cart'
    
    def ready(self):
        """
        Start the APScheduler when Django is ready
        This will run the abandoned cart email checker every 2 minutes (testing mode)
        """
        import os
        import sys
        
        # Only start scheduler once when server starts
        # Skip during migrations, shell, etc.
        if 'runserver' not in sys.argv:
            return
        
        # For Windows: RUN_MAIN is set after first reload
        # Start scheduler only in the reloader process (not the initial process)
        if os.environ.get('RUN_MAIN') == 'true':
            from .scheduler import start_scheduler
            try:
                start_scheduler()
            except Exception as e:
                import traceback
                traceback.print_exc()