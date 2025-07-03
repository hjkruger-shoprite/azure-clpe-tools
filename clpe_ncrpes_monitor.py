#!/usr/bin/env python3
"""
CLPE NCRPES Service Health Monitor - Integration Testing

A Python script to monitor the ncrpes.exe service on CLPE (Central Loyalty Promotions Engine)
Windows Virtual Machines in the Integration Testing subscription using Azure Run Command API.

🔒 SECURITY RESTRICTED VERSION
- Subscription: Integration Testing only (5b479b96-2b99-464d-a824-2761380620ea)
- VM Filter: Only VMs tagged with System:CENTRAL_LOYALTY_PROMOTIONS_ENGINE
- Service: ncrpes.exe monitoring
"""

import json
import sys
import time
from datetime import datetime
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


class CLPENCRPESMonitor:
    def __init__(self):
        """Initialize the CLPE NCRPES Monitor."""
        # Integration Testing subscription ID
        self.subscription_id = "5b479b96-2b99-464d-a824-2761380620ea"
        self.clpe_tag = "System:CENTRAL_LOYALTY_PROMOTIONS_ENGINE"
        self.service_name = "ncrpes.exe"
        
        self.credential = DefaultAzureCredential()
        self.compute_client = ComputeManagementClient(self.credential, self.subscription_id)
        self.resource_client = ResourceManagementClient(self.credential, self.subscription_id)

    def get_clpe_vms(self) -> List[Dict]:
        """Get all CLPE Windows VMs in the integration subscription."""
        print("🔍 Discovering CLPE VMs...")
        vms = []
        
        try:
            for vm in self.compute_client.virtual_machines.list_all():
                # Check if it's a Windows VM with CLPE tag
                if (vm.storage_profile.os_disk.os_type.name.lower() == 'windows' and
                    vm.tags and self.clpe_tag in vm.tags.values()):
                    
                    vm_info = {
                        'name': vm.name,
                        'resource_group': vm.id.split('/')[4],
                        'location': vm.location,
                        'vm_size': vm.hardware_profile.vm_size,
                        'power_state': 'unknown',
                        'tags': vm.tags or {},
                        'os_version': 'Windows Server 2016 Datacenter'  # Based on your README
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
            print(f"❌ Error fetching CLPE VMs: {e}")
            return []

    def select_clpe_vm(self, vms: List[Dict]) -> Optional[Dict]:
        """Interactive CLPE VM selection."""
        if not vms:
            print("❌ No CLPE VMs found!")
            print("Make sure VMs are tagged with 'System:CENTRAL_LOYALTY_PROMOTIONS_ENGINE'")
            return None
        
        print(f"\n✅ Found {len(vms)} CLPE VM(s):")
        for i, vm in enumerate(vms, 1):
            status_emoji = "🟢" if vm['power_state'] == 'running' else "🔴"
            vm_type = "Database Server" if "DB" in vm['name'].upper() else "Web Server"
            print(f"{i}. {vm['name']} - {vm_type}")
            print(f"   Resource Group: {vm['resource_group']}")
            print(f"   Status: {vm['power_state']} {status_emoji}")
            print(f"   Size: {vm['vm_size']}")
            print(f"   OS: {vm['os_version']}")
        
        while True:
            try:
                choice = input(f"\nSelect CLPE VM (1-{len(vms)}) or 'all' for all VMs: ").strip().lower()
                if choice in ['q', 'quit', 'exit']:
                    return None
                
                if choice == 'all':
                    return {'all': True, 'vms': vms}
                
                vm_index = int(choice) - 1
                if 0 <= vm_index < len(vms):
                    selected_vm = vms[vm_index]
                    print(f"\n📋 Selected CLPE VM: {selected_vm['name']}")
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
                print("❌ Please enter a valid number or 'all'.")
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                return None

    def monitor_ncrpes_service(self, vm: Dict) -> Dict:
        """Monitor the ncrpes.exe service on the specified CLPE VM."""
        print(f"\n🔍 Monitoring ncrpes.exe service on {vm['name']}...")
        
        # PowerShell script to check ncrpes.exe service and process
        powershell_script = f"""
$serviceName = "ncrpes"
$processName = "ncrpes"
$results = @{{}}

# Check if ncrpes service exists
try {{
    $service = Get-Service -Name $serviceName -ErrorAction Stop
    $results.ServiceFound = $true
    $results.ServiceName = $service.Name
    $results.ServiceDisplayName = $service.DisplayName
    $results.ServiceStatus = $service.Status.ToString()
    $results.ServiceStartType = $service.StartType.ToString()
}} catch {{
    $results.ServiceFound = $false
    $results.ServiceError = $_.Exception.Message
}}

# Check for ncrpes.exe process
try {{
    $processes = Get-Process -Name $processName -ErrorAction SilentlyContinue
    if ($processes) {{
        $results.ProcessFound = $true
        $results.ProcessCount = $processes.Count
        $results.Processes = @()
        
        foreach ($proc in $processes) {{
            $processInfo = @{{
                PID = $proc.Id
                ProcessName = $proc.ProcessName
                StartTime = if ($proc.StartTime) {{ $proc.StartTime.ToString("yyyy-MM-dd HH:mm:ss") }} else {{ "Unknown" }}
                CPU = [math]::Round($proc.CPU, 2)
                WorkingSet = [math]::Round($proc.WorkingSet64/1MB, 2)
                VirtualMemory = [math]::Round($proc.VirtualMemorySize64/1MB, 2)
                HandleCount = $proc.HandleCount
                ThreadCount = $proc.Threads.Count
            }}
            $results.Processes += $processInfo
        }}
    }} else {{
        $results.ProcessFound = $false
    }}
}} catch {{
    $results.ProcessFound = $false
    $results.ProcessError = $_.Exception.Message
}}

# Check system performance
try {{
    $cpu = Get-WmiObject -Class Win32_Processor | Measure-Object -Property LoadPercentage -Average
    $memory = Get-WmiObject -Class Win32_OperatingSystem
    $results.SystemInfo = @{{
        CPUUsage = [math]::Round($cpu.Average, 2)
        TotalMemoryGB = [math]::Round($memory.TotalVisibleMemorySize/1MB, 2)
        FreeMemoryGB = [math]::Round($memory.FreePhysicalMemory/1MB, 2)
        MemoryUsagePercent = [math]::Round((($memory.TotalVisibleMemorySize - $memory.FreePhysicalMemory) / $memory.TotalVisibleMemorySize) * 100, 2)
    }}
}} catch {{
    $results.SystemInfo = @{{ Error = $_.Exception.Message }}
}}

# Add timestamp
$results.Timestamp = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
$results.ComputerName = $env:COMPUTERNAME

$results | ConvertTo-Json -Depth 4
"""
        
        try:
            # Execute the PowerShell script using Azure Run Command
            print("⏳ Executing NCRPES service check...")
            
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
                        'vm_name': vm['name'],
                        'data': service_results,
                        'raw_output': output
                    }
                except json.JSONDecodeError:
                    return {
                        'success': False,
                        'vm_name': vm['name'],
                        'error': 'Failed to parse service information',
                        'raw_output': output
                    }
            else:
                return {
                    'success': False,
                    'vm_name': vm['name'],
                    'error': 'No output received from VM',
                    'raw_output': ''
                }
                
        except AzureError as e:
            return {
                'success': False,
                'vm_name': vm['name'],
                'error': f'Azure API error: {str(e)}',
                'raw_output': ''
            }
        except Exception as e:
            return {
                'success': False,
                'vm_name': vm['name'],
                'error': f'Unexpected error: {str(e)}',
                'raw_output': ''
            }

    def display_ncrpes_results(self, results: Dict):
        """Display NCRPES service monitoring results."""
        if not results['success']:
            print(f"❌ NCRPES monitoring failed on {results['vm_name']}: {results['error']}")
            if results['raw_output']:
                print(f"Raw output: {results['raw_output']}")
            return
        
        data = results['data']
        vm_name = results['vm_name']
        
        print(f"\n🏥 NCRPES Service Health Report - {vm_name}")
        print("=" * 80)
        print(f"📅 Timestamp: {data.get('Timestamp', 'Unknown')}")
        print(f"💻 Computer: {data.get('ComputerName', 'Unknown')}")
        
        # Service Status
        print(f"\n🔧 NCRPES Service Status:")
        if data.get('ServiceFound'):
            status = data.get('ServiceStatus', 'Unknown')
            status_emoji = "🟢" if status == 'Running' else "🔴" if status == 'Stopped' else "🟡"
            print(f"   {status_emoji} Service Name: {data.get('ServiceName', 'ncrpes')}")
            print(f"   Display Name: {data.get('ServiceDisplayName', 'N/A')}")
            print(f"   Status: {status}")
            print(f"   Start Type: {data.get('ServiceStartType', 'Unknown')}")
        else:
            print(f"   ❌ NCRPES service not found")
            if data.get('ServiceError'):
                print(f"   Error: {data['ServiceError']}")
        
        # Process Status
        print(f"\n⚙️  NCRPES Process Status:")
        if data.get('ProcessFound'):
            process_count = data.get('ProcessCount', 0)
            print(f"   🟢 Found {process_count} ncrpes.exe process(es)")
            
            for i, proc in enumerate(data.get('Processes', []), 1):
                print(f"\n   Process {i}:")
                print(f"     PID: {proc.get('PID', 'Unknown')}")
                print(f"     Start Time: {proc.get('StartTime', 'Unknown')}")
                print(f"     CPU Time: {proc.get('CPU', 0)}s")
                print(f"     Memory (Working Set): {proc.get('WorkingSet', 0)} MB")
                print(f"     Virtual Memory: {proc.get('VirtualMemory', 0)} MB")
                print(f"     Handles: {proc.get('HandleCount', 0)}")
                print(f"     Threads: {proc.get('ThreadCount', 0)}")
        else:
            print(f"   ❌ No ncrpes.exe processes found")
            if data.get('ProcessError'):
                print(f"   Error: {data['ProcessError']}")
        
        # System Information
        print(f"\n🖥️  System Performance:")
        sys_info = data.get('SystemInfo', {})
        if 'Error' not in sys_info:
            cpu_usage = sys_info.get('CPUUsage', 0)
            memory_usage = sys_info.get('MemoryUsagePercent', 0)
            
            cpu_emoji = "🟢" if cpu_usage < 70 else "🟡" if cpu_usage < 90 else "🔴"
            mem_emoji = "🟢" if memory_usage < 80 else "🟡" if memory_usage < 95 else "🔴"
            
            print(f"   {cpu_emoji} CPU Usage: {cpu_usage}%")
            print(f"   {mem_emoji} Memory Usage: {memory_usage}%")
            print(f"   Total Memory: {sys_info.get('TotalMemoryGB', 0)} GB")
            print(f"   Free Memory: {sys_info.get('FreeMemoryGB', 0)} GB")
        else:
            print(f"   ❌ System info error: {sys_info['Error']}")
        
        print("\n" + "=" * 80)

    def run_clpe_monitoring(self):
        """Main method to run CLPE NCRPES monitoring."""
        print("🏥 CLPE NCRPES Service Monitor - Integration Testing")
        print("=" * 65)
        print("🔒 Restricted to: Integration testing subscription")
        print("🏷️  VM Filter: System:CENTRAL_LOYALTY_PROMOTIONS_ENGINE")
        print("⚙️  Service: ncrpes.exe")
        print("=" * 65)
        
        # Get CLPE VMs
        vms = self.get_clpe_vms()
        
        # Select VM(s)
        selection = self.select_clpe_vm(vms)
        if not selection:
            print("👋 No VM selected. Exiting.")
            return
        
        # Security confirmation
        print(f"\n🔒 SECURITY CONFIRMATION")
        print(f"You are about to monitor ncrpes.exe service on:")
        if selection.get('all'):
            print(f"   VMs: All {len(selection['vms'])} CLPE VMs")
        else:
            print(f"   VM: {selection['name']}")
        print(f"   Subscription: Integration testing")
        print(f"   System: CENTRAL_LOYALTY_PROMOTIONS_ENGINE")
        print(f"   Service: ncrpes.exe")
        
        confirm = input(f"\nDo you confirm this is the correct CLPE system? (y/N): ").strip().lower()
        if confirm != 'y':
            print("👋 CLPE monitoring cancelled.")
            return
        
        # Perform monitoring
        if selection.get('all'):
            print(f"\n🔍 Monitoring ncrpes.exe on all {len(selection['vms'])} CLPE VMs...")
            for vm in selection['vms']:
                results = self.monitor_ncrpes_service(vm)
                self.display_ncrpes_results(results)
                if vm != selection['vms'][-1]:  # Not the last VM
                    print("\n" + "─" * 80 + "\n")
        else:
            results = self.monitor_ncrpes_service(selection)
            self.display_ncrpes_results(results)
        
        print(f"\n✅ CLPE NCRPES monitoring completed!")


def main():
    """Main function."""
    print("🏥 CLPE NCRPES Service Monitor")
    print("=" * 40)
    
    try:
        # Initialize monitor
        monitor = CLPENCRPESMonitor()
        
        # Run monitoring
        monitor.run_clpe_monitoring()
        
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
