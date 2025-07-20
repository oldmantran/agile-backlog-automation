#!/usr/bin/env python3
"""
Comprehensive comparison between 8B and 70B models for backlog generation.
"""

import os
import sys
import time
import json
from datetime import datetime

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.ollama_client import OllamaClient
from config.config_loader import Config
from agents.epic_strategist import EpicStrategist

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
        
        cost = client.estimate_cost(result['tokens_used'])
        
        return {
            'model': model_name,
            'time': generation_time,
            'tokens': result['tokens_used'],
            'speed': tokens_per_second,
            'cost': cost['total_cost'],
            'response': result['content']
        }
        
    except Exception as e:
        print(f"❌ {model_name} failed: {e}")
        return None

def test_backlog_quality(model_name, product_vision):
    """Test backlog generation quality."""
    print(f"📋 Testing {model_name} backlog quality...")
    
    try:
        # Set environment for specific model
        os.environ["LLM_PROVIDER"] = "ollama"
        os.environ["OLLAMA_MODEL"] = model_name
        
        config = Config()
        epic_agent = EpicStrategist(config)
        
        context = {
            'project_name': 'Test Banking App',
            'domain': 'fintech',
            'budget_constraints': 'Standard',
            'max_epics': 2,
            'target_users': 'Bank customers',
            'timeline': '6 months'
        }
        
        start_time = time.time()
        epics = epic_agent.generate_epics(product_vision, context)
        end_time = time.time()
        
        generation_time = end_time - start_time
        
        return {
            'model': model_name,
            'time': generation_time,
            'epics': epics,
            'epic_count': len(epics)
        }
        
    except Exception as e:
        print(f"❌ {model_name} backlog test failed: {e}")
        return None

def display_performance_results(results):
    """Display performance comparison results."""
    print("\n📊 Performance Comparison Results:")
    print("=" * 60)
    
    for result in results:
        if result:
            print(f"\n🔹 {result['model'].upper()}:")
            print(f"   ⏱️  Time: {result['time']:.2f}s")
            print(f"   📊 Tokens: {result['tokens']}")
            print(f"   🚀 Speed: {result['speed']:.1f} tokens/second")
            print(f"   💰 Cost: ${result['cost']:.4f}")
            print(f"   📄 Response: {result['response'][:80]}...")
    
    if len(results) >= 2:
        results = [r for r in results if r]
        if len(results) >= 2:
            faster = min(results, key=lambda x: x['time'])
            slower = max(results, key=lambda x: x['time'])
            
            speed_ratio = faster['speed'] / slower['speed']
            cost_ratio = faster['cost'] / slower['cost']
            
            print(f"\n🏆 PERFORMANCE SUMMARY:")
            print(f"   Fastest: {faster['model']} ({faster['speed']:.1f} tokens/sec)")
            print(f"   Slowest: {slower['model']} ({slower['speed']:.1f} tokens/sec)")
            print(f"   Speed difference: {speed_ratio:.1f}x faster")
            print(f"   Cost difference: {cost_ratio:.1f}x cheaper")

def display_quality_results(results):
    """Display quality comparison results."""
    print("\n📋 Quality Comparison Results:")
    print("=" * 60)
    
    for result in results:
        if result:
            print(f"\n🔹 {result['model'].upper()} Backlog Generation:")
            print(f"   ⏱️  Time: {result['time']:.2f}s")
            print(f"   📊 Epics generated: {result['epic_count']}")
            
            for i, epic in enumerate(result['epics'], 1):
                print(f"   📋 Epic {i}: {epic.get('title', 'Unknown')}")
                print(f"      Priority: {epic.get('priority', 'Medium')}")
                print(f"      Description: {epic.get('description', 'No description')[:60]}...")

def main():
    """Run comprehensive comparison."""
    print("🚀 Comprehensive Model Comparison: 8B vs 70B")
    print("=" * 60)
    
    # Test prompt for performance
    test_prompt = "Create a simple user story for a login feature in 2-3 sentences."
    
    # Product vision for quality test
    product_vision = """
    Create a mobile banking application that allows users to:
    - Check account balances
    - Transfer money between accounts
    - Pay bills
    - View transaction history
    - Set up recurring payments
    
    The app should be secure, user-friendly, and work on both iOS and Android.
    """
    
    print("🧪 Testing Performance...")
    performance_results = []
    
    # Test 8B performance
    result_8b = test_model_performance("llama3.1:8b", test_prompt)
    performance_results.append(result_8b)
    
    # Test 70B performance
    result_70b = test_model_performance("llama3.1:70b", test_prompt)
    performance_results.append(result_70b)
    
    print("\n📋 Testing Quality...")
    quality_results = []
    
    # Test 8B quality
    result_8b_quality = test_backlog_quality("llama3.1:8b", product_vision)
    quality_results.append(result_8b_quality)
    
    # Test 70B quality
    result_70b_quality = test_backlog_quality("llama3.1:70b", product_vision)
    quality_results.append(result_70b_quality)
    
    # Display results
    display_performance_results(performance_results)
    display_quality_results(quality_results)
    
    # Recommendations
    print("\n🎯 RECOMMENDATIONS:")
    print("=" * 60)
    
    if performance_results and quality_results:
        perf_results = [r for r in performance_results if r]
        qual_results = [r for r in quality_results if r]
        
        if len(perf_results) >= 2 and len(qual_results) >= 2:
            faster = min(perf_results, key=lambda x: x['time'])
            slower = max(perf_results, key=lambda x: x['time'])
            
            speed_ratio = faster['speed'] / slower['speed']
            
            print(f"🚀 For Development/Testing:")
            print(f"   Use: {faster['model']}")
            print(f"   Reason: {speed_ratio:.1f}x faster, {faster['cost']/slower['cost']:.1f}x cheaper")
            
            print(f"\n🎯 For Production Quality:")
            print(f"   Use: {slower['model']}")
            print(f"   Reason: Higher quality output, better for final deliverables")
            
            print(f"\n💡 Hybrid Approach:")
            print(f"   - Use {faster['model']} for development, testing, iterations")
            print(f"   - Use {slower['model']} for final production backlog generation")
    
    print("\n" + "=" * 60)
    print("✅ Comprehensive comparison completed!")

if __name__ == "__main__":
    main() 