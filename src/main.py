"""
Easy-KME Server - ETSI GS QKD 014 Key Management Entity
Main application entry point.
"""

# Load environment variables from .env file FIRST
from dotenv import load_dotenv
load_dotenv()

import logging
import uvicorn
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware

from .config import get_settings
from .api.routes import router

# Configure logging
import os
os.makedirs('logs', exist_ok=True)

# Get settings for logging configuration
settings = get_settings()
log_level = getattr(logging, settings.log_level.upper(), logging.INFO)

# Configure logging handlers
handlers = []

# Console handler (always present)
console_handler = logging.StreamHandler()
console_handler.setLevel(log_level)
console_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler.setFormatter(console_formatter)
handlers.append(console_handler)

# File handler for debug logs (only when log level is DEBUG)
if log_level == logging.DEBUG:
    file_handler = logging.FileHandler('logs/debug.log')
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(file_formatter)
    handlers.append(file_handler)

# Configure root logger
logging.basicConfig(
    level=log_level,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=handlers
)

logger = logging.getLogger(__name__)

# Log debug mode status immediately after configuration
if log_level == logging.DEBUG:
    logger.debug("DEBUG MODE: KME logging configured in debug mode")
    logger.debug(f"Debug logs will be written to: {os.path.abspath('logs/debug.log')}")

