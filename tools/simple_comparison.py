#!/usr/bin/env python3
"""
Simple comparison between 8B and 70B models.
"""

import os
import sys
import time

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.ollama_client import OllamaClient

def test_model(model_name):
    """Test a single model."""
    try:
        client = OllamaClient(model=model_name)
        
        start_time = time.time()
        result = client.generate(
            prompt="Write a simple user story for login feature.",
            system_prompt="Be concise.",
            temperature=0.7,
            max_tokens=50
        )
        end_time = time.time()
        
        generation_time = end_time - start_time
        tokens_per_second = result['tokens_used'] / generation_time
        cost = client.estimate_cost(result['tokens_used'])
        
        return {
            'model': model_name,
            'time': generation_time,
            'speed': tokens_per_second,
            'cost': cost['total_cost'],
            'response': result['content'][:80]
        }
    except Exception as e:
        print(f"❌ {model_name}: {e}")
        return None

def main():
    """Run simple comparison."""
    print("🚀 Simple Model Comparison")
    print("=" * 40)
    
    # Test 8B
    print("Testing 8B...")
    result_8b = test_model("llama3.1:8b")
    
    # Test 70B
    print("Testing 70B...")
    result_70b = test_model("llama3.1:70b")
    
    print("\n📊 RESULTS:")
    print("=" * 40)
    
    if result_8b:
        print(f"8B: {result_8b['time']:.1f}s, {result_8b['speed']:.0f} tokens/sec, ${result_8b['cost']:.4f}")
        print(f"    Response: {result_8b['response']}")
    
    if result_70b:
        print(f"70B: {result_70b['time']:.1f}s, {result_70b['speed']:.0f} tokens/sec, ${result_70b['cost']:.4f}")
        print(f"     Response: {result_70b['response']}")
    
    if result_8b and result_70b:
        speed_ratio = result_8b['speed'] / result_70b['speed']
        cost_ratio = result_8b['cost'] / result_70b['cost']
        
        print(f"\n🏆 SUMMARY:")
        print(f"8B is {speed_ratio:.1f}x faster and {cost_ratio:.1f}x cheaper")
        
        if speed_ratio > 2:
            print("🎯 RECOMMENDATION: Use 8B for development (much faster)")
        else:
            print("🎯 RECOMMENDATION: Both models are reasonably fast")

if __name__ == "__main__":
    main() 