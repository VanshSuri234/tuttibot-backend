#!/usr/bin/env python3
"""
GPU Manager for TuttiBot v02 - Temporal Alignment Pipeline
==========================================================

Comprehensive GPU detection, management, and fallback system that works
on both local systems and HPC environments like IIIT-H Ada.

Features:
- Automatic GPU detection (CUDA/TensorFlow)
- CPU fallback with warning messages
- SLURM/HPC environment detection
- GPU memory monitoring and cleanup
- Command-line GPU control options
- Multi-GPU support with selection

Author: TuttiBot Team
Version: 2.0.1
"""

import os
import sys
import logging
import subprocess
import psutil
from typing import Dict, List, Optional, Tuple
import warnings

# Suppress TensorFlow warnings during import
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
warnings.filterwarnings('ignore', category=FutureWarning)

try:
    import tensorflow as tf
    tf.get_logger().setLevel('ERROR')
    HAS_TENSORFLOW = True
except ImportError:
    tf = None
    HAS_TENSORFLOW = False

try:
    import torch
    HAS_PYTORCH = True
except ImportError:
    torch = None
    HAS_PYTORCH = False

class GPUManager:
    """Comprehensive GPU management for TuttiBot pipeline"""
    
    def __init__(self, force_cpu: bool = False, gpu_id: Optional[int] = None):
        """
        Initialize GPU Manager
        
        Args:
            force_cpu: Force CPU-only mode
            gpu_id: Specific GPU ID to use (None for auto-select)
        """
        self.force_cpu = force_cpu
        self.requested_gpu_id = gpu_id
        self.current_device = None
        self.environment_info = self._detect_environment()
        self.gpu_info = self._detect_gpus()
        self.device_config = self._configure_device()
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
        
    def _detect_environment(self) -> Dict:
        """Detect if running on HPC/SLURM vs local system"""
        env_info = {
            'is_hpc': False,
            'is_slurm': False,
            'slurm_job_id': None,
            'slurm_node': None,
            'available_cpus': psutil.cpu_count(),
            'total_memory_gb': round(psutil.virtual_memory().total / (1024**3), 2)
        }
        
        # Check for SLURM environment
        if 'SLURM_JOB_ID' in os.environ:
            env_info['is_hpc'] = True
            env_info['is_slurm'] = True
            env_info['slurm_job_id'] = os.environ.get('SLURM_JOB_ID')
            env_info['slurm_node'] = os.environ.get('SLURM_NODELIST')
            env_info['slurm_cpus'] = os.environ.get('SLURM_CPUS_PER_TASK')
            env_info['slurm_mem'] = os.environ.get('SLURM_MEM_PER_NODE')
        
        # Check for other HPC indicators
        elif any(indicator in os.environ for indicator in ['PBS_JOBID', 'LSB_JOBID', 'JOB_ID']):
            env_info['is_hpc'] = True
        
        return env_info
    
    def _detect_gpus(self) -> Dict:
        """Detect available GPUs and their capabilities"""
        gpu_info = {
            'has_cuda': False,
            'cuda_version': None,
            'tensorflow_gpus': [],
            'pytorch_gpus': [],
            'nvidia_smi_available': False,
            'gpu_count': 0,
            'gpu_details': []
        }
        
        # Check NVIDIA-SMI availability
        try:
            result = subprocess.run(['nvidia-smi', '--query-gpu=name,memory.total,memory.free', 
                                   '--format=csv,noheader,nounits'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                gpu_info['nvidia_smi_available'] = True
                lines = result.stdout.strip().split('\n')
                for i, line in enumerate(lines):
                    if line.strip():
                        parts = line.split(', ')
                        if len(parts) >= 3:
                            gpu_info['gpu_details'].append({
                                'id': i,
                                'name': parts[0].strip(),
                                'total_memory_mb': int(parts[1]),
                                'free_memory_mb': int(parts[2])
                            })
                gpu_info['gpu_count'] = len(gpu_info['gpu_details'])
        except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
            pass
        
        # Check TensorFlow GPU support
        if HAS_TENSORFLOW:
            try:
                tf_gpus = tf.config.list_physical_devices('GPU')
                gpu_info['tensorflow_gpus'] = tf_gpus
                if tf_gpus:
                    gpu_info['has_cuda'] = True
                    # Try to get CUDA version
                    try:
                        gpu_info['cuda_version'] = tf.test.gpu_device_name()
                    except:
                        pass
            except Exception:
                pass
        
        # Check PyTorch GPU support
        if HAS_PYTORCH:
            try:
                if torch.cuda.is_available():
                    gpu_info['has_cuda'] = True
                    gpu_info['pytorch_gpus'] = [torch.cuda.get_device_name(i) 
                                              for i in range(torch.cuda.device_count())]
                    if not gpu_info['gpu_count']:
                        gpu_info['gpu_count'] = torch.cuda.device_count()
            except Exception:
                pass
        
        return gpu_info
    
    def _configure_device(self) -> Dict:
        """Configure the device based on detection and user preferences"""
        config = {
            'use_gpu': False,
            'device_type': 'cpu',
            'device_id': None,
            'tf_device': '/CPU:0',
            'torch_device': 'cpu',
            'memory_limit_mb': None
        }
        
        # Force CPU mode
        if self.force_cpu:
            return config
        
        # No GPUs available
        if not self.gpu_info['has_cuda'] or self.gpu_info['gpu_count'] == 0:
            return config
        
        # Configure GPU
        config['use_gpu'] = True
        config['device_type'] = 'gpu'
        
        # Select GPU ID
        if self.requested_gpu_id is not None:
            if self.requested_gpu_id < self.gpu_info['gpu_count']:
                config['device_id'] = self.requested_gpu_id
            else:
                self.logger.warning(f"Requested GPU {self.requested_gpu_id} not available. Using GPU 0.")
                config['device_id'] = 0
        else:
            # Auto-select GPU with most free memory
            if self.gpu_info['gpu_details']:
                best_gpu = max(self.gpu_info['gpu_details'], 
                             key=lambda x: x['free_memory_mb'])
                config['device_id'] = best_gpu['id']
            else:
                config['device_id'] = 0
        
        # Set device strings
        config['tf_device'] = f'/GPU:{config["device_id"]}'
        config['torch_device'] = f'cuda:{config["device_id"]}'
        
        return config
    
    def setup_tensorflow(self) -> bool:
        """Setup TensorFlow with appropriate device configuration"""
        if not HAS_TENSORFLOW:
            return False
        
        try:
            if self.device_config['use_gpu']:
                # Configure GPU memory growth to avoid OOM
                gpus = tf.config.experimental.list_physical_devices('GPU')
                if gpus:
                    try:
                        for gpu in gpus:
                            tf.config.experimental.set_memory_growth(gpu, True)
                        
                        # Set visible devices
                        if self.device_config['device_id'] is not None:
                            tf.config.experimental.set_visible_devices(
                                gpus[self.device_config['device_id']], 'GPU'
                            )
                        
                        self.logger.info(f"TensorFlow configured for GPU {self.device_config['device_id']}")
                        return True
                    except RuntimeError as e:
                        self.logger.warning(f"GPU setup failed: {e}")
                        return False
            else:
                # Force CPU mode
                tf.config.experimental.set_visible_devices([], 'GPU')
                self.logger.info("TensorFlow configured for CPU mode")
                return True
        except Exception as e:
            self.logger.error(f"TensorFlow setup error: {e}")
            return False
    
    def setup_pytorch(self) -> bool:
        """Setup PyTorch with appropriate device configuration"""
        if not HAS_PYTORCH:
            return False
        
        try:
            if self.device_config['use_gpu'] and torch.cuda.is_available():
                torch.cuda.set_device(self.device_config['device_id'])
                self.logger.info(f"PyTorch configured for GPU {self.device_config['device_id']}")
                return True
            else:
                self.logger.info("PyTorch configured for CPU mode")
                return True
        except Exception as e:
            self.logger.error(f"PyTorch setup error: {e}")
            return False
    
    def get_device_info(self) -> Dict:
        """Get comprehensive device information"""
        return {
            'environment': self.environment_info,
            'gpu_detection': self.gpu_info,
            'device_config': self.device_config,
            'libraries': {
                'tensorflow': HAS_TENSORFLOW,
                'pytorch': HAS_PYTORCH
            }
        }
    
    def print_status(self):
        """Print comprehensive GPU/environment status"""
        print("\n" + "=" * 70)
        print("🖥️  TuttiBot v02 - System & GPU Status")
        print("=" * 70)
        
        # Environment info
        print("📍 ENVIRONMENT:")
        if self.environment_info['is_slurm']:
            print(f"   🏢 Running on HPC/SLURM")
            print(f"   🔢 Job ID: {self.environment_info['slurm_job_id']}")
            print(f"   🖥️  Node: {self.environment_info['slurm_node']}")
            print(f"   ⚙️  SLURM CPUs: {self.environment_info.get('slurm_cpus', 'N/A')}")
            print(f"   💾 SLURM Memory: {self.environment_info.get('slurm_mem', 'N/A')}")
        elif self.environment_info['is_hpc']:
            print(f"   🏢 Running on HPC environment")
        else:
            print(f"   🏠 Running on local system")
        
        print(f"   💻 Available CPUs: {self.environment_info['available_cpus']}")
        print(f"   💾 Total Memory: {self.environment_info['total_memory_gb']} GB")
        
        # GPU info
        print("\n🎮 GPU STATUS:")
        if self.force_cpu:
            print("   ⚠️  CPU-only mode forced via --cpu-only flag")
        elif not self.gpu_info['has_cuda']:
            print("   ⚠️  No GPU detected, switching to CPU")
        elif self.gpu_info['gpu_count'] == 0:
            print("   ⚠️  No GPUs available, switching to CPU")
        else:
            print(f"   ✅ GPU acceleration enabled")
            print(f"   🎯 Using GPU {self.device_config['device_id']}")
            print(f"   🔢 Total GPUs detected: {self.gpu_info['gpu_count']}")
            
            # Show GPU details
            for gpu in self.gpu_info['gpu_details']:
                status = "🎯 [SELECTED]" if gpu['id'] == self.device_config['device_id'] else ""
                print(f"      GPU {gpu['id']}: {gpu['name']} "
                      f"({gpu['free_memory_mb']}/{gpu['total_memory_mb']} MB free) {status}")
        
        # Library status
        print("\n📚 LIBRARIES:")
        print(f"   TensorFlow: {'✅ Available' if HAS_TENSORFLOW else '❌ Not installed'}")
        print(f"   PyTorch: {'✅ Available' if HAS_PYTORCH else '❌ Not installed'}")
        
        print("=" * 70 + "\n")
    
    def monitor_gpu_memory(self) -> Optional[Dict]:
        """Monitor GPU memory usage"""
        if not self.device_config['use_gpu'] or not self.gpu_info['nvidia_smi_available']:
            return None
        
        try:
            result = subprocess.run([
                'nvidia-smi', '--query-gpu=memory.used,memory.total,utilization.gpu',
                '--format=csv,noheader,nounits', f'--id={self.device_config["device_id"]}'
            ], capture_output=True, text=True, timeout=5)
            
            if result.returncode == 0:
                parts = result.stdout.strip().split(', ')
                if len(parts) >= 3:
                    return {
                        'used_memory_mb': int(parts[0]),
                        'total_memory_mb': int(parts[1]),
                        'gpu_utilization_percent': int(parts[2]),
                        'memory_utilization_percent': round(int(parts[0]) / int(parts[1]) * 100, 1)
                    }
        except Exception:
            pass
        
        return None
    
    def cleanup_gpu_memory(self):
        """Cleanup GPU memory"""
        try:
            if HAS_TENSORFLOW and self.device_config['use_gpu']:
                # Clear TensorFlow session
                tf.keras.backend.clear_session()
                
            if HAS_PYTORCH and self.device_config['use_gpu']:
                # Clear PyTorch cache
                torch.cuda.empty_cache()
                
            self.logger.info("GPU memory cleaned up")
        except Exception as e:
            self.logger.warning(f"GPU cleanup warning: {e}")
    
    def get_optimal_batch_size(self, base_batch_size: int = 32) -> int:
        """Get optimal batch size based on available GPU memory"""
        if not self.device_config['use_gpu']:
            return max(1, base_batch_size // 4)  # Smaller batches for CPU
        
        memory_info = self.monitor_gpu_memory()
        if memory_info:
            free_memory_gb = (memory_info['total_memory_mb'] - memory_info['used_memory_mb']) / 1024
            if free_memory_gb < 2:
                return max(1, base_batch_size // 4)
            elif free_memory_gb < 4:
                return max(1, base_batch_size // 2)
            else:
                return base_batch_size
        
        return base_batch_size

def create_gpu_manager(force_cpu: bool = False, gpu_id: Optional[int] = None) -> GPUManager:
    """Factory function to create GPU manager"""
    return GPUManager(force_cpu=force_cpu, gpu_id=gpu_id)

# Convenience functions for backward compatibility
def is_gpu_available() -> bool:
    """Check if GPU is available"""
    manager = GPUManager()
    return manager.device_config['use_gpu']

def get_device_string(framework: str = 'tensorflow') -> str:
    """Get device string for specified framework"""
    manager = GPUManager()
    if framework.lower() == 'tensorflow':
        return manager.device_config['tf_device']
    elif framework.lower() == 'pytorch':
        return manager.device_config['torch_device']
    else:
        return 'cpu'

if __name__ == '__main__':
    # Demo/test the GPU manager
    import argparse
    
    parser = argparse.ArgumentParser(description='GPU Manager Test')
    parser.add_argument('--cpu-only', action='store_true', help='Force CPU-only mode')
    parser.add_argument('--gpu-id', type=int, help='Specific GPU ID to use')
    
    args = parser.parse_args()
    
    manager = GPUManager(force_cpu=args.cpu_only, gpu_id=args.gpu_id)
    manager.print_status()
    
    # Test memory monitoring
    memory_info = manager.monitor_gpu_memory()
    if memory_info:
        print("🔍 GPU Memory Status:")
        print(f"   Used: {memory_info['used_memory_mb']} MB")
        print(f"   Total: {memory_info['total_memory_mb']} MB")
        print(f"   Utilization: {memory_info['memory_utilization_percent']}%")
