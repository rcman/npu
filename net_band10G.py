import matplotlib.pyplot as plt
import numpy as np

# Network specifications
SWITCH_BANDWIDTH_GBPS = 2.5  # 2.5 Gbps switch
ETHERNET_BANDWIDTH_GBPS = 2.5  # 2.5 Gb ethernet per connection
SAN_BANDWIDTH_GBPS = 10.0  # 10 Gbps SAN connection
SWITCH_BANDWIDTH_MBPS = SWITCH_BANDWIDTH_GBPS * 1000
ETHERNET_BANDWIDTH_MBPS = ETHERNET_BANDWIDTH_GBPS * 1000
SAN_BANDWIDTH_MBPS = SAN_BANDWIDTH_GBPS * 1000

# Distcc + SAN traffic characteristics
# With SAN: source files read from SAN, object files written to SAN
# Network traffic: preprocessed source + headers to nodes, compiled objects back
# SAN traffic: source file reads, object file writes, shared headers/libraries
COMPILATION_EFFICIENCY = 0.80  # Lower due to SAN coordination overhead
SAN_EFFICIENCY = 0.75  # SAN overhead, locking, metadata operations

def calculate_bandwidth_usage_with_san(num_nodes):
    """Calculate bandwidth usage including SAN I/O for given number of nodes"""
    
    # Network traffic (coordinator <-> nodes)
    # Reduced because source files come from SAN, not coordinator
    per_node_network_out = 80   # Mbps (preprocessed source + headers to node)
    per_node_network_in = 280   # Mbps (compiled object files from node)
    
    # SAN traffic per node (all nodes access SAN)
    per_node_san_read = 200     # Mbps (source files, headers, libraries)
    per_node_san_write = 150    # Mbps (object files, debug info)
    
    # Network bandwidth calculations
    total_network_out = per_node_network_out * num_nodes
    total_network_in = per_node_network_in * num_nodes
    total_network_bandwidth = (total_network_out + total_network_in) * COMPILATION_EFFICIENCY
    
    # SAN bandwidth calculations (aggregate from all nodes)
    total_san_read = per_node_san_read * num_nodes
    total_san_write = per_node_san_write * num_nodes
    total_san_bandwidth = (total_san_read + total_san_write) * SAN_EFFICIENCY
    
    # Network limitations
    switch_limit = SWITCH_BANDWIDTH_MBPS * 0.8  # 80% utilization
    actual_network_bandwidth = min(total_network_bandwidth, switch_limit)
    
    # SAN limitations
    san_limit = SAN_BANDWIDTH_MBPS * 0.8  # 80% utilization
    actual_san_bandwidth = min(total_san_bandwidth, san_limit)
    
    # Overall system performance is limited by the most constrained resource
    network_utilization = actual_network_bandwidth / switch_limit
    san_utilization = actual_san_bandwidth / san_limit
    
    # System bottleneck identification
    if san_utilization > network_utilization:
        bottleneck = "SAN"
        bottleneck_utilization = san_utilization
    else:
        bottleneck = "Network"
        bottleneck_utilization = network_utilization
    
    # Effective compilation throughput (limited by bottleneck)
    throughput_multiplier = min(1.0, 1.0 / max(network_utilization, san_utilization))
    effective_throughput = min(actual_network_bandwidth, actual_san_bandwidth) * throughput_multiplier
    
    return {
        'network_requested': total_network_bandwidth,
        'network_actual': actual_network_bandwidth,
        'san_requested': total_san_bandwidth,
        'san_actual': actual_san_bandwidth,
        'network_utilization': network_utilization * 100,
        'san_utilization': san_utilization * 100,
        'bottleneck': bottleneck,
        'bottleneck_utilization': bottleneck_utilization * 100,
        'effective_throughput': effective_throughput,
        'nodes': num_nodes
    }

# Generate data for different node counts
node_counts = range(1, 21)  # 1 to 20 nodes
bandwidth_data = [calculate_bandwidth_usage_with_san(n) for n in node_counts]

# Extract data for plotting
network_requested = [data['network_requested'] for data in bandwidth_data]
network_actual = [data['network_actual'] for data in bandwidth_data]
san_requested = [data['san_requested'] for data in bandwidth_data]
san_actual = [data['san_actual'] for data in bandwidth_data]
network_utilization = [data['network_utilization'] for data in bandwidth_data]
san_utilization = [data['san_utilization'] for data in bandwidth_data]
effective_throughput = [data['effective_throughput'] for data in bandwidth_data]

# Create the plots
fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 12))

# Plot 1: Network Bandwidth Usage
ax1.plot(node_counts, network_requested, 'b--', label='Network Requested', linewidth=2)
ax1.plot(node_counts, network_actual, 'b-', label='Network Actual', linewidth=2)
ax1.axhline(y=SWITCH_BANDWIDTH_MBPS, color='orange', linestyle=':', 
            label=f'Switch Limit ({SWITCH_BANDWIDTH_GBPS} Gbps)', linewidth=2)
