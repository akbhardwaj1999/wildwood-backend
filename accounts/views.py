from rest_framework import status, generics, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import send_mail
from django.conf import settings
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from .serializers import (
    UserRegistrationSerializer,
    UserSerializer,
    UserUpdateSerializer,
    UserListSerializer,
    PasswordResetRequestSerializer,
    PasswordResetSerializer
)

User = get_user_model()


class UserRegistrationView(generics.CreateAPIView):
    """
    Register a new user account.
    
    Creates a new user with the provided information and returns JWT tokens for authentication.
    """
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [permissions.AllowAny]

    @swagger_auto_schema(
        operation_description="Register a new user account. Returns user data and JWT access token (valid for 30 days).",
        request_body=UserRegistrationSerializer,
        responses={
            201: openapi.Response(
                description="User registered successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(type=openapi.TYPE_STRING),
                        'user': openapi.Schema(type=openapi.TYPE_OBJECT),
                        'access_token': openapi.Schema(type=openapi.TYPE_STRING, description='JWT Access Token (valid for 30 days)'),
                    }
                )
            ),
            400: 'Bad Request - Invalid data provided'
        },
        tags=['Authentication']
    )
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        
        # Send welcome email
        try:
            # Clean and validate FROM email address
            from_email = settings.DEFAULT_FROM_EMAIL
            if ',' in from_email:
                from_email = from_email.split(',')[0].strip()
            from_email = from_email.strip()
            
            if from_email and '@' in from_email:
                subject = 'Welcome to Wild Wud!'
                message = f"""
Hello {user.first_name or user.username},

Welcome to Wild Wud! We're excited to have you join our community of unique woodcraft enthusiasts.

Your account has been successfully created:
- Username: {user.username}
- Email: {user.email}

As a thank you for registering, you'll receive 10% off on your first purchase!

Start exploring our unique handcrafted wooden products and discover something special for your home.

Best regards,
Wild Wud Team
"""
                send_mail(
                    subject,
                    message,
                    from_email,
                    [user.email],
                    fail_silently=True,  # Don't fail registration if email fails
                )
        except Exception as e:
            # Log error but don't fail registration
            print(f"Error sending welcome email: {e}")
        
        return Response({
            'message': 'User registered successfully. Welcome email has been sent.',
            'user': UserSerializer(user).data,
            'access_token': str(refresh.access_token),  # Only access token (valid for 30 days)
        }, status=status.HTTP_201_CREATED)


@swagger_auto_schema(
    method='post',
    operation_description="Authenticate user and get JWT access token (valid for 30 days) for API access.",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        required=['username', 'password'],
        properties={
            'username': openapi.Schema(type=openapi.TYPE_STRING, description='Username'),
            'password': openapi.Schema(type=openapi.TYPE_STRING, description='Password', format='password'),
        }
    ),
    responses={
        200: openapi.Response(
            description="Login successful",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'message': openapi.Schema(type=openapi.TYPE_STRING),
                    'user': openapi.Schema(type=openapi.TYPE_OBJECT),
                    'access_token': openapi.Schema(type=openapi.TYPE_STRING, description='JWT Access Token (valid for 30 days)'),
                }
            )
        ),
        400: 'Bad Request - Missing credentials',
        401: 'Unauthorized - Invalid credentials or inactive account'
    },
    tags=['Authentication']
)
@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def login_view(request):
    """
    Authenticate user and get JWT access token.
    
    Returns user data and JWT access token (valid for 30 days) upon successful authentication.
    """
    username = request.data.get('username')
    password = request.data.get('password')

    if not username or not password:
        return Response(
            {'error': 'Username and password are required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    user = authenticate(username=username, password=password)

    if user is None:
        return Response(
            {'error': 'Invalid credentials'},
            status=status.HTTP_401_UNAUTHORIZED
        )

    if not user.is_active:
        return Response(
            {'error': 'User account is disabled'},
            status=status.HTTP_401_UNAUTHORIZED
        )

    # Generate JWT tokens
    refresh = RefreshToken.for_user(user)

    return Response({
        'message': 'Login successful',
        'user': UserSerializer(user).data,
        'access_token': str(refresh.access_token),  # Only access token (valid for 30 days)
    }, status=status.HTTP_200_OK)


@swagger_auto_schema(
    method='post',
    operation_description="Logout user. Access token will remain valid until it expires (30 days).",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={}
    ),
    responses={
        200: openapi.Response(
            description="Logout successful",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'message': openapi.Schema(type=openapi.TYPE_STRING),
                }
            )
        ),
        401: 'Unauthorized - Authentication required'
    },
    security=[{'Bearer': []}],
    tags=['Authentication']
)
@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def logout_view(request):
    """
    Logout user.
    
    Requires authentication. Note: Access token will remain valid until it expires (30 days).
    """
    return Response({'message': 'Logout successful'}, status=status.HTTP_200_OK)


