#!/usr/bin/env python3
"""
Analyze why epic quality assessment is failing for logistics domain.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.epic_quality_assessor import EpicQualityAssessor
from utils.safe_logger import safe_print
import json

def main():
    safe_print("[ANALYSIS] Epic Quality Assessment Failure Analysis")
    safe_print("=" * 80)
    
    # The product vision from the log
    product_vision = """Project: Backlog Automation
Domain: logistics

Warehouse Asset Health Check App Product Vision Statement
Vision:
To empower warehouse operators with a seamless, near-real-time, and comprehensive solution for monitoring and maintaining loading dock assets, ensuring minimal downtime and maximum operational efficiency through proactive, data-driven insights.
Problem:
Distribution centers face significant operational disruptions due to damaged or non-functioning loading dock assets, such as doors, lift gates, and motors. These issues lead to costly downtime, delayed shipments, and reduced productivity. Manual inspections are time-consuming, inconsistent, and often fail to detect early signs of potential failures, making preventative maintenance challenging.
Solution:
The Warehouse Asset Survey application is an iPad-based platform designed to revolutionize asset management in distribution centers. By integrating visual inspections with advanced camera-based monitoring systems, the app provides a continuous 360-degree view of loading dock assets' health. It leverages real-time visual and audio data to detect anomalies, predict potential failures, and recommend preventative maintenance actions. Key features include: 
	· Intuitive Inspection Interface: Streamlined workflows for warehouse inspectors to log visual inspections, capture images, and document asset conditions directly on the iPad. 
	· Smart Monitoring: AI-powered analysis of camera and audio feeds to identify early signs of wear, damage, or operational anomalies in doors, lift gates, and motors. 
	· Real-Time Alerts: Instant notifications to flag critical issues and prioritize maintenance tasks, minimizing downtime. 
	· Predictive Insights: Data-driven recommendations for preventative maintenance schedules to address issues before they lead to failures. 
	· Comprehensive Reporting: Centralized dashboards providing a holistic view of asset health across all docking bays, accessible anytime, anywhere.
Impact:
The Warehouse Asset Survey application transforms reactive maintenance into a proactive strategy, reducing downtime, optimizing resource allocation, and enhancing operational reliability. By delivering actionable insights and a near-real-time view of asset conditions, it ensures distribution centers operate at peak performance, saving time and costs while improving overall efficiency.
Who It's For:
Warehouse managers, maintenance teams, and inspectors at distribution centers who are committed to minimizing operational disruptions and maximizing the longevity of critical loading dock assets.
Why It Matters:
In a fast-paced logistics environment, every minute of downtime translates to lost revenue and customer dissatisfaction. Our solution empowers clients to stay ahead of asset failures, ensuring their distribution centers run smoothly and efficiently, with a focus on prevention and operational excellence."""

    # The epic that was generated (based on log pattern)
    test_epic = {
        "title": "Loading Dock Asset Health Monitoring System",
        "description": "Develop a comprehensive ai-powered system for real-time monitoring of loading dock assets including doors, lift gates, and motors. The platform will leverage visual and audio analysis to detect anomalies, predict failures, and recommend preventative maintenance schedules. This epic encompasses building the core monitoring infrastructure, analytics engine, and alert mechanisms to transform reactive maintenance into a proactive strategy for distribution centers."
    }
    
    # Create assessor and analyze
    assessor = EpicQualityAssessor()
    domain = "logistics"
    
    safe_print("\n[EPIC] Title: " + test_epic['title'])
    safe_print("[EPIC] Description: " + test_epic['description'][:100] + "...")
    
    # Run assessment
    assessment = assessor.assess_epic(test_epic, domain, product_vision)
    
    safe_print(f"\n[ASSESSMENT] Score: {assessment.score}/100 ({assessment.rating})")
    
    # Detailed analysis
    safe_print("\n[ANALYSIS] Key Phrase Extraction:")
    
    # Extract key terms from vision
    vision_lower = product_vision.lower()
    key_terms = [
        "warehouse asset survey",
        "ipad-based platform", 
        "loading dock assets",
        "visual inspections",
        "camera-based monitoring",
        "360-degree view",
        "intuitive inspection interface",
        "smart monitoring",
        "real-time alerts",
        "predictive insights",
        "comprehensive reporting",
        "warehouse managers",
        "maintenance teams",
        "inspectors"
    ]
    
    epic_text = f"{test_epic['title'].lower()} {test_epic['description'].lower()}"
    
    safe_print("\n[VISION KEY TERMS] Checking presence in epic:")
    found_count = 0
    for term in key_terms:
        found = term in epic_text
        status = "[FOUND]" if found else "[MISSING]"
        safe_print(f"  {status} {term}")
        if found:
            found_count += 1
    
    safe_print(f"\n[SUMMARY] Found {found_count}/{len(key_terms)} key terms")
    
    # Check domain terms
    safe_print("\n[DOMAIN TERMS] Logistics domain indicators:")
    domain_terms = assessor.domain_indicators.get('logistics', [])
    found_domain = [term for term in domain_terms if term in epic_text]
    safe_print(f"  Found: {', '.join(found_domain)}")
    safe_print(f"  Count: {len(found_domain)}/{len(domain_terms)}")
    
    # Show assessment details
    safe_print("\n[STRENGTHS]")
    for strength in assessment.strengths:
        safe_print(f"  + {strength}")
    
    safe_print("\n[ISSUES]")
    for issue in assessment.specific_issues:
        safe_print(f"  - {issue}")
    
    safe_print("\n[SUGGESTIONS]")
    for suggestion in assessment.improvement_suggestions:
        safe_print(f"  * {suggestion}")
    
    # Recommendations
    safe_print("\n[RECOMMENDATIONS]")
    safe_print("1. Epic needs to include more specific terms from the vision:")
    safe_print("   - 'Warehouse Asset Survey' (product name)")
    safe_print("   - 'iPad-based platform' or 'iPad'")
    safe_print("   - Target users: 'warehouse managers', 'maintenance teams', 'inspectors'")
    safe_print("   - Specific features: 'intuitive inspection interface', '360-degree view'")
    
    safe_print("\n2. Consider enhancing the prompt to:")
    safe_print("   - Explicitly require product name inclusion")
    safe_print("   - Mandate target user specification")
    safe_print("   - Request specific feature references from vision")

if __name__ == "__main__":
    main()