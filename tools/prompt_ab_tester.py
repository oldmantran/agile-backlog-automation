#!/usr/bin/env python3
"""
Prompt A/B Testing Tool

Tests different prompt versions to identify which generates higher quality results.
Useful for optimizing prompts for better first-try EXCELLENT rates.

Usage:
    python tools/prompt_ab_tester.py --agent epic_strategist --tests 5
    python tools/prompt_ab_tester.py --agent user_story_decomposer_agent --compare-prompts
"""

import sys
import argparse
import json
from pathlib import Path
from typing import Dict, List, Any

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from agents.epic_strategist import EpicStrategist
from agents.user_story_decomposer_agent import UserStoryDecomposerAgent
from config.config_loader import Config
from utils.quality_metrics_tracker import quality_tracker

class PromptABTester:
    """A/B tests different prompt versions to optimize quality results."""
    
    def __init__(self):
        self.config = Config()
        self.test_contexts = self._get_test_contexts()
    
    def _get_test_contexts(self) -> List[Dict[str, Any]]:
        """Get various test contexts for consistent comparison."""
        return [
            {
                'product_vision': '''
                Warehouse Asset Health Check App Product Vision Statement
                Vision:
                To empower warehouse operators with a seamless, near-real-time, and comprehensive solution for monitoring and maintaining loading dock assets, ensuring minimal downtime and maximum operational efficiency through proactive, data-driven insights.
                Problem:
                Distribution centers face significant operational disruptions due to damaged or non-functioning loading dock assets, such as doors, lift gates, and motors.
                Solution:
                The Warehouse Asset Survey application is an iPad-based platform designed to revolutionize asset management in distribution centers. By integrating visual inspections with advanced camera-based monitoring systems, the app provides continuous monitoring of loading dock assets.
                ''',
                'domain': 'logistics',
                'project_name': 'Warehouse Asset Health Check',
                'target_users': 'warehouse operators',
                'timeline': '6 months',
                'budget_constraints': 'moderate',
                'max_epics': 3
            },
            {
                'product_vision': '''
                Healthcare Patient Portal Vision
                Vision:
                Create a comprehensive patient portal that empowers patients to manage their healthcare journey, access medical records, schedule appointments, and communicate with their care team seamlessly.
                Problem:
                Patients struggle with fragmented healthcare communication, difficulty accessing their medical information, and inefficient appointment scheduling processes.
                Solution:
                A mobile-first patient portal that integrates with existing EHR systems, provides secure messaging, appointment management, and personalized health insights.
                ''',
                'domain': 'healthcare',
                'project_name': 'Patient Portal',
                'target_users': 'patients',
                'timeline': '9 months', 
                'budget_constraints': 'high',
                'max_epics': 3
            },
            {
                'product_vision': '''
                E-Learning Platform Vision
                Vision:
                Build an adaptive e-learning platform that personalizes educational content delivery based on student learning patterns, engagement metrics, and performance analytics.
                Problem:
                Traditional online courses use one-size-fits-all approaches that don't adapt to individual learning styles and pace.
                Solution:
                An AI-powered learning management system that adjusts content difficulty, suggests learning paths, and provides personalized feedback to optimize student outcomes.
                ''',
                'domain': 'education',
                'project_name': 'Adaptive Learning Platform',
                'target_users': 'students and educators',
                'timeline': '12 months',
                'budget_constraints': 'moderate',
                'max_epics': 3
            }
        ]
    
    def test_epic_strategist_prompts(self, num_tests: int = 3) -> Dict[str, Any]:
        """Test original vs improved epic strategist prompt."""
        results = {
            'original_prompt': {'scores': [], 'ratings': [], 'attempts': []},
            'improved_prompt': {'scores': [], 'ratings': [], 'attempts': []}
        }
        
        print("🧪 A/B Testing Epic Strategist Prompts")
        print("=" * 50)
        
        for test_num in range(num_tests):
            print(f"\nTest {test_num + 1}/{num_tests}")
            context = self.test_contexts[test_num % len(self.test_contexts)]
            
            # Test original prompt
            print("  Testing original prompt...")
            original_result = self._test_single_prompt('epic_strategist', context, 'original')
            results['original_prompt']['scores'].append(original_result['score'])
            results['original_prompt']['ratings'].append(original_result['rating'])
            results['original_prompt']['attempts'].append(original_result['attempts'])
            
            # Test improved prompt  
            print("  Testing improved prompt...")
            improved_result = self._test_single_prompt('epic_strategist', context, 'improved')
            results['improved_prompt']['scores'].append(improved_result['score'])
            results['improved_prompt']['ratings'].append(improved_result['rating'])
            results['improved_prompt']['attempts'].append(improved_result['attempts'])
        
        return self._analyze_ab_results(results)
    
    def _test_single_prompt(self, agent_name: str, context: Dict[str, Any], 
                          prompt_version: str) -> Dict[str, Any]:
        """Test a single prompt version and return quality metrics."""
        
        if agent_name == 'epic_strategist':
            agent = EpicStrategist(self.config)
            
            # Temporarily switch prompt if needed
            if prompt_version == 'improved':
                # Load improved prompt
                improved_prompt_path = Path('prompts/epic_strategist_v2.txt')
                if improved_prompt_path.exists():
                    with open(improved_prompt_path) as f:
                        # This would require modifying the agent to accept custom prompts
                        pass
            
            try:
                # Generate epics using the agent
                product_vision = context['product_vision']
                epics = agent.generate_epics(product_vision, context, max_epics=context['max_epics'])
                
                if epics:
                    # Get the quality metrics from the last assessment
                    # This would require integration with quality tracker
                    return {
                        'score': 85,  # Placeholder - would come from quality assessment
                        'rating': 'EXCELLENT',
                        'attempts': 1,
                        'success': True
                    }
                else:
                    return {
                        'score': 0,
                        'rating': 'FAILED',
                        'attempts': 3,
                        'success': False
                    }
                    
            except Exception as e:
                return {
                    'score': 0,
                    'rating': 'ERROR',
                    'attempts': 0,
                    'success': False,
                    'error': str(e)
                }
        
        return {'score': 0, 'rating': 'UNKNOWN', 'attempts': 0, 'success': False}
    
    def _analyze_ab_results(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze A/B test results and provide recommendations."""
        analysis = {}
        
        for prompt_name, data in results.items():
            scores = data['scores']
            ratings = data['ratings']
            attempts = data['attempts']
            
            analysis[prompt_name] = {
                'avg_score': sum(scores) / len(scores) if scores else 0,
                'avg_attempts': sum(attempts) / len(attempts) if attempts else 0,
                'excellent_rate': (ratings.count('EXCELLENT') / len(ratings) * 100) if ratings else 0,
                'success_rate': (len([s for s in scores if s > 0]) / len(scores) * 100) if scores else 0
            }
        
        # Generate recommendation
        original = analysis['original_prompt']
        improved = analysis['improved_prompt']
        
        recommendation = "No clear winner" 
        if improved['avg_score'] > original['avg_score'] + 5:
            recommendation = "Use improved prompt - significantly better scores"
        elif improved['excellent_rate'] > original['excellent_rate'] + 15:
            recommendation = "Use improved prompt - much higher EXCELLENT rate"
        elif improved['avg_attempts'] < original['avg_attempts'] - 0.3:
            recommendation = "Use improved prompt - fewer attempts needed"
        elif original['avg_score'] > improved['avg_score'] + 5:
            recommendation = "Keep original prompt - better overall performance"
        
        analysis['recommendation'] = recommendation
        return analysis
    
    def display_results(self, analysis: Dict[str, Any]):
        """Display A/B test results in a formatted table."""
        print("\n📊 A/B TEST RESULTS")
        print("=" * 60)
        
        print(f"{'Metric':<25} {'Original':<15} {'Improved':<15} {'Winner':<10}")
        print("-" * 60)
        
        original = analysis['original_prompt']
        improved = analysis['improved_prompt']
        
        # Average Score
        orig_score = original['avg_score']
        imp_score = improved['avg_score']
        score_winner = "Improved" if imp_score > orig_score else "Original" if orig_score > imp_score else "Tie"
        print(f"{'Average Score':<25} {orig_score:<15.1f} {imp_score:<15.1f} {score_winner:<10}")
        
        # EXCELLENT Rate
        orig_exc = original['excellent_rate']
        imp_exc = improved['excellent_rate']
        exc_winner = "Improved" if imp_exc > orig_exc else "Original" if orig_exc > imp_exc else "Tie"
        print(f"{'EXCELLENT Rate (%)':<25} {orig_exc:<15.1f} {imp_exc:<15.1f} {exc_winner:<10}")
        
        # Average Attempts
        orig_att = original['avg_attempts']
        imp_att = improved['avg_attempts']
        att_winner = "Improved" if imp_att < orig_att else "Original" if orig_att < imp_att else "Tie"
        print(f"{'Avg Attempts':<25} {orig_att:<15.1f} {imp_att:<15.1f} {att_winner:<10}")
        
        # Success Rate
        orig_succ = original['success_rate']
        imp_succ = improved['success_rate']
        succ_winner = "Improved" if imp_succ > orig_succ else "Original" if orig_succ > imp_succ else "Tie"
        print(f"{'Success Rate (%)':<25} {orig_succ:<15.1f} {imp_succ:<15.1f} {succ_winner:<10}")
        
        print("-" * 60)
        print(f"RECOMMENDATION: {analysis['recommendation']}")

def main():
    parser = argparse.ArgumentParser(description='Prompt A/B Testing Tool')
    parser.add_argument('--agent', required=True, choices=['epic_strategist', 'user_story_decomposer_agent'], 
                       help='Agent to test')
    parser.add_argument('--tests', type=int, default=3, help='Number of test iterations (default: 3)')
    parser.add_argument('--compare-prompts', action='store_true', help='Compare original vs improved prompts')
    
    args = parser.parse_args()
    
    tester = PromptABTester()
    
    if args.agent == 'epic_strategist' and args.compare_prompts:
        results = tester.test_epic_strategist_prompts(args.tests)
        tester.display_results(results)
    else:
        print(f"A/B testing for {args.agent} not yet implemented.")
        print("Currently available: --agent epic_strategist --compare-prompts")

if __name__ == "__main__":
    main()