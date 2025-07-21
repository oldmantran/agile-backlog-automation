#!/usr/bin/env python3
"""
Optimize Ollama GPU settings for RTX 4090 to speed up 70B model performance.
"""

import requests
import json
import time
from datetime import datetime

def optimize_ollama_gpu():
    """Optimize Ollama GPU settings for RTX 4090."""
    
    print("🚀 Optimizing Ollama GPU Settings for RTX 4090")
    print("=" * 50)
    print(f"📅 Optimization started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # RTX 4090 has 24GB VRAM - we can load most of the 70B model in GPU memory
    optimized_config = {
        "num_gpu": 1,           # Use 1 GPU
        "num_thread": 16,       # Use 16 CPU threads for non-GPU layers
        "num_ctx": 4096,        # Context length of 4096 tokens
        "gpu_layers": 100,      # Load 100 layers on GPU (maximize GPU usage)
        "rope_freq_base": 10000,
        "rope_freq_scale": 0.5,
        "temperature": 0.7,
        "top_p": 0.9,
        "top_k": 40,
        "repeat_penalty": 1.1,
        "seed": -1
    }
    
    print("🔧 Applying optimized GPU configuration:")
    print(f"  • GPU Layers: {optimized_config['gpu_layers']}")
    print(f"  • Context Length: {optimized_config['num_ctx']}")
    print(f"  • CPU Threads: {optimized_config['num_thread']}")
    print(f"  • GPU Count: {optimized_config['num_gpu']}")
    print()
    
    # Test the optimized configuration
    test_prompt = "Generate 2 epics for a task management app. Respond with only a JSON array."
    
    payload = {
        "model": "llama3.1:70b",
        "prompt": test_prompt,
        "stream": False,
        "options": optimized_config
    }
    
    try:
        print("🔄 Testing optimized configuration...")
        start_time = time.time()
        
        response = requests.post(
            "http://localhost:11434/api/generate",
            json=payload,
            timeout=300
        )
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"⏱️ Response time: {duration:.2f} seconds")
        print()
        
        if response.status_code == 200:
            result = response.json()
            content = result.get('response', '')
            
            print("✅ Optimized configuration working!")
            print("📝 Response:")
            print("-" * 30)
            print(content)
            print("-" * 30)
            
            # Performance analysis
            if duration < 60:
                print("🎉 EXCELLENT: Response time under 1 minute!")
            elif duration < 120:
                print("✅ GOOD: Response time under 2 minutes")
            else:
                print("⚠️ SLOW: Response time over 2 minutes")
                
        else:
            print(f"❌ Error: HTTP {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.Timeout:
        print("❌ Request timed out - configuration may need adjustment")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print()
    print("📋 Optimization Recommendations:")
    print("1. If still slow, try reducing gpu_layers to 80-90")
    print("2. Increase num_thread to 20-24 if you have more CPU cores")
    print("3. Consider using llama3.1:34b for faster responses")
    print("4. Monitor GPU memory usage with: nvidia-smi")
    print()
    print("🏁 Optimization completed")

def create_optimized_modelfile():
    """Create an optimized Modelfile for the 70B model."""
    
    modelfile_content = """# Optimized Modelfile for RTX 4090
FROM llama3.1:70b

# GPU optimization settings
PARAMETER num_gpu 1
PARAMETER num_thread 16
PARAMETER num_ctx 4096
PARAMETER gpu_layers 100
PARAMETER rope_freq_base 10000
PARAMETER rope_freq_scale 0.5

# Generation settings
PARAMETER temperature 0.7
PARAMETER top_p 0.9
PARAMETER top_k 40
PARAMETER repeat_penalty 1.1
PARAMETER seed -1
"""
    
    with open("tools/optimized_70b_modelfile", "w") as f:
        f.write(modelfile_content)
    
    print("📄 Created optimized Modelfile: tools/optimized_70b_modelfile")
    print("To use it: ollama create llama3.1:70b-optimized -f tools/optimized_70b_modelfile")

if __name__ == "__main__":
    optimize_ollama_gpu()
    create_optimized_modelfile() 