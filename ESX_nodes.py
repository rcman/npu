import matplotlib.pyplot as plt
import numpy as np

# ESXi Infrastructure Specifications
ESXI_HOST_COUNT = 4  # Number of ESXi hosts in cluster
VM_PER_HOST = 8      # VMs per ESXi host
LOCAL_NAS_BANDWIDTH_GBPS = 20.0  # Local NAS (could be NVMe, RAID arrays, etc.)
HOST_NETWORK_GBPS = 10.0         # 10G network per ESXi host
VM_NETWORK_ALLOCATION_MBPS = 1000 # Network allocation per VM
HOST_STORAGE_GBPS = 12.0         # Storage bandwidth per host (NVMe/SAN)

# Convert to Mbps
LOCAL_NAS_BANDWIDTH_MBPS = LOCAL_NAS_BANDWIDTH_GBPS * 1000
HOST_NETWORK_MBPS = HOST_NETWORK_GBPS * 1000
HOST_STORAGE_MBPS = HOST_STORAGE_GBPS * 1000

# ESXi overhead factors
VMWARE_CPU_OVERHEAD = 0.15      # 15% CPU overhead for virtualization
VMWARE_MEMORY_OVERHEAD = 0.10   # 10% memory overhead
VMWARE_STORAGE_OVERHEAD = 0.20  # 20% storage overhead (VMFS, snapshots, etc.)
VMWARE_NETWORK_OVERHEAD = 0.08  # 8% network overhead (vSwitch, etc.)

# Storage contention models
def calculate_storage_contention(vms_per_host, io_pattern='mixed'):
    """Calculate storage performance degradation due to VM contention"""
    if vms_per_host <= 2:
        return 1.0  # No contention
    elif vms_per_host <= 4:
        return 0.85  # Light contention
    elif vms_per_host <= 6:
        return 0.70  # Moderate contention
    elif vms_per_host <= 8:
        return 0.55  # Heavy contention
    else:
        return 0.40  # Severe contention

def calculate_esxi_distcc_performance(num_nodes):
    """Calculate distcc performance in ESXi environment"""
    
    # Determine VM distribution across hosts
    total_hosts_needed = min(ESXI_HOST_COUNT, np.ceil(num_nodes / VM_PER_HOST))
    vms_per_active_host = np.ceil(num_nodes / total_hosts_needed)
    
    # Per-VM resource allocation (with ESXi overhead)
    vm_cpu_allocation = (100 / vms_per_active_host) * (1 - VMWARE_CPU_OVERHEAD)
    vm_memory_allocation = (100 / vms_per_active_host) * (1 - VMWARE_MEMORY_OVERHEAD)
    vm_storage_bw = (HOST_STORAGE_MBPS / vms_per_active_host) * (1 - VMWARE_STORAGE_OVERHEAD)
    vm_network_bw = min(VM_NETWORK_ALLOCATION_MBPS, HOST_NETWORK_MBPS / vms_per_active_host) * (1 - VMWARE_NETWORK_OVERHEAD)
    
    # Storage contention effects
    storage_contention_factor = calculate_storage_contention(vms_per_active_host)
    effective_vm_storage_bw = vm_storage_bw * storage_contention_factor
    
    # Distcc traffic patterns per VM
    vm_distcc_network_out = 80   # Mbps (source distribution)
    vm_distcc_network_in = 280   # Mbps (compiled objects)
    vm_nas_read = 250           # Mbps (source files, headers)
    vm_nas_write = 180          # Mbps (object files, logs)
    
    # Calculate aggregate demands
    total_network_out = vm_distcc_network_out * num_nodes
    total_network_in = vm_distcc_network_in * num_nodes
    total_network_demand = total_network_out + total_network_in
    
    total_nas_read = vm_nas_read * num_nodes
    total_nas_write = vm_nas_write * num_nodes
    total_nas_demand = total_nas_read + total_nas_write
    
    # Infrastructure limitations
    # Network: Limited by host network capacity
    available_network_bw = total_hosts_needed * HOST_NETWORK_MBPS * 0.8  # 80% utilization
    actual_network_bw = min(total_network_demand, available_network_bw)
    
    # Storage: Limited by NAS capacity and host storage links
    available_storage_bw = min(
        LOCAL_NAS_BANDWIDTH_MBPS * 0.8,  # NAS capacity
        total_hosts_needed * HOST_STORAGE_MBPS * 0.8  # Host storage links
    )
    actual_storage_bw = min(total_nas_demand, available_storage_bw)
    
    # Per-VM effective performance
    effective_vm_network = min(vm_network_bw, actual_network_bw / num_nodes)
    effective_vm_storage = min(effective_vm_storage_bw, actual_storage_bw / num_nodes)
    
    # Overall performance bottleneck analysis
    network_utilization = actual_network_bw / available_network_bw
    storage_utilization = actual_storage_bw / available_storage_bw
    
    # Resource contention penalties
    cpu_contention_penalty = max(0, (vms_per_active_host - 4) * 0.05)  # 5% per VM over 4
    memory_contention_penalty = max(0, (vms_per_active_host - 4) * 0.03)  # 3% per VM over 4
    
    # Effective compilation throughput
    resource_efficiency = 1.0 - cpu_contention_penalty - memory_contention_penalty
    bottleneck_factor = max(network_utilization, storage_utilization)
    
    if bottleneck_factor > 1.0:
        effective_throughput = min(actual_network_bw, actual_storage_bw) / bottleneck_factor
    else:
        effective_throughput = min(actual_network_bw, actual_storage_bw)
    
    effective_throughput *= resource_efficiency
    
    return {
        'num_nodes': num_nodes,
        'hosts_used': int(total_hosts_needed),
        'vms_per_host': vms_per_active_host,
        'network_demand': total_network_demand,
        'network_actual': actual_network_bw,
        'storage_demand': total_nas_demand,
        'storage_actual': actual_storage_bw,
        'network_utilization': network_utilization * 100,
        'storage_utilization': storage_utilization * 100,
        'cpu_efficiency': (1 - cpu_contention_penalty) * 100,
        'memory_efficiency': (1 - memory_contention_penalty) * 100,
        'storage_contention': storage_contention_factor * 100,
        'effective_throughput': effective_throughput,
        'bottleneck': 'Storage' if storage_utilization > network_utilization else 'Network',
        'vm_storage_bw': effective_vm_storage,
        'vm_network_bw': effective_vm_network
    }

