from django.apps import AppConfig


class CartConfig(AppConfig):
    name = 'cart'
    
    def ready(self):
        """
        Start the APScheduler when Django is ready
        This will run the abandoned cart email checker every 2 minutes (testing mode)
        Works for both development (runserver) and production (WSGI/PythonAnywhere)
        """
        import os
        import sys
        
        # Skip during migrations, shell, test commands, etc.
        if any(command in sys.argv for command in ['migrate', 'makemigrations', 'shell', 'test', 'collectstatic']):
            return
        
        # For development (runserver): Only start in reloader process
        if 'runserver' in sys.argv:
            if os.environ.get('RUN_MAIN') != 'true':
                return
        
        # For production (WSGI/PythonAnywhere): Start scheduler
        # Use a flag to prevent multiple starts
        if not hasattr(self, '_scheduler_started'):
            from .scheduler import start_scheduler
            try:
                start_scheduler()
                self._scheduler_started = True
            except Exception as e:
                import traceback
                traceback.print_exc()