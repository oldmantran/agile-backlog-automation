"""
Backlog Generation Summary Report Generator

This module generates comprehensive summary reports for backlog generation runs,
including quality metrics, rejection statistics, and performance analysis.
"""

import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import re
from pathlib import Path


class BacklogSummaryReportGenerator:
    """Generates comprehensive summary reports for backlog generation runs."""
    
    def __init__(self):
        self.quality_thresholds = {
            'EXCELLENT': 80,
            'GOOD': 65,
            'FAIR': 50,
            'POOR': 0
        }
        
    def generate_report(self, job_data: Dict[str, Any], log_content: str) -> Dict[str, Any]:
        """
        Generate a comprehensive summary report for a backlog generation run.
        
        Args:
            job_data: Job data from database
            log_content: Full log content from the run
            
        Returns:
            Dictionary containing the complete report data
        """
        # Extract key metrics from logs
        metrics = self._extract_metrics_from_logs(log_content)
        
        # Parse raw summary if available
        raw_summary = {}
        if job_data.get('raw_summary'):
            try:
                raw_summary = json.loads(job_data['raw_summary']) if isinstance(job_data['raw_summary'], str) else job_data['raw_summary']
            except:
                pass
        
        # Extract vision statement and quality
        vision_data = self._extract_vision_data(log_content, raw_summary)
        
        # Generate report
        report = {
            'metadata': {
                'project_name': job_data.get('project_name', 'Unknown'),
                'job_id': raw_summary.get('job_id', 'Unknown'),
                'generation_date': job_data.get('created_at', ''),
                'report_generated': datetime.now().isoformat(),
                'area_path': raw_summary.get('azure_config', {}).get('areaPath', 'N/A'),
                'iteration_path': raw_summary.get('azure_config', {}).get('iterationPath', 'N/A'),
                'domain': raw_summary.get('domain', 'Unknown'),
                'llm_models': self._extract_llm_models(log_content)
            },
            'vision_statement': vision_data,
            'generation_summary': {
                'execution_time': job_data.get('execution_time_seconds', 0),
                'execution_time_formatted': self._format_duration(job_data.get('execution_time_seconds', 0)),
                'stages_completed': metrics.get('stages_completed', 0),
                'parallel_processing': metrics.get('parallel_processing', False),
                'worker_count': metrics.get('worker_count', 0),
                'test_artifacts_included': raw_summary.get('test_artifacts_included', False)
            },
            'work_item_statistics': {
                'total_generated': self._calculate_total_generated(job_data),
                'by_type': {
                    'epics': job_data.get('epics_generated', 0),
                    'features': job_data.get('features_generated', 0),
                    'user_stories': job_data.get('user_stories_generated', 0),
                    'tasks': job_data.get('tasks_generated', 0),
                    'test_cases': job_data.get('test_cases_generated', 0)
                },
                'azure_devops_upload': {
                    'total_uploaded': metrics.get('items_uploaded', 0),
                    'upload_success_rate': self._calculate_upload_success_rate(job_data, metrics),
                    'upload_time': metrics.get('upload_time', 0)
                }
            },
            'quality_assessment': {
                'overall_quality_score': self._calculate_overall_quality_score(metrics),
                'by_stage': {
                    'epics': metrics.get('epic_quality', {}),
                    'features': metrics.get('feature_quality', {}),
                    'user_stories': metrics.get('story_quality', {}),
                    'tasks': metrics.get('task_quality', {})
                },
                'rejection_analysis': {
                    'total_rejected': metrics.get('total_rejected', 0),
                    'total_approved': metrics.get('total_approved', 0),
                    'rejection_rate': self._calculate_rejection_rate(metrics),
                    'most_common_rejection_reasons': metrics.get('rejection_reasons', []),
                    'replacement_attempts': metrics.get('replacement_attempts', 0)
                }
            },
            'performance_analysis': {
                'hardware_tier': metrics.get('hardware_tier', 'Unknown'),
                'cpu_cores': metrics.get('cpu_cores', 0),
                'memory_gb': metrics.get('memory_gb', 0),
                'stages_timing': metrics.get('stage_timings', {}),
                'high_latency_operations': metrics.get('high_latency_ops', []),
                'parallel_efficiency': self._calculate_parallel_efficiency(metrics)
            },
            'domain_alignment': {
                'domain': raw_summary.get('domain', 'Unknown'),
                'domain_terminology_usage': metrics.get('domain_terms_count', 0),
                'domain_specific_features': metrics.get('domain_features', []),
                'vision_alignment_score': metrics.get('vision_alignment_score', 0)
            },
            'recommendations': self._generate_recommendations(metrics, job_data),
            'raw_metrics': metrics
        }
        
        return report
    
    def _extract_metrics_from_logs(self, log_content: str) -> Dict[str, Any]:
        """Extract key metrics from log content."""
        metrics = {
            'total_rejected': 0,
            'total_approved': 0,
            'rejection_reasons': [],
            'replacement_attempts': 0,
            'stage_timings': {},
            'high_latency_ops': [],
            'epic_quality': {'excellent': 0, 'good': 0, 'fair': 0, 'poor': 0},
            'feature_quality': {'excellent': 0, 'good': 0, 'fair': 0, 'poor': 0},
            'story_quality': {'excellent': 0, 'good': 0, 'fair': 0, 'poor': 0},
            'task_quality': {'excellent': 0, 'good': 0, 'fair': 0, 'poor': 0}
        }
        
        # Count rejections and approvals
        metrics['total_rejected'] = len(re.findall(r'Task REJECTED', log_content))
        metrics['total_approved'] = len(re.findall(r'Task approved', log_content))
        
        # Count replacement attempts
        replacement_matches = re.findall(r'REPLACEMENT.*?(\d+) replacement', log_content)
        metrics['replacement_attempts'] = sum(int(m) for m in replacement_matches)
        
        # Extract quality ratings by type
        for match in re.finditer(r'(EPIC|FEATURE|USER STORY|TASK) QUALITY ASSESSMENT.*?Rating: (\w+)', log_content, re.DOTALL):
            item_type = match.group(1).lower().replace(' ', '_')
            rating = match.group(2).lower()
            
            if item_type == 'epic':
                metrics['epic_quality'][rating] = metrics['epic_quality'].get(rating, 0) + 1
            elif item_type == 'feature':
                metrics['feature_quality'][rating] = metrics['feature_quality'].get(rating, 0) + 1
            elif item_type == 'user_story':
                metrics['story_quality'][rating] = metrics['story_quality'].get(rating, 0) + 1
            elif item_type == 'task':
                metrics['task_quality'][rating] = metrics['task_quality'].get(rating, 0) + 1
        
        # Extract rejection reasons
        for match in re.finditer(r'IMPROVEMENT SUGGESTIONS:.*?\n((?:\s*\*.*?\n)+)', log_content):
            suggestions = match.group(1)
            for suggestion in re.findall(r'\*\s*(.+)', suggestions):
                metrics['rejection_reasons'].append(suggestion.strip())
        
        # Extract hardware info
        hw_match = re.search(r'Hardware: (\d+)C/\d+T.*?(\d+\.\d+)GB RAM', log_content)
        if hw_match:
            metrics['cpu_cores'] = int(hw_match.group(1))
            metrics['memory_gb'] = float(hw_match.group(2))
        
        tier_match = re.search(r'System: (\w+) performance tier', log_content)
        if tier_match:
            metrics['hardware_tier'] = tier_match.group(1)
        
        # Extract high latency operations
        for match in re.finditer(r'High latency \((\d+\.\d+)ms\) detected for stage \'(\w+)\'', log_content):
            metrics['high_latency_ops'].append({
                'stage': match.group(2),
                'latency_ms': float(match.group(1))
            })
        
        # Extract parallel processing info
        parallel_match = re.search(r'Parallel processing was enabled with (\d+) workers', log_content)
        if parallel_match:
            metrics['parallel_processing'] = True
            metrics['worker_count'] = int(parallel_match.group(1))
        
        # Extract upload metrics
        upload_match = re.search(r'Upload completed: (\d+) successful, (\d+) failed', log_content)
        if upload_match:
            metrics['items_uploaded'] = int(upload_match.group(1))
            metrics['upload_failures'] = int(upload_match.group(2))
        
        return metrics
    
    def _extract_vision_data(self, log_content: str, raw_summary: Dict) -> Dict[str, Any]:
        """Extract vision statement data and quality assessment."""
        vision_data = {
            'statement': '',
            'quality_score': 0,
            'quality_rating': 'Unknown',
            'key_elements': []
        }
        
        # Extract vision statement
        vision_match = re.search(r'Executive Summary.*?Integration Requirements.*?months\.', log_content, re.DOTALL)
        if vision_match:
            vision_data['statement'] = vision_match.group(0).strip()
        
        # Calculate quality score based on content
        if vision_data['statement']:
            score = 0
            
            # Check for key elements
            if 'Executive Summary' in vision_data['statement']:
                score += 15
                vision_data['key_elements'].append('Executive Summary')
            if 'Vision Statement' in vision_data['statement']:
                score += 15
                vision_data['key_elements'].append('Vision Statement')
            if 'Target Audience' in vision_data['statement']:
                score += 15
                vision_data['key_elements'].append('Target Audience')
            if 'Core Features' in vision_data['statement']:
                score += 15
                vision_data['key_elements'].append('Core Features')
            if 'Value Proposition' in vision_data['statement']:
                score += 15
                vision_data['key_elements'].append('Value Proposition')
            if 'Technical Architecture' in vision_data['statement']:
                score += 10
                vision_data['key_elements'].append('Technical Architecture')
            if 'Success Metrics' in vision_data['statement']:
                score += 10
                vision_data['key_elements'].append('Success Metrics')
            if 'Integration Requirements' in vision_data['statement']:
                score += 5
                vision_data['key_elements'].append('Integration Requirements')
            
            vision_data['quality_score'] = score
            
            # Determine rating
            if score >= 80:
                vision_data['quality_rating'] = 'EXCELLENT'
            elif score >= 65:
                vision_data['quality_rating'] = 'GOOD'
            elif score >= 50:
                vision_data['quality_rating'] = 'FAIR'
            else:
                vision_data['quality_rating'] = 'POOR'
        
        return vision_data
    
    def _extract_llm_models(self, log_content: str) -> Dict[str, str]:
        """Extract LLM models used for each agent."""
        models = {}
        
        for match in re.finditer(r'Refreshed config for (\w+): (\w+) \(([^)]+)\)', log_content):
            agent = match.group(1)
            provider = match.group(2)
            model = match.group(3)
            models[agent] = f"{provider}/{model}"
        
        return models
    
    def _calculate_total_generated(self, job_data: Dict) -> int:
        """Calculate total work items generated."""
        return (job_data.get('epics_generated', 0) +
                job_data.get('features_generated', 0) +
                job_data.get('user_stories_generated', 0) +
                job_data.get('tasks_generated', 0) +
                job_data.get('test_cases_generated', 0))
    
    def _calculate_upload_success_rate(self, job_data: Dict, metrics: Dict) -> float:
        """Calculate upload success rate."""
        total_generated = self._calculate_total_generated(job_data)
        items_uploaded = metrics.get('items_uploaded', 0)
        
        if total_generated > 0:
            return round((items_uploaded / total_generated) * 100, 2)
        return 0.0
    
    def _calculate_overall_quality_score(self, metrics: Dict) -> float:
        """Calculate overall quality score across all work items."""
        total_items = 0
        weighted_score = 0
        
        # Weight different ratings
        weights = {'excellent': 100, 'good': 75, 'fair': 50, 'poor': 25}
        
        for stage in ['epic_quality', 'feature_quality', 'story_quality', 'task_quality']:
            if stage in metrics:
                for rating, count in metrics[stage].items():
                    if rating in weights:
                        total_items += count
                        weighted_score += weights[rating] * count
        
        if total_items > 0:
            return round(weighted_score / total_items, 2)
        return 0.0
    
    def _calculate_rejection_rate(self, metrics: Dict) -> float:
        """Calculate rejection rate."""
        total_assessed = metrics.get('total_rejected', 0) + metrics.get('total_approved', 0)
        if total_assessed > 0:
            return round((metrics.get('total_rejected', 0) / total_assessed) * 100, 2)
        return 0.0
    
    def _calculate_parallel_efficiency(self, metrics: Dict) -> float:
        """Calculate parallel processing efficiency."""
        # Simple efficiency calculation based on latency
        if metrics.get('high_latency_ops'):
            avg_latency = sum(op['latency_ms'] for op in metrics['high_latency_ops']) / len(metrics['high_latency_ops'])
            # Assume ideal latency is 10000ms (10 seconds)
            efficiency = min(100, (10000 / avg_latency) * 100)
            return round(efficiency, 2)
        return 100.0
    
    def _format_duration(self, seconds: float) -> str:
        """Format duration in human-readable format."""
        if seconds < 60:
            return f"{seconds:.1f} seconds"
        elif seconds < 3600:
            minutes = seconds / 60
            return f"{minutes:.1f} minutes"
        else:
            hours = seconds / 3600
            return f"{hours:.1f} hours"
    
    def _generate_recommendations(self, metrics: Dict, job_data: Dict) -> List[str]:
        """Generate recommendations based on metrics."""
        recommendations = []
        
        # Check rejection rate
        rejection_rate = self._calculate_rejection_rate(metrics)
        if rejection_rate > 30:
            recommendations.append(f"High rejection rate ({rejection_rate}%). Consider adjusting quality thresholds or improving prompts.")
        
        # Check for high latency
        if metrics.get('high_latency_ops'):
            recommendations.append("High latency detected in some operations. Consider optimizing parallel processing settings.")
        
        # Check overall quality
        overall_quality = self._calculate_overall_quality_score(metrics)
        if overall_quality < 70:
            recommendations.append(f"Overall quality score ({overall_quality}/100) could be improved. Review agent prompts and domain alignment.")
        
        # Check test artifacts
        if not job_data.get('test_cases_generated', 0):
            recommendations.append("No test artifacts were generated. Consider enabling test generation for comprehensive coverage.")
        
        return recommendations
    
    def format_markdown_report(self, report_data: Dict[str, Any]) -> str:
        """Format the report data as a markdown document."""
        md = []
        
        # Header
        md.append("# Backlog Generation Summary Report")
        md.append(f"\n**Project**: {report_data['metadata']['project_name']}")
        md.append(f"**Generated**: {report_data['metadata']['generation_date']}")
        md.append(f"**Domain**: {report_data['metadata']['domain']}")
        md.append(f"**Area Path**: {report_data['metadata']['area_path']}")
        md.append("\n---\n")
        
        # Vision Statement Section
        md.append("## Product Vision Statement")
        vision = report_data['vision_statement']
        md.append(f"\n**Quality Score**: {vision['quality_score']}/100 ({vision['quality_rating']})")
        md.append(f"\n**Key Elements Present**: {', '.join(vision['key_elements'])}")
        md.append("\n### Vision Statement:")
        md.append("```")
        md.append(vision['statement'])
        md.append("```\n")
        
        # Generation Summary
        md.append("## Generation Summary")
        summary = report_data['generation_summary']
        md.append(f"\n- **Execution Time**: {summary['execution_time_formatted']}")
        md.append(f"- **Parallel Processing**: {'Yes' if summary['parallel_processing'] else 'No'}")
        if summary['parallel_processing']:
            md.append(f"- **Worker Count**: {summary['worker_count']}")
        md.append(f"- **Test Artifacts**: {'Included' if summary['test_artifacts_included'] else 'Not Included'}")
        md.append("")
        
        # Work Item Statistics
        md.append("## Work Item Statistics")
        stats = report_data['work_item_statistics']
        md.append(f"\n**Total Generated**: {stats['total_generated']} work items")
        md.append("\n### Breakdown by Type:")
        for item_type, count in stats['by_type'].items():
            if count > 0:
                md.append(f"- **{item_type.title()}**: {count}")
        
        upload = stats['azure_devops_upload']
        md.append(f"\n### Azure DevOps Upload:")
        md.append(f"- **Items Uploaded**: {upload['total_uploaded']}")
        md.append(f"- **Success Rate**: {upload['upload_success_rate']}%")
        md.append("")
        
        # Quality Assessment
        md.append("## Quality Assessment")
        quality = report_data['quality_assessment']
        md.append(f"\n**Overall Quality Score**: {quality['overall_quality_score']}/100")
        
        md.append("\n### Quality Distribution by Stage:")
        for stage, ratings in quality['by_stage'].items():
            if any(ratings.values()):
                md.append(f"\n**{stage.title()}**:")
                for rating, count in ratings.items():
                    if count > 0:
                        md.append(f"- {rating.title()}: {count}")
        
        rejection = quality['rejection_analysis']
        md.append(f"\n### Rejection Analysis:")
        md.append(f"- **Total Rejected**: {rejection['total_rejected']}")
        md.append(f"- **Total Approved**: {rejection['total_approved']}")
        md.append(f"- **Rejection Rate**: {rejection['rejection_rate']}%")
        md.append(f"- **Replacement Attempts**: {rejection['replacement_attempts']}")
        
        if rejection['most_common_rejection_reasons']:
            md.append("\n**Most Common Rejection Reasons**:")
            # Count occurrences
            reason_counts = {}
            for reason in rejection['most_common_rejection_reasons']:
                reason_counts[reason] = reason_counts.get(reason, 0) + 1
            
            # Sort by count and show top 5
            sorted_reasons = sorted(reason_counts.items(), key=lambda x: x[1], reverse=True)[:5]
            for reason, count in sorted_reasons:
                md.append(f"- {reason} ({count} occurrences)")
        md.append("")
        
        # Performance Analysis
        md.append("## Performance Analysis")
        perf = report_data['performance_analysis']
        md.append(f"\n- **Hardware Tier**: {perf['hardware_tier']}")
        md.append(f"- **CPU Cores**: {perf['cpu_cores']}")
        md.append(f"- **Memory**: {perf['memory_gb']} GB")
        md.append(f"- **Parallel Efficiency**: {perf['parallel_efficiency']}%")
        
        if perf['high_latency_operations']:
            md.append("\n**High Latency Operations**:")
            for op in perf['high_latency_operations']:
                md.append(f"- {op['stage']}: {op['latency_ms']/1000:.1f} seconds")
        md.append("")
        
        # Domain Alignment
        md.append("## Domain Alignment")
        domain = report_data['domain_alignment']
        md.append(f"\n- **Domain**: {domain['domain']}")
        md.append(f"- **Domain Terminology Usage**: {domain['domain_terminology_usage']} terms")
        md.append(f"- **Vision Alignment Score**: {domain['vision_alignment_score']}%")
        md.append("")
        
        # LLM Models Used
        md.append("## LLM Models Configuration")
        for agent, model in report_data['metadata']['llm_models'].items():
            md.append(f"- **{agent}**: {model}")
        md.append("")
        
        # Recommendations
        if report_data['recommendations']:
            md.append("## Recommendations")
            for rec in report_data['recommendations']:
                md.append(f"- {rec}")
            md.append("")
        
        # Footer
        md.append("---")
        md.append(f"\n*Report generated on {report_data['metadata']['report_generated']}*")
        
        return "\n".join(md)