# Benchmark different scaling scenarios
scenarios = {
    'standard': {
        'name': 'Standard ESXi (4 hosts, 8 VMs/host)',
        'host_count': 4,
        'vm_per_host': 8,
        'storage_tier': 'Standard'
    },
    'high_density': {
        'name': 'High Density (4 hosts, 12 VMs/host)',
        'host_count': 4,
        'vm_per_host': 12,
        'storage_tier': 'Standard'
    },
    'scale_out': {
        'name': 'Scale-Out (8 hosts, 6 VMs/host)',
        'host_count': 8,
        'vm_per_host': 6,
        'storage_tier': 'Standard'
    },
    'premium_storage': {
        'name': 'Premium Storage (NVMe, 4 hosts)',
        'host_count': 4,
        'vm_per_host': 8,
        'storage_tier': 'Premium'
    }
}

# Generate performance data
node_counts = range(1, 33)  # 1 to 32 nodes (common VM counts)
performance_data = [calculate_esxi_distcc_performance(n) for n in node_counts]

# Create comprehensive visualization
fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))

# Extract data for plotting
throughput = [d['effective_throughput'] for d in performance_data]
network_util = [d['network_utilization'] for d in performance_data]
storage_util = [d['storage_utilization'] for d in performance_data]
cpu_efficiency = [d['cpu_efficiency'] for d in performance_data]
memory_efficiency = [d['memory_efficiency'] for d in performance_data]
storage_contention = [d['storage_contention'] for d in performance_data]
vm_storage_bw = [d['vm_storage_bw'] for d in performance_data]

# Plot 1: Effective Throughput vs Node Count
ax1.plot(node_counts, throughput, 'b-', linewidth=3, marker='o', markersize=4, label='Effective Throughput')
ax1.set_xlabel('Number of VM Nodes')
ax1.set_ylabel('Throughput (Mbps)')
ax1.set_title('ESXi Cluster: Distcc Throughput vs Node Count')
ax1.grid(True, alpha=0.3)
ax1.legend()

# Add performance zones
ax1.axvspan(1, 8, alpha=0.2, color='green', label='Optimal Zone')
ax1.axvspan(8, 16, alpha=0.2, color='yellow', label='Contention Zone')
ax1.axvspan(16, 32, alpha=0.2, color='red', label='Saturation Zone')

# Plot 2: Resource Utilization
ax2.plot(node_counts, network_util, 'g-', linewidth=2, label='Network Utilization', marker='s', markersize=3)
ax2.plot(node_counts, storage_util, 'r-', linewidth=2, label='Storage Utilization', marker='^', markersize=3)
ax2.axhline(y=100, color='black', linestyle='--', alpha=0.5, label='100% Capacity')
ax2.set_xlabel('Number of VM Nodes')
ax2.set_ylabel('Utilization (%)')
ax2.set_title('Infrastructure Resource Utilization')
ax2.legend()
ax2.grid(True, alpha=0.3)
ax2.set_ylim(0, 120)

