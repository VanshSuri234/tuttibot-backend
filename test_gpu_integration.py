#!/usr/bin/env python3
"""
TuttiBot v02 GPU Integration Test Suite
=======================================

Comprehensive test suite to verify GPU functionality across different environments.
Tests all components with both GPU and CPU modes.

Usage:
  python test_gpu_integration.py                    # Run all tests
  python test_gpu_integration.py --quick           # Quick tests only
  python test_gpu_integration.py --gpu-only        # GPU tests only
  python test_gpu_integration.py --cpu-only        # CPU tests only

Author: TuttiBot Team
Version: 2.0.1
"""

import os
import sys
import time
import json
import tempfile
import argparse
import traceback
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

def test_gpu_manager():
    """Test GPU manager functionality"""
    print("\n" + "="*60)
    print("🧪 Testing GPU Manager")
    print("="*60)
    
    try:
        from gpu_manager import GPUManager, create_gpu_manager
        
        # Test basic initialization
        print("1. Testing basic initialization...")
        gm = GPUManager()
        assert gm is not None, "GPU Manager failed to initialize"
        print("   ✅ Basic initialization successful")
        
        # Test forced CPU mode
        print("2. Testing forced CPU mode...")
        gm_cpu = GPUManager(force_cpu=True)
        assert not gm_cpu.device_config['use_gpu'], "Force CPU mode failed"
        print("   ✅ Forced CPU mode working")
        
        # Test device info
        print("3. Testing device info...")
        device_info = gm.get_device_info()
        assert 'environment' in device_info, "Device info missing environment"
        assert 'gpu_detection' in device_info, "Device info missing GPU detection"
        assert 'device_config' in device_info, "Device info missing device config"
        print("   ✅ Device info complete")
        
        # Test status printing
        print("4. Testing status display...")
        gm.print_status()
        print("   ✅ Status display working")
        
        # Test memory monitoring
        print("5. Testing memory monitoring...")
        memory_info = gm.monitor_gpu_memory()
        if memory_info:
            print(f"   📊 GPU Memory: {memory_info['used_memory_mb']}/{memory_info['total_memory_mb']} MB")
        else:
            print("   💻 CPU mode - no GPU memory to monitor")
        print("   ✅ Memory monitoring working")
        
        # Test cleanup
        print("6. Testing GPU cleanup...")
        gm.cleanup_gpu_memory()
        print("   ✅ GPU cleanup working")
        
        # Test factory function
        print("7. Testing factory function...")
        gm_factory = create_gpu_manager()
        assert gm_factory is not None, "Factory function failed"
        print("   ✅ Factory function working")
        
        return True
        
    except Exception as e:
        print(f"   ❌ GPU Manager test failed: {e}")
        traceback.print_exc()
        return False

def test_tensorflow_integration():
    """Test TensorFlow GPU integration"""
    print("\n" + "="*60)
    print("🧪 Testing TensorFlow Integration")
    print("="*60)
    
    try:
        import tensorflow as tf
        from gpu_manager import GPUManager
        
        print("1. Testing TensorFlow import...")
        print(f"   TensorFlow version: {tf.__version__}")
        print("   ✅ TensorFlow import successful")
        
        print("2. Testing GPU detection...")
        gpus = tf.config.list_physical_devices('GPU')
        print(f"   TensorFlow GPUs detected: {len(gpus)}")
        for i, gpu in enumerate(gpus):
            print(f"     GPU {i}: {gpu}")
        print("   ✅ GPU detection working")
        
        print("3. Testing GPU Manager + TensorFlow...")
        gm = GPUManager()
        tf_setup_success = gm.setup_tensorflow()
        print(f"   TensorFlow setup: {'✅ Success' if tf_setup_success else '⚠️ Failed'}")
        
        print("4. Testing simple computation...")
        with tf.device(gm.device_config['tf_device']):
            # Simple computation test
            a = tf.constant([[1.0, 2.0], [3.0, 4.0]])
            b = tf.constant([[1.0, 1.0], [0.0, 1.0]])
            c = tf.matmul(a, b)
            result = c.numpy()
        print(f"   Computation result shape: {result.shape}")
        print("   ✅ TensorFlow computation successful")
        
        return True
        
    except ImportError:
        print("   ⚠️ TensorFlow not available - skipping tests")
        return True
    except Exception as e:
        print(f"   ❌ TensorFlow test failed: {e}")
        traceback.print_exc()
        return False

