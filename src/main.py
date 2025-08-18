"""
Easy-KME Server - ETSI GS QKD 014 Key Management Entity
Main application entry point.
"""

import logging
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from fastapi import Request

from .config import get_settings
from .api.routes import router

# Load environment variables from .env file
load_dotenv()

# Configure logging
settings = get_settings()
log_level = getattr(logging, settings.log_level.upper(), logging.INFO)

# Create logs directory if it doesn't exist
import os
os.makedirs('logs', exist_ok=True)

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

# Include API routes
app.include_router(router)


@app.on_event("startup")
async def startup_event():
    """Application startup event."""
    settings = get_settings()
    logger.info(f"Starting Easy-KME server on {settings.kme_host}:8000")
    logger.info(f"KME ID: {settings.kme_id}")


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
