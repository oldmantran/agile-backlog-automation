# Modular Prompt System Guide

The Agile Backlog Automation system now features a powerful **modular, template-based prompt system** that allows for dynamic context injection and role-specific prompts.

## 🎯 Overview

### Key Features
- **Role-Specific Prompts**: Each agent has specialized, domain-aware prompts
- **Dynamic Context**: Prompts adapt based on project type, domain, and custom context
- **Template-Based**: Easy to customize and maintain prompt templates
- **Variable Substitution**: Support for placeholder variables like `${project_name}`, `${domain}`

### Supported Project Types
- **Fintech**: Banking, payments, cryptocurrency, financial services
- **Healthcare**: Medical apps, patient management, HIPAA compliance
- **E-commerce**: Online retail, marketplace, payment processing
- **Education**: Learning platforms, student management, FERPA compliance
- **Mobile App**: iOS/Android applications, cross-platform development
- **SaaS**: Software as a Service, multi-tenant applications

## 🚀 Quick Start

### Basic Usage
```bash
# Run with project type context
python tools/run_pipeline.py --project-type fintech

# Run with custom project context
python tools/run_pipeline.py \
  --project-name "MyApp" \
  --domain "e-commerce" \
  --tech-stack "React, Node.js, PostgreSQL" \
  --timeline "4 months"

# Run specific stage with context
python tools/run_pipeline.py --run epic --project-type healthcare --project-name "PatientPortal"
```

### Advanced Context Customization
```bash
# Full context override
python tools/run_pipeline.py \
  --project-type saas \
  --project-name "TaskMaster Pro" \
  --domain "productivity software" \
  --tech-stack "Vue.js, Python FastAPI, MongoDB" \
  --team-size "8-12 developers" \
  --timeline "12 months"
```

## 📝 Context Variables

### Project Information
- `project_name`: Name of your project
- `domain`: Project domain/industry
- `methodology`: Development methodology (default: Agile/Scrum)

### Technical Context
- `tech_stack`: Technology stack and frameworks
- `architecture_pattern`: System architecture (default: Microservices)
- `database_type`: Database technology
- `cloud_platform`: Cloud provider (AWS, Azure, GCP)
- `platform`: Target platform (Web, Mobile, Desktop)

### Team Context
- `team_size`: Development team size
- `sprint_duration`: Sprint length (default: 2 weeks)
- `experience_level`: Team experience level

### Business Context
- `target_users`: Primary user personas
- `timeline`: Project timeline
- `budget_constraints`: Budget considerations
- `compliance_requirements`: Regulatory requirements

### Quality Context
- `test_environment`: Testing infrastructure
- `quality_standards`: Quality standards and practices
- `security_requirements`: Security standards

## 🛠️ Customizing Prompts

### Prompt Template Structure
Prompt templates are located in the `prompts/` directory:
- `prompts/epic_strategist.txt`
- `prompts/feature_decomposer.txt`
- `prompts/developer_agent.txt`
- `prompts/qa_tester_agent.txt`

### Adding Variables
Use Python string.Template syntax for variables:
```text
You are working on ${project_name} in the ${domain} domain.
The target users are ${target_users}.
Technology stack: ${tech_stack}
```

### Required Variables by Agent

#### Epic Strategist
- `project_name`, `domain`, `target_users`, `timeline`, `budget_constraints`

#### Feature Decomposer
- `project_name`, `domain`, `target_users`, `platform`, `integrations`, `methodology`

#### Developer Agent
- `project_name`, `domain`, `tech_stack`, `architecture_pattern`, `database_type`, `cloud_platform`, `team_size`, `sprint_duration`

#### QA Tester Agent
- No required variables (uses default context)

## 🧪 Testing the System

### Test Prompt Templates
```bash
# Test all templates and variable substitution
python tools/test_prompt_system.py
```

### Validate Templates
```python
from utils.prompt_manager import prompt_manager

# Check template status
templates_info = prompt_manager.list_templates()
for agent, info in templates_info.items():
    print(f"{agent}: {info['required_variables']}")

# Validate specific template
validation = prompt_manager.validate_template('epic_strategist')
print(validation)
```

## 📋 Project Type Presets

### Fintech Context
```yaml
domain: financial technology
compliance_requirements: PCI DSS, SOX, GDPR
security_requirements: Banking-grade security
target_users: Financial institution users
integrations: Banking APIs, Payment processors
```

### Healthcare Context
```yaml
domain: healthcare technology
compliance_requirements: HIPAA, FDA, GDPR
security_requirements: HIPAA-compliant security
target_users: Healthcare providers and patients
integrations: EHR systems, Medical devices
```

### E-commerce Context
```yaml
domain: e-commerce
compliance_requirements: PCI DSS, GDPR, CCPA
security_requirements: E-commerce security standards
target_users: Online shoppers and merchants
integrations: Payment gateways, Inventory systems
```

## 🔧 Programmatic Usage

### Using ProjectContext
```python
from config.config_loader import Config
from utils.project_context import ProjectContext

# Initialize context
config = Config()
project_context = ProjectContext(config)

# Set project type
project_context.set_project_type('fintech')

# Add custom context
project_context.update_context({
    'project_name': 'CryptoWallet',
    'timeline': '6 months'
})

# Get agent-specific context
epic_context = project_context.get_context('epic_strategist')
```

### Using PromptManager
```python
from utils.prompt_manager import prompt_manager

# Generate prompt with context
context = {
    'project_name': 'MyApp',
    'domain': 'fintech',
    'target_users': 'crypto traders'
}

prompt = prompt_manager.get_prompt('epic_strategist', context)
```

## 🚀 Advanced Examples

### Crypto Trading Platform
```bash
python tools/run_pipeline.py \
  --project-type fintech \
  --project-name "CryptoTrader Pro" \
  --domain "cryptocurrency trading" \
  --tech-stack "React, Node.js, WebSocket, Redis" \
  --timeline "8 months" \
  --team-size "10-15 developers"
```

### Healthcare Patient Portal
```bash
python tools/run_pipeline.py \
  --project-type healthcare \
  --project-name "PatientConnect" \
  --domain "patient engagement" \
  --tech-stack "Vue.js, Python Django, PostgreSQL" \
  --timeline "12 months"
```

### E-learning Platform
```bash
python tools/run_pipeline.py \
  --project-type education \
  --project-name "LearnHub" \
  --domain "online education" \
  --tech-stack "Next.js, Node.js, MongoDB" \
  --timeline "6 months"
```

## 📊 Output Impact

The modular prompt system produces more relevant and context-aware outputs:

### Before (Generic)
- Generic software development terminology
- One-size-fits-all approach
- Limited domain knowledge

### After (Context-Aware)
- Domain-specific terminology and requirements
- Industry-appropriate compliance considerations
- Tailored technical recommendations
- Relevant user personas and use cases

## 🔄 Best Practices

1. **Choose Appropriate Project Type**: Select the preset that best matches your domain
2. **Customize Key Variables**: Override important context like project name and timeline
3. **Validate Templates**: Test templates before production use
4. **Review Generated Content**: Verify outputs align with your specific requirements
5. **Iterate on Context**: Refine context variables based on output quality

## 🛡️ Error Handling

The system includes robust error handling:
- Missing templates fall back to basic prompts
- Unknown variables are safely ignored
- Validation helps identify required context

## 📈 Future Enhancements

Planned improvements:
- GUI for context configuration
- Additional project type presets
- Prompt template versioning
- Real-time template editing
- Context inheritance and profiles
