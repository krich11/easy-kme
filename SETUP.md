# Easy-KME Setup Guide

This guide explains how to set up the Easy-KME server from scratch using the automated setup script.

## Quick Start

For a complete automated setup, run:

```bash
./setup_kme.sh
```

Then select option `10) Run Complete Setup (All Steps)` from the menu.

## Manual Setup Steps

If you prefer to run setup steps individually, use the menu-driven interface:

```bash
./setup_kme.sh
```

### Step-by-Step Process

#### 1. Prerequisites Check/Install
- **What it does**: Checks for required system packages (Python 3.8+, pip, git, OpenSSL, Nginx, curl, jq)
- **Status indicator**: Shows ✓ when all prerequisites are satisfied
- **Auto-install**: Can automatically install missing packages using apt/yum/dnf

#### 2. Virtual Environment Setup
- **What it does**: Creates a Python virtual environment and installs all Python dependencies
- **Creates**: `venv/` directory with isolated Python environment
- **Installs**: All packages from `requirements.txt`

#### 3. Directory Structure Creation
- **What it does**: Creates necessary directories with proper permissions
- **Creates**:
  - `data/` - Key storage directory (755 permissions)
  - `logs/` - Log files directory (755 permissions)
  - `certs/ca/` - CA certificates (700 permissions)
  - `certs/kme/` - KME certificates (700 permissions)
  - `certs/sae/` - SAE certificates (700 permissions)

#### 4. Environment Configuration
- **What it does**: Creates `.env` file with default configuration
- **Backup**: Automatically backs up existing `.env` to `.env.backup`
- **Configuration**: Sets up all necessary environment variables for the KME server

#### 5. KME Certificate Import
- **What it does**: Imports KME certificate from P12 file
- **Requires**: P12 file containing KME certificate and private key
- **Extracts**: Certificate to `certs/kme/kme.crt` and private key to `certs/kme/kme.key`
- **Updates**: `.env` file with correct certificate paths
- **Security**: Sets proper file permissions (644 for cert, 600 for key)

#### 6. CA Certificate Import
- **What it does**: Imports CA certificate (PEM format)
- **Requires**: CA certificate file in PEM format
- **Copies**: To `certs/ca/ca.crt`
- **Updates**: `.env` file with CA certificate path
- **Security**: Sets 644 permissions

#### 7. SAE Certificate Import
- **What it does**: Imports multiple SAE certificates from P12 files
- **Requires**: P12 files for each SAE
- **Process**: Interactive - prompts for each SAE P12 file and name
- **Extracts**: Each SAE certificate to `certs/sae/{sae_name}.crt` and key to `certs/sae/{sae_name}.key`
- **Security**: Sets proper file permissions for each certificate

#### 8. Nginx Configuration
- **What it does**: Sets up Nginx as reverse proxy for mTLS termination
- **Copies**: `nginx.conf` to `/etc/nginx/sites-available/easy-kme`
- **Links**: Creates symlink in `/etc/nginx/sites-enabled/`
- **Tests**: Validates Nginx configuration
- **Reloads**: Nginx service with new configuration

#### 9. Setup Verification
- **What it does**: Comprehensive verification of all setup components
- **Checks**: All files, directories, and configurations
- **Reports**: Status of each component with detailed feedback
- **Issues**: Lists any problems found with specific guidance

## P12 File Import Process

The setup script handles P12 file imports automatically:

1. **Password Prompt**: Securely prompts for P12 password (hidden input)
2. **Certificate Extraction**: Uses OpenSSL to extract certificate and private key
3. **File Naming**: Uses provided names (e.g., "kme", "SAE_001")
4. **Permission Setting**: Automatically sets secure file permissions
5. **Path Updates**: Updates `.env` file with correct certificate paths

### Example P12 Import

```bash
# KME Certificate
Enter path to KME P12 file: /path/to/kme.p12
Enter P12 password: [hidden]

# SAE Certificates
Enter path to SAE P12 file: /path/to/sae1.p12
Enter SAE name: SAE_001
Enter P12 password: [hidden]

Enter path to SAE P12 file: /path/to/sae2.p12
Enter SAE name: SAE_002
Enter P12 password: [hidden]

Enter path to SAE P12 file: done
```

## Status Indicators

The setup menu shows real-time status of each component:

- **✓ Green**: Component is properly configured
- **✗ Red**: Component needs attention

This allows you to see exactly what's been completed and what still needs to be done.

## Post-Setup Steps

After successful setup:

1. **Start the server**:
   ```bash
   ./start_kme.sh
   ```

2. **Test the API**:
   ```bash
   ./test_kme_api.sh
   ```

3. **Monitor logs**:
   ```bash
   tail -f logs/kme.log
   ```

## Troubleshooting

### Common Issues

1. **Permission Denied**: Ensure you have sudo access for package installation
2. **P12 Import Fails**: Verify P12 password and file integrity
3. **Nginx Configuration Error**: Check if port 8443 is available
4. **Certificate Path Issues**: Verify certificate files exist and are readable

### Manual Certificate Setup

If you prefer to manually create certificates, see the documentation in the `certs/` directory:
- `certs/README-CA.md` - CA certificate creation
- `certs/README-KME.md` - KME certificate creation  
- `certs/README-SAE-CERT.md` - SAE certificate creation

### Environment Variables

Key environment variables in `.env`:

- `KME_HOST` - Server host (default: 0.0.0.0)
- `KME_PORT` - Server port (default: 8443)
- `KME_ID` - KME identifier (default: KME_LAB_001)
- `REQUIRE_CLIENT_CERT` - Enable mTLS (default: true)
- `ALLOW_HEADER_AUTH` - Allow header-based auth (default: false)

## Security Notes

- Certificate directories have restricted permissions (700)
- Private keys have restricted permissions (600)
- P12 passwords are not stored and are only used during import
- The setup script uses secure practices for file handling

## Support

For issues with the setup process:

1. Check the verification step (option 9) for specific issues
2. Review log files in the `logs/` directory
3. Ensure all prerequisites are properly installed
4. Verify certificate files are valid and properly formatted
