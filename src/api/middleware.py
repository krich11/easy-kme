"""
Authentication middleware for Easy-KMS server.
Handles client authentication and SAE ID extraction.
"""

import logging
from typing import Optional
from datetime import datetime
from fastapi import Request, HTTPException, Depends
from ..services.auth_service import AuthService

logger = logging.getLogger(__name__)


def get_nginx_certificate_info(request: Request) -> Optional[dict]:
    """Extract certificate verification info from nginx headers."""
    logger.info("=== Nginx Certificate Info Debug ===")
    logger.info(f"All headers: {dict(request.headers)}")
    
    # Get nginx certificate verification info
    client_verified = request.headers.get("X-Client-Verified")
    client_dn = request.headers.get("X-Client-DN")
    client_issuer = request.headers.get("X-Client-Issuer")
    ssl_protocol = request.headers.get("X-SSL-Protocol")
    ssl_cipher = request.headers.get("X-SSL-Cipher")
    
    logger.info(f"X-Client-Verified: {client_verified}")
    logger.info(f"X-Client-DN: {client_dn}")
    logger.info(f"X-Client-Issuer: {client_issuer}")
    logger.info(f"X-SSL-Protocol: {ssl_protocol}")
    logger.info(f"X-SSL-Cipher: {ssl_cipher}")
    
    if client_verified == "SUCCESS" and client_dn:
        logger.info("Certificate verification successful via nginx")
        logger.info("=== End Nginx Certificate Info Debug ===")
        return {
            "verified": client_verified,
            "dn": client_dn,
            "issuer": client_issuer,
            "ssl_protocol": ssl_protocol,
            "ssl_cipher": ssl_cipher
        }
    else:
        logger.warning(f"Certificate verification failed or missing: verified={client_verified}, dn={client_dn}")
        logger.info("=== End Nginx Certificate Info Debug ===")
        return None


def create_certificate_extension(request: Request, sae_id: str) -> Optional[dict]:
    """Create certificate extension data for API responses."""
    cert_info = get_nginx_certificate_info(request)
    
    if cert_info:
        return {
            "client_verified": cert_info["verified"],
            "client_dn": cert_info["dn"],
            "client_issuer": cert_info["issuer"],
            "ssl_protocol": cert_info.get("ssl_protocol", "unknown"),
            "ssl_cipher": cert_info.get("ssl_cipher", "unknown"),
            "timestamp": datetime.utcnow().isoformat(),
            "sae_id": sae_id
        }
    return None


def authenticate_client(request: Request) -> str:
    """Authenticate client and return SAE ID from nginx certificate verification."""
    auth_service = AuthService()

    # Get certificate verification info from nginx headers
    cert_info = get_nginx_certificate_info(request)

    if cert_info and cert_info["verified"] == "SUCCESS":
        try:
            # Extract SAE ID from the DN (Common Name)
            # DN format: "CN=SAE_001,OU=Easy-KMS Lab,O=HPE-Networking,ST=TX,C=US"
            dn = cert_info["dn"]
            sae_id = None
            
            # Parse DN to extract CN (Common Name)
            for part in dn.split(','):
                if part.strip().startswith('CN='):
                    sae_id = part.strip()[3:]  # Remove "CN=" prefix
                    break
            
            if sae_id:
                logger.info(f"Nginx certificate authentication successful for SAE: {sae_id}")
                logger.info(f"Certificate DN: {dn}")
                logger.info(f"Certificate Issuer: {cert_info['issuer']}")
                request.state.sae_id = sae_id
                return sae_id
            else:
                logger.warning(f"Could not extract SAE ID from DN: {dn}")
                raise HTTPException(
                    status_code=401,
                    detail="Could not extract SAE ID from certificate DN"
                )
        except Exception as e:
            logger.error(f"Error during nginx certificate authentication: {e}")
            raise HTTPException(
                status_code=401,
                detail=f"Certificate authentication error: {str(e)}"
            )

    # Fallback to header-based authentication for testing
    header_sae_id = request.headers.get("x-sae-id") or request.headers.get("X-SAE-ID")
    if header_sae_id:
        logger.warning(f"Using header-based authentication for SAE {header_sae_id} (fallback)")
        request.state.sae_id = header_sae_id
        return header_sae_id

    # No valid authentication found
    raise HTTPException(
        status_code=401,
        detail="Client certificate required for authentication"
    )


def get_sae_id(request: Request) -> str:
    """Dependency to get SAE ID from request."""
    return authenticate_client(request) 