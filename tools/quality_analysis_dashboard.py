#!/usr/bin/env python3
"""
Quality Analysis Dashboard

Provides comprehensive analysis of agent quality metrics and generates
actionable improvement recommendations.

Usage:
    python tools/quality_analysis_dashboard.py
    python tools/quality_analysis_dashboard.py --agent epic_strategist
    python tools/quality_analysis_dashboard.py --days 30
    python tools/quality_analysis_dashboard.py --report
"""

import sys
import argparse
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from utils.quality_metrics_tracker import quality_tracker

def display_performance_summary(agent_name=None, days=7):
    """Display performance summary in a formatted table."""
    print(f"QUALITY PERFORMANCE SUMMARY (Last {days} days)")
    print("=" * 80)
    
    summary = quality_tracker.get_agent_performance_summary(agent_name, days)
    
    if not summary:
        print("No data available for the specified criteria.")
        return
    
    # Header
    print(f"{'Agent':<20} {'Items':<6} {'1st Try':<8} {'Overall':<8} {'Avg Att':<7} {'Avg Score':<9} {'Failures':<8}")
    print(f"{'Name':<20} {'Total':<6} {'EXCL %':<8} {'EXCL %':<8} {'empts':<7} {'(0-100)':<9} {'Rate %':<8}")
    print("-" * 80)
    
    # Sort by first-try excellent rate (descending)
    sorted_agents = sorted(summary.items(), key=lambda x: x[1]['first_try_excellent_rate'], reverse=True)
    
    for agent, metrics in sorted_agents:
        print(f"{agent:<20} {metrics['total_items']:<6} {metrics['first_try_excellent_rate']:<8.1f} "
              f"{metrics['overall_excellent_rate']:<8.1f} {metrics['avg_attempts']:<7.1f} "
              f"{metrics['avg_final_score']:<9.1f} {metrics['failure_rate']:<8.1f}")
    
    print()

def display_model_comparison(days=7):
    """Display model performance comparison."""
    print(f"MODEL PERFORMANCE COMPARISON (Last {days} days)")
    print("=" * 70)
    
    comparison = quality_tracker.get_model_comparison(days)
    
    if not comparison:
        print("No model data available.")
        return
    
    # Header
    print(f"{'Model':<25} {'Items':<6} {'1st Try':<8} {'Overall':<8} {'Avg Att':<7} {'Avg Score':<9}")
    print(f"{'Provider/Name':<25} {'Total':<6} {'EXCL %':<8} {'EXCL %':<8} {'empts':<7} {'(0-100)':<9}")
    print("-" * 70)
    
    # Sort by first-try excellent rate (descending)
    sorted_models = sorted(comparison.items(), key=lambda x: x[1]['first_try_excellent_rate'], reverse=True)
    
    for model, metrics in sorted_models:
        print(f"{model:<25} {metrics['total_items']:<6} {metrics['first_try_excellent_rate']:<8.1f} "
              f"{metrics['overall_excellent_rate']:<8.1f} {metrics['avg_attempts']:<7.1f} "
              f"{metrics['avg_final_score']:<9.1f}")
    
    print()