# Create FastAPI application
app = FastAPI(
    title="Easy-KME",
    description="ETSI GS QKD 014 Key Management Entity (KME) Server",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add API logging middleware for debug mode
@app.middleware("http")
async def log_api_requests(request: Request, call_next):
    """Log API requests and responses in debug mode."""
    settings = get_settings()
    
    if settings.log_level == "DEBUG":
        # Log request details
        logger.debug(f"=== API REQUEST ===")
        logger.debug(f"Method: {request.method}")
        logger.debug(f"URL: {request.url}")
        logger.debug(f"Headers: {dict(request.headers)}")
        
        # Log request body for POST/PUT requests
        if request.method in ["POST", "PUT", "PATCH"]:
            try:
                body = await request.body()
                if body:
                    # Try to parse as JSON
                    try:
                        import json
                        json_body = json.loads(body.decode('utf-8'))
                        logger.debug(f"Request Body (JSON): {json.dumps(json_body, indent=2)}")
                    except json.JSONDecodeError:
                        logger.debug(f"Request Body (raw): {body.decode('utf-8')}")
            except Exception as e:
                logger.debug(f"Error reading request body: {e}")
        
        # Process the request
        response = await call_next(request)
        
        # Log response details
        logger.debug(f"=== API RESPONSE ===")
        logger.debug(f"Status Code: {response.status_code}")
        logger.debug(f"Response Headers: {dict(response.headers)}")
        
        # Log response body
        try:
            response_body = b""
            async for chunk in response.body_iterator:
                response_body += chunk
            
            # Try to parse as JSON
            try:
                import json
                json_response = json.loads(response_body.decode('utf-8'))
                logger.debug(f"Response Body (JSON): {json.dumps(json_response, indent=2)}")
            except json.JSONDecodeError:
                logger.debug(f"Response Body (raw): {response_body.decode('utf-8')}")
            
            # Create new response with the body
            return Response(
                content=response_body,
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type=response.media_type
            )
        except Exception as e:
            logger.debug(f"Error reading response body: {e}")
            return response
    else:
        # Not in debug mode, just pass through
        return await call_next(request)

# Include API routes
app.include_router(router)


@app.on_event("startup")
async def startup_event():
    """Application startup event."""
    settings = get_settings()
    logger.info(f"Starting Easy-KME server on {settings.kme_host}:8000")
    logger.info(f"KME ID: {settings.kme_id}")
    
    # Log debug mode status
    if settings.log_level == "DEBUG":
        logger.debug("DEBUG MODE: KME is running in debug mode - detailed logging enabled")
        logger.debug(f"Debug logs will be written to: {os.path.abspath('logs/debug.log')}")


@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown event."""
    logger.info("Shutting down Easy-KME server")


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Easy-KME Server",
        "version": "1.0.0",
        "specification": "ETSI GS QKD 014 v1.1.1",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check(request: Request):
    """Health check endpoint with client certificate information."""
    from cryptography import x509
    from cryptography.hazmat.backends import default_backend
    import base64
    
    settings = get_settings()
    
    # Debug logging - show all headers
    logger.info("=== Health Check Debug ===")
    logger.info(f"All headers: {dict(request.headers)}")
    
    # Initialize certificate info
    cert_info = {
        "status": "healthy",
        "server": "FastAPI with nginx mTLS termination",
        "client_certificate": None,
        "debug": {
            "all_headers": dict(request.headers),
            "nginx_headers": {}
        }
    }
    
    # Extract client certificate from nginx headers
    client_cert_pem = request.headers.get("X-Client-Certificate")
    client_verified = request.headers.get("X-Client-Verified")
    client_dn = request.headers.get("X-Client-DN")
    
    # Debug logging for nginx headers
    logger.info(f"X-Client-Certificate: {'FOUND' if client_cert_pem else 'NOT FOUND'}")
    logger.info(f"X-Client-Verified: {client_verified}")
    logger.info(f"X-Client-DN: {client_dn}")
    
    # Store debug info
    cert_info["debug"]["nginx_headers"] = {
        "X-Client-Certificate": "FOUND" if client_cert_pem else "NOT FOUND",
        "X-Client-Verified": client_verified,
        "X-Client-DN": client_dn
    }
    
    if client_cert_pem:
        logger.info("Certificate found in nginx headers, parsing...")
        try:
            # Parse the certificate
            cert = x509.load_pem_x509_certificate(
                client_cert_pem.encode('utf-8'), 
                default_backend()
            )
            
            logger.info("Certificate parsed successfully")
            
            # Extract salient characteristics
            cert_info["client_certificate"] = {
                "subject": {
                    "common_name": cert.subject.get_attributes_for_oid(x509.NameOID.COMMON_NAME)[0].value if cert.subject.get_attributes_for_oid(x509.NameOID.COMMON_NAME) else None,
                    "organization": cert.subject.get_attributes_for_oid(x509.NameOID.ORGANIZATION_NAME)[0].value if cert.subject.get_attributes_for_oid(x509.NameOID.ORGANIZATION_NAME) else None,
                    "organizational_unit": cert.subject.get_attributes_for_oid(x509.NameOID.ORGANIZATIONAL_UNIT_NAME)[0].value if cert.subject.get_attributes_for_oid(x509.NameOID.ORGANIZATIONAL_UNIT_NAME) else None,
                    "country": cert.subject.get_attributes_for_oid(x509.NameOID.COUNTRY_NAME)[0].value if cert.subject.get_attributes_for_oid(x509.NameOID.COUNTRY_NAME) else None,
                    "state": cert.subject.get_attributes_for_oid(x509.NameOID.STATE_OR_PROVINCE_NAME)[0].value if cert.subject.get_attributes_for_oid(x509.NameOID.STATE_OR_PROVINCE_NAME) else None,
                    "locality": cert.subject.get_attributes_for_oid(x509.NameOID.LOCALITY_NAME)[0].value if cert.subject.get_attributes_for_oid(x509.NameOID.LOCALITY_NAME) else None,
                },
                "issuer": {
                    "common_name": cert.issuer.get_attributes_for_oid(x509.NameOID.COMMON_NAME)[0].value if cert.issuer.get_attributes_for_oid(x509.NameOID.COMMON_NAME) else None,
                    "organization": cert.issuer.get_attributes_for_oid(x509.NameOID.ORGANIZATION_NAME)[0].value if cert.issuer.get_attributes_for_oid(x509.NameOID.ORGANIZATION_NAME) else None,
                },
                "serial_number": str(cert.serial_number),
                "not_valid_before": cert.not_valid_before.isoformat(),
                "not_valid_after": cert.not_valid_after.isoformat(),
                "signature_algorithm": cert.signature_algorithm_oid._name,
                "public_key_algorithm": cert.public_key_algorithm._name,
                "version": cert.version.value,
                "nginx_verified": client_verified,
                "nginx_dn": client_dn
            }
            
            logger.info(f"Certificate subject: {cert_info['client_certificate']['subject']}")
            
        except Exception as e:
            logger.error(f"Failed to parse certificate: {e}")
            cert_info["client_certificate"] = {
                "error": f"Failed to parse certificate: {str(e)}",
                "raw_pem": client_cert_pem[:100] + "..." if len(client_cert_pem) > 100 else client_cert_pem
            }
    else:
        logger.warning("No certificate found in nginx headers")
        cert_info["client_certificate"] = {
            "status": "no_certificate_provided",
            "nginx_verified": client_verified,
            "nginx_dn": client_dn
        }
    
    logger.info("=== End Health Check Debug ===")
    return cert_info


def run_server():
    """Run the KME server with HTTP (nginx handles SSL)."""
    settings = get_settings()
    
    logger.info("Starting Easy-KME server with HTTP (nginx handles mTLS)...")
    
    # Run with uvicorn on HTTP (nginx handles SSL)
    uvicorn.run(
        app,
        host=settings.kme_host,
        port=8000,  # Fixed port for nginx upstream
        log_level="info"
    )


if __name__ == "__main__":
    run_server() 
