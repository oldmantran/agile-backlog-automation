"""
Cost tracking module for LLM usage across agents.
Aggregates costs per job and provides reporting.
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
from utils.safe_logger import get_safe_logger

logger = get_safe_logger(__name__)

@dataclass
class AgentCost:
    """Track cost for a single agent execution."""
    agent_name: str
    provider: str
    model: str
    prompt_tokens: int
    completion_tokens: int
    cost: float
    timestamp: datetime = field(default_factory=datetime.now)
    
@dataclass 
class JobCostSummary:
    """Summary of costs for an entire job."""
    job_id: str
    total_cost: float
    total_prompt_tokens: int
    total_completion_tokens: int
    agent_costs: List[AgentCost]
    start_time: datetime
    end_time: Optional[datetime] = None
    
    @property
    def duration_minutes(self) -> float:
        """Calculate job duration in minutes."""
        if self.end_time:
            return (self.end_time - self.start_time).total_seconds() / 60
        return 0
    
    @property
    def cost_by_agent(self) -> Dict[str, float]:
        """Group costs by agent."""
        costs = {}
        for ac in self.agent_costs:
            if ac.agent_name not in costs:
                costs[ac.agent_name] = 0
            costs[ac.agent_name] += ac.cost
        return costs
    
    @property
    def cost_by_provider(self) -> Dict[str, float]:
        """Group costs by provider."""
        costs = {}
        for ac in self.agent_costs:
            if ac.provider not in costs:
                costs[ac.provider] = 0
            costs[ac.provider] += ac.cost
        return costs

class CostTracker:
    """Track and aggregate LLM costs across workflow execution."""
    
    def __init__(self):
        self.job_costs: Dict[str, JobCostSummary] = {}
        
    def start_job(self, job_id: str):
        """Start tracking costs for a new job."""
        self.job_costs[job_id] = JobCostSummary(
            job_id=job_id,
            total_cost=0.0,
            total_prompt_tokens=0,
            total_completion_tokens=0,
            agent_costs=[],
            start_time=datetime.now()
        )
        logger.info(f"[COST] Started cost tracking for job {job_id}")
        
    def track_agent_cost(self, job_id: str, agent_name: str, provider: str, 
                        model: str, prompt_tokens: int, completion_tokens: int, cost: float):
        """Track cost for a single agent execution."""
        if job_id not in self.job_costs:
            logger.warning(f"[COST] Job {job_id} not found, creating new tracking")
            self.start_job(job_id)
            
        agent_cost = AgentCost(
            agent_name=agent_name,
            provider=provider,
            model=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            cost=cost
        )
        
        summary = self.job_costs[job_id]
        summary.agent_costs.append(agent_cost)
        summary.total_cost += cost
        summary.total_prompt_tokens += prompt_tokens
        summary.total_completion_tokens += completion_tokens
        
        logger.info(
            f"[COST] {agent_name} ({provider}/{model}): "
            f"${cost:.4f} ({prompt_tokens} + {completion_tokens} tokens)"
        )
        
    def end_job(self, job_id: str) -> Optional[JobCostSummary]:
        """End cost tracking for a job and return summary."""
        if job_id not in self.job_costs:
            logger.warning(f"[COST] Job {job_id} not found for ending")
            return None
            
        summary = self.job_costs[job_id]
        summary.end_time = datetime.now()
        
        # Log comprehensive summary
        logger.info(f"[COST] ========== Job Cost Summary: {job_id} ==========")
        logger.info(f"[COST] Total Cost: ${summary.total_cost:.4f}")
        logger.info(f"[COST] Total Tokens: {summary.total_prompt_tokens + summary.total_completion_tokens:,} "
                   f"(Prompt: {summary.total_prompt_tokens:,}, Completion: {summary.total_completion_tokens:,})")
        logger.info(f"[COST] Duration: {summary.duration_minutes:.1f} minutes")
        logger.info(f"[COST] Cost/minute: ${summary.total_cost / max(summary.duration_minutes, 0.1):.4f}")
        
        # Cost by agent
        logger.info("[COST] --- Cost by Agent ---")
        for agent, cost in summary.cost_by_agent.items():
            percentage = (cost / summary.total_cost * 100) if summary.total_cost > 0 else 0
            logger.info(f"[COST]   {agent}: ${cost:.4f} ({percentage:.1f}%)")
            
        # Cost by provider
        logger.info("[COST] --- Cost by Provider ---")
        for provider, cost in summary.cost_by_provider.items():
            percentage = (cost / summary.total_cost * 100) if summary.total_cost > 0 else 0
            logger.info(f"[COST]   {provider}: ${cost:.4f} ({percentage:.1f}%)")
            
        logger.info(f"[COST] ===============================================")
        
        return summary
        
    def get_job_summary(self, job_id: str) -> Optional[JobCostSummary]:
        """Get current cost summary for a job."""
        return self.job_costs.get(job_id)
        
    def get_formatted_summary(self, job_id: str) -> Dict[str, Any]:
        """Get formatted summary for reporting."""
        summary = self.get_job_summary(job_id)
        if not summary:
            return {}
            
        return {
            'job_id': job_id,
            'total_cost': f"${summary.total_cost:.4f}",
            'total_tokens': summary.total_prompt_tokens + summary.total_completion_tokens,
            'prompt_tokens': summary.total_prompt_tokens,
            'completion_tokens': summary.total_completion_tokens,
            'duration_minutes': round(summary.duration_minutes, 1),
            'cost_per_minute': f"${summary.total_cost / max(summary.duration_minutes, 0.1):.4f}",
            'agent_costs': {
                agent: f"${cost:.4f}" 
                for agent, cost in summary.cost_by_agent.items()
            },
            'provider_costs': {
                provider: f"${cost:.4f}"
                for provider, cost in summary.cost_by_provider.items()
            },
            'execution_count': len(summary.agent_costs)
        }

# Global cost tracker instance
cost_tracker = CostTracker()