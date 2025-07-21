#!/usr/bin/env python3
"""
Optimize Ollama GPU settings for RTX 4090 with memory constraints.
"""

import requests
import json
import time
from datetime import datetime

def test_gpu_configurations():
    """Test different GPU configurations to find the optimal balance."""
    
    print("🚀 Testing GPU Configurations for RTX 4090")
    print("=" * 50)
    print(f"📅 Testing started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Test configurations with different GPU layer counts
    configs = [
        {"name": "Conservative", "gpu_layers": 50, "num_thread": 16, "num_ctx": 2048},
        {"name": "Balanced", "gpu_layers": 70, "num_thread": 16, "num_ctx": 3072},
        {"name": "Aggressive", "gpu_layers": 90, "num_thread": 16, "num_ctx": 4096},
    ]
    
    test_prompt = "Generate 2 epics for a task management app. Respond with only a JSON array."
    
    best_config = None
    best_time = float('inf')
    
    for config in configs:
        print(f"🔄 Testing {config['name']} configuration:")
        print(f"  • GPU Layers: {config['gpu_layers']}")
        print(f"  • Context Length: {config['num_ctx']}")
        print(f"  • CPU Threads: {config['num_thread']}")
        
        payload = {
            "model": "llama3.1:70b",
            "prompt": test_prompt,
            "stream": False,
            "options": {
                "num_gpu": 1,
                "num_thread": config['num_thread'],
                "num_ctx": config['num_ctx'],
                "gpu_layers": config['gpu_layers'],
                "rope_freq_base": 10000,
                "rope_freq_scale": 0.5,
                "temperature": 0.7,
                "top_p": 0.9,
                "top_k": 40,
                "repeat_penalty": 1.1,
                "seed": -1
            }
        }
        
        try:
            start_time = time.time()
            response = requests.post(
                "http://localhost:11434/api/generate",
                json=payload,
                timeout=300
            )
            end_time = time.time()
            duration = end_time - start_time
            
            if response.status_code == 200:
                result = response.json()
                content = result.get('response', '')
                
                print(f"  ✅ Success: {duration:.2f} seconds")
                
                if duration < best_time:
                    best_time = duration
                    best_config = config
                    
            else:
                print(f"  ❌ Error: HTTP {response.status_code}")
                if "memory" in response.text.lower():
                    print(f"  💾 Memory issue: {response.text}")
                
        except requests.exceptions.Timeout:
            print(f"  ⏱️ Timeout after 5 minutes")
        except Exception as e:
            print(f"  ❌ Error: {e}")
        
        print()
    
    # Report results
    if best_config:
        print("🎉 Best Configuration Found:")
        print(f"  • Name: {best_config['name']}")
        print(f"  • GPU Layers: {best_config['gpu_layers']}")
        print(f"  • Context Length: {best_config['num_ctx']}")
        print(f"  • Response Time: {best_time:.2f} seconds")
        
        # Create optimized configuration file
        create_optimized_config(best_config, best_time)
    else:
        print("❌ No working configuration found")
        print("💡 Try using llama3.1:34b instead for better performance")

def create_optimized_config(config, response_time):
    """Create an optimized configuration file."""
    
    config_data = {
        "model": "llama3.1:70b",
        "optimization": {
            "name": config['name'],
            "response_time_seconds": response_time,
            "gpu_layers": config['gpu_layers'],
            "num_thread": config['num_thread'],
            "num_ctx": config['num_ctx']
        },
        "ollama_options": {
            "num_gpu": 1,
            "num_thread": config['num_thread'],
            "num_ctx": config['num_ctx'],
            "gpu_layers": config['gpu_layers'],
            "rope_freq_base": 10000,
            "rope_freq_scale": 0.5,
            "temperature": 0.7,
            "top_p": 0.9,
            "top_k": 40,
            "repeat_penalty": 1.1,
            "seed": -1
        }
    }
    
    with open("tools/optimized_70b_config.json", "w") as f:
        json.dump(config_data, f, indent=2)
    
    print()
    print("📄 Created optimized configuration: tools/optimized_70b_config.json")
    print("💡 Use this configuration in your Ollama client for best performance")

def test_34b_model():
    """Test the 34B model as an alternative."""
    
    print("🔄 Testing llama3.1:34b as alternative...")
    
    test_prompt = "Generate 2 epics for a task management app. Respond with only a JSON array."
    
    payload = {
        "model": "llama3.1:34b",
        "prompt": test_prompt,
        "stream": False,
        "options": {
            "num_gpu": 1,
            "num_thread": 16,
            "num_ctx": 4096,
            "gpu_layers": 100,  # 34B can use more GPU layers
            "temperature": 0.7,
            "top_p": 0.9,
            "top_k": 40,
            "repeat_penalty": 1.1,
            "seed": -1
        }
    }
    
    try:
        start_time = time.time()
        response = requests.post(
            "http://localhost:11434/api/generate",
            json=payload,
            timeout=120
        )
        end_time = time.time()
        duration = end_time - start_time
        
        if response.status_code == 200:
            result = response.json()
            content = result.get('response', '')
            
            print(f"✅ 34B Model: {duration:.2f} seconds")
            print("📝 Response:")
            print("-" * 30)
            print(content)
            print("-" * 30)
            
            if duration < 30:
                print("🎉 EXCELLENT: 34B model is much faster!")
                print("💡 Consider using 34B for most tasks")
            
        else:
            print(f"❌ 34B Error: HTTP {response.status_code}")
            
    except Exception as e:
        print(f"❌ 34B Error: {e}")

if __name__ == "__main__":
    test_gpu_configurations()
    print()
    test_34b_model() 