"""
QA Test Management Completeness Validator
Ensures all features have test plans, all stories have test suites, and all test cases are properly linked.
"""

import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass


@dataclass
class TestOrganizationReport:
    """Report on test organization completeness"""
    total_features: int
    features_with_test_plans: int
    total_user_stories: int
    stories_with_test_suites: int
    total_test_cases: int
    linked_test_cases: int
    missing_test_plans: List[str]
    missing_test_suites: List[str]
    unlinked_test_cases: List[str]
    completeness_score: float


class QACompletenessValidator:
    """Validates QA test organization completeness"""
    
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def validate_test_organization(self, epics: List[Dict[str, Any]]) -> TestOrganizationReport:
        """
        Validate that all features have test plans, all stories have test suites,
        and all test cases are properly linked.
        """
        self.logger.info("Validating test organization completeness")
        
        # Initialize counters
        total_features = 0
        features_with_test_plans = 0
        total_user_stories = 0
        stories_with_test_suites = 0
        total_test_cases = 0
        linked_test_cases = 0
        
        # Track missing items
        missing_test_plans = []
        missing_test_suites = []
        unlinked_test_cases = []
        
        # Process each epic
        for epic in epics:
            for feature in epic.get('features', []):
                total_features += 1
                feature_name = feature.get('title', f"Feature {feature.get('id', 'unknown')}")
                
                # Check if feature has test plan
                if feature.get('test_plan'):
                    features_with_test_plans += 1
                else:
                    missing_test_plans.append(feature_name)
                
                # Process user stories
                for user_story in feature.get('user_stories', []):
                    total_user_stories += 1
                    story_name = user_story.get('title', f"Story {user_story.get('id', 'unknown')}")
                    
                    # Check if story has test suite
                    if user_story.get('test_suite'):
                        stories_with_test_suites += 1
                    else:
                        missing_test_suites.append(f"{feature_name} -> {story_name}")
                    
                    # Process test cases
                    for test_case in user_story.get('test_cases', []):
                        total_test_cases += 1
                        test_case_name = test_case.get('title', f"Test Case {test_case.get('id', 'unknown')}")
                        
                        # Check if test case is linked to suite (improved validation)
                        is_linked = (
                            test_case.get('test_suite_id') or 
                            test_case.get('linked_to_suite') or
                            (user_story.get('test_suite') and test_case.get('user_story_id'))
                        )
                        
                        if is_linked:
                            linked_test_cases += 1
                        else:
                            unlinked_test_cases.append(f"{story_name} -> {test_case_name}")
        
        # Calculate completeness score
        completeness_score = self._calculate_completeness_score(
            total_features, features_with_test_plans,
            total_user_stories, stories_with_test_suites,
            total_test_cases, linked_test_cases
        )
        
        report = TestOrganizationReport(
            total_features=total_features,
            features_with_test_plans=features_with_test_plans,
            total_user_stories=total_user_stories,
            stories_with_test_suites=stories_with_test_suites,
            total_test_cases=total_test_cases,
            linked_test_cases=linked_test_cases,
            missing_test_plans=missing_test_plans,
            missing_test_suites=missing_test_suites,
            unlinked_test_cases=unlinked_test_cases,
            completeness_score=completeness_score
        )
        
        self.logger.info(f"Test organization completeness: {completeness_score:.1%}")
        return report
    
    def _calculate_completeness_score(self, 
                                    total_features: int, features_with_test_plans: int,
                                    total_user_stories: int, stories_with_test_suites: int,
                                    total_test_cases: int, linked_test_cases: int) -> float:
        """Calculate overall completeness score"""
        
        if total_features == 0:
            return 0.0
        
        # Weight the different aspects
        plan_score = (features_with_test_plans / total_features) if total_features > 0 else 0
        suite_score = (stories_with_test_suites / total_user_stories) if total_user_stories > 0 else 0
        linking_score = (linked_test_cases / total_test_cases) if total_test_cases > 0 else 0
        
        # Weighted average (test plans are most critical)
        return (plan_score * 0.5) + (suite_score * 0.3) + (linking_score * 0.2)
    
    def generate_completeness_report(self, report: TestOrganizationReport) -> str:
        """Generate a human-readable completeness report"""
        
        report_lines = [
            "📊 QA Test Organization Completeness Report",
            "=" * 50,
            f"Overall Completeness Score: {report.completeness_score:.1%}",
            "",
            "📋 Test Plan Coverage:",
            f"  Features with Test Plans: {report.features_with_test_plans}/{report.total_features} ({report.features_with_test_plans/report.total_features:.1%})",
            "",
            "📁 Test Suite Coverage:",
            f"  User Stories with Test Suites: {report.stories_with_test_suites}/{report.total_user_stories} ({report.stories_with_test_suites/report.total_user_stories:.1%})",
            "",
            "🔗 Test Case Linking:",
            f"  Test Cases Linked to Suites: {report.linked_test_cases}/{report.total_test_cases} ({report.linked_test_cases/report.total_test_cases:.1%})",
            ""
        ]
        
        # Add missing items
        if report.missing_test_plans:
            report_lines.extend([
                "❌ Missing Test Plans:",
                *[f"  - {plan}" for plan in report.missing_test_plans[:10]],
                f"  ... and {len(report.missing_test_plans) - 10} more" if len(report.missing_test_plans) > 10 else "",
                ""
            ])
        
        if report.missing_test_suites:
            report_lines.extend([
                "❌ Missing Test Suites:",
                *[f"  - {suite}" for suite in report.missing_test_suites[:10]],
                f"  ... and {len(report.missing_test_suites) - 10} more" if len(report.missing_test_suites) > 10 else "",
                ""
            ])
        
        if report.unlinked_test_cases:
            report_lines.extend([
                "❌ Unlinked Test Cases:",
                *[f"  - {case}" for case in report.unlinked_test_cases[:10]],
                f"  ... and {len(report.unlinked_test_cases) - 10} more" if len(report.unlinked_test_cases) > 10 else "",
                ""
            ])
        
        # Add recommendations
        recommendations = self._generate_recommendations(report)
        if recommendations:
            report_lines.extend([
                "🔧 Recommendations:",
                *[f"  - {rec}" for rec in recommendations]
            ])
        
        return "\n".join(report_lines)
    
    def _generate_recommendations(self, report: TestOrganizationReport) -> List[str]:
        """Generate specific recommendations based on completeness report"""
        recommendations = []
        
        # Test plan recommendations
        if report.features_with_test_plans < report.total_features:
            missing_plans = report.total_features - report.features_with_test_plans
            recommendations.append(f"Create {missing_plans} missing test plans for features")
        
        # Test suite recommendations
        if report.stories_with_test_suites < report.total_user_stories:
            missing_suites = report.total_user_stories - report.stories_with_test_suites
            recommendations.append(f"Create {missing_suites} missing test suites for user stories")
        
        # Test case linking recommendations
        if report.linked_test_cases < report.total_test_cases:
            unlinked_cases = report.total_test_cases - report.linked_test_cases
            recommendations.append(f"Link {unlinked_cases} test cases to their respective test suites")
        
        # Overall recommendations
        if report.completeness_score < 0.8:
            recommendations.append("Consider running automated test organization remediation")
        
        if report.completeness_score < 0.5:
            recommendations.append("Test organization needs significant improvement before production")
        
        return recommendations

    def auto_remediate_test_organization(self, epics: List[Dict[str, Any]], ado_client=None) -> Dict[str, Any]:
        """
        Automatically remediate missing test organization elements
        """
        self.logger.info("Starting automatic test organization remediation")
        
        remediation_result = {
            'test_plans_created': 0,
            'test_suites_created': 0,
            'test_cases_linked': 0,
            'errors': []
        }
        
        try:
            # Process each epic
            for epic in epics:
                for feature in epic.get('features', []):
                    
                    # Ensure test plan exists
                    if not feature.get('test_plan') and ado_client:
                        try:
                            test_plan = ado_client.ensure_test_plan_exists(
                                feature_id=feature.get('id'),
                                feature_name=feature.get('title', 'Unknown Feature')
                            )
                            if test_plan:
                                feature['test_plan'] = test_plan
                                remediation_result['test_plans_created'] += 1
                        except Exception as e:
                            remediation_result['errors'].append(f"Failed to create test plan for {feature.get('title', 'Unknown')}: {e}")
                    
                    # Ensure test suites exist for each user story
                    for user_story in feature.get('user_stories', []):
                        if not user_story.get('test_suite') and ado_client and feature.get('test_plan'):
                            try:
                                test_suite = ado_client.ensure_test_suite_exists(
                                    test_plan_id=feature['test_plan']['id'],
                                    user_story_id=user_story.get('id'),
                                    user_story_name=user_story.get('title', 'Unknown Story')
                                )
                                if test_suite:
                                    user_story['test_suite'] = test_suite
                                    remediation_result['test_suites_created'] += 1
                            except Exception as e:
                                remediation_result['errors'].append(f"Failed to create test suite for {user_story.get('title', 'Unknown')}: {e}")
                        
                        # Link test cases to suite
                        if user_story.get('test_suite'):
                            suite_id = user_story['test_suite']['id']
                            for test_case in user_story.get('test_cases', []):
                                if not test_case.get('test_suite_id') and ado_client:
                                    try:
                                        # Link test case to suite
                                        success = ado_client.add_test_case_to_suite(
                                            test_plan_id=feature['test_plan']['id'],
                                            test_suite_id=suite_id,
                                            test_case_id=test_case.get('id')
                                        )
                                        if success:
                                            test_case['test_suite_id'] = suite_id
                                            test_case['linked_to_suite'] = True
                                            remediation_result['test_cases_linked'] += 1
                                    except Exception as e:
                                        remediation_result['errors'].append(f"Failed to link test case {test_case.get('title', 'Unknown')}: {e}")
            
            self.logger.info(f"Test organization remediation completed: {remediation_result}")
            return remediation_result
            
        except Exception as e:
            self.logger.error(f"Test organization remediation failed: {e}")
            remediation_result['errors'].append(f"Global remediation error: {e}")
            return remediation_result
