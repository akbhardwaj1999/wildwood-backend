import datetime
import os
import time
import requests
from io import BytesIO
from django.core.files.base import ContentFile
from django.core.files import File
from decimal import Decimal
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .models import GalleryItem, Variant, VariantImage, Review, Category

# Check if running on PythonAnywhere (proxy issues)
IS_PYTHONANYWHERE = 'PYTHONANYWHERE_DOMAIN' in os.environ or 'akumar15.pythonanywhere.com' in os.environ.get('ALLOWED_HOSTS', '')

# Create a session with retry strategy
def create_session():
    """Create a requests session with retry strategy"""
    session = requests.Session()
    
    # Retry strategy
    retry_strategy = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"]
    )
    
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    
    # Set headers to mimic a browser
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
    })
    
    # Disable proxy for PythonAnywhere
    if IS_PYTHONANYWHERE:
        session.proxies = {'http': None, 'https': None}
    
    return session

# Global session
_global_session = None

def get_session():
    """Get or create global session"""
    global _global_session
    if _global_session is None:
        _global_session = create_session()
    return _global_session


def yesterday():
    return datetime.date.today() - datetime.timedelta(1)


def import_products_from_json_data(json_data):
    """
    Import products from JSON data (called from admin panel)
    Returns: dict with import statistics
    """
    stats = {
        'created': 0,
        'skipped': 0,
        'images': 0,
        'reviews': 0,
        'errors': 0
    }
    
    # Get or create default category
    default_category, _ = Category.objects.get_or_create(
        title='Imported Products',
        defaults={'description': 'Products imported from JSON'}
    )
    
    # If json_data is not a list, try to handle it
    if not isinstance(json_data, list):
        return stats
    
    for idx, product_data in enumerate(json_data):
        try:
            # Handle both lowercase and UPPERCASE field names
            title = (product_data.get('title') or product_data.get('TITLE') or '').strip()
            
            if not title:
                continue
            
            # Check if product already exists
            existing_product = GalleryItem.objects.filter(title__iexact=title).first()
            
            if existing_product:
                # Product exists - check if it needs reviews
                from django.utils import timezone
                from datetime import datetime
                
                reviews_data = product_data.get('reviews') or product_data.get('REVIEWS') or []
                if existing_product.reviews.count() == 0 and reviews_data:
                    # Import reviews for existing product
                    for review_data in reviews_data:
                        # Parse review date from JSON
                        date_reviewed_str = review_data.get('date_reviewed') or review_data.get('date', '')
                        
                        # Try multiple date formats
                        date_added = None
                        date_formats = [
                            '%d/%b/%Y',  # 01/Feb/2024
                            '%m/%d/%Y',  # 01/20/2025 (MM/DD/YYYY)
                            '%d/%m/%Y',  # 20/01/2025 (DD/MM/YYYY)
                        ]
                        
                        for fmt in date_formats:
                            try:
                                # Parse date and make it timezone-aware
                                parsed_date = datetime.strptime(date_reviewed_str, fmt)
                                date_added = timezone.make_aware(parsed_date, timezone.get_current_timezone())
                                break  # Success! Stop trying other formats
                            except (ValueError, AttributeError):
                                continue  # Try next format
                        
                        if date_added is None:
                            # All formats failed, use current date
                            date_added = timezone.now()
                        
                        Review.objects.create(
                            product=existing_product,
                            content=review_data.get('message') or review_data.get('review', ''),
                            rating=review_data.get('star_rating') or review_data.get('rating', 5),
                            import_author=review_data.get('reviewer') or review_data.get('author', 'Anonymous'),
                            is_imported=True,
                            date_added=date_added  # Use parsed date
                        )
                        stats['reviews'] += 1
                
                stats['skipped'] += 1
                continue
            
            # Get description
            description = product_data.get('description') or product_data.get('DESCRIPTION') or ''
            
            # Get tags for meta keywords (convert underscores to spaces, commas already there)
            tags = product_data.get('TAGS') or product_data.get('tags') or ''
            meta_keywords = tags.replace('_', ' ')  # dog_figure -> dog figure
            
            # Use TITLE for meta description (max 255 chars as per model field limit)
            meta_description = title[:255] if len(title) > 255 else title
            
            # Create new product
            product = GalleryItem.objects.create(
                title=title,
                description=description,
                category=default_category,
                active=True,
                metaKeyWords=meta_keywords,
                metaKeyDescription=meta_description
            )
            
            # Create variant (handle both formats)
            price = product_data.get('PRICE') or product_data.get('price', 0)
            quantity = product_data.get('QUANTITY') or product_data.get('quantity') or product_data.get('stock', 0)
            
            # Download first image before creating variant (required fields)
            images = product_data.get('IMAGES') or product_data.get('images', [])
            first_image_content = None
            first_image_filename = None
            
            if images:
                try:
                    # Download first image with retry logic
                    session = get_session()
                    max_retries = 3
                    retry_delay = 2
                    
                    for attempt in range(max_retries):
                        try:
                            response = session.get(images[0], timeout=30, stream=True)
                            if response.status_code == 200:
                                first_image_content = ContentFile(response.content)
                                first_image_filename = f"product_{product.id}_img_0.jpg"
                                stats['images'] += 1
                                break  # Success, exit retry loop
                            else:
                                if attempt < max_retries - 1:
                                    time.sleep(retry_delay * (attempt + 1))
                                    continue
                        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
                            if attempt < max_retries - 1:
                                time.sleep(retry_delay * (attempt + 1))
                                continue
                            else:
                                raise e
                except Exception as e:
                    pass
            
            # Create placeholder image if no images available
            if not first_image_content:
                try:
                    from PIL import Image
                    # Create a simple placeholder image (1x1 pixel)
                    placeholder = Image.new('RGB', (1, 1), color='white')
                    img_io = BytesIO()
                    placeholder.save(img_io, format='JPEG')
                    img_io.seek(0)
                    first_image_content = ContentFile(img_io.read(), name='placeholder.jpg')
                    first_image_filename = f"product_{product.id}_placeholder.jpg"
                except ImportError:
                    # If PIL not available, create a minimal JPEG placeholder manually
                    # Minimal valid JPEG (1x1 white pixel)
                    minimal_jpeg = b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00H\x00H\x00\x00\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t\x08\n\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a\x1f\x1e\x1d\x1a\x1c\x1c $.\' ",#\x1c\x1c(7),01444\x1f\'9=82<.342\xff\xc0\x00\x11\x08\x00\x01\x00\x01\x01\x01\x11\x00\x02\x11\x01\x03\x11\x01\xff\xc4\x00\x14\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x08\xff\xc4\x00\x14\x10\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xff\xda\x00\x0c\x03\x01\x00\x02\x11\x03\x11\x00\x3f\x00\xaa\xff\xd9'
                    first_image_content = ContentFile(minimal_jpeg, name='placeholder.jpg')
                    first_image_filename = f"product_{product.id}_placeholder.jpg"
            
            # Create variant with first image
            variant = Variant(
                product=product,
                title='',
                price=Decimal(str(price)),
                quantity=int(quantity),
                volume=1,  # Default volume
                weight=1   # Default weight
            )
            # Save images before saving variant
            variant.image.save(first_image_filename, first_image_content, save=False)
            variant.largeImage.save(first_image_filename, first_image_content, save=False)
            variant.save()
            
            # Set as default variant
            product.default_variant = variant
            product.save(update_fields=['default_variant'])
            
            # Download and save additional images (if any)
            for idx, image_url in enumerate(images[1:], start=1):  # Start from index 1
                try:
                    # Download image with retry logic
                    session = get_session()
                    max_retries = 3
                    retry_delay = 2
                    
                    for attempt in range(max_retries):
                        try:
                            response = session.get(image_url, timeout=30, stream=True)
                            if response.status_code == 200:
                                image_content = ContentFile(response.content)
                                filename = f"product_{product.id}_img_{idx}.jpg"
                                
                                # Additional images - save to VariantImage
                                variant_image = VariantImage(
                                    variant=variant,
                                    name=f"Image {idx}"
                                )
                                variant_image.image.save(filename, image_content, save=True)
                                
                                stats['images'] += 1
                                break  # Success, exit retry loop
                            else:
                                if attempt < max_retries - 1:
                                    time.sleep(retry_delay * (attempt + 1))
                                    continue
                        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
                            if attempt < max_retries - 1:
                                time.sleep(retry_delay * (attempt + 1))
                                continue
                            else:
                                raise e
                except Exception as e:
                    pass
            
            # Import reviews (handle both formats)
            from django.utils import timezone
            from datetime import datetime
            
            reviews_data = product_data.get('REVIEWS') or product_data.get('reviews', [])
            for review_data in reviews_data:
                # Parse review date from JSON - try multiple formats
                date_reviewed_str = review_data.get('date_reviewed') or review_data.get('date', '')
                
                # Try multiple date formats
                date_added = None
                date_formats = [
                    '%d/%b/%Y',  # 01/Feb/2024
                    '%m/%d/%Y',  # 01/20/2025 (MM/DD/YYYY)
                    '%d/%m/%Y',  # 20/01/2025 (DD/MM/YYYY)
                ]
                
                for fmt in date_formats:
                    try:
                        # Parse date and make it timezone-aware
                        parsed_date = datetime.strptime(date_reviewed_str, fmt)
                        date_added = timezone.make_aware(parsed_date, timezone.get_current_timezone())
                        break  # Success! Stop trying other formats
                    except (ValueError, AttributeError):
                        continue  # Try next format
                
                if date_added is None:
                    # All formats failed, use current date
                    date_added = timezone.now()
                
                Review.objects.create(
                    product=product,
                    content=review_data.get('message') or review_data.get('review', ''),
                    rating=review_data.get('star_rating') or review_data.get('rating', 5),
                    import_author=review_data.get('reviewer') or review_data.get('author', 'Anonymous'),
                    is_imported=True,
                    date_added=date_added  # Use parsed date from JSON
                )
                stats['reviews'] += 1
            
            stats['created'] += 1
            
        except Exception as e:
            stats['errors'] += 1
    
    return stats
