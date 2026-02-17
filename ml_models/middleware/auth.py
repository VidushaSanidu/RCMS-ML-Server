import os
import jwt
import json
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin
from functools import wraps
import logging

logger = logging.getLogger(__name__)


class JWTAuthenticationMiddleware(MiddlewareMixin):
    """
    Middleware to authenticate JWT tokens from Express.js backend
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        super().__init__(get_response)
    
    def process_request(self, request):
        # Skip authentication for health checks and public endpoints
        public_paths = [
            '/health/',
            '/admin/',
            '/api/ml/health/',
            '/api/ml/models/',
        ]
        
        # Check if the path is public
        if any(request.path.startswith(path) for path in public_paths):
            return None
        
        # Extract JWT token from Authorization header
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        if not auth_header.startswith('Bearer '):
            return JsonResponse({
                'error': 'Authentication required',
                'message': 'Please provide a valid JWT token in Authorization header'
            }, status=401)
        
        token = auth_header.split(' ')[1]
        
        try:
            # Verify JWT token using the same secret as Express.js backend
            jwt_secret = os.getenv('JWT_SECRET')
            if not jwt_secret:
                logger.error("JWT_SECRET not found in environment variables")
                return JsonResponse({
                    'error': 'Server configuration error',
                    'message': 'JWT secret not configured'
                }, status=500)
            
            # Decode the token
            decoded_token = jwt.decode(token, jwt_secret, algorithms=['HS256'])
            
            # Add user information to request
            request.user_id = decoded_token.get('id')
            request.jwt_payload = decoded_token
            
            logger.info(f"Authenticated user ID: {request.user_id}")
            
        except jwt.ExpiredSignatureError:
            return JsonResponse({
                'error': 'Token expired',
                'message': 'Your session has expired. Please login again.'
            }, status=401)
        
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid JWT token: {str(e)}")
            return JsonResponse({
                'error': 'Invalid token',
                'message': 'Please provide a valid authentication token'
            }, status=401)
        
        except Exception as e:
            logger.error(f"JWT authentication error: {str(e)}")
            return JsonResponse({
                'error': 'Authentication failed',
                'message': 'An error occurred during authentication'
            }, status=500)
        
        return None


def require_auth(view_func):
    """
    Decorator to require authentication for specific views
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not hasattr(request, 'user_id') or not request.user_id:
            return JsonResponse({
                'error': 'Authentication required',
                'message': 'This endpoint requires authentication'
            }, status=401)
        
        return view_func(request, *args, **kwargs)
    
    return wrapper


def require_role(allowed_roles):
    """
    Decorator to require specific roles for views
    Note: This requires extending the JWT payload to include role information
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not hasattr(request, 'jwt_payload') or not request.jwt_payload:
                return JsonResponse({
                    'error': 'Authentication required',
                    'message': 'This endpoint requires authentication'
                }, status=401)
            
            user_role = request.jwt_payload.get('role', '').upper()
            allowed_roles_upper = [role.upper() for role in allowed_roles]
            
            if user_role not in allowed_roles_upper:
                return JsonResponse({
                    'error': 'Insufficient permissions',
                    'message': f'This endpoint requires one of the following roles: {", ".join(allowed_roles)}'
                }, status=403)
            
            return view_func(request, *args, **kwargs)
        
        return wrapper
    return decorator
