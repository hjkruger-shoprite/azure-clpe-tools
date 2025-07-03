# Azure CLPE Management Tools - Integration Testing

A collection of Python scripts for managing Azure Windows Virtual Machines in the CLPE (Central Loyalty Promotions Engine) environment.

**🔒 SECURITY RESTRICTED VERSION**
- **Subscription:** Integration Testing only (`5b479b96-2b99-464d-a824-2761380620ea`)
- **VM Filter:** Only VMs tagged with `System:CENTRAL_LOYALTY_PROMOTIONS_ENGINE`
- **Purpose:** CLPE (Central Loyalty Promotions Engine) management and monitoring

## Tools Included

### 1. 🏥 CLPE NCRPES Service Monitor
Monitor the health of the `ncrpes.exe` service across all CLPE VMs.

**Features:**
- Real-time service status monitoring
- Process performance metrics
- System health indicators
- Multi-VM monitoring support

**Quick Start:**
```bash
./setup_clpe_monitor.sh
source clpe_monitor_env/bin/activate
python clpe_ncrpes_monitor.py
```

### 2. 📁 Azure Windows VM File Renamer
Rename files on CLPE VMs using Azure Run Command API.

**Features:**
- Secure file operations via Azure Run Command
- Interactive VM selection
- Built-in safety confirmations

**Quick Start:**
```bash
./setup.sh
source azure_file_renamer_env/bin/activate
python azure_file_renamer.py
```

## CLPE Infrastructure

The tools currently manage these CLPE VMs:

1. **CLPEINTDB1** - Database Server
   - Resource Group: SHOPRITERG-CLPE-INT02
   - Size: Standard_F4s_v2 (4 vCPUs, 8GB RAM)
   - OS: Windows Server 2016 Datacenter

2. **CLPEINTWEB1** - Web Server 1
   - Resource Group: SHOPRITERG-CLPE-INT02
   - Size: Standard_B2ms (2 vCPUs, 8GB RAM)
   - OS: Windows Server 2016 Datacenter

3. **CLPEINTWEB2** - Web Server 2
   - Resource Group: SHOPRITERG-CLPE-INT02
   - Size: Standard_B2ms (2 vCPUs, 8GB RAM)
   - OS: Windows Server 2016 Datacenter

## Prerequisites

1. **Python 3.7+** installed on your system
2. **Azure CLI** installed and configured
3. **Access to Integration Testing subscription**
4. **Virtual Machine Contributor** role on CLPE VMs
5. **Authentication** to Shoprite Azure tenant

## Security

- Uses Azure Run Command API (no direct network access to VMs required)
- Authenticates using Azure CLI credentials or managed identity
- No passwords or keys stored in scripts
- Requires appropriate Azure RBAC permissions
- Restricted to Integration Testing subscription only

## Branch Structure

- **main**: Stable releases and documentation
- **IntegrationTesting**: Active development and testing branch for CLPE environment ⭐ **CURRENT BRANCH**
- **feature/***: Feature development branches

## Development Notes (IntegrationTesting Branch)

This branch contains the latest development version with:
- Enhanced NCRPES monitoring capabilities
- Real-time service health reporting
- Multi-VM monitoring support
- Improved error handling and logging

### Testing Status:
- ✅ CLPE VM Discovery
- ✅ NCRPES Service Detection
- ✅ Process Monitoring
- ✅ System Performance Metrics
- 🔄 Multi-VM Batch Monitoring (In Progress)
- 🔄 Automated Health Alerts (Planned)

## Contributing

1. Create a feature branch from `IntegrationTesting`
2. Make your changes
3. Test thoroughly in the Integration environment
4. Submit a pull request to `IntegrationTesting`

## License

MIT License - see LICENSE file for details

## Support

For issues and questions:
1. Check the troubleshooting sections in individual tool documentation
2. Review Azure documentation
3. Open an issue on GitHub

## Changelog

### v2.0.0 - CLPE Service Monitoring
- Added CLPE NCRPES Service Monitor
- Enhanced security restrictions
- Multi-VM monitoring support
- Comprehensive service health reporting

### v1.0.0 - File Management
- Initial release with Azure File Renamer
- Basic file renaming functionality
- Interactive VM selection
- Azure Run Command integration
