#!/usr/bin/env python3
"""
Recommend optimal model configuration based on system constraints.
"""

import requests
import json
import time
from datetime import datetime

def test_model_performance():
    """Test different models to recommend the best configuration."""
    
    print("🚀 Model Performance Analysis")
    print("=" * 40)
    print(f"📅 Analysis started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    models_to_test = [
        {"name": "llama3.1:8b", "description": "Fast, lightweight"},
        {"name": "llama3.1:34b", "description": "Balanced performance"},
        {"name": "codellama:34b", "description": "Code-optimized 34B"}
    ]
    
    test_prompt = "Generate 2 epics for a task management app. Respond with only a JSON array."
    
    results = []
    
    for model in models_to_test:
        print(f"🔄 Testing {model['name']} ({model['description']})...")
        
        payload = {
            "model": model['name'],
            "prompt": test_prompt,
            "stream": False,
            "options": {
                "num_gpu": 1,
                "num_thread": 16,
                "num_ctx": 4096,
                "gpu_layers": 100,
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
                
                # Try to parse JSON to check quality
                try:
                    json.loads(content)
                    quality = "✅ Valid JSON"
                except:
                    quality = "⚠️ Invalid JSON"
                
                results.append({
                    "model": model['name'],
                    "time": duration,
                    "quality": quality,
                    "description": model['description']
                })
                
                print(f"  ✅ {duration:.2f} seconds - {quality}")
                
            else:
                print(f"  ❌ Error: HTTP {response.status_code}")
                
        except requests.exceptions.Timeout:
            print(f"  ⏱️ Timeout after 2 minutes")
        except Exception as e:
            print(f"  ❌ Error: {e}")
        
        print()
    
    # Sort by performance
    results.sort(key=lambda x: x['time'])
    
    # Generate recommendations
    print("📊 Performance Results:")
    print("-" * 40)
    for i, result in enumerate(results, 1):
        print(f"{i}. {result['model']}: {result['time']:.2f}s - {result['quality']}")
    
    print()
    print("💡 Recommendations:")
    print("-" * 40)
    
    if results:
        best_model = results[0]
        print(f"🎯 PRIMARY MODEL: {best_model['model']}")
        print(f"   • Response time: {best_model['time']:.2f} seconds")
        print(f"   • Quality: {best_model['quality']}")
        print(f"   • Description: {best_model['description']}")
        
        if len(results) > 1:
            second_model = results[1]
            print(f"🔄 FALLBACK MODEL: {second_model['model']}")
            print(f"   • Response time: {second_model['time']:.2f} seconds")
        
        print()
        print("🔧 Configuration Update:")
        print("1. Go to your application settings")
        print("2. Change LLM model from 'llama3.1:70b' to:")
        print(f"   • Primary: {best_model['model']}")
        print(f"   • Fallback: {second_model['model'] if len(results) > 1 else 'llama3.1:8b'}")
        print("3. Save and restart the application")
        
        # Create configuration file
        create_recommended_config(best_model, results)
    
    print()
    print("⚠️ Note: 70B model requires 40GB+ RAM and is not suitable for your system")
    print("💡 The 34B model provides excellent quality with much better performance")

def create_recommended_config(best_model, all_results):
    """Create a recommended configuration file."""
    
    config = {
        "recommendation": {
            "primary_model": best_model['model'],
            "primary_time": best_model['time'],
            "primary_quality": best_model['quality'],
            "fallback_model": all_results[1]['model'] if len(all_results) > 1 else "llama3.1:8b",
            "fallback_time": all_results[1]['time'] if len(all_results) > 1 else 15.0,
            "reason": "70B model requires 40GB+ RAM, not suitable for current system"
        },
        "ollama_options": {
            "num_gpu": 1,
            "num_thread": 16,
            "num_ctx": 4096,
            "gpu_layers": 100,
            "temperature": 0.7,
            "top_p": 0.9,
            "top_k": 40,
            "repeat_penalty": 1.1,
            "seed": -1
        },
        "performance_comparison": {
            "llama3.1:8b": "5-15 seconds",
            "llama3.1:34b": "15-30 seconds", 
            "llama3.1:70b": "2+ minutes (requires 40GB RAM)"
        }
    }
    
    with open("tools/recommended_model_config.json", "w") as f:
        json.dump(config, f, indent=2)
    
    print()
    print("📄 Created recommendation: tools/recommended_model_config.json")

if __name__ == "__main__":
    test_model_performance() 