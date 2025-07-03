#!/usr/bin/env python3
"""
Azure Windows VM Service Health Checker

A Python script to check the health of Windows services on Azure Virtual Machines
using Azure Run Command API.

Features:
- Discovers Azure Windows VMs
- Interactive VM selection
- Service status verification
- Multiple service checks
- No direct network access required to VMs
"""

import json
import sys
import time
from typing import List, Dict, Optional

try:
    from azure.identity import DefaultAzureCredential
    from azure.mgmt.compute import ComputeManagementClient
    from azure.mgmt.resource import ResourceManagementClient
    from azure.core.exceptions import AzureError
except ImportError:
    print("❌ Required Azure libraries not found!")
    print("Install with: pip install azure-identity azure-mgmt-compute azure-mgmt-resource")
    sys.exit(1)


class AzureServiceHealthChecker:
    def __init__(self, subscription_id: str):
        """Initialize the Azure Service Health Checker."""
        self.subscription_id = subscription_id
        self.credential = DefaultAzureCredential()
        self.compute_client = ComputeManagementClient(self.credential, subscription_id)
        self.resource_client = ResourceManagementClient(self.credential, subscription_id)

    def get_windows_vms(self, tag_filter: Optional[str] = None) -> List[Dict]:
        """Get all Windows VMs in the subscription, optionally filtered by tag."""
        print("🔍 Discovering Windows VMs...")
        vms = []
        
        try:
            for vm in self.compute_client.virtual_machines.list_all():
                # Check if it's a Windows VM
                if vm.storage_profile.os_disk.os_type.name.lower() == 'windows':
                    # Apply tag filter if specified
                    if tag_filter:
                        if not vm.tags or tag_filter not in vm.tags.values():
                            continue
                    
                    vm_info = {
                        'name': vm.name,
                        'resource_group': vm.id.split('/')[4],
                        'location': vm.location,
                        'vm_size': vm.hardware_profile.vm_size,
                        'power_state': 'unknown',
                        'tags': vm.tags or {}
                    }
                    
                    # Get power state
                    try:
                        instance_view = self.compute_client.virtual_machines.instance_view(
                            vm_info['resource_group'], vm.name
                        )
                        for status in instance_view.statuses:
                            if status.code.startswith('PowerState/'):
                                vm_info['power_state'] = status.code.split('/')[-1]
                                break
                    except Exception as e:
                        print(f"⚠️  Could not get power state for {vm.name}: {e}")
                    
                    vms.append(vm_info)
            
            return vms
        except AzureError as e:
            print(f"❌ Error fetching VMs: {e}")
            return []

    def select_vm(self, vms: List[Dict]) -> Optional[Dict]:
        """Interactive VM selection."""
        if not vms:
            print("❌ No Windows VMs found!")
            return None
        
        print(f"\n✅ Found {len(vms)} Windows VM(s):")
        for i, vm in enumerate(vms, 1):
            status_emoji = "🟢" if vm['power_state'] == 'running' else "🔴"
            tags_str = ", ".join([f"{k}:{v}" for k, v in vm['tags'].items()]) if vm['tags'] else "No tags"
            print(f"{i}. {vm['name']} (RG: {vm['resource_group']}) - {vm['power_state']} {status_emoji}")
            print(f"   Size: {vm['vm_size']}, Location: {vm['location']}")
            print(f"   Tags: {tags_str}")
        
        while True:
            try:
                choice = input(f"\nSelect VM (1-{len(vms)}): ").strip()
                if choice.lower() in ['q', 'quit', 'exit']:
                    return None
                
                vm_index = int(choice) - 1
                if 0 <= vm_index < len(vms):
                    selected_vm = vms[vm_index]
                    print(f"\n📋 Selected VM: {selected_vm['name']}")
                    print(f"Power State: {selected_vm['power_state']}")
                    
                    if selected_vm['power_state'] != 'running':
                        print("⚠️  Warning: VM is not in running state")
                        confirm = input("Continue anyway? (y/N): ").strip().lower()
                        if confirm != 'y':
                            return None
                    
                    return selected_vm
                else:
                    print("❌ Invalid selection. Please try again.")
            except ValueError:
                print("❌ Please enter a valid number.")
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                return None

    def check_service_health(self, vm: Dict, service_names: List[str]) -> Dict:
        """Check the health of specified services on the VM."""
        print(f"\n🔍 Checking service health on {vm['name']}...")
        
        # Create PowerShell script to check services
        services_list = "', '".join(service_names)
        powershell_script = f"""
$services = @('{services_list}')
$results = @()

foreach ($serviceName in $services) {{
    try {{
        $service = Get-Service -Name $serviceName -ErrorAction Stop
        $processInfo = ""
        
        if ($service.Status -eq 'Running' -and $service.ServiceType -ne 'Win32ShareProcess') {{
            try {{
                $process = Get-Process -Id (Get-WmiObject -Class Win32_Service -Filter "Name='$serviceName'").ProcessId -ErrorAction SilentlyContinue
                if ($process) {{
                    $processInfo = "PID: $($process.Id), CPU: $([math]::Round($process.CPU, 2))s, Memory: $([math]::Round($process.WorkingSet64/1MB, 2))MB"
                }}
            }} catch {{
                $processInfo = "Process info unavailable"
            }}
        }}
        
        $results += [PSCustomObject]@{{
            ServiceName = $serviceName
            Status = $service.Status
            StartType = $service.StartType
            ProcessInfo = $processInfo
            Error = $null
        }}
    }} catch {{
        $results += [PSCustomObject]@{{
            ServiceName = $serviceName
            Status = "NotFound"
            StartType = "Unknown"
            ProcessInfo = ""
            Error = $_.Exception.Message
        }}
    }}
}}

$results | ConvertTo-Json -Depth 3
"""
        
        try:
            # Execute the PowerShell script using Azure Run Command
            print("⏳ Executing service health check...")
            
            run_command_result = self.compute_client.virtual_machines.begin_run_command(
                resource_group_name=vm['resource_group'],
                vm_name=vm['name'],
                parameters={
                    'command_id': 'RunPowerShellScript',
                    'script': [powershell_script],
                    'parameters': []
                }
            ).result()
            
            # Parse the output
            if run_command_result.value and len(run_command_result.value) > 0:
                output = run_command_result.value[0].message
                try:
                    service_results = json.loads(output)
                    return {
                        'success': True,
                        'services': service_results if isinstance(service_results, list) else [service_results],
                        'raw_output': output
                    }
                except json.JSONDecodeError:
                    return {
                        'success': False,
                        'error': 'Failed to parse service information',
                        'raw_output': output
                    }
            else:
                return {
                    'success': False,
                    'error': 'No output received from VM',
                    'raw_output': ''
                }
                
        except AzureError as e:
            return {
                'success': False,
                'error': f'Azure API error: {str(e)}',
                'raw_output': ''
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Unexpected error: {str(e)}',
                'raw_output': ''
            }

    def display_service_results(self, results: Dict):
        """Display service health check results in a formatted way."""
        if not results['success']:
            print(f"❌ Service health check failed: {results['error']}")
            if results['raw_output']:
                print(f"Raw output: {results['raw_output']}")
            return
        
        print("\n📊 Service Health Results:")
        print("=" * 80)
        
        for service in results['services']:
            status = service['Status']
            name = service['ServiceName']
            
            # Status emoji
            if status == 'Running':
                status_emoji = "🟢"
            elif status == 'Stopped':
                status_emoji = "🔴"
            elif status == 'NotFound':
                status_emoji = "❓"
            else:
                status_emoji = "🟡"
            
            print(f"\n{status_emoji} Service: {name}")
            print(f"   Status: {status}")
            print(f"   Start Type: {service['StartType']}")
            
            if service['ProcessInfo']:
                print(f"   Process: {service['ProcessInfo']}")
            
            if service['Error']:
                print(f"   Error: {service['Error']}")
        
        print("\n" + "=" * 80)

    def run_health_check(self):
        """Main method to run the service health check."""
        print("🏥 Azure Windows VM Service Health Checker")
        print("=" * 50)
        
        # Get VMs
        vms = self.get_windows_vms()
        
        # Select VM
        selected_vm = self.select_vm(vms)
        if not selected_vm:
            print("👋 No VM selected. Exiting.")
            return
        
        # Get services to check
        print(f"\n🔧 Service Health Check for: {selected_vm['name']}")
        print("Enter service names to check (one per line, empty line to finish):")
        print("Examples: W3SVC, MSSQLSERVER, Spooler, Themes")
        
        services = []
        while True:
            service = input("Service name: ").strip()
            if not service:
                break
            services.append(service)
        
        if not services:
            print("❌ No services specified. Exiting.")
            return
        
        print(f"\n🎯 Will check {len(services)} service(s): {', '.join(services)}")
        confirm = input("Proceed with health check? (y/N): ").strip().lower()
        if confirm != 'y':
            print("👋 Health check cancelled.")
            return
        
        # Perform health check
        results = self.check_service_health(selected_vm, services)
        
        # Display results
        self.display_service_results(results)
        
        print(f"\n✅ Service health check completed for {selected_vm['name']}!")


def main():
    """Main function."""
    print("🏥 Azure Windows VM Service Health Checker")
    print("=" * 50)
    
    # Get subscription ID
    subscription_id = input("Enter Azure Subscription ID: ").strip()
    if not subscription_id:
        print("❌ Subscription ID is required!")
        sys.exit(1)
    
    try:
        # Initialize checker
        checker = AzureServiceHealthChecker(subscription_id)
        
        # Run health check
        checker.run_health_check()
        
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