# Plot 3: VM Performance Efficiency
ax3.plot(node_counts, cpu_efficiency, 'purple', linewidth=2, label='CPU Efficiency', marker='o', markersize=3)
ax3.plot(node_counts, memory_efficiency, 'orange', linewidth=2, label='Memory Efficiency', marker='s', markersize=3)
ax3.plot(node_counts, storage_contention, 'brown', linewidth=2, label='Storage Efficiency', marker='^', markersize=3)
ax3.set_xlabel('Number of VM Nodes')
ax3.set_ylabel('Efficiency (%)')
ax3.set_title('VM Resource Efficiency vs Contention')
ax3.legend()
ax3.grid(True, alpha=0.3)
ax3.set_ylim(40, 105)

# Plot 4: Per-VM Storage Bandwidth
ax4.plot(node_counts, vm_storage_bw, 'red', linewidth=3, marker='D', markersize=4)
ax4.set_xlabel('Number of VM Nodes')
ax4.set_ylabel('Per-VM Storage BW (Mbps)')
ax4.set_title('Storage Bandwidth per VM (with Contention)')
ax4.grid(True, alpha=0.3)

# Add annotations for key transition points
sweet_spot = 8  # VMs per host
contention_start = 16  # Heavy contention starts
ax4.axvline(x=sweet_spot, color='green', linestyle=':', alpha=0.7, label='Sweet Spot')
ax4.axvline(x=contention_start, color='red', linestyle=':', alpha=0.7, label='Heavy Contention')
ax4.legend()

plt.tight_layout()

# Performance analysis and recommendations
print("ESXi CLUSTER DISTCC PERFORMANCE ANALYSIS")
print("=" * 60)

# Find optimal configurations
optimal_performance = 0
optimal_nodes = 0
for i, data in enumerate(performance_data):
    efficiency_score = (data['effective_throughput'] / (i + 1))  # Throughput per node
    if efficiency_score > optimal_performance and data['storage_contention'] > 70:
        optimal_performance = efficiency_score
        optimal_nodes = i + 1

print(f"\nOptimal Configuration:")
print(f"  Recommended nodes: {optimal_nodes}")
print(f"  Throughput per node: {optimal_performance:.0f} Mbps")
print(f"  Total throughput: {performance_data[optimal_nodes-1]['effective_throughput']:.0f} Mbps")

# Benchmark results at key node counts
benchmark_nodes = [4, 8, 16, 24, 32]
print(f"\nBenchmark Results:")
print("Nodes | Hosts | VMs/Host | Throughput | Net Util | Storage Util | Bottleneck")
print("-" * 75)

for nodes in benchmark_nodes:
    if nodes <= len(performance_data):
        data = performance_data[nodes-1]
        print(f"{nodes:5d} | {data['hosts_used']:5d} | {data['vms_per_host']:8.1f} | "
              f"{data['effective_throughput']:8.0f} | {data['network_utilization']:7.1f}% | "
              f"{data['storage_utilization']:10.1f}% | {data['bottleneck']:8s}")

print(f"\nPerformance Zones:")
print(f"  OPTIMAL (1-8 nodes):    High per-VM performance, minimal contention")
print(f"  CONTENTION (9-16 nodes): Moderate performance degradation")
print(f"  SATURATION (17+ nodes):  Severe contention, poor scaling")

print(f"\nInfrastructure Bottlenecks:")
print(f"  • Network becomes bottleneck at: ~{next((i+1 for i, d in enumerate(performance_data) if d['network_utilization'] > 95), 'N/A')} nodes")
print(f"  • Storage becomes bottleneck at: ~{next((i+1 for i, d in enumerate(performance_data) if d['storage_utilization'] > 95), 'N/A')} nodes")
print(f"  • VM contention significant at: ~{next((i+1 for i, d in enumerate(performance_data) if d['storage_contention'] < 70), 'N/A')} nodes")

print(f"\nScaling Recommendations:")
print(f"  1. SMALL SCALE (≤8 nodes):   Use current 4-host cluster")
print(f"  2. MEDIUM SCALE (9-16 nodes): Add more ESXi hosts, reduce VMs per host")
print(f"  3. LARGE SCALE (17+ nodes):   Upgrade storage tier or use dedicated build hosts")
print(f"  4. ENTERPRISE (25+ nodes):   Consider bare-metal nodes for compilation")

print(f"\nKey ESXi Considerations:")
print(f"  • VM overhead: ~{VMWARE_CPU_OVERHEAD*100:.0f}% CPU, ~{VMWARE_STORAGE_OVERHEAD*100:.0f}% storage")
print(f"  • Storage contention major factor beyond 6-8 VMs per host")
print(f"  • Network rarely bottleneck due to VM bandwidth limits")
print(f"  • Memory/CPU contention grows linearly with VM density")

plt.show()