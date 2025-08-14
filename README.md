# Easy-KME

A comprehensive Key Management Entity (KME) solution designed for simplicity and security.

## Overview

Easy-KME provides a streamlined approach to key management, offering both ease of use and robust security features. This project aims to simplify the complex process of managing cryptographic keys while maintaining enterprise-grade security standards.

## Features

- **Simple Key Management**: Intuitive interface for key creation, storage, and management
- **Secure Storage**: Enterprise-grade encryption for key storage
- **Access Control**: Role-based access control for key operations
- **Audit Logging**: Comprehensive logging of all key operations
- **API Integration**: RESTful API for seamless integration with existing systems

## Getting Started

### Prerequisites

- Python 3.8 or higher
- OpenSSL (version 1.1.1 or later)
- Linux/Unix environment
- Generated certificates (see [Certificate Authority Setup](README-CA.md))

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/easy-kme.git
cd easy-kme

# Install dependencies
pip install -r requirements.txt

# Generate certificates (see README-CA.md)
# Follow the certificate generation guide

# Configure environment
cp env.example .env
# Edit .env with your configuration

# Run the application
python run.py
```

### Configuration

All configuration is handled through environment variables in the `.env` file. See [KME Server Configuration](README-KME.md) for detailed configuration options.

## Documentation

### Setup and Configuration
- [Certificate Authority Setup](README-CA.md) - Complete CA and certificate generation guide
- [KME Server Configuration](README-KME.md) - Server setup, configuration, and operation
- [SAE Client Integration](README-SAE-CERT.md) - SAE client certificate setup and integration

### API Reference
- [ETSI GS QKD 014 Specification](docs/gs_qkd014v010101p.txt) - Original ETSI specification
- Interactive API Documentation - Available at `/docs` when server is running

## Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

For support and questions:
- Create an issue on GitHub
- Check the [KME Server Configuration](README-KME.md) troubleshooting section
- Review the [SAE Client Integration](README-SAE-CERT.md) troubleshooting section
- Verify certificate setup using [Certificate Authority Setup](README-CA.md)

## Roadmap

- [ ] Core KME functionality
- [ ] Web-based management interface
- [ ] API endpoints
- [ ] Integration examples
- [ ] Performance optimizations
- [ ] Additional security features

---

**Note**: This project is currently in development. Documentation and features will be updated as the project evolves. 