def identify_improvement_opportunities():
    """Identify specific improvement opportunities."""
    print("IMPROVEMENT OPPORTUNITIES")
    print("=" * 50)
    
    summary = quality_tracker.get_agent_performance_summary()
    if not summary:
        print("No data available for analysis.")
        return
    
    # Find agents with low first-try success rates
    low_performers = [(agent, metrics) for agent, metrics in summary.items() 
                     if metrics['first_try_excellent_rate'] < 30 and metrics['total_items'] >= 3]
    
    if low_performers:
        print("CRITICAL: Agents with <30% first-try EXCELLENT rate:")
        for agent, metrics in sorted(low_performers, key=lambda x: x[1]['first_try_excellent_rate']):
            print(f"   - {agent}: {metrics['first_try_excellent_rate']:.1f}% "
                  f"({metrics['total_items']} items, avg {metrics['avg_attempts']:.1f} attempts)")
        print()
    
    # Find agents with high retry counts
    high_retry = [(agent, metrics) for agent, metrics in summary.items() 
                 if metrics['avg_attempts'] > 2.5 and metrics['total_items'] >= 3]
    
    if high_retry:
        print("MEDIUM: Agents with excessive retries (>2.5 avg attempts):")
        for agent, metrics in sorted(high_retry, key=lambda x: x[1]['avg_attempts'], reverse=True):
            print(f"   - {agent}: {metrics['avg_attempts']:.1f} avg attempts "
                  f"({metrics['first_try_excellent_rate']:.1f}% first-try success)")
        print()
    
    # Find high failure rates
    high_failure = [(agent, metrics) for agent, metrics in summary.items() 
                   if metrics['failure_rate'] > 10 and metrics['total_items'] >= 3]
    
    if high_failure:
        print("CRITICAL: Agents with high failure rates (>10%):")
        for agent, metrics in sorted(high_failure, key=lambda x: x[1]['failure_rate'], reverse=True):
            print(f"   - {agent}: {metrics['failure_rate']:.1f}% failures "
                  f"(avg score: {metrics['avg_final_score']:.1f})")
        print()

def generate_prompt_optimization_suggestions():
    """Generate specific prompt optimization suggestions."""
    print("PROMPT OPTIMIZATION SUGGESTIONS")
    print("=" * 50)
    
    summary = quality_tracker.get_agent_performance_summary()
    if not summary:
        print("No data available for analysis.")
        return
    
    for agent, metrics in summary.items():
        if metrics['total_items'] < 3:
            continue
            
        print(f"\n### {agent}")
        
        # Analyze performance patterns
        first_try_rate = metrics['first_try_excellent_rate']
        avg_score = metrics['avg_final_score']
        
        if first_try_rate < 20:
            print("   CRITICAL ISSUES:")
            if avg_score < 70:
                print("   - Fundamental prompt issues - LLM not understanding requirements")
                print("   - Consider: Simplify language, add more examples, clarify success criteria")
            else:
                print("   - Quality threshold too high for current prompt design")
                print("   - Consider: Add specific quality guidelines, improve context clarity")
        
        elif first_try_rate < 50:
            print("   IMPROVEMENT NEEDED:")
            if metrics['avg_attempts'] > 2.5:
                print("   - Inconsistent results - prompt lacks specificity")
                print("   - Consider: Add more constraints, improve template variables")
            if avg_score < 80:
                print("   - Struggling to meet quality bar consistently") 
                print("   - Consider: Add domain-specific examples, clarify success criteria")
        
        elif first_try_rate >= 70:
            print("   PERFORMING WELL:")
            print("   - Good baseline performance - minor optimizations possible")
            print("   - Consider: Fine-tune for consistency, add edge case handling")
        
        # Specific recommendations based on failure patterns
        if metrics['failure_rate'] > 5:
            print("   - High failure rate suggests prompt brittleness")
            print("   - Recommendation: Add fallback strategies, improve error handling")

def main():
    parser = argparse.ArgumentParser(description='Quality Analysis Dashboard')
    parser.add_argument('--agent', help='Filter by specific agent name')
    parser.add_argument('--days', type=int, default=7, help='Number of days to analyze (default: 7)')
    parser.add_argument('--report', action='store_true', help='Generate full improvement report')
    
    args = parser.parse_args()
    
    if args.report:
        print(quality_tracker.generate_improvement_report())
        return
    
    # Display dashboard
    print("\nAGILE BACKLOG AUTOMATION - QUALITY ANALYSIS DASHBOARD")
    print("=" * 80)
    
    display_performance_summary(args.agent, args.days)
    
    if not args.agent:  # Only show comparisons for full dashboard
        display_model_comparison(args.days)
        identify_improvement_opportunities()
        generate_prompt_optimization_suggestions()
    
    print("\nTIP: Use --report flag to generate a detailed improvement report")
    print("TIP: Use --agent <name> to focus on specific agent analysis")

if __name__ == "__main__":
    main()