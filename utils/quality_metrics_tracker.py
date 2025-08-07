#!/usr/bin/env python3
"""
Quality Metrics Tracker

Tracks agent performance metrics to identify patterns and improvement opportunities:
- First-try success rates by agent
- Quality score distributions 
- Retry patterns and failure reasons
- Model performance comparisons
- Domain-specific quality patterns
"""

import json
import sqlite3
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from pathlib import Path

logger = logging.getLogger(__name__)

@dataclass
class QualityAttempt:
    """Represents a single quality assessment attempt."""
    attempt_number: int
    rating: str
    score: int
    strengths: List[str]
    weaknesses: List[str]
    improvement_suggestions: List[str]
    timestamp: str

@dataclass
class QualityMetrics:
    """Comprehensive quality metrics for a single work item generation."""
    job_id: str
    agent_name: str
    work_item_type: str  # Epic, Feature, User Story, Task
    work_item_title: str
    domain: str
    model_provider: str
    model_name: str
    
    # Attempt tracking
    total_attempts: int
    final_rating: str
    final_score: int
    first_try_excellent: bool
    success_attempt: Optional[int]  # Which attempt succeeded (None if all failed)
    
    # Quality progression
    attempts: List[QualityAttempt]
    
    # Context factors
    context_length: int  # Length of input context
    template_used: str
    parallel_processing: bool
    
    # Timing
    start_time: str
    end_time: str
    total_duration_seconds: float
    
    # Failure analysis
    failed: bool
    failure_reason: Optional[str]

