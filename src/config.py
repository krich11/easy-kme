"""
Configuration management for Easy-KMS server.
Simple environment-backed settings with validation (no external dependencies).
"""

import os
from pathlib import Path


class Settings:
    """Application settings loaded from environment variables."""
    
    def __init__(self):
        # KME Server Configuration
        self.kme_host: str = os.getenv("KME_HOST", "0.0.0.0")
        self.kme_port: int = int(os.getenv("KME_PORT", "8443"))
        self.kme_id: str = os.getenv("KME_ID", "KME_LAB_001")
    
        # Certificate Configuration
        self.kme_cert_path: str = os.getenv("KME_CERT_PATH", "./certs/kme_cert.pem")
        self.kme_key_path: str = os.getenv("KME_KEY_PATH", "./certs/kme_key.pem")
        self.ca_cert_path: str = os.getenv("CA_CERT_PATH", "./certs/ca_cert.pem")
    
        # Storage Configuration
        self.data_dir: str = os.getenv("DATA_DIR", "./data")
        self.key_pool_size: int = int(os.getenv("KEY_POOL_SIZE", "1000"))
        self.key_size: int = int(os.getenv("KEY_SIZE", "256"))
    
        # Security Settings
        self.require_client_cert: bool = os.getenv("REQUIRE_CLIENT_CERT", "true").lower() == "true"
        self.verify_ca: bool = os.getenv("VERIFY_CA", "true").lower() == "true"
        self.allow_header_auth: bool = os.getenv("ALLOW_HEADER_AUTH", "false").lower() == "true"
    
        # Logging Configuration
        self.log_level: str = os.getenv("LOG_LEVEL", "INFO").upper()
        self.log_file: str = os.getenv("LOG_FILE", "./logs/kme.log")
    
        # API Configuration
        self.api_version: str = os.getenv("API_VERSION", "v1")
        self.api_prefix: str = os.getenv("API_PREFIX", "/api")

        # Spec-related limits
        self.max_key_per_request: int = int(os.getenv("KEY_MAX_PER_REQUEST", "128"))
        self.key_max_size: int = int(os.getenv("KEY_MAX_SIZE", "1024"))
        self.key_min_size: int = int(os.getenv("KEY_MIN_SIZE", "8"))
        self.max_sae_id_count: int = int(os.getenv("MAX_SAE_ID_COUNT", "8"))
    
        # Validate and normalize
        self._validate()

    def _validate(self):
        # Validate log level
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if self.log_level not in valid_levels:
            raise ValueError(f"Invalid log level: {self.log_level}")

        # Ensure data dir exists
        Path(self.data_dir).mkdir(parents=True, exist_ok=True)

        # Validate cert files exist
        for path in (self.kme_cert_path, self.kme_key_path, self.ca_cert_path):
            p = Path(path)
            if not (p.exists() or p.is_symlink()):
                raise ValueError(f"Certificate file not found: {path}")


from functools import lru_cache


@lru_cache
def get_settings() -> Settings:
    """Create and cache the Settings instance."""
    return Settings()