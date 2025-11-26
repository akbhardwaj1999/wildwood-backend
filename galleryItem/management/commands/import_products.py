"""
Django management command to import products from JSON file
Usage: python manage.py import_products simple_matched_data.json
"""
import json
import os
from django.core.management.base import BaseCommand, CommandError
from galleryItem.utils import import_products_from_json_data


class Command(BaseCommand):
    help = 'Import products from JSON file into the database'

    def add_arguments(self, parser):
        parser.add_argument(
            'json_file',
            type=str,
            help='Path to the JSON file containing product data'
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=None,
            help='Limit the number of products to import (for testing)'
        )
        parser.add_argument(
            '--skip-existing',
            action='store_true',
            help='Skip products that already exist (by title)'
        )

    def handle(self, *args, **options):
        json_file_path = options['json_file']
        limit = options.get('limit')
        skip_existing = options.get('skip_existing', False)

        # Check if file exists
        if not os.path.exists(json_file_path):
            raise CommandError(f'File "{json_file_path}" does not exist.')

        # Read JSON file
        self.stdout.write(f'Reading JSON file: {json_file_path}')
        try:
            with open(json_file_path, 'r', encoding='utf-8') as f:
                json_data = json.load(f)
        except json.JSONDecodeError as e:
            raise CommandError(f'Invalid JSON file: {e}')
        except Exception as e:
            raise CommandError(f'Error reading file: {e}')

        # Validate JSON structure
        if not isinstance(json_data, list):
            raise CommandError('JSON file must contain an array of products.')

        # Limit products if specified
        if limit:
            json_data = json_data[:limit]
            self.stdout.write(self.style.WARNING(f'Limiting import to {limit} products'))

        total_products = len(json_data)
        self.stdout.write(f'Found {total_products} products in JSON file')

        # Import products
        self.stdout.write('Starting import...')
        stats = import_products_from_json_data(json_data)

        # Display results
        self.stdout.write('\n' + '='*50)
        self.stdout.write(self.style.SUCCESS('Import completed!'))
        self.stdout.write('='*50)
        self.stdout.write(f'Products created: {stats["created"]}')
        self.stdout.write(f'Products skipped: {stats["skipped"]}')
        self.stdout.write(f'Images downloaded: {stats["images"]}')
        self.stdout.write(f'Reviews imported: {stats["reviews"]}')
        self.stdout.write(f'Errors: {stats["errors"]}')
        self.stdout.write('='*50)

        if stats['errors'] > 0:
            self.stdout.write(self.style.WARNING(
                f'Warning: {stats["errors"]} products had errors during import. '
                'Check the console output above for details.'
            ))