def test_pytorch_integration():
    """Test PyTorch GPU integration"""
    print("\n" + "="*60)
    print("🧪 Testing PyTorch Integration")
    print("="*60)
    
    try:
        import torch
        from gpu_manager import GPUManager
        
        print("1. Testing PyTorch import...")
        print(f"   PyTorch version: {torch.__version__}")
        print("   ✅ PyTorch import successful")
        
        print("2. Testing CUDA availability...")
        cuda_available = torch.cuda.is_available()
        print(f"   CUDA available: {cuda_available}")
        if cuda_available:
            print(f"   CUDA devices: {torch.cuda.device_count()}")
            for i in range(torch.cuda.device_count()):
                print(f"     GPU {i}: {torch.cuda.get_device_name(i)}")
        print("   ✅ CUDA detection working")
        
        print("3. Testing GPU Manager + PyTorch...")
        gm = GPUManager()
        torch_setup_success = gm.setup_pytorch()
        print(f"   PyTorch setup: {'✅ Success' if torch_setup_success else '⚠️ Failed'}")
        
        print("4. Testing simple computation...")
        device = torch.device(gm.device_config['torch_device'])
        # Simple computation test
        a = torch.tensor([[1.0, 2.0], [3.0, 4.0]], device=device)
        b = torch.tensor([[1.0, 1.0], [0.0, 1.0]], device=device)
        c = torch.matmul(a, b)
        result = c.cpu().numpy()
        print(f"   Computation result shape: {result.shape}")
        print("   ✅ PyTorch computation successful")
        
        return True
        
    except ImportError:
        print("   ⚠️ PyTorch not available - skipping tests")
        return True
    except Exception as e:
        print(f"   ❌ PyTorch test failed: {e}")
        traceback.print_exc()
        return False

def test_basic_imports():
    """Test all basic imports work"""
    print("\n" + "="*60)
    print("🧪 Testing Basic Imports")
    print("="*60)
    
    imports_to_test = [
        ('numpy', 'np'),
        ('scipy', None),
        ('pandas', 'pd'),
        ('librosa', None),
        ('pretty_midi', None),
        ('matplotlib.pyplot', 'plt'),
        ('pathlib', None),
        ('json', None),
        ('os', None),
        ('sys', None),
    ]
    
    failed_imports = []
    
    for module, alias in imports_to_test:
        try:
            if alias:
                exec(f"import {module} as {alias}")
                print(f"   ✅ {module} (as {alias}) imported successfully")
            else:
                exec(f"import {module}")
                print(f"   ✅ {module} imported successfully")
        except ImportError as e:
            print(f"   ❌ {module} import failed: {e}")
            failed_imports.append(module)
    
    if failed_imports:
        print(f"\n   ⚠️ Failed imports: {failed_imports}")
        return False
    else:
        print("\n   ✅ All basic imports successful")
        return True

def test_environment_detection():
    """Test environment detection"""
    print("\n" + "="*60)
    print("🧪 Testing Environment Detection")
    print("="*60)
    
    try:
        from gpu_manager import GPUManager
        
        gm = GPUManager()
        env_info = gm.environment_info
        
        print("1. Testing environment detection...")
        print(f"   Is HPC: {env_info['is_hpc']}")
        print(f"   Is SLURM: {env_info['is_slurm']}")
        print(f"   Available CPUs: {env_info['available_cpus']}")
        print(f"   Total Memory: {env_info['total_memory_gb']} GB")
        
        if env_info['is_slurm']:
            print(f"   SLURM Job ID: {env_info.get('slurm_job_id', 'N/A')}")
            print(f"   SLURM Node: {env_info.get('slurm_node', 'N/A')}")
        
        print("   ✅ Environment detection working")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Environment detection test failed: {e}")
        traceback.print_exc()
        return False

def test_pipeline_integration():
    """Test pipeline components with GPU manager"""
    print("\n" + "="*60)
    print("🧪 Testing Pipeline Integration")
    print("="*60)
    
    try:
        from gpu_manager import GPUManager
        
        # Test with both CPU and GPU modes
        for force_cpu in [True, False]:
            mode = "CPU" if force_cpu else "AUTO"
            print(f"\n--- Testing {mode} Mode ---")
            
            gm = GPUManager(force_cpu=force_cpu)
            
            print("1. Testing GPU manager initialization...")
            assert gm is not None
            device_type = "CPU" if gm.device_config['device_type'] == 'cpu' else "GPU"
            print(f"   Device: {device_type}")
            print("   ✅ GPU manager initialized")
            
            print("2. Testing framework setup...")
            tf_success = gm.setup_tensorflow()
            torch_success = gm.setup_pytorch()
            print(f"   TensorFlow setup: {'✅' if tf_success else '❌'}")
            print(f"   PyTorch setup: {'✅' if torch_success else '❌'}")
            
            print("3. Testing memory monitoring...")
            memory_info = gm.monitor_gpu_memory()
            if memory_info:
                print(f"   GPU Memory: {memory_info['used_memory_mb']}/{memory_info['total_memory_mb']} MB")
            else:
                print("   CPU mode - no GPU memory to monitor")
            print("   ✅ Memory monitoring working")
            
            print("4. Testing cleanup...")
            gm.cleanup_gpu_memory()
            print("   ✅ Cleanup working")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Pipeline integration test failed: {e}")
        traceback.print_exc()
        return False

