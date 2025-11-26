"""
Django management command to create demo users for testing
Usage: python manage.py create_demo_users
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()


class Command(BaseCommand):
    help = 'Create 3 demo users for login/signup testing'

    def handle(self, *args, **options):
        demo_users = [
            {
                'username': 'demo_user1',
                'email': 'demo1@example.com',
                'first_name': 'Demo',
                'last_name': 'User 1',
                'password': 'DemoPass123!'
            },
            {
                'username': 'demo_user2',
                'email': 'demo2@example.com',
                'first_name': 'Demo',
                'last_name': 'User 2',
                'password': 'DemoPass123!'
            },
            {
                'username': 'demo_user3',
                'email': 'demo3@example.com',
                'first_name': 'Demo',
                'last_name': 'User 3',
                'password': 'DemoPass123!'
            }
        ]

        created_count = 0
        skipped_count = 0

        for user_data in demo_users:
            username = user_data['username']
            
            # Check if user already exists
            if User.objects.filter(username=username).exists():
                self.stdout.write(self.style.WARNING(f'User "{username}" already exists. Skipping...'))
                skipped_count += 1
                continue

            # Create user
            user = User.objects.create_user(
                username=user_data['username'],
                email=user_data['email'],
                first_name=user_data['first_name'],
                last_name=user_data['last_name'],
                password=user_data['password']
            )

            self.stdout.write(self.style.SUCCESS(
                f'✓ Created user: {user.username} ({user.email})'
            ))
            created_count += 1

        self.stdout.write('\n' + '='*50)
        self.stdout.write(self.style.SUCCESS('Demo users creation completed!'))
        self.stdout.write('='*50)
        self.stdout.write(f'Users created: {created_count}')
        self.stdout.write(f'Users skipped: {skipped_count}')
        self.stdout.write('='*50)
        self.stdout.write('\nLogin credentials for all users:')
        self.stdout.write('Username: demo_user1, demo_user2, demo_user3')
        self.stdout.write('Password: DemoPass123!')
        self.stdout.write('='*50)

