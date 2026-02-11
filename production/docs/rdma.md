# RDMA Support

High-performance networking with RDMA acceleration.

---

## What is RDMA?

Remote Direct Memory Access (RDMA) enables low-latency, high-throughput network communication between computers.

### Benefits

- **Low Latency**: Microsecond-scale communication
- **High Throughput**: Up to 200 Gbps per link
- **CPU Offload**: Direct memory access without CPU intervention
- **Scalability**: Perfect for distributed computing

---

## Supported Transport Protocols

Ollama CLI supports multiple RDMA transport protocols:

| Transport | Description | Speed | Use Case |
|-----------|-------------|-------|----------|
| **InfiniBand** | Native RDMA protocol | 100-200 Gbps | High-performance clusters |
| **RoCE v1** | RDMA over Converged Ethernet | 10-50 Gbps | Data center networks |
| **RoCE v2** | RDMA over UDP | 10-50 Gbps | Labeled subnet networks |
| **iWARP** | Internet Wide Area RDMA | 10-40 Gbps | Wide area networks |
| **USB<>RDMA** | USB-based adapter | 10 Gbps | External connectivity |
| **Thunderbolt<>RDMA** | Thunderbolt adapter | 40 Gbps | High-speed external |
| **Network<>RDMA** | TCP/IP fallback | Variable | General purpose |

---

## Supported Devices

### Mellanox ConnectX Series

- ConnectX-4: 25/40/50 Gbps
- ConnectX-5: 100/400 Gbps
- ConnectX-6: 100/200/400 Gbps

### Intel OPA Series

- E810-XXV: 100 Gbps
- E810-XXDA: 200 Gbps

### Cisco VIC Series

- VIC 1500 series: Up to 100 Gbps

---

## Installation

### Check if RDMA is Available

```bash
# Install rdma tools (Linux)
sudo apt install rdma-core
# or
sudo yum install rdma-core
```

### Detect RDMA Devices

```bash
ollama-cli rdma detect
```

Expected output:
```
Found RDMA devices:
  mlx5_0
    Type: network_rdma
    Transport: roce_v2
    Vendor: Mellanox
```

---

## Usage

### 1. Detect RDMA Devices

```bash
ollama-cli rdma detect
```

### 2. Check RDMA Status

```bash
ollama-cli rdma status
```

### 3. Connect to RDMA Device

```bash
ollama-cli rdma connect mlx5_0
```

### 4. Check Acceleration Status

```bash
ollama-cli accelerate check
```

### 5. Enable RDMA Acceleration

```bash
ollama-cli accelerate enable rdma
```

---

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `RDMA_DEVICE` | `mlx5_0` | Default RDMA device |
| `RDMA_QP_TYPE` | `RC` | Queue pair type (RC=Reliable Connected) |
| `RDMA_MTU` | `4096` | Maximum transmission unit |
| `RDMA_TIMEOUT` | `14` | Timeout exponent |

### Configuration Files

Create `~/.ollama/rdma/config.json`:

```json
{
  "devices": [
    {
      "name": "mlx5_0",
      "transport": "roce_v2",
      "mtu": 4096,
      "enabled": true
    }
  ],
  "cluster": {
    "name": "default",
    "leader": "192.168.1.100"
  }
}
```

---

## Performance Tuning

### Adjust MTU

```bash
# Set larger MTU for better throughput
rdma link set mlx5_0 mtu 4096
```

### Enable Jumbo Frames

```bash
# For networks supporting jumbo frames
sudo ip link set eth0 mtu 9000
```

### Configure Queue Pair

```bash
# Create queue pair
rdma qp add mlx5_0 qp-type rc
```

---

## Cluster Setup

### 1. Identify Cluster Members

```bash
# On leader node
ollama-cli exo discover
```

### 2. Configure Cluster

```bash
# Leader node
ollama-cli exo configure --leader

# Worker nodes
ollama-cli exo configure --worker --leader <leader-ip>
```

### 3. Connect Cluster via RDMA

```bash
# Enable cluster RDMA
ollama-cli rdma connect --cluster
```

---

## Troubleshooting

### "RDMA device not found"

```bash
# Check available devices
rdma link show

# Verify kernel module is loaded
lsmod | grep mlx5
```

### "Connection refused" on RDMA

```bash
# Check RDMA port state
rdma link show <device>

# Verify firewall settings
sudo iptables -L
```

### Low throughput

```bash
# Check link speed
cat /sys/class/infiniband/mlx5_0/device/speed

# Check for errors
cat /sys/class/infiniband/mlx5_0/device/errors
```

---

## Best Practices

1. **Use RDMA for local clusters**
   - Best for same-rack communication
   - Not ideal for cross-datacenter

2. **Enable jumbo frames**
   - Set MTU to 9000 on all network interfaces
   - Verify end-to-end support

3. **Monitor RDMA statistics**
   ```bash
   cat /sys/class/infiniband/mlx5_0/ports/1/counters/px_rx_data
   ```

4. **Load balancing**
   - Distribute workload across multiple RDMA devices
   - Use cluster mode for multi-node setups

---

## Related Documentation

- [CLI Reference](cli_reference.md)
- [High-Performance Computing](../README.md#high-performance-computing)
- [Getting Started](getting_started.md)
