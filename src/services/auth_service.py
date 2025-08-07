"""
Authentication service for Easy-KMS server.
Handles certificate-based authentication and SAE ID extraction.
"""

import ssl
from typing import Optional, Tuple
from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa, padding
import logging
from datetime import datetime

from ..config import get_settings
from ..models.data_models import SAERegistry
from .storage_service import StorageService

logger = logging.getLogger(__name__)


class AuthService:
    """Certificate-based authentication service."""
    
    def __init__(self):
        self.settings = get_settings()
        self.storage_service = StorageService()
    
    def extract_sae_id_from_cert(self, client_cert: bytes) -> Optional[str]:
        """Extract SAE ID from client certificate."""
        try:
            # Parse the certificate
            cert = x509.load_der_x509_certificate(client_cert, default_backend())
            
            # Extract SAE ID from subject DN
            # Common Name (CN) is typically used for SAE ID
            sae_id = None
            for name in cert.subject.get_attributes_for_oid(x509.NameOID.COMMON_NAME):
                sae_id = name.value
                break
            
            if not sae_id:
                # Try alternative fields if CN is not available
                for name in cert.subject.get_attributes_for_oid(x509.NameOID.ORGANIZATIONAL_UNIT_NAME):
                    sae_id = name.value
                    break
            
            return sae_id
            
        except Exception as e:
            logger.error(f"Error extracting SAE ID from certificate: {e}")
            return None
    
    def verify_client_certificate(self, client_cert: bytes) -> bool:
        """Verify client certificate against CA."""
        try:
            # Load CA certificate
            with open(self.settings.ca_cert_path, 'rb') as f:
                ca_cert_data = f.read()
            
            ca_cert = x509.load_pem_x509_certificate(ca_cert_data, default_backend())
            
            # Load client certificate
            client_cert_obj = x509.load_der_x509_certificate(client_cert, default_backend())
            
            # Verify certificate chain
            ca_public_key = ca_cert.public_key()
            ca_public_key.verify(
                client_cert_obj.signature,
                client_cert_obj.tbs_certificate_bytes,
                padding.PKCS1v15(),
                client_cert_obj.signature_hash_algorithm
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Certificate verification failed: {e}")
            return False
    
    def register_sae(self, sae_id: str, client_cert: bytes) -> bool:
        """Register a new SAE or update existing registration."""
        try:
            cert = x509.load_der_x509_certificate(client_cert, default_backend())
            
            # Extract certificate details
            subject = str(cert.subject)
            serial = str(cert.serial_number)
            
            # Get existing SAE registry
            sae_registry = self.storage_service.get_sae_registry()
            
            # Check if SAE already exists
            existing_sae = None
            for sae in sae_registry:
                if sae.sae_id == sae_id:
                    existing_sae = sae
                    break
            
            if existing_sae:
                # Update existing SAE
                existing_sae.certificate_subject = subject
                existing_sae.certificate_serial = serial
                existing_sae.last_seen = datetime.utcnow()
            else:
                # Create new SAE registration
                new_sae = SAERegistry(
                    sae_id=sae_id,
                    certificate_subject=subject,
                    certificate_serial=serial
                )
                sae_registry.append(new_sae)
            
            # Save updated registry
            self.storage_service.save_sae_registry(sae_registry)
            logger.info(f"SAE {sae_id} registered/updated successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error registering SAE {sae_id}: {e}")
            return False
    
    def authenticate_client(self, client_cert: bytes) -> Tuple[bool, Optional[str]]:
        """Authenticate client certificate and extract SAE ID."""
        if not client_cert:
            logger.warning("No client certificate provided")
            return False, None
        
        # Verify certificate
        if not self.verify_client_certificate(client_cert):
            logger.warning("Client certificate verification failed")
            return False, None
        
        # Extract SAE ID
        sae_id = self.extract_sae_id_from_cert(client_cert)
        if not sae_id:
            logger.warning("Could not extract SAE ID from certificate")
            return False, None
        
        # Register/update SAE
        if not self.register_sae(sae_id, client_cert):
            logger.warning(f"Failed to register SAE {sae_id}")
            return False, None
        
        logger.info(f"Client authenticated successfully: SAE ID = {sae_id}")
        return True, sae_id
    
    def is_sae_authorized(self, sae_id: str, key_ids: list) -> bool:
        """Check if SAE is authorized to access specific keys."""
        try:
            keys = self.storage_service.get_keys()
            sessions = self.storage_service.get_sessions()
            
            # Check if SAE is authorized for any of the requested keys
            for key_id in key_ids:
                key = next((k for k in keys if k.key_id == key_id), None)
                if not key:
                    logger.warning(f"Key {key_id} not found")
                    return False
                
                # Check if SAE is master or slave for this key
                if key.master_sae_id == sae_id:
                    return True
                
                if sae_id in key.slave_sae_ids:
                    return True
            
            logger.warning(f"SAE {sae_id} not authorized for requested keys")
            return False
            
        except Exception as e:
            logger.error(f"Error checking SAE authorization: {e}")
            return False 