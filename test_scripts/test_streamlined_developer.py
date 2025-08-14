#!/usr/bin/env python3
"""Test the streamlined developer agent"""

import json
import os
import sys
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config.config_loader import Config
from agents.developer_agent import DeveloperAgent
from utils.task_quality_assessor import TaskQualityAssessor

def test_streamlined_developer():
    """Test the streamlined developer agent with quality assessment."""
    
    print("=" * 80)
    print("TESTING STREAMLINED DEVELOPER AGENT")
    print("=" * 80)
    
    # Initialize config
    config = Config()
    
    # Set up Ollama configuration for test
    import os
    os.environ['LLM_PROVIDER'] = 'ollama'
    os.environ['OLLAMA_MODEL'] = 'qwen2.5:14b-instruct-q4_K_M'
    os.environ['OLLAMA_BASE_URL'] = 'http://localhost:11434'
    
    # Initialize the developer agent
    developer_agent = DeveloperAgent(config, user_id="test_user")
    
    # Test user story (from our previous user story test)
    test_user_story = {
        "title": "As an Urban Commuter, I want to request a ride with one tap so that I can minimize booking time during rush hour",
        "user_story": "As an Urban Commuter, I want to request a ride with one tap so that I can minimize booking time during rush hour",
        "description": "As an Urban Commuter, I want to request a ride with one tap so that I can minimize booking time during rush hour. The mobile app displays a prominent 'Request Ride' button that uses current location and learns frequent destinations, dispatching nearest autonomous vehicle within 45 seconds.",
        "acceptance_criteria": [
            "Given I open the app, When I tap 'Request Ride', Then vehicle dispatch begins within 2 seconds",
            "Given my location is detected, When no destination is set, Then app suggests my top 3 frequent destinations"
        ],
        "story_points": 5,
        "priority": "High",
        "category": "ui_ux",
        "user_type": "existing_user"
    }
    
    # Test context
    test_context = {
        'domain': 'Transportation/Mobility',
        'project_name': 'Autonomous Ride Platform',
        'tech_stack': 'React Native, Node.js, MongoDB, Redis, Socket.IO',
        'architecture_pattern': 'Microservices',
        'database_type': 'MongoDB with Redis cache',
        'cloud_platform': 'AWS (ECS, Lambda, RDS)',
        'team_size': '8 developers',
        'sprint_duration': '2 weeks',
        'product_vision': 'Transform urban mobility with AI-powered autonomous ride-sharing that delivers sub-60 second dispatch times and 99.9% reliability for campus communities.',
        'epic_context': 'One-Tap Ride Request & Real-Time Dispatch',
        'feature_context': 'Real-Time Vehicle Dispatch Engine'
    }
    
    # Generate tasks
    print(f"\nGenerating tasks for user story: {test_user_story['title'][:60]}...")
    print("-" * 60)
    
    try:
        tasks = developer_agent.generate_tasks(
            user_story=test_user_story,
            context=test_context,
            max_tasks=5  # Generate up to 5 tasks for testing
        )
        
        print(f"\nGenerated {len(tasks)} tasks")
        
        # Initialize quality assessor for detailed analysis
        assessor = TaskQualityAssessor()
        
        total_score = 0
        quality_results = []
        
        for i, task in enumerate(tasks):
            print(f"\n{'='*60}")
            print(f"TASK {i+1}")
            print(f"{'='*60}")
            print(f"Title: {task.get('title', 'N/A')}")
            print(f"Category: {task.get('category', 'N/A')}")
            print(f"Time Estimate: {task.get('time_estimate', 'N/A')} hours")
            print(f"Story Points: {task.get('story_points', 'N/A')}")
            print(f"Complexity: {task.get('complexity', 'N/A')}")
            print(f"\nDescription:")
            print(f"  {task.get('description', 'N/A')[:200]}...")
            
            print(f"\nDependencies:")
            for dep in task.get('dependencies', []):
                print(f"  - {dep}")
            
            print(f"\nAcceptance Criteria:")
            for j, criterion in enumerate(task.get('acceptance_criteria', [])):
                print(f"  {j+1}. {criterion}")
            
            if 'technical_details' in task:
                print(f"\nTechnical Details:")
                details = task.get('technical_details', {})
                if 'endpoints' in details:
                    print(f"  Endpoints: {', '.join(details['endpoints'])}")
                if 'models' in details:
                    print(f"  Models: {', '.join(details['models'])}")
                if 'services' in details:
                    print(f"  Services: {', '.join(details['services'])}")
            
            # Assess quality
            assessment = assessor.assess_task(
                task=task,
                user_story=test_user_story,
                domain=test_context['domain'],
                product_vision=test_context['product_vision']
            )
            
            print(f"\nQuality Assessment:")
            print(f"  Rating: {assessment.rating} ({assessment.score}/100)")
            if assessment.strengths:
                print("  Strengths:")
                for strength in assessment.strengths:
                    print(f"    + {strength}")
            if assessment.weaknesses or assessment.specific_issues:
                print("  Issues:")
                for issue in assessment.specific_issues + assessment.weaknesses:
                    print(f"    - {issue}")
            
            total_score += assessment.score
            quality_results.append({
                'task': task.get('title', f'Task {i+1}'),
                'rating': assessment.rating,
                'score': assessment.score
            })
        
        # Summary
        avg_score = total_score / len(tasks) if tasks else 0
        print(f"\n{'='*60}")
        print("SUMMARY")
        print(f"{'='*60}")
        print(f"Total Tasks: {len(tasks)}")
        print(f"Average Quality Score: {avg_score:.1f}/100")
        print("\nIndividual Scores:")
        for result in quality_results:
            print(f"  - {result['task'][:50]}... : {result['rating']} ({result['score']}/100)")
        
        # Determine overall result
        passing_threshold = 75
        if avg_score >= passing_threshold:
            print(f"\n[PASS]: Average score {avg_score:.1f} meets threshold of {passing_threshold}")
        else:
            print(f"\n[FAIL]: Average score {avg_score:.1f} below threshold of {passing_threshold}")
        
        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"test_results/developer_test_{timestamp}.json"
        os.makedirs("test_results", exist_ok=True)
        
        with open(output_file, 'w') as f:
            json.dump({
                'user_story': test_user_story,
                'context': test_context,
                'tasks': tasks,
                'quality_results': quality_results,
                'average_score': avg_score,
                'passed': avg_score >= passing_threshold
            }, f, indent=2)
        
        print(f"\nResults saved to: {output_file}")
        
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_streamlined_developer()