from rest_framework import status, generics, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.password_validation import validate_password
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from .serializers import (
    UserRegistrationSerializer,
    UserSerializer,
    UserUpdateSerializer,
    UserListSerializer
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
        
        return Response({
            'message': 'User registered successfully',
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

