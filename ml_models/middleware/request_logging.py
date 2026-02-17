import logging
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware(MiddlewareMixin):
    """
    Middleware to log request details for debugging JSON parse errors
    """
    
    def process_request(self, request):
        # Only log for ML prediction endpoints
        if '/api/ml/predict/' in request.path:
            logger.info(f"Request to {request.path}")
            logger.info(f"Method: {request.method}")
            logger.info(f"Content-Type: {request.content_type}")
            logger.info(f"Content-Length: {request.META.get('CONTENT_LENGTH', 'unknown')}")
            
            # Log raw body for debugging
            try:
                if hasattr(request, 'body'):
                    raw_body = request.body.decode('utf-8')
                    logger.info(f"Raw body length: {len(raw_body)}")
                    logger.info(f"Raw body: {raw_body}")
                    
                    # Show raw bytes around position 298 (where the error occurs)
                    if len(raw_body) > 290:
                        start_pos = max(0, 290)
                        end_pos = min(len(raw_body), 310)
                        context = raw_body[start_pos:end_pos]
                        logger.info(f"Bytes around position 298: {context!r}")
                        logger.info(f"Raw bytes: {raw_body[start_pos:end_pos].encode('utf-8')}")
                    
                    # Check for invisible characters and whitespace
                    if raw_body:
                        if not raw_body.strip():
                            logger.warning("Body is only whitespace")
                        elif raw_body != raw_body.strip():
                            logger.warning(f"Body has leading/trailing whitespace")
                            logger.info(f"Leading chars: {raw_body[:10]!r}")
                            logger.info(f"Trailing chars: {raw_body[-10:]!r}")
                        
                        # Check each line for issues
                        lines = raw_body.split('\n')
                        for i, line in enumerate(lines, 1):
                            if line != line.strip():
                                logger.info(f"Line {i} has extra whitespace: {line!r}")
                        
                        if not raw_body.strip().startswith('{'):
                            logger.warning("Body doesn't start with '{'")
                        if not raw_body.strip().endswith('}'):
                            logger.warning("Body doesn't end with '}'")
                        
                        # Check for unquoted property names
                        import re
                        unquoted_props = re.findall(r'\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*:', raw_body)
                        if unquoted_props:
                            logger.warning(f"Possible unquoted property names: {unquoted_props}")
                            
            except Exception as e:
                logger.error(f"Error reading request body: {e}")
        
        return None
