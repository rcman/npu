Here are the key insights that change everything:
Linux NPU Driver Support is Robust:

Intel NPU drivers work great on Linux with Level Zero API
AMD XDNA drivers support NPU access on AMD processors
RISC-V systems can run NPU-enabled applications through emerging AI acceleration solutions
All NPUs are accessible through standard Linux device interfaces (/dev/accel/accel0, etc.)

Proven Software Architectures Exist:

OpenVINO Model Server can expose Intel NPUs via gRPC/REST APIs
llama.cpp RPC architecture enables distributed inference with rpc-server workers
LocalAI's P2P federated mode provides automatic discovery and load balancing
Custom gRPC services offer maximum flexibility for your specific needs

Your Architecture is Highly Feasible:

Each machine runs a Linux NPU service daemon exposing the local NPU
Master system acts as coordinator/load balancer over WiFi-7
Cross-architecture communication works through standardized APIs
No special hardware needed - just applications accessing NPU device files

Recommended Implementation Path:

Start with OpenVINO Model Server for Intel NPUs
Create custom gRPC services for AMD/RISC-V NPUs
Implement master coordinator with service discovery
Add load balancing and fault tolerance
Optimize for WiFi-7 performance

This is a much more practical approach than trying to access NPUs remotely at the hardware level. You're essentially building a distributed AI inference cluster using proven software patterns!