class UserProfileView(generics.RetrieveAPIView):
    """
    Get current authenticated user's profile information.

    Returns the profile details of the currently authenticated user.
    Requires authentication.
    """
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Get current user's profile information.",
        responses={
            200: UserSerializer,
            401: 'Unauthorized - Authentication required'
        },
        security=[{'Bearer': []}],
        tags=['User Profile']
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_object(self):
        return self.request.user


class UserProfileUpdateView(generics.UpdateAPIView):
    """
    Update current authenticated user's profile.
    
    Allows updating user information including password change.
    Requires authentication.
    """
    serializer_class = UserUpdateSerializer
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Update current user's profile. Can update name, email, username, and password.",
        request_body=UserUpdateSerializer,
        responses={
            200: openapi.Response(
                description="Profile updated successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(type=openapi.TYPE_STRING),
                        'user': openapi.Schema(type=openapi.TYPE_OBJECT),
                    }
                )
            ),
            400: 'Bad Request - Invalid data provided',
            401: 'Unauthorized - Authentication required'
        },
        security=[{'Bearer': []}],
        tags=['User Profile']
    )
    def put(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Partially update current user's profile.",
        request_body=UserUpdateSerializer,
        responses={
            200: openapi.Response(
                description="Profile updated successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(type=openapi.TYPE_STRING),
                        'user': openapi.Schema(type=openapi.TYPE_OBJECT),
                    }
                )
            ),
            400: 'Bad Request - Invalid data provided',
            401: 'Unauthorized - Authentication required'
        },
        security=[{'Bearer': []}],
        tags=['User Profile']
    )
    def patch(self, request, *args, **kwargs):
        return self.partial_update(request, *args, **kwargs)

    def get_object(self):
        return self.request.user

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        return Response({
            'message': 'Profile updated successfully',
            'user': UserSerializer(instance).data
        }, status=status.HTTP_200_OK)


