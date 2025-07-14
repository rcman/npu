import matplotlib.pyplot as plt
import numpy as np

# Network specifications
SWITCH_BANDWIDTH_GBPS = 2.5  # 2.5 Gbps switch
ETHERNET_BANDWIDTH_GBPS = 2.5  # 2.5 Gb ethernet per connection
SWITCH_BANDWIDTH_MBPS = SWITCH_BANDWIDTH_GBPS * 1000  # Convert to Mbps
ETHERNET_BANDWIDTH_MBPS = ETHERNET_BANDWIDTH_GBPS * 1000

# Distcc traffic characteristics
# Typical distcc workflow: source files out, object files back
# Source files are smaller, object files are larger
# Assume 70% of traffic is outbound (object files), 30% inbound (source files)
SOURCE_TO_OBJECT_RATIO = 0.3  # Source files are ~30% of total traffic
COMPILATION_EFFICIENCY = 0.85  # Not 100% efficient due to coordination overhead

def calculate_bandwidth_usage(num_nodes):
    """Calculate bandwidth usage for given number of nodes"""
    
    # Each node needs bidirectional communication with the coordinator
    # Outbound: source files to nodes
    # Inbound: compiled object files from nodes
    
    # Per-node bandwidth requirement (assuming optimal distribution)
    per_node_outbound = 150  # Mbps (source files to node)
    per_node_inbound = 350   # Mbps (object files from node)
    
    # Total bandwidth requirements
    total_outbound = per_node_outbound * num_nodes
    total_inbound = per_node_inbound * num_nodes
    total_bandwidth = total_outbound + total_inbound
    
    # Apply efficiency factor
    effective_bandwidth = total_bandwidth * COMPILATION_EFFICIENCY
    
    # Network limitations
    # Each node is limited by its ethernet connection
    max_per_node = ETHERNET_BANDWIDTH_MBPS * 0.8  # 80% utilization for stability
    theoretical_max = max_per_node * num_nodes
    
    # Switch becomes bottleneck when aggregate exceeds switch capacity
    switch_limit = SWITCH_BANDWIDTH_MBPS * 0.8  # 80% utilization
    
    # Actual bandwidth is limited by the most restrictive factor
    actual_bandwidth = min(effective_bandwidth, theoretical_max, switch_limit)
    
    return {
        'requested': effective_bandwidth,
        'actual': actual_bandwidth,
        'switch_limited': actual_bandwidth >= switch_limit * 0.95,
        'efficiency': actual_bandwidth / effective_bandwidth if effective_bandwidth > 0 else 0
    }

# Generate data for different node counts
node_counts = range(1, 21)  # 1 to 20 nodes
bandwidth_data = [calculate_bandwidth_usage(n) for n in node_counts]

# Extract data for plotting
requested_bandwidth = [data['requested'] for data in bandwidth_data]
actual_bandwidth = [data['actual'] for data in bandwidth_data]
efficiency = [data['efficiency'] * 100 for data in bandwidth_data]

# Create the plots
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))

# Plot 1: Bandwidth Usage
ax1.plot(node_counts, requested_bandwidth, 'b--', label='Requested Bandwidth', linewidth=2)
ax1.plot(node_counts, actual_bandwidth, 'r-', label='Actual Bandwidth', linewidth=2)
ax1.axhline(y=SWITCH_BANDWIDTH_MBPS, color='orange', linestyle=':', 
            label=f'Switch Limit ({SWITCH_BANDWIDTH_GBPS} Gbps)', linewidth=2)
ax1.axhline(y=ETHERNET_BANDWIDTH_MBPS, color='green', linestyle=':', 
            label=f'Single Ethernet ({ETHERNET_BANDWIDTH_GBPS} Gbps)', linewidth=2)

ax1.set_xlabel('Number of Nodes')
ax1.set_ylabel('Bandwidth (Mbps)')
ax1.set_title('Distcc Network Bandwidth Usage vs Number of Nodes')
ax1.legend()
ax1.grid(True, alpha=0.3)
ax1.set_ylim(0, 3000)

# Add annotations for key points
# Find where switch becomes limiting factor
switch_limit_node = None
for i, data in enumerate(bandwidth_data):
    if data['switch_limited']:
        switch_limit_node = i + 1
        break

if switch_limit_node:
    ax1.annotate(f'Switch becomes bottleneck\nat {switch_limit_node} nodes', 
                xy=(switch_limit_node, actual_bandwidth[switch_limit_node-1]), 
                xytext=(switch_limit_node + 3, actual_bandwidth[switch_limit_node-1] + 200),
                arrowprops=dict(arrowstyle='->', color='red'))

# Plot 2: Network Efficiency
ax2.plot(node_counts, efficiency, 'g-', linewidth=2, marker='o', markersize=4)
ax2.set_xlabel('Number of Nodes')
ax2.set_ylabel('Network Efficiency (%)')
ax2.set_title('Network Efficiency vs Number of Nodes')
ax2.grid(True, alpha=0.3)
ax2.set_ylim(0, 105)

# Add efficiency annotations
ax2.axhline(y=100, color='gray', linestyle='--', alpha=0.5)
ax2.text(15, 95, 'Ideal Efficiency', fontsize=10, alpha=0.7)

plt.tight_layout()

# Print some statistics
print("Distcc Network Analysis Summary:")
print(f"Switch Capacity: {SWITCH_BANDWIDTH_GBPS} Gbps ({SWITCH_BANDWIDTH_MBPS} Mbps)")
print(f"Ethernet per node: {ETHERNET_BANDWIDTH_GBPS} Gbps ({ETHERNET_BANDWIDTH_MBPS} Mbps)")
print()

# Key findings
optimal_nodes = 0
max_actual = 0
for i, data in enumerate(bandwidth_data):
    if data['actual'] > max_actual:
        max_actual = data['actual']
        optimal_nodes = i + 1

print(f"Optimal number of nodes: {optimal_nodes}")
print(f"Maximum actual bandwidth: {max_actual:.0f} Mbps ({max_actual/1000:.2f} Gbps)")
print(f"Network efficiency at optimal: {bandwidth_data[optimal_nodes-1]['efficiency']*100:.1f}%")

if switch_limit_node:
    print(f"Switch becomes bottleneck at: {switch_limit_node} nodes")
    print(f"Bandwidth utilization at bottleneck: {actual_bandwidth[switch_limit_node-1]:.0f} Mbps")

plt.show()

# Additional analysis: Cost-benefit of adding nodes
print("\nNode scaling analysis:")
print("Nodes | Actual BW (Mbps) | Efficiency (%) | BW per Node (Mbps)")
print("-" * 65)
for i, data in enumerate(bandwidth_data[:10]):  # Show first 10 nodes
    nodes = i + 1
    bw_per_node = data['actual'] / nodes
    print(f"{nodes:5d} | {data['actual']:13.0f} | {data['efficiency']*100:11.1f} | {bw_per_node:14.0f}")