#!/usr/bin/env python3
# simple_rk3588_test.py - Test server for Orange Pi 5
import socket
import threading
import time
import numpy as np
import sys
import os

# Try to import RKNN
try:
    from rknnlite.api import RKNNLite
    RKNN_AVAILABLE = True
    print("✓ RKNN library imported successfully")
except ImportError as e:
    print(f"✗ RKNN library not available: {e}")
    print("Installing rknnlite...")
    os.system("pip3 install rknnlite")
    try:
        from rknnlite.api import RKNNLite
        RKNN_AVAILABLE = True
        print("✓ RKNN library installed and imported")
    except ImportError:
        RKNN_AVAILABLE = False
        print("✗ Could not install RKNN library")

class SimpleRK3588Server:
    def __init__(self, model_path=None):
        self.model_path = model_path
        self.rknn = None
        self.model_loaded = False
        
        if RKNN_AVAILABLE and model_path and os.path.exists(model_path):
            self.load_model()
        elif model_path:
            print(f"Model file not found: {model_path}")
        else:
            print("No model specified - running in test mode")
    
    def load_model(self):
        """Load RKNN model"""
        try:
            print(f"Loading model: {self.model_path}")
            self.rknn = RKNNLite()
            
            # Load RKNN model
            ret = self.rknn.load_rknn(self.model_path)
            if ret != 0:
                print(f"✗ Failed to load RKNN model! Error code: {ret}")
                return False
            
            # Initialize runtime
            print("Initializing NPU runtime...")
            ret = self.rknn.init_runtime()
            if ret != 0:
                print(f"✗ Failed to init NPU runtime! Error code: {ret}")
                return False
            
            self.model_loaded = True
            print("✓ Model loaded successfully!")
            return True
            
        except Exception as e:
            print(f"✗ Error loading model: {e}")
            return False
    
    def run_inference(self, input_data):
        """Run inference on input data"""
        if not self.model_loaded:
            # Simulate inference for testing
            print("Simulating inference (no model loaded)")
            time.sleep(0.1)  # Simulate processing time
            # Return dummy result
            return np.random.rand(1000).astype(np.float32).tobytes()
        
        try:
            # Convert input data to numpy array
            if isinstance(input_data, bytes):
                input_array = np.frombuffer(input_data, dtype=np.uint8)
            else:
                input_array = input_data
            
            print(f"Input data shape: {input_array.shape}")
            
            # For now, let's reshape to a common size (you'll need to adjust this)
            # This is just for testing - replace with your model's input shape
            try:
                input_array = input_array.reshape((1, 224, 224, 3))
            except:
                print("Warning: Could not reshape input, using as-is")
            
            # Run inference
            start_time = time.time()
            outputs = self.rknn.inference(inputs=[input_array])
            end_time = time.time()
            
            inference_time = (end_time - start_time) * 1000
            print(f"✓ Inference completed in {inference_time:.2f} ms")
            
            # Convert outputs to bytes
            if outputs and len(outputs) > 0:
                result_bytes = b''
                for output in outputs:
                    result_bytes += output.astype(np.float32).tobytes()
                return result_bytes
            else:
                print("No outputs from inference")
                return b''
                
        except Exception as e:
            print(f"✗ Inference error: {e}")
            return b''
    
    def handle_client(self, client_socket, client_address):
        """Handle client connection"""
        print(f"🔗 New client: {client_address}")
        
        try:
            # Receive data size
            size_data = client_socket.recv(4)
            if len(size_data) < 4:
                print("Failed to receive data size")
                return
            
            data_size = int.from_bytes(size_data, byteorder='little')
            print(f"📥 Expecting {data_size} bytes")
            
            # Receive input data
            input_data = b''
            while len(input_data) < data_size:
                chunk = client_socket.recv(min(8192, data_size - len(input_data)))
                if not chunk:
                    print("Client disconnected during transfer")
                    return
                input_data += chunk
                
                # Show progress for large transfers
                if len(input_data) % 10000 == 0:
                    progress = (len(input_data) / data_size) * 100
                    print(f"📥 Progress: {progress:.1f}%")
            
            print(f"✓ Received {len(input_data)} bytes")
            
            # Run inference
            print("🧠 Running NPU inference...")
            results = self.run_inference(input_data)
            
            if results:
                # Send result size
                result_size = len(results)
                client_socket.send(result_size.to_bytes(4, byteorder='little'))
                
                # Send results
                client_socket.send(results)
                print(f"📤 Sent {result_size} bytes back to client")
            else:
                # Send empty result
                client_socket.send((0).to_bytes(4, byteorder='little'))
                print("📤 Sent empty result (inference failed)")
                
        except Exception as e:
            print(f"✗ Error with client {client_address}: {e}")
        finally:
            client_socket.close()
            print(f"🔌 Client {client_address} disconnected")
    
    def start_server(self, host='0.0.0.0', port=8080):
        """Start the server"""
        print(f"🚀 Starting RK3588 NPU Server...")
        print(f"📍 Host: {host}:{port}")
        print(f"🧠 NPU Available: {RKNN_AVAILABLE}")
        print(f"📦 Model Loaded: {self.model_loaded}")
        
        # Create server socket
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        try:
            server_socket.bind((host, port))
            server_socket.listen(5)
            
            print(f"✅ Server listening on {host}:{port}")
            print("🔄 Waiting for clients...")
            print("Press Ctrl+C to stop")
            
            while True:
                try:
                    client_socket, client_address = server_socket.accept()
                    
                    # Handle each client in a separate thread
                    client_thread = threading.Thread(
                        target=self.handle_client,
                        args=(client_socket, client_address),
                        daemon=True
                    )
                    client_thread.start()
                    
                except KeyboardInterrupt:
                    print("\n🛑 Shutting down server...")
                    break
                except Exception as e:
                    print(f"Accept error: {e}")
                    
        except Exception as e:
            print(f"✗ Server error: {e}")
        finally:
            server_socket.close()
            if self.rknn:
                self.rknn.release()
            print("✅ Server stopped")

def test_npu_setup():
    """Test NPU hardware setup"""
    print("🔍 Testing NPU setup...")
    
    # Check device files
    import glob
    dri_devices = glob.glob('/dev/dri/renderD*')
    if dri_devices:
        print(f"✓ Found DRI devices: {dri_devices}")
    else:
        print("✗ No DRI devices found")
    
    # Check for NPU module
    try:
        with open('/proc/modules', 'r') as f:
            modules = f.read()
        if 'rknpu' in modules:
            print("✓ RKNPU kernel module loaded")
        else:
            print("✗ RKNPU kernel module not loaded")
    except:
        print("? Could not check kernel modules")
    
    # Check NPU version if available
    try:
        with open('/sys/kernel/debug/rknpu/version', 'r') as f:
            version = f.read().strip()
        print(f"✓ NPU version: {version}")
    except:
        print("? NPU version not available")

def main():
    print("=" * 50)
    print("🍊 Orange Pi 5 NPU Server Test")
    print("=" * 50)
    
    # Test NPU setup first
    test_npu_setup()
    print()
    
    if len(sys.argv) < 2:
        print("Usage: python3 simple_rk3588_test.py [model.rknn] [port]")
        print("Running in test mode without model...")
        model_path = None
    else:
        model_path = sys.argv[1]
    
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 8080
    
    try:
        server = SimpleRK3588Server(model_path)
        server.start_server(port=port)
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"✗ Fatal error: {e}")

if __name__ == "__main__":
    main()
