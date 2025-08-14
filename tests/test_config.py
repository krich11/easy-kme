"""
Basic tests for Easy-KME configuration.
"""

import pytest
from pathlib import Path
import tempfile
import os

from src.config import Settings


def test_settings_defaults():
    """Test that settings have proper defaults."""
    # Create temporary environment
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create test certificates
        cert_dir = Path(temp_dir) / "certs"
        cert_dir.mkdir()
        
        # Create dummy certificate files
        (cert_dir / "kme_cert.pem").write_text("dummy cert")
        (cert_dir / "kme_key.pem").write_text("dummy key")
        (cert_dir / "ca_cert.pem").write_text("dummy ca")
        
        # Set environment variables
        os.environ["KME_CERT_PATH"] = str(cert_dir / "kme_cert.pem")
        os.environ["KME_KEY_PATH"] = str(cert_dir / "kme_key.pem")
        os.environ["CA_CERT_PATH"] = str(cert_dir / "ca_cert.pem")
        os.environ["DATA_DIR"] = str(Path(temp_dir) / "data")
        
        # Test settings creation
        settings = Settings()
        
        assert settings.kme_host == "0.0.0.0"
        assert settings.kme_port == 8443
        assert settings.kme_id == "KME_LAB_001"
        assert settings.key_pool_size == 1000
        assert settings.key_size == 256
        assert settings.require_client_cert is True
        assert settings.verify_ca is True


def test_settings_validation():
    """Test settings validation."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Test with missing certificate files
        os.environ["KME_CERT_PATH"] = "/nonexistent/cert.pem"
        
        with pytest.raises(ValueError, match="Certificate file not found"):
            Settings()


if __name__ == "__main__":
    pytest.main([__file__]) 
