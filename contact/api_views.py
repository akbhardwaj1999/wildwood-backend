from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.core.mail import send_mail
from django.conf import settings
from .models import ContactMessage
from .serializers import ContactMessageSerializer


@api_view(['POST'])
@permission_classes([AllowAny])
def submit_contact_form(request):
    """
    Submit contact form and send email notification to admin
    """
    serializer = ContactMessageSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response({
            'error': 'Invalid form data',
            'details': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Save contact message to database
    contact_message = serializer.save()
    
    # Prepare email content
    subject = f'New Contact Form Message from {contact_message.name}'
    message = f"""
You have received a new message from the Wild Wud contact form:

Name: {contact_message.name}
Email: {contact_message.email}
Date: {contact_message.created_at.strftime("%Y-%m-%d %H:%M:%S")}

Message:
{contact_message.message}

---
This is an automated message from the Wild Wud website.
Please reply directly to {contact_message.email} to respond.
"""
    
    # Get admin email from settings or use default
    admin_email = getattr(settings, 'ADMIN_EMAIL', None)
    if not admin_email:
        # Try to get from DEFAULT_FROM_EMAIL or use a default
        admin_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'admin@wildwud.com')
    
    # Clean email address (remove commas if multiple)
    if ',' in admin_email:
        admin_email = admin_email.split(',')[0].strip()
    admin_email = admin_email.strip()
    
    # Clean FROM email
    from_email = settings.DEFAULT_FROM_EMAIL
    if ',' in from_email:
        from_email = from_email.split(',')[0].strip()
    from_email = from_email.strip()
    
    # Send email to admin
    email_sent = False
    email_error = None
    
    try:
        if admin_email and '@' in admin_email:
            send_mail(
                subject,
                message,
                from_email,
                [admin_email],
                fail_silently=False,
            )
            email_sent = True
    except Exception as e:
        email_error = str(e)
        print(f"Error sending contact form email: {e}")
    
    # Send confirmation email to user
    user_confirmation_sent = False
    try:
        user_subject = 'Thank you for contacting Wild Wud!'
        user_message = f"""
Hello {contact_message.name},

Thank you for reaching out to us! We have received your message and will get back to you as soon as possible.

Your Message:
{contact_message.message}

We typically respond within 24-48 hours.

Best regards,
Wild Wud Team
"""
        if contact_message.email and '@' in contact_message.email:
            send_mail(
                user_subject,
                user_message,
                from_email,
                [contact_message.email],
                fail_silently=True,  # Don't fail if user email fails
            )
            user_confirmation_sent = True
    except Exception as e:
        print(f"Error sending confirmation email to user: {e}")
    
    # Return response
    if email_sent:
        return Response({
            'message': 'Your message has been sent successfully! We will get back to you soon.',
            'success': True
        }, status=status.HTTP_201_CREATED)
    else:
        # Message saved but email failed
        return Response({
            'message': 'Your message has been received. However, there was an issue sending the notification email. We will still review your message.',
            'success': True,
            'warning': 'Email notification may not have been sent to admin.'
        }, status=status.HTTP_201_CREATED)