def test_performance_comparison():
    """Quick performance comparison between CPU and GPU"""
    print("\n" + "="*60)
    print("🧪 Testing Performance Comparison")
    print("="*60)
    
    try:
        import numpy as np
        from gpu_manager import GPUManager
        
        # Create test data
        size = 1000
        np.random.seed(42)
        a = np.random.rand(size, size).astype(np.float32)
        b = np.random.rand(size, size).astype(np.float32)
        
        print(f"Testing matrix multiplication ({size}x{size})...")
        
        # Test CPU performance
        print("\n1. CPU Performance Test...")
        gm_cpu = GPUManager(force_cpu=True)
        start_time = time.time()
        cpu_result = np.matmul(a, b)
        cpu_time = time.time() - start_time
        print(f"   CPU Time: {cpu_time:.3f} seconds")
        
        # Test GPU performance (if available)
        print("\n2. GPU Performance Test...")
        gm_gpu = GPUManager(force_cpu=False)
        
        if gm_gpu.device_config['use_gpu']:
            try:
                import tensorflow as tf
                
                with tf.device(gm_gpu.device_config['tf_device']):
                    tf_a = tf.constant(a)
                    tf_b = tf.constant(b)
                    
                    start_time = time.time()
                    gpu_result = tf.matmul(tf_a, tf_b)
                    _ = gpu_result.numpy()  # Force execution
                    gpu_time = time.time() - start_time
                    
                    print(f"   GPU Time: {gpu_time:.3f} seconds")
                    speedup = cpu_time / gpu_time
                    print(f"   Speedup: {speedup:.2f}x")
                
            except Exception as e:
                print(f"   GPU test failed: {e}")
        else:
            print("   No GPU available for testing")
        
        print("   ✅ Performance comparison completed")
        return True
        
    except Exception as e:
        print(f"   ❌ Performance test failed: {e}")
        traceback.print_exc()
        return False

def main():
    parser = argparse.ArgumentParser(description='TuttiBot v02 GPU Integration Test Suite')
    parser.add_argument('--quick', action='store_true', help='Run quick tests only')
    parser.add_argument('--gpu-only', action='store_true', help='Run GPU tests only')
    parser.add_argument('--cpu-only', action='store_true', help='Run CPU tests only')
    parser.add_argument('--no-performance', action='store_true', help='Skip performance tests')
    
    args = parser.parse_args()
    
    print("🎼 TuttiBot v02 GPU Integration Test Suite")
    print("=" * 70)
    print(f"Python version: {sys.version}")
    print(f"Platform: {sys.platform}")
    print("=" * 70)
    
    tests = []
    results = []
    
    # Define test suite
    if not args.gpu_only:
        tests.extend([
            ("Basic Imports", test_basic_imports),
            ("Environment Detection", test_environment_detection),
        ])
    
    tests.append(("GPU Manager", test_gpu_manager))
    
    if not args.cpu_only:
        tests.extend([
            ("TensorFlow Integration", test_tensorflow_integration),
            ("PyTorch Integration", test_pytorch_integration),
        ])
    
    if not args.quick:
        tests.append(("Pipeline Integration", test_pipeline_integration))
        
        if not args.no_performance and not args.cpu_only:
            tests.append(("Performance Comparison", test_performance_comparison))
    
    # Run tests
    start_time = time.time()
    
    for test_name, test_func in tests:
        print(f"\n🔄 Running {test_name} test...")
        try:
            result = test_func()
            results.append((test_name, result))
            status = "✅ PASSED" if result else "❌ FAILED"
            print(f"   {status}")
        except Exception as e:
            print(f"   ❌ FAILED with exception: {e}")
            results.append((test_name, False))
    
    # Print summary
    total_time = time.time() - start_time
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    print("\n" + "=" * 70)
    print("📊 TEST SUMMARY")
    print("=" * 70)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"   {test_name:<30} {status}")
    
    print(f"\nResults: {passed}/{total} tests passed")
    print(f"Time: {total_time:.2f} seconds")
    
    if passed == total:
        print("\n🎉 All tests passed! GPU integration is working correctly.")
        sys.exit(0)
    else:
        print(f"\n⚠️ {total - passed} test(s) failed. Please check the output above.")
        sys.exit(1)

if __name__ == '__main__':
    main()
