"""
Main FastAPI application for Easy-KMS server.
"""

import ssl
import logging
from pathlib import Path
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from .config import get_settings
from .api.routes import router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI application
app = FastAPI(
    title="Easy-KMS",
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
    logger.info(f"Starting Easy-KMS server on {settings.kme_host}:{settings.kme_port}")
    logger.info(f"KME ID: {settings.kme_id}")
    logger.info(f"Certificate path: {settings.kme_cert_path}")
    logger.info(f"Key path: {settings.kme_key_path}")
    logger.info(f"CA certificate path: {settings.ca_cert_path}")


@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown event."""
    logger.info("Shutting down Easy-KMS server")


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Easy-KMS Server",
        "version": "1.0.0",
        "specification": "ETSI GS QKD 014 v1.1.1",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


def create_ssl_context() -> ssl.SSLContext:
    """Create SSL context for mTLS."""
    settings = get_settings()
    
    # Create SSL context
    ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    ssl_context.verify_mode = ssl.CERT_REQUIRED
    ssl_context.check_hostname = False
    
    # Load server certificate and key
    ssl_context.load_cert_chain(
        certfile=settings.kme_cert_path,
        keyfile=settings.kme_key_path
    )
    
    # Load CA certificate for client verification
    ssl_context.load_verify_locations(cafile=settings.ca_cert_path)
    
    return ssl_context


def run_server():
    """Run the KME server with mTLS support."""
    settings = get_settings()
    
    # Create SSL context
    ssl_context = create_ssl_context()
    
    # Configure uvicorn
    uvicorn.run(
        "src.main:app",
        host=settings.kme_host,
        port=settings.kme_port,
        ssl_keyfile=settings.kme_key_path,
        ssl_certfile=settings.kme_cert_path,
        ssl_ca_certs=settings.ca_cert_path,
        ssl_verify_mode=ssl.CERT_REQUIRED,
        reload=False,  # Set to True for development
        log_level=settings.log_level.lower()
    )


if __name__ == "__main__":
    run_server() 