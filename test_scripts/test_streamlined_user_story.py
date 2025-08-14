#!/usr/bin/env python3
"""Test the streamlined user story decomposer"""

import json
import os
import sys
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config.config_loader import Config
from agents.user_story_decomposer_agent import UserStoryDecomposerAgent
from utils.user_story_quality_assessor_v2 import UserStoryQualityAssessor

def test_streamlined_user_story():
    """Test the streamlined user story decomposer with quality assessment."""
    
    print("=" * 80)
    print("TESTING STREAMLINED USER STORY DECOMPOSER")
    print("=" * 80)
    
    # Initialize config
    config = Config()
    
    # Set up Ollama configuration for test
    import os
    os.environ['LLM_PROVIDER'] = 'ollama'
    os.environ['OLLAMA_MODEL'] = 'qwen2.5:14b-instruct-q4_K_M'
    os.environ['OLLAMA_BASE_URL'] = 'http://localhost:11434'
    
    # Initialize the user story decomposer
    user_story_agent = UserStoryDecomposerAgent(config, user_id="test_user")
    
    # Test feature (from our previous feature test)
    test_feature = {
        "title": "Real-Time Vehicle Dispatch Engine",
        "description": "Enable Urban Commuters and College Students to request autonomous vehicles through mobile app with sub-60 second dispatch times using GPS tracking, ML route optimization, and real-time fleet management across urban campus zones.",
        "priority": "High",
        "estimated_story_points": 21,
        "dependencies": [],
        "ui_ux_requirements": [
            "Mobile-responsive dispatch interface",
            "Real-time vehicle location map",
            "ETA countdown timer",
            "Accessibility WCAG 2.1 AA compliance"
        ],
        "technical_considerations": [
            "WebSocket connections for real-time updates",
            "Redis for dispatch queue management",
            "PostGIS for geospatial queries",
            "Kubernetes for container orchestration"
        ],
        "business_value": "Reduces average wait time by 40%, increases ride completion rate by 25%, enables 10,000+ daily rides across campus zones with 99.9% dispatch reliability.",
        "edge_cases": [
            "Network connectivity loss during dispatch",
            "Simultaneous high-volume requests",
            "Vehicle breakdowns mid-route",
            "GPS signal loss in parking structures"
        ]
    }
    
    # Test context
    test_context = {
        'domain': 'Transportation/Mobility',
        'project_name': 'Autonomous Ride Platform',
        'methodology': 'Agile/Scrum',
        'target_users': 'Urban Commuters, College Students, Tourists',
        'platform': 'iOS and Android mobile apps',
        'team_velocity': '30-40 points per sprint',
        'product_vision': 'Transform urban mobility with AI-powered autonomous ride-sharing that delivers sub-60 second dispatch times and 99.9% reliability for campus communities.',
        'epic_context': 'One-Tap Ride Request & Real-Time Dispatch'
    }
    
    # Generate user stories
    print(f"\nGenerating user stories for feature: {test_feature['title']}")
    print("-" * 60)
    
    try:
        user_stories = user_story_agent.decompose_feature_to_user_stories(
            feature=test_feature,
            context=test_context,
            max_user_stories=3  # Generate 3 user stories for testing
        )
        
        print(f"\nGenerated {len(user_stories)} user stories")
        
        # Initialize quality assessor for detailed analysis
        assessor = UserStoryQualityAssessor()
        
        total_score = 0
        quality_results = []
        
        for i, story in enumerate(user_stories):
            print(f"\n{'='*60}")
            print(f"USER STORY {i+1}")
            print(f"{'='*60}")
            print(f"Title: {story.get('title', 'N/A')}")
            print(f"User Story: {story.get('user_story', 'N/A')}")
            print(f"Description: {story.get('description', 'N/A')[:200]}...")
            print(f"Story Points: {story.get('story_points', 'N/A')}")
            print(f"Priority: {story.get('priority', 'N/A')}")
            print(f"Category: {story.get('category', 'N/A')}")
            print(f"\nAcceptance Criteria ({len(story.get('acceptance_criteria', []))}):")
            for j, criterion in enumerate(story.get('acceptance_criteria', [])):
                print(f"  {j+1}. {criterion}")
            
            # Assess quality
            assessment = assessor.assess_user_story(
                story=story,
                feature=test_feature,
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
                'story': story.get('title', f'Story {i+1}'),
                'rating': assessment.rating,
                'score': assessment.score
            })
        
        # Summary
        avg_score = total_score / len(user_stories) if user_stories else 0
        print(f"\n{'='*60}")
        print("SUMMARY")
        print(f"{'='*60}")
        print(f"Total User Stories: {len(user_stories)}")
        print(f"Average Quality Score: {avg_score:.1f}/100")
        print("\nIndividual Scores:")
        for result in quality_results:
            print(f"  - {result['story'][:50]}... : {result['rating']} ({result['score']}/100)")
        
        # Determine overall result
        passing_threshold = 75
        if avg_score >= passing_threshold:
            print(f"\n[PASS]: Average score {avg_score:.1f} meets threshold of {passing_threshold}")
        else:
            print(f"\n[FAIL]: Average score {avg_score:.1f} below threshold of {passing_threshold}")
        
        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"test_results/user_story_test_{timestamp}.json"
        os.makedirs("test_results", exist_ok=True)
        
        with open(output_file, 'w') as f:
            json.dump({
                'feature': test_feature,
                'context': test_context,
                'user_stories': user_stories,
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
    test_streamlined_user_story()