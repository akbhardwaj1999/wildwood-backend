"""
Abandoned Cart Email Scheduler using APScheduler
Runs every hour to check for abandoned carts and send reminder emails
"""

import logging
import os
from datetime import timedelta
from django.utils import timezone
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from collections import defaultdict

logger = logging.getLogger(__name__)


def send_abandoned_cart_emails():
    """
    Check for abandoned carts and send reminder emails
    Runs every hour via APScheduler
    """
    from .models import Order
    
    logger.info("=" * 60)
    logger.info("🔍 Starting abandoned cart email check...")
    logger.info(f"Current time: {timezone.now()}")
    logger.info("=" * 60)
    
    # Define time thresholds for different reminder emails
    # TESTING MODE: Using minutes instead of hours for quick testing
    # First reminder: 2 minutes after cart creation (for testing)
    # Second reminder: 5 minutes after cart creation (for testing)
    # Third reminder: 10 minutes after cart creation (for testing)
    
    # PRODUCTION VALUES (change when going live):
    # 'hours_ago': 1, 24, 72 (1 hour, 24 hours, 72 hours)
    
    reminders = [
        {
            'hours_ago': 2/60,  # 2 minutes (for testing)
            'email_count': 0,  # First email
            'subject': '🛒 You left something in your cart!',
            'discount_code': None,
        },
        {
            'hours_ago': 5/60,  # 5 minutes (for testing)
            'email_count': 1,  # Second email
            'subject': '⏰ Don\'t miss out on your cart items!',
            'discount_code': None,
        },
        {
            'hours_ago': 10/60,  # 10 minutes (for testing)
            'email_count': 2,  # Third email
            'subject': '🎁 Last chance - Special discount inside!',
            'discount_code': 'COMEBACK10',  # 10% off
        },
    ]
    
    total_emails_sent = 0
    
    # Track which carts already got emails in this run (prevent multiple emails per cart per run)
    carts_emailed_this_run = set()
    
    # Process reminders in normal order (1st > 2nd > 3rd)
    # IMPORTANT: Each cart can only get ONE email per run
    # If a cart qualifies for multiple reminders, only the first one (in order) will be sent
    for reminder in reminders:
        # Calculate time threshold
        time_ago = timezone.now() - timedelta(hours=reminder['hours_ago'])
        
        # Find abandoned carts (orders that are not finalized/ordered)
        # Use start_date (cart creation time) for abandonment threshold
        # Use last_updated only for ordering (to get most recent cart)
        # IMPORTANT: Order by -last_updated to get the MOST RECENT cart first
        abandoned_orders = Order.objects.filter(
            user__isnull=False,                          # Registered users only
            ordered=False,                               # Not checked out yet
            start_date__lt=time_ago,                     # Cart created before threshold (not last_updated!)
            abandoned_email_count=reminder['email_count'], # Correct reminder sequence
            items__isnull=False                          # Has items in cart
        ).exclude(
            user__email=''                               # Has valid email
        ).exclude(
            user__email__isnull=True
        ).distinct().select_related('user').prefetch_related(
            'items__variant__product'
            # Note: 'items__variant__image' cannot be prefetched (ImageField doesn't support prefetch)
        ).order_by('-last_updated')  # Most recently updated cart first
        
        order_count = abandoned_orders.count()
        logger.info(f"📧 Found {order_count} abandoned carts for reminder #{reminder['email_count'] + 1} (created before {time_ago}, email_count={reminder['email_count']})")
        
        # Group orders by user and only send email for the MOST RECENT cart per user
        # This prevents sending emails for old abandoned carts when user has a new active cart
        processed_users = set()
        
        # Send email to each user (ONLY ONE EMAIL PER CART PER RUN)
        # Note: abandoned_orders is already ordered by -last_updated in the query above
        for order in abandoned_orders:
            # Skip if we already processed this user in THIS RUN
            if order.user.id in processed_users:
                logger.info(f"⏭️  Skipping older cart for {order.user.email} (already processed newer cart)")
                continue
            
            # IMPORTANT: Only send ONE email per cart per run
            # Skip if this cart already got an email in this run
            if order.id in carts_emailed_this_run:
                continue
            
            processed_users.add(order.user.id)
            try:
                # IMPORTANT: Refresh order from DB to get latest items
                # This ensures we have the most up-to-date cart data
                order.refresh_from_db()
                
                # IMPORTANT: Get fresh items from database to avoid stale data
                # Use select_related and prefetch_related for optimal performance
                fresh_items = order.items.select_related('variant__product', 'variant').all()
                
                # Build cart items data
                cart_items = []
                total_amount = 0
                
                for item in fresh_items:
                    item_total = item.get_raw_total_item_price()
                    
                    # Build full image URL for email
                    image_url = None
                    if item.variant.image:
                        # Use full URL with domain for email images
                        image_url = f"{settings.SITE_URL}{item.variant.image.url}"
                    
                    cart_items.append({
                        'product': item.variant.product,
                        'variant': item.variant,
                        'quantity': item.quantity,
                        'price': item.get_raw_item_price(),
                        'total': item_total,
                        'image_url': image_url,
                    })
                    total_amount += item_total
                
                # Prepare email context with cart recovery link
                # Use order reference number to restore cart session
                # Frontend URL format: /cart/recover/[reference_number]
                frontend_url = os.environ.get('FRONTEND_URL', 'http://localhost:3000')
                cart_recovery_url = f"{frontend_url}/cart/recover/{order.reference_number}"
                
                # Create coupon if discount_code is provided (for 3rd email)
                discount_code = reminder['discount_code']
                if discount_code:
                    from .models import Coupon
                    from decimal import Decimal
                    
                    # Get or create the abandoned cart coupon
                    coupon, created = Coupon.objects.get_or_create(
                        code=discount_code,
                        defaults={
                            'title': 'Abandoned Cart Recovery Discount',
                            'description': '10% off on your abandoned cart items!',
                            'discount': Decimal('10.00'),
                            'discount_type': Coupon.DiscountType.PERCENTAGE,
                            'minimum_order_amount': Decimal('0.00'),
                            'single_use_per_user': False,  # Can be used by multiple users
                            'active': True,
                        }
                    )
                    
                    # Ensure coupon is active
                    if not coupon.active:
                        coupon.active = True
                        coupon.save(update_fields=['active'])
                    
                    logger.info(f"🎟️  Coupon '{discount_code}' {'created' if created else 'found'} for abandoned cart email")
                
                context = {
                    'user': order.user,
                    'first_name': order.user.first_name or 'Customer',
                    'cart_items': cart_items,
                    'total_amount': total_amount,
                    'cart_count': len(cart_items),
                    'cart_url': cart_recovery_url,  # Use recovery link instead
                    'checkout_url': cart_recovery_url,  # Both go to recovery first
                    'discount_code': discount_code,
                    'reminder_number': reminder['email_count'] + 1,
                }
                
                # Render email templates
                html_content = render_to_string('email/abandoned_cart.html', context)
                text_content = render_to_string('email/abandoned_cart.txt', context)
                
                # Send email with mixed content (allows inline images)
                email = EmailMultiAlternatives(
                    subject=reminder['subject'],
                    body=text_content,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    to=[order.user.email],
                )
                email.attach_alternative(html_content, "text/html")
                email.mixed_subtype = 'related'  # Allow inline images
                
                # Attach product images inline (for better email client compatibility)
                try:
                    for idx, item in enumerate(fresh_items):
                        if item.variant.image:
                            # Read image file
                            image_path = item.variant.image.path
                            with open(image_path, 'rb') as img_file:
                                img_data = img_file.read()
                                # Get MIME subtype from file extension
                                file_ext = os.path.splitext(image_path)[1].lower()
                                subtype_map = {
                                    '.jpg': 'jpeg',
                                    '.jpeg': 'jpeg',
                                    '.png': 'png',
                                    '.gif': 'gif',
                                    '.webp': 'webp',
                                }
                                # MIMEImage expects subtype like 'jpeg', 'png', etc.
                                image_subtype = subtype_map.get(file_ext, 'jpeg')  # Default to JPEG
                                
                                # Attach as inline image with CID
                                from email.mime.image import MIMEImage
                                img = MIMEImage(img_data, _subtype=image_subtype)
                                img.add_header('Content-ID', f'<product_image_{idx}>')
                                img.add_header('Content-Disposition', 'inline')
                                email.attach(img)
                except Exception as img_error:
                    logger.warning(f"⚠️ Could not attach inline images: {img_error}")
                
                # Send email with retry logic (handle SMTP connection issues)
                max_retries = 3
                retry_delay = 2  # seconds
                email_sent = False
                
                for attempt in range(1, max_retries + 1):
                    try:
                        # Close any existing connection before retry
                        if attempt > 1:
                            from django.core.mail import get_connection
                            try:
                                connection = get_connection()
                                if hasattr(connection, 'close'):
                                    connection.close()
                            except:
                                pass
                            import time
                            time.sleep(retry_delay)
                        
                        email.send()
                        email_sent = True
                        break  # Success, exit retry loop
                        
                    except Exception as send_error:
                        error_msg = str(send_error)
                        if attempt < max_retries:
                            logger.warning(f"⚠️ Email send attempt {attempt} failed for {order.user.email}: {error_msg}. Retrying...")
                        else:
                            # All retries failed
                            logger.error(f"❌ Failed to send email to {order.user.email} after {max_retries} attempts: {error_msg}")
                            raise  # Re-raise to be caught by outer exception handler
                
                # Only update order if email was successfully sent
                if email_sent:
                    # Update order - mark email as sent
                    order.abandoned_email_count += 1
                    order.abandoned_email_sent = True
                    order.abandoned_email_sent_at = timezone.now()
                    order.save(update_fields=['abandoned_email_count', 'abandoned_email_sent', 'abandoned_email_sent_at'])
                    
                    # Mark this cart as emailed in this run (prevent multiple emails in same run)
                    carts_emailed_this_run.add(order.id)
                    
                    total_emails_sent += 1
                    logger.info(f"✅ Sent abandoned cart email #{order.abandoned_email_count} to {order.user.email}")
                
            except Exception as e:
                logger.error(f"❌ Error sending abandoned cart email to {order.user.email}: {e}")
                import traceback
                traceback.print_exc()
                continue
    
    logger.info("=" * 60)
    logger.info(f"✨ Abandoned cart email check complete. Sent {total_emails_sent} emails.")
    logger.info(f"End time: {timezone.now()}")
    logger.info("=" * 60)
    return total_emails_sent


