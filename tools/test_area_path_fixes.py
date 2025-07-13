#!/usr/bin/env python3
"""
Test script to validate Azure DevOps area path fixes
"""

import sys
sys.path.append('.')

from agents.qa_lead_agent import QALeadAgent
from config.config_loader import Config

def test_area_path_detection():
    """Test the fixed area path detection logic"""
    print('🔧 Testing area path detection fixes...')
    
    # Create test context that matches our ride sharing project
    test_context = {
        'project_context': {
            'project_name': 'AI Generated Project',
            'domain': 'software_development',
            'description': 'Product Vision Statement for RideSharing App',
            'vision': {
                'visionStatement': 'To revolutionize urban mobility by providing a seamless, safe, and sustainable ride-sharing experience powered by autonomous vehicles...'
            }
        }
    }
    
    # Initialize QA Lead Agent
    config = Config()
    qa_agent = QALeadAgent(config)
    
    # Test area path detection
    area_path = qa_agent._determine_area_path(test_context)
    
    print(f'📍 Detected area path: "{area_path}"')
    
    # Validate the result
    expected_area_path = "Ride Sharing"
    if area_path == expected_area_path:
        print(f'✅ Area path detection is correct: {area_path}')
        return True
    else:
        print(f'❌ Area path detection failed. Expected: "{expected_area_path}", Got: "{area_path}"')
        return False

def test_different_project_types():
    """Test area path detection for different project types"""
    print('\n🔍 Testing different project types...')
    
    config = Config()
    qa_agent = QALeadAgent(config)
    
    test_cases = [
        {
            'name': 'Oil & Gas Project',
            'context': {
                'project_context': {
                    'project_name': 'Drilling Operations',
                    'domain': 'oil_gas',
                    'description': 'Oil drilling management system'
                }
            },
            'expected': 'Oil and Gas Operations'
        },
        {
            'name': 'Fintech Project', 
            'context': {
                'project_context': {
                    'project_name': 'Payment System',
                    'domain': 'fintech',
                    'description': 'Banking and payment processing'
                }
            },
            'expected': 'Financial Services'
        },
        {
            'name': 'E-commerce Project',
            'context': {
                'project_context': {
                    'project_name': 'Shopping Platform',
                    'domain': 'ecommerce',
                    'description': 'Online retail platform'
                }
            },
            'expected': 'E-Commerce'
        }
    ]
    
    all_correct = True
    for test_case in test_cases:
        area_path = qa_agent._determine_area_path(test_case['context'])
        status = '✅' if area_path == test_case['expected'] else '❌'
        print(f"{status} {test_case['name']}: {area_path} (expected {test_case['expected']})")
        if area_path != test_case['expected']:
            all_correct = False
    
    return all_correct

if __name__ == "__main__":
    print('🚀 Testing Azure DevOps area path fixes...\n')
    
    # Test 1: Basic area path detection for ride sharing
    result1 = test_area_path_detection()
    
    # Test 2: Different project types
    result2 = test_different_project_types()
    
    # Summary
    print('\n📊 Test Results Summary:')
    print(f'✅ Ride sharing detection: {"PASS" if result1 else "FAIL"}')
    print(f'✅ Multiple project types: {"PASS" if result2 else "FAIL"}')
    
    if result1 and result2:
        print('\n🎉 All area path detection tests passed!')
        print('\n📋 Recommended next steps:')
        print('1. Update existing Azure DevOps test plans to use "Ride Sharing" area path')
        print('2. Run a small test workflow to validate the fix works end-to-end')
        print('3. Verify test cases are properly linked to test suites in Azure DevOps')
    else:
        print('\n❌ Some tests failed. Please review the area path detection logic.')
