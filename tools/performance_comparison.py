#!/usr/bin/env python3
"""
Performance comparison between 8B and 70B models.
"""

import os
import sys
import time

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.ollama_client import OllamaClient

def test_model_performance(model_name, test_prompt, max_tokens=100):
    """Test performance of a specific model."""
    print(f"🧪 Testing {model_name}...")
    
    try:
        client = OllamaClient(model=model_name)
        
        start_time = time.time()
        result = client.generate(
            prompt=test_prompt,
            system_prompt="You are a helpful assistant. Provide concise responses.",
            temperature=0.7,
            max_tokens=max_tokens
        )
        end_time = time.time()
        
        generation_time = end_time - start_time
        tokens_per_second = result['tokens_used'] / generation_time
        
        print(f"✅ {model_name} Results:")
        print(f"   ⏱️  Time: {generation_time:.2f}s")
        print(f"   📊 Tokens: {result['tokens_used']}")
        print(f"   🚀 Speed: {tokens_per_second:.1f} tokens/second")
        print(f"   💰 Cost: ${client.estimate_cost(result['tokens_used'])['total_cost']:.4f}")
        print(f"   📄 Response: {result['content'][:100]}...")
        print()
        
        return {
            'model': model_name,
            'time': generation_time,
            'tokens': result['tokens_used'],
            'speed': tokens_per_second,
            'cost': client.estimate_cost(result['tokens_used'])['total_cost']
        }
        
    except Exception as e:
        print(f"❌ {model_name} failed: {e}")
        return None

def main():
    """Run performance comparison."""
    print("🚀 Model Performance Comparison")
    print("=" * 50)
    
    test_prompt = "Create a simple user story for a login feature in 2-3 sentences."
    
    results = []
    
    # Test 8B model
    result_8b = test_model_performance("llama3.1:8b", test_prompt)
    if result_8b:
        results.append(result_8b)
    
    # Test 70B model (if available)
    try:
        result_70b = test_model_performance("llama3.1:70b", test_prompt)
        if result_70b:
            results.append(result_70b)
    except:
        print("⚠️  70B model not available for comparison")
    
    # Compare results
    if len(results) >= 2:
        print("📊 Performance Comparison:")
        print("=" * 50)
        
        faster = min(results, key=lambda x: x['time'])
        slower = max(results, key=lambda x: x['time'])
        
        speed_ratio = faster['speed'] / slower['speed']
        cost_ratio = faster['cost'] / slower['cost']
        
        print(f"🏆 Fastest: {faster['model']} ({faster['speed']:.1f} tokens/sec)")
        print(f"🐌 Slowest: {slower['model']} ({slower['speed']:.1f} tokens/sec)")
        print(f"⚡ Speed difference: {speed_ratio:.1f}x faster")
        print(f"💰 Cost difference: {cost_ratio:.1f}x cheaper")
        
        if speed_ratio > 2:
            print("🎯 Recommendation: Use faster model for development/testing")
        else:
            print("🎯 Recommendation: Both models are reasonably fast")
    
    print("\n" + "=" * 50)
    print("✅ Performance comparison completed!")

if __name__ == "__main__":
    main() 