def start_scheduler():
    """
    Initialize and start APScheduler for abandoned cart emails
    Called from cart/apps.py when Django starts
    
    NOTE: Using MemoryJobStore for development to avoid SQLite locking issues.
    For production with PostgreSQL, switch back to DjangoJobStore.
    """
    from apscheduler.schedulers.background import BackgroundScheduler
    from apscheduler.jobstores.memory import MemoryJobStore
    from apscheduler.executors.pool import ThreadPoolExecutor
    
    try:
        # Configure executors and job defaults
        executors = {
            'default': ThreadPoolExecutor(1)  # Single thread to avoid DB locks
        }
        job_defaults = {
            'coalesce': True,  # Combine missed runs
            'max_instances': 1,  # Only one instance at a time
            'misfire_grace_time': 60  # 1 minute grace period
        }
        
        # Use MemoryJobStore for development (no SQLite locking issues)
        # For production with PostgreSQL, use: from django_apscheduler.jobstores import DjangoJobStore
        jobstores = {
            'default': MemoryJobStore()
        }
        
        scheduler = BackgroundScheduler(
            jobstores=jobstores,
            executors=executors,
            job_defaults=job_defaults
        )
        
        # Schedule the abandoned cart email task
        # TESTING MODE: Running every 2 minutes for quick testing
        # PRODUCTION: Change to hours=1 when going live
        scheduler.add_job(
            send_abandoned_cart_emails,
            trigger='interval',
            minutes=2,  # Every 2 minutes (for testing)
            # hours=1,  # Uncomment for production
            id='send_abandoned_cart_emails',
            replace_existing=True,
            name='Send Abandoned Cart Emails'
        )
        
        scheduler.start()
        logger.info("🚀 Abandoned Cart Email Scheduler started! Running every 2 minutes (TESTING MODE)")
        
    except Exception as e:
        logger.error(f"❌ Failed to start scheduler: {e}")
        import traceback
        traceback.print_exc()