class UserListView(generics.ListAPIView):
    """
    List all users (Admin/Staff only).
    
    Returns a paginated list of all users. Only accessible by admin users.
    """
    queryset = User.objects.all().order_by('-date_joined')
    serializer_class = UserListSerializer
    permission_classes = [permissions.IsAdminUser]

    @swagger_auto_schema(
        operation_description="Get list of all users. Admin access required.",
        responses={
            200: UserListSerializer(many=True),
            401: 'Unauthorized - Authentication required',
            403: 'Forbidden - Admin access required'
        },
        security=[{'Bearer': []}],
        tags=['Admin']
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


@swagger_auto_schema(
    method='post',
    operation_description="Request password reset. Sends password reset email to the user.",
    request_body=PasswordResetRequestSerializer,
    responses={
        200: openapi.Response(
            description="Password reset email sent successfully",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'message': openapi.Schema(type=openapi.TYPE_STRING),
                }
            )
        ),
        400: 'Bad Request - Invalid email format'
    },
    tags=['Authentication']
)
@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def password_reset_request(request):
    """
    Request password reset.
    
    Sends a password reset email to the user if the email exists.
    For security, always returns success message even if email doesn't exist.
    """
    serializer = PasswordResetRequestSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    
    email = serializer.validated_data['email']
    User = get_user_model()
    
    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        # Don't reveal if email exists or not for security
        return Response({
            'message': 'If an account exists with this email, a password reset link has been sent.'
        }, status=status.HTTP_200_OK)
    
    # Generate password reset token
    token = default_token_generator.make_token(user)
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    
    # Create reset link
    # Frontend URL - adjust based on your frontend URL
    frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')
    reset_link = f"{frontend_url}/reset-password?token={token}&uid={uid}"
    
    # Send email
    subject = 'Password Reset Request - Wild Wud'
    message = f"""
Hello {user.first_name or user.username},

You requested to reset your password for your Wild Wud account.

Please click on the following link to reset your password:
{reset_link}

This link will expire in 24 hours.

If you did not request this password reset, please ignore this email.

Best regards,
Wild Wud Team
"""
    
    # Clean and validate FROM email address
    from_email = settings.DEFAULT_FROM_EMAIL
    # Remove any commas and extra spaces, take only first email if multiple
    if ',' in from_email:
        from_email = from_email.split(',')[0].strip()
    from_email = from_email.strip()
    
    # Validate email format
    if not from_email or '@' not in from_email:
        print(f"Invalid FROM email address: {from_email}")
        return Response({
            'error': 'Email configuration error. Please contact support.',
            'success': False
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    try:
        send_mail(
            subject,
            message,
            from_email,  # Use cleaned email
            [email],
            fail_silently=False,
        )
        # Email sent successfully
        return Response({
            'message': 'Password reset email has been sent successfully. Please check your inbox.',
            'success': True
        }, status=status.HTTP_200_OK)
    except Exception as e:
        # Log error for debugging
        import traceback
        print(f"Error sending password reset email: {e}")
        print(traceback.format_exc())
        
        # Return specific error message based on error type
        error_message = 'Failed to send email. Please check your email configuration or try again later.'
        
        # Check for common email errors
        error_str = str(e).lower()
        if 'authentication' in error_str or 'login' in error_str:
            error_message = 'Email authentication failed. Please check your email credentials.'
        elif 'connection' in error_str or 'timeout' in error_str:
            error_message = 'Unable to connect to email server. Please try again later.'
        elif 'invalid' in error_str or 'format' in error_str:
            error_message = 'Invalid email address. Please check and try again.'
        
        return Response({
            'error': error_message,
            'success': False
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@swagger_auto_schema(
    method='post',
    operation_description="Verify password reset token validity.",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        required=['token', 'uid'],
        properties={
            'token': openapi.Schema(type=openapi.TYPE_STRING, description='Password reset token'),
            'uid': openapi.Schema(type=openapi.TYPE_STRING, description='User ID encoded in base64'),
        }
    ),
    responses={
        200: openapi.Response(
            description="Token is valid",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'valid': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                    'message': openapi.Schema(type=openapi.TYPE_STRING),
                }
            )
        ),
        400: 'Bad Request - Invalid token or uid'
    },
    tags=['Authentication']
)
@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def password_reset_verify(request):
    """
    Verify password reset token.
    
    Checks if the provided token and uid are valid for password reset.
    """
    token = request.data.get('token')
    uid = request.data.get('uid')
    
    if not token or not uid:
        return Response({
            'valid': False,
            'message': 'Token and uid are required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        # Decode user ID
        user_id = force_str(urlsafe_base64_decode(uid))
        User = get_user_model()
        user = User.objects.get(pk=user_id)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        return Response({
            'valid': False,
            'message': 'Invalid reset link'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Check if token is valid
    if not default_token_generator.check_token(user, token):
        return Response({
            'valid': False,
            'message': 'Invalid or expired reset link'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    return Response({
        'valid': True,
        'message': 'Token is valid'
    }, status=status.HTTP_200_OK)


@swagger_auto_schema(
    method='post',
    operation_description="Reset password using token and uid.",
    request_body=PasswordResetSerializer,
    responses={
        200: openapi.Response(
            description="Password reset successful",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'message': openapi.Schema(type=openapi.TYPE_STRING),
                }
            )
        ),
        400: 'Bad Request - Invalid token, uid, or password'
    },
    tags=['Authentication']
)
@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def password_reset_confirm(request):
    """
    Reset password with token.
    
    Resets the user's password using the provided token and uid.
    """
    serializer = PasswordResetSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    
    token = serializer.validated_data['token']
    new_password = serializer.validated_data['new_password']
    uid = request.data.get('uid')  # Get uid from request data
    
    if not uid:
        return Response({
            'error': 'User ID (uid) is required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        # Decode user ID
        user_id = force_str(urlsafe_base64_decode(uid))
        User = get_user_model()
        user = User.objects.get(pk=user_id)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        return Response({
            'error': 'Invalid reset link'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Check if token is valid
    if not default_token_generator.check_token(user, token):
        return Response({
            'error': 'Invalid or expired reset link'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Reset password
    user.set_password(new_password)
    user.save()
    
    return Response({
        'message': 'Password has been reset successfully. You can now login with your new password.'
    }, status=status.HTTP_200_OK)


