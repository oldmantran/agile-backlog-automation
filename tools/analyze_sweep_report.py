#!/usr/bin/env python3
"""
Analyze the backlog sweeper report to understand discrepancy counts
"""

import json
import sys

def analyze_sweep_report(report_file):
    """Analyze the sweep report to understand the discrepancy counts."""
    
    with open(report_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print("🔍 Backlog Sweeper Report Analysis")
    print("=" * 50)
    
    # Summary
    summary = data.get('summary', {})
    print(f"📊 Summary:")
    print(f"   Total Discrepancies: {summary.get('total_discrepancies', 0)}")
    print(f"   High Priority: {summary.get('high_priority_count', 0)}")
    print(f"   Medium Priority: {summary.get('medium_priority_count', 0)}")
    print(f"   Low Priority: {summary.get('low_priority_count', 0)}")
    print()
    
    # Analyze high priority issues by type
    high_priority = data.get('discrepancies_by_priority', {}).get('high', [])
    
    issue_types = {}
    work_item_types = {}
    suggested_agents = {}
    
    for issue in high_priority:
        issue_type = issue.get('type', 'unknown')
        work_item_type = issue.get('work_item_type', 'unknown')
        suggested_agent = issue.get('suggested_agent', 'unknown')
        
        issue_types[issue_type] = issue_types.get(issue_type, 0) + 1
        work_item_types[work_item_type] = work_item_types.get(work_item_type, 0) + 1
        suggested_agents[suggested_agent] = suggested_agents.get(suggested_agent, 0) + 1
    
    print("🚨 High Priority Issues by Type:")
    for issue_type, count in sorted(issue_types.items()):
        print(f"   {issue_type}: {count}")
    print()
    
    print("📋 High Priority Issues by Work Item Type:")
    for work_item_type, count in sorted(work_item_types.items()):
        print(f"   {work_item_type}: {count}")
    print()
    
    print("🤖 High Priority Issues by Suggested Agent:")
    for agent, count in sorted(suggested_agents.items()):
        print(f"   {agent}: {count}")
    print()
    
    # Analyze orphaned work items specifically
    orphaned_items = [i for i in high_priority if i.get('type') == 'orphaned_work_item']
    
    if orphaned_items:
        print(f"🔗 Orphaned Work Items Analysis ({len(orphaned_items)} total):")
        
        orphaned_by_type = {}
        for item in orphaned_items:
            work_item_type = item.get('work_item_type', 'unknown')
            orphaned_by_type[work_item_type] = orphaned_by_type.get(work_item_type, 0) + 1
        
        for work_item_type, count in sorted(orphaned_by_type.items()):
            print(f"   {work_item_type}: {count}")
        
        # Show some examples
        print("\n📝 Sample Orphaned Items:")
        for i, item in enumerate(orphaned_items[:5]):
            print(f"   {i+1}. [{item.get('work_item_type')} {item.get('work_item_id')}] {item.get('title', 'No title')}")
        
        if len(orphaned_items) > 5:
            print(f"   ... and {len(orphaned_items) - 5} more")
    
    print()
    print("💡 Key Insights:")
    
    # Check if this is mostly orphaned test cases
    if orphaned_items and len(orphaned_items) > len(high_priority) * 0.8:
        print("   ⚠️  Most issues are orphaned work items (likely test cases without parents)")
        print("   🔧 This suggests a hierarchy/linking problem rather than feature decomposition issues")
    
    # Check agent assignments
    if suggested_agents.get('feature_decomposer_agent', 0) > 100:
        print("   ⚠️  Feature Decomposer Agent has many assignments - likely due to orphaned items")
        print("   🔧 Consider if these should be assigned to QA Lead Agent instead")

if __name__ == "__main__":
    report_file = "sweep_report_RE34B_20250721_162345.json"
    if len(sys.argv) > 1:
        report_file = sys.argv[1]
    
    try:
        analyze_sweep_report(report_file)
    except FileNotFoundError:
        print(f"❌ Report file not found: {report_file}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error analyzing report: {e}")
        sys.exit(1) 