class QualityMetricsTracker:
    """Tracks and analyzes agent quality performance metrics."""
    
    def __init__(self, db_path: str = "backlog_jobs.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize quality metrics tracking tables."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Quality metrics table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS quality_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    job_id TEXT NOT NULL,
                    agent_name TEXT NOT NULL,
                    work_item_type TEXT NOT NULL,
                    work_item_title TEXT,
                    domain TEXT,
                    model_provider TEXT,
                    model_name TEXT,
                    
                    total_attempts INTEGER,
                    final_rating TEXT,
                    final_score INTEGER,
                    first_try_excellent BOOLEAN,
                    success_attempt INTEGER,
                    
                    context_length INTEGER,
                    template_used TEXT,
                    parallel_processing BOOLEAN,
                    
                    start_time TEXT,
                    end_time TEXT,
                    total_duration_seconds REAL,
                    
                    failed BOOLEAN,
                    failure_reason TEXT,
                    
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Quality attempts table (detailed attempt history)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS quality_attempts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    metrics_id INTEGER,
                    attempt_number INTEGER,
                    rating TEXT,
                    score INTEGER,
                    strengths TEXT,  -- JSON array
                    weaknesses TEXT,  -- JSON array
                    improvement_suggestions TEXT,  -- JSON array
                    timestamp TEXT,
                    
                    FOREIGN KEY (metrics_id) REFERENCES quality_metrics (id)
                )
            ''')
            
            # Indexes for performance
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_quality_metrics_job_agent ON quality_metrics (job_id, agent_name)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_quality_metrics_model ON quality_metrics (model_provider, model_name)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_quality_metrics_domain ON quality_metrics (domain)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_quality_attempts_metrics ON quality_attempts (metrics_id)')
            
            conn.commit()
    
    def start_tracking(self, job_id: str, agent_name: str, work_item_type: str, 
                      work_item_title: str, context: Dict[str, Any]) -> str:
        """Start tracking quality metrics for a work item generation."""
        metrics_id = f"{job_id}_{agent_name}_{work_item_type}_{datetime.now().strftime('%H%M%S')}"
        
        # Extract context information
        domain = context.get('domain', 'unknown')
        model_provider = context.get('model_provider', 'unknown')
        model_name = context.get('model_name', 'unknown')
        context_length = len(str(context.get('product_vision', '')))
        template_used = context.get('template_name', 'default')
        parallel_processing = context.get('parallel_processing', False)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO quality_metrics (
                    job_id, agent_name, work_item_type, work_item_title, domain,
                    model_provider, model_name, context_length, template_used,
                    parallel_processing, start_time, failed
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                job_id, agent_name, work_item_type, work_item_title[:100], domain,
                model_provider, model_name, context_length, template_used,
                parallel_processing, datetime.now().isoformat(), False
            ))
            
            # Get the actual database row ID
            db_metrics_id = cursor.lastrowid
        
        logger.info(f"Started quality tracking: {metrics_id} (DB ID: {db_metrics_id})")
        return str(db_metrics_id)
    
    def record_attempt(self, metrics_id: str, attempt_number: int, rating: str, 
                      score: int, strengths: List[str], weaknesses: List[str], 
                      improvement_suggestions: List[str]):
        """Record a quality assessment attempt."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO quality_attempts (
                    metrics_id, attempt_number, rating, score, strengths,
                    weaknesses, improvement_suggestions, timestamp
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                int(metrics_id), attempt_number, rating, score,
                json.dumps(strengths), json.dumps(weaknesses),
                json.dumps(improvement_suggestions), datetime.now().isoformat()
            ))
        
        logger.debug(f"Recorded attempt {attempt_number} for metrics {metrics_id}: {rating} ({score})")
    
    def complete_tracking(self, metrics_id: str, final_rating: str, final_score: int,
                         success_attempt: Optional[int], failed: bool = False,
                         failure_reason: Optional[str] = None):
        """Complete quality tracking with final results."""
        first_try_excellent = (success_attempt == 1 and final_rating == "EXCELLENT") if success_attempt else False
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Get total attempts
            cursor.execute('SELECT COUNT(*) FROM quality_attempts WHERE metrics_id = ?', (int(metrics_id),))
            total_attempts = cursor.fetchone()[0]
            
            # Update main metrics record
            cursor.execute('''
                UPDATE quality_metrics SET
                    total_attempts = ?, final_rating = ?, final_score = ?,
                    first_try_excellent = ?, success_attempt = ?,
                    end_time = ?, failed = ?, failure_reason = ?
                WHERE id = ?
            ''', (
                total_attempts, final_rating, final_score, first_try_excellent,
                success_attempt, datetime.now().isoformat(), failed, failure_reason,
                int(metrics_id)
            ))
            
            # Update duration
            cursor.execute('''
                UPDATE quality_metrics SET
                    total_duration_seconds = (
                        julianday(end_time) - julianday(start_time)
                    ) * 86400
                WHERE id = ?
            ''', (int(metrics_id),))
        
        logger.info(f"Completed quality tracking {metrics_id}: {final_rating} ({final_score}) in {total_attempts} attempts")
    
    def get_agent_performance_summary(self, agent_name: Optional[str] = None, 
                                    days: int = 7) -> Dict[str, Any]:
        """Get performance summary for agent(s) over specified days."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            where_clause = "WHERE datetime(created_at) >= datetime('now', '-{} days')".format(days)
            if agent_name:
                where_clause += " AND agent_name = ?"
                params = (agent_name,)
            else:
                params = ()
            
            # Overall metrics
            cursor.execute(f'''
                SELECT 
                    agent_name,
                    COUNT(*) as total_items,
                    AVG(total_attempts) as avg_attempts,
                    AVG(final_score) as avg_final_score,
                    SUM(CASE WHEN first_try_excellent = 1 THEN 1 ELSE 0 END) as first_try_excellent_count,
                    SUM(CASE WHEN final_rating = 'EXCELLENT' THEN 1 ELSE 0 END) as excellent_count,
                    SUM(CASE WHEN failed = 1 THEN 1 ELSE 0 END) as failed_count,
                    AVG(total_duration_seconds) as avg_duration
                FROM quality_metrics 
                {where_clause}
                GROUP BY agent_name
                ORDER BY total_items DESC
            ''', params)
            
            results = cursor.fetchall()
            
            summary = {}
            for row in results:
                agent = row[0]
                total = row[1]
                summary[agent] = {
                    'total_items': total,
                    'avg_attempts': round(row[2], 2) if row[2] else 0,
                    'avg_final_score': round(row[3], 1) if row[3] else 0,
                    'first_try_excellent_rate': round((row[4] / total) * 100, 1) if total > 0 else 0,
                    'overall_excellent_rate': round((row[5] / total) * 100, 1) if total > 0 else 0,
                    'failure_rate': round((row[6] / total) * 100, 1) if total > 0 else 0,
                    'avg_duration_seconds': round(row[7], 2) if row[7] else 0
                }
            
            return summary
    
    def get_model_comparison(self, days: int = 7) -> Dict[str, Any]:
        """Compare performance across different models."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT 
                    model_provider,
                    model_name,
                    COUNT(*) as total_items,
                    AVG(total_attempts) as avg_attempts,
                    AVG(final_score) as avg_final_score,
                    SUM(CASE WHEN first_try_excellent = 1 THEN 1 ELSE 0 END) as first_try_excellent_count,
                    SUM(CASE WHEN final_rating = 'EXCELLENT' THEN 1 ELSE 0 END) as excellent_count
                FROM quality_metrics 
                WHERE datetime(created_at) >= datetime('now', '-{} days')
                GROUP BY model_provider, model_name
                ORDER BY avg_final_score DESC
            '''.format(days))
            
            results = cursor.fetchall()
            
            comparison = {}
            for row in results:
                model_key = f"{row[0]}/{row[1]}"
                total = row[2]
                comparison[model_key] = {
                    'total_items': total,
                    'avg_attempts': round(row[3], 2) if row[3] else 0,
                    'avg_final_score': round(row[4], 1) if row[4] else 0,
                    'first_try_excellent_rate': round((row[5] / total) * 100, 1) if total > 0 else 0,
                    'overall_excellent_rate': round((row[6] / total) * 100, 1) if total > 0 else 0
                }
            
            return comparison
    
    def generate_improvement_report(self) -> str:
        """Generate a comprehensive improvement report."""
        agent_summary = self.get_agent_performance_summary()
        model_comparison = self.get_model_comparison()
        
        report = ["# Quality Metrics Analysis Report\n"]
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        # Agent performance
        report.append("## Agent Performance Summary (Last 7 Days)\n")
        for agent, metrics in agent_summary.items():
            report.append(f"### {agent}")
            report.append(f"- Total Items: {metrics['total_items']}")
            report.append(f"- First-Try EXCELLENT Rate: {metrics['first_try_excellent_rate']}%")
            report.append(f"- Overall EXCELLENT Rate: {metrics['overall_excellent_rate']}%")
            report.append(f"- Average Attempts: {metrics['avg_attempts']}")
            report.append(f"- Average Final Score: {metrics['avg_final_score']}")
            report.append(f"- Failure Rate: {metrics['failure_rate']}%")
            report.append("")
        
        # Model comparison
        report.append("## Model Performance Comparison\n")
        for model, metrics in model_comparison.items():
            report.append(f"### {model}")
            report.append(f"- First-Try EXCELLENT Rate: {metrics['first_try_excellent_rate']}%")
            report.append(f"- Average Final Score: {metrics['avg_final_score']}")
            report.append(f"- Average Attempts: {metrics['avg_attempts']}")
            report.append("")
        
        # Recommendations
        report.append("## Improvement Recommendations\n")
        
        # Find worst performing agent
        worst_agent = min(agent_summary.items(), key=lambda x: x[1]['first_try_excellent_rate'])
        report.append(f"- **Priority Agent**: {worst_agent[0]} needs prompt optimization (only {worst_agent[1]['first_try_excellent_rate']}% first-try EXCELLENT)")
        
        # Find best model
        if model_comparison:
            best_model = max(model_comparison.items(), key=lambda x: x[1]['first_try_excellent_rate'])
            report.append(f"- **Recommended Model**: {best_model[0]} shows best performance ({best_model[1]['first_try_excellent_rate']}% first-try EXCELLENT)")
        
        return "\n".join(report)

# Global instance for easy access
quality_tracker = QualityMetricsTracker()