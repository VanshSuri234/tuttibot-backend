#!/bin/bash
# SLURM Job Script for TuttiBot on ADA HPC
# Submit with: sbatch tuttibot_job.slurm

#SBATCH --job-name=tuttibot
#SBATCH --output=tuttibot_%j.out
#SBATCH --error=tuttibot_%j.err
#SBATCH --time=02:00:00                    # 2 hours max
#SBATCH --partition=gpu                    # or 'cpu' for CPU-only
#SBATCH --gres=gpu:1                       # Request 1 GPU (remove for CPU-only)
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=16G                          # 16GB RAM

# Load modules (adjust based on ADA's available modules)
module load python/3.10
module load gcc/9.3.0
module load cuda/11.8                      # Only if using GPU partition

# Set environment variables
export OMP_NUM_THREADS=$SLURM_CPUS_PER_TASK
export CUDA_VISIBLE_DEVICES=$SLURM_GPUS_ON_NODE

# Activate virtual environment
source tuttibot_env/bin/activate

# Change to work directory
cd $SLURM_SUBMIT_DIR

echo "=========================================="
echo "TUTTIBOT JOB STARTED"
echo "Job ID: $SLURM_JOB_ID"
echo "Node: $SLURM_NODELIST"
echo "GPUs: $CUDA_VISIBLE_DEVICES"
echo "CPUs: $SLURM_CPUS_PER_TASK"
echo "Memory: $SLURM_MEM_PER_NODE MB"
echo "=========================================="

# Check GPU availability
if command -v nvidia-smi &> /dev/null; then
    echo "GPU Information:"
    nvidia-smi --query-gpu=name,memory.total,utilization.gpu --format=csv,noheader,nounits
fi

# Run compatibility check first
echo "Running compatibility check..."
python hpc_compatibility_check.py

echo "----------------------------------------"
echo "RUNNING PROCESSING LAYER"
echo "----------------------------------------"

# Run processing layer
cd PROCESSING_LAYER
python processing_layer.py

echo "----------------------------------------"
echo "RUNNING EXTRACTION LAYER"
echo "----------------------------------------"

# Run extraction layer
cd ../EXTRACTION_LAYER
python extraction_layer.py

echo "=========================================="
echo "TUTTIBOT JOB COMPLETED"
echo "Check output files in shared_data/"
echo "=========================================="