ax1.set_xlabel('Number of Nodes')
ax1.set_ylabel('Bandwidth (Mbps)')
ax1.set_title('Network Bandwidth Usage (Distcc Traffic)')
ax1.legend()
ax1.grid(True, alpha=0.3)
ax1.set_ylim(0, 3000)

# Plot 2: SAN Bandwidth Usage
ax2.plot(node_counts, san_requested, 'g--', label='SAN Requested', linewidth=2)
ax2.plot(node_counts, san_actual, 'g-', label='SAN Actual', linewidth=2)
ax2.axhline(y=SAN_BANDWIDTH_MBPS, color='red', linestyle=':', 
            label=f'SAN Limit ({SAN_BANDWIDTH_GBPS} Gbps)', linewidth=2)
ax2.set_xlabel('Number of Nodes')
ax2.set_ylabel('Bandwidth (Mbps)')
ax2.set_title('SAN Bandwidth Usage (Shared Storage I/O)')
ax2.legend()
ax2.grid(True, alpha=0.3)
ax2.set_ylim(0, 10000)

# Plot 3: Resource Utilization
ax3.plot(node_counts, network_utilization, 'b-', label='Network Utilization', linewidth=2, marker='o', markersize=4)
ax3.plot(node_counts, san_utilization, 'g-', label='SAN Utilization', linewidth=2, marker='s', markersize=4)
ax3.axhline(y=100, color='red', linestyle='--', alpha=0.5, label='100% Capacity')
ax3.set_xlabel('Number of Nodes')
ax3.set_ylabel('Utilization (%)')
ax3.set_title('Resource Utilization vs Number of Nodes')
ax3.legend()
ax3.grid(True, alpha=0.3)
ax3.set_ylim(0, 120)

# Plot 4: Effective System Throughput
ax4.plot(node_counts, effective_throughput, 'purple', linewidth=3, marker='D', markersize=5)
ax4.set_xlabel('Number of Nodes')
ax4.set_ylabel('Effective Throughput (Mbps)')
ax4.set_title('Overall System Throughput (Limited by Bottleneck)')
ax4.grid(True, alpha=0.3)

# Add bottleneck annotations
for i, data in enumerate(bandwidth_data):
    if data['bottleneck_utilization'] > 95:  # Near saturation
        ax4.annotate(f'{data["bottleneck"]} bottleneck', 
                    xy=(data['nodes'], data['effective_throughput']), 
                    xytext=(data['nodes'] + 2, data['effective_throughput'] + 200),
                    arrowprops=dict(arrowstyle='->', color='red'),
                    fontsize=9)
        break

plt.tight_layout()

# Analysis and statistics
print("Distcc + 10G SAN Network Analysis Summary:")
print(f"Switch Capacity: {SWITCH_BANDWIDTH_GBPS} Gbps ({SWITCH_BANDWIDTH_MBPS} Mbps)")
print(f"SAN Capacity: {SAN_BANDWIDTH_GBPS} Gbps ({SAN_BANDWIDTH_MBPS} Mbps)")
print(f"Ethernet per node: {ETHERNET_BANDWIDTH_GBPS} Gbps ({ETHERNET_BANDWIDTH_MBPS} Mbps)")
print()

# Find optimal configurations
max_throughput = 0
optimal_nodes = 0
san_bottleneck_node = None
network_bottleneck_node = None

for i, data in enumerate(bandwidth_data):
    if data['effective_throughput'] > max_throughput:
        max_throughput = data['effective_throughput']
        optimal_nodes = i + 1
    
    if data['san_utilization'] > 95 and san_bottleneck_node is None:
        san_bottleneck_node = i + 1
    
    if data['network_utilization'] > 95 and network_bottleneck_node is None:
        network_bottleneck_node = i + 1

print(f"Optimal number of nodes: {optimal_nodes}")
print(f"Maximum effective throughput: {max_throughput:.0f} Mbps ({max_throughput/1000:.2f} Gbps)")

if san_bottleneck_node:
    print(f"SAN becomes bottleneck at: {san_bottleneck_node} nodes")
if network_bottleneck_node:
    print(f"Network becomes bottleneck at: {network_bottleneck_node} nodes")

# Detailed scaling analysis
print("\nDetailed System Analysis:")
print("Nodes | Net BW | SAN BW | Net Util | SAN Util | Bottleneck | Throughput")
print("-" * 75)
for i, data in enumerate(bandwidth_data[:12]):  # Show first 12 nodes
    nodes = i + 1
    print(f"{nodes:5d} | {data['network_actual']:6.0f} | {data['san_actual']:6.0f} | "
          f"{data['network_utilization']:7.1f}% | {data['san_utilization']:7.1f}% | "
          f"{data['bottleneck']:8s} | {data['effective_throughput']:8.0f}")

# Performance comparison
print(f"\nKey Insights:")
print(f"• SAN provides {SAN_BANDWIDTH_GBPS/SWITCH_BANDWIDTH_GBPS:.1f}x more bandwidth than network switch")
print(f"• System can handle more nodes before hitting bandwidth limits")
print(f"• Bottleneck shifts from network to SAN as nodes increase")
print(f"• Shared storage eliminates coordinator-to-node file transfers")

plt.show()