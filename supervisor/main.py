#!/usr/bin/env python3
"""
Main entry point for the Agile Backlog Automation Supervisor.

This module provides command-line interface and programmatic access to the
complete workflow orchestration system.
"""

import argparse
import sys
import os
import yaml
import json
from typing import Dict, Any, Optional

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from supervisor.supervisor import WorkflowSupervisor
from config.config_loader import Config
from utils.logger import setup_logger


def main():
    """Main entry point for the supervisor."""
    parser = argparse.ArgumentParser(
        description="Agile Backlog Automation Supervisor - Orchestrate multi-agent workflow",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Interactive mode with all stages
  python supervisor/main.py

  # Run with project type context
  python supervisor/main.py --project-type fintech --project-name "CryptoWallet"

  # Run specific stages only
  python supervisor/main.py --stages epic_strategist feature_decomposer_agent user_story_decomposer_agent

  # Resume from existing output
  python supervisor/main.py --resume-from output/intermediate_epic_strategist_20250630_120000.json

  # Full automation with Azure DevOps integration
  python supervisor/main.py --input vision.yaml --project-type healthcare --azure-devops --no-review

  # Human review mode
  python supervisor/main.py --human-review --save-intermediate
        """
    )
    
    # Input options
    parser.add_argument(
        '--input', 
        type=str, 
        help='Input YAML file with product vision and optional existing data'
    )
    parser.add_argument(
        '--resume-from',
        type=str,
        help='Resume workflow from existing JSON output file'
    )
    
    # Workflow control
    parser.add_argument(
        '--stages',
        nargs='+',
        choices=['epic_strategist', 'feature_decomposer_agent', 'user_story_decomposer_agent', 'developer_agent', 'qa_lead_agent'],
        help='Specific stages to execute (default: all)'
    )
    parser.add_argument(
        '--human-review',
        action='store_true',
        help='Enable human review checkpoints between stages'
    )
    parser.add_argument(
        '--no-review',
        action='store_true',
        help='Disable all human review prompts (full automation)'
    )
    
    # Context configuration
    parser.add_argument(
        '--project-type',
        choices=['fintech', 'healthcare', 'ecommerce', 'education', 'mobile_app', 'saas'],
        help='Apply predefined project context'
    )
    parser.add_argument(
        '--project-name',
        type=str,
        help='Override project name'
    )
    parser.add_argument(
        '--domain',
        type=str,
        help='Override project domain'
    )
    parser.add_argument(
        '--tech-stack',
        type=str,
        help='Override technology stack'
    )
    parser.add_argument(
        '--timeline',
        type=str,
        help='Override project timeline'
    )
    parser.add_argument(
        '--team-size',
        type=str,
        help='Override team size'
    )
    
    # Output and integration options
    parser.add_argument(
        '--save-intermediate',
        action='store_true',
        help='Save intermediate outputs after each stage'
    )
    parser.add_argument(
        '--azure-devops',
        action='store_true',
        help='Create work items in Azure DevOps'
    )
    parser.add_argument(
        '--output-dir',
        type=str,
        default='output',
        help='Directory for output files (default: output)'
    )
    
    # Configuration
    parser.add_argument(
        '--config',
        type=str,
        help='Path to custom configuration file'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    
    args = parser.parse_args()
    
    # Setup logging
    log_level = 'DEBUG' if args.verbose else 'INFO'
    logger = setup_logger("supervisor_main", "logs/supervisor_main.log", log_level)
    
    try:
        # Initialize supervisor
        logger.info("Initializing Workflow Supervisor")
        supervisor = WorkflowSupervisor(args.config)
        
        # Configure project context
        custom_context = build_custom_context(args)
        supervisor.configure_project_context(args.project_type, custom_context)
        
        # Determine execution mode
        if args.resume_from:
            execute_resume_mode(supervisor, args, logger)
        elif args.input:
            execute_file_mode(supervisor, args, logger)
        else:
            execute_interactive_mode(supervisor, args, logger)
            
    except KeyboardInterrupt:
        logger.info("Workflow interrupted by user")
        print("\\n❌ Workflow interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Workflow failed: {e}", exc_info=True)
        print(f"❌ Workflow failed: {e}")
        sys.exit(1)


def build_custom_context(args) -> Dict[str, Any]:
    """Build custom context from command line arguments."""
    context = {}
    
    if args.project_name:
        context['project_name'] = args.project_name
    if args.domain:
        context['domain'] = args.domain
    if args.tech_stack:
        context['tech_stack'] = args.tech_stack
    if args.timeline:
        context['timeline'] = args.timeline
    if args.team_size:
        context['team_size'] = args.team_size
    
    return context if context else None


def execute_interactive_mode(supervisor: WorkflowSupervisor, args, logger):
    """Execute workflow in interactive mode."""
    logger.info("Starting interactive mode")
    
    print("🧠 Agile Backlog Automation Supervisor")
    print("=" * 50)
    
    # Get product vision from user
    print("\\nEnter your product vision:")
    print("(Tip: Describe what you want to build, who will use it, and why it matters)")
    vision = input("Vision: ").strip()
    
    if not vision:
        print("❌ Product vision is required")
        sys.exit(1)
    
    # Execute workflow
    execute_workflow(supervisor, vision, args, logger)


def execute_file_mode(supervisor: WorkflowSupervisor, args, logger):
    """Execute workflow from input file."""
    logger.info(f"Starting file mode with input: {args.input}")
    
    try:
        with open(args.input, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        
        vision = data.get('product_vision', '')
        if not vision:
            raise ValueError("Input file must contain 'product_vision' field")
        
        print(f"📄 Loaded product vision from: {args.input}")
        print(f"Vision: {vision[:100]}...")
        
        # Execute workflow
        execute_workflow(supervisor, vision, args, logger)
        
    except Exception as e:
        logger.error(f"Failed to load input file: {e}")
        print(f"❌ Failed to load input file: {e}")
        sys.exit(1)


def execute_resume_mode(supervisor: WorkflowSupervisor, args, logger):
    """Resume workflow from existing output."""
    logger.info(f"Resuming workflow from: {args.resume_from}")
    
    try:
        with open(args.resume_from, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Determine which stage to resume from based on filename
        filename = os.path.basename(args.resume_from)
        if 'epic_strategist' in filename:
            resume_stage = 'feature_decomposer_agent'
        elif 'feature_decomposer_agent' in filename:
            resume_stage = 'developer_agent'
        elif 'developer_agent' in filename:
            resume_stage = 'qa_lead_agent'
        else:
            # If can't determine, ask user
            all_stages = ['epic_strategist', 'feature_decomposer_agent', 'user_story_decomposer_agent', 'developer_agent', 'qa_lead_agent']
            print("Available stages:")
            for i, stage in enumerate(all_stages, 1):
                print(f"{i}. {stage}")
            
            choice = input("Which stage to resume from? (1-4): ").strip()
            try:
                resume_stage = all_stages[int(choice) - 1]
            except (ValueError, IndexError):
                print("❌ Invalid choice")
                sys.exit(1)
        
        print(f"🔄 Resuming from stage: {resume_stage}")
        
        # Resume workflow
        result = supervisor.resume_workflow_from_stage(resume_stage, data)
        
        print(f"\\n✅ Workflow completed successfully!")
        print_execution_summary(result)
        
    except Exception as e:
        logger.error(f"Failed to resume workflow: {e}")
        print(f"❌ Failed to resume workflow: {e}")
        sys.exit(1)


def execute_workflow(supervisor: WorkflowSupervisor, vision: str, args, logger):
    """Execute the main workflow."""
    logger.info("Executing workflow")
    
    # Determine human review setting
    human_review = args.human_review and not args.no_review
    
    # Execute workflow
    result = supervisor.execute_workflow(
        product_vision=vision,
        stages=args.stages,
        human_review=human_review,
        save_outputs=True,  # Always save outputs
        integrate_azure=args.azure_devops
    )
    
    print(f"\\n✅ Workflow completed successfully!")
    print_execution_summary(result)
    
    # Show Azure DevOps integration results
    if args.azure_devops and result.get('azure_integration'):
        azure_result = result['azure_integration']
        if azure_result['status'] == 'success':
            print(f"\\n🔗 Azure DevOps Integration:")
            print(f"   Created {len(azure_result['work_items_created'])} work items")
        else:
            print(f"\\n❌ Azure DevOps Integration Failed:")
            print(f"   Error: {azure_result.get('error', 'Unknown error')}")


def print_execution_summary(result: Dict[str, Any]):
    """Print a summary of workflow execution."""
    metadata = result.get('metadata', {})
    summary = metadata.get('execution_summary', {})
    
    print("\\n📊 Execution Summary:")
    print(f"   Epics Generated: {summary.get('epics_generated', 0)}")
    print(f"   Features Generated: {summary.get('features_generated', 0)}")
    print(f"   Tasks Generated: {summary.get('tasks_generated', 0)}")
    print(f"   Stages Completed: {summary.get('stages_completed', 0)}")
    
    if summary.get('execution_time_seconds'):
        print(f"   Execution Time: {summary['execution_time_seconds']:.1f} seconds")
    
    # Show output files
    outputs = metadata.get('outputs_generated', [])
    if outputs:
        print(f"\\n💾 Output Files:")
        for output in outputs[-2:]:  # Show last 2 outputs
            print(f"   {output}")


if __name__ == "__main__":
    main()
