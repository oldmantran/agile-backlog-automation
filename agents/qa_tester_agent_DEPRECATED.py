"""
DEPRECATED QA Tester Agent

This agent has been deprecated and replaced by the distributed QA architecture:
- QA Lead Agent: Orchestrates testing activities and handles Backlog Sweeper assignments
- Test Plan Agent: Creates test plans for features
- Test Suite Agent: Creates test suites and assigns orphaned test cases
- Test Case Agent: Creates individual test cases

All functionality previously handled by QATesterAgent has been distributed among these specialized agents.

The supervisor should route all testing requests to the QA Lead Agent, which will then
delegate work to the appropriate sub-agents.

Date Deprecated: July 12, 2025
Replacement: QA Lead Agent + distributed testing agents
"""

# This file remains for backward compatibility but should not be used
# Import the new QA Lead Agent instead

from agents.qa_lead_agent import QALeadAgent

class QATesterAgent:
    """DEPRECATED - Use QALeadAgent instead"""
    
    def __init__(self, config):
        raise DeprecationWarning(
            "QATesterAgent is deprecated. Use QALeadAgent with distributed testing agents instead."
        )
