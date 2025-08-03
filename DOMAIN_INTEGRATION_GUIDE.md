# Domain Management System Integration Guide

This guide explains how to integrate the new domain management system into your agile backlog automation application.

## Overview

The domain management system enhances the backlog generation process by:
- **User-selectable domains**: Users can choose specific industry domains during project creation
- **Database-driven patterns**: Domain patterns, user types, and vocabulary are stored in the database
- **Multi-domain support**: Projects can have multiple domains with weighted importance
- **Extensible design**: Users can request new domains, and admins can add them

## Implementation Steps

### 1. Database Setup

Run the migration to create domain tables and populate with existing data:

```bash
cd /path/to/agile-backlog-automation
python domain_migration.py
```

This will:
- Create 7 new database tables for domain management
- Migrate existing hardcoded domain data from `VisionContextExtractor`
- Set up indexes and views for performance

### 2. API Integration

Add domain management endpoints to your FastAPI server:

```python
# In unified_api_server.py or main server file
from domain_api_endpoints import add_domain_endpoints

# Add after creating your FastAPI app
app = FastAPI()
add_domain_endpoints(app)
```

### 3. Frontend Integration

#### A. Add Domain Selector to New Project Screen

```typescript
// In your new project component
import DomainSelector from './components/DomainSelector';

const NewProjectScreen = () => {
  const [selectedDomains, setSelectedDomains] = useState<DomainSelection[]>([]);
  
  const handleDomainSelectionChange = (selections: DomainSelection[]) => {
    setSelectedDomains(selections);
  };

  const handleProjectSubmit = async (projectData) => {
    // Include domain selections in project submission
    const projectWithDomains = {
      ...projectData,
      selected_domains: selectedDomains
    };
    
    // Submit project and save domain selections
    await submitProject(projectWithDomains);
  };

  return (
    <div>
      {/* Existing project form fields */}
      
      <DomainSelector
        onSelectionChange={handleDomainSelectionChange}
        maxSelections={3}
        allowMultiple={true}
      />
      
      {/* Submit button */}
    </div>
  );
};
```

#### B. Update Project Context Extraction

```python
# In your project creation/processing logic
from utils.vision_context_extractor import VisionContextExtractor

def process_project_with_domains(project_data, selected_domains):
    extractor = VisionContextExtractor()
    
    if selected_domains:
        # Use user-selected domains
        context = extractor.extract_context_with_selected_domains(
            project_data=project_data,
            selected_domains=selected_domains
        )
    else:
        # Fall back to auto-detection
        context = extractor.extract_context(project_data)
    
    return context
```

### 4. Backend Processing Updates

#### A. Update Supervisor to Use Domain Context

```python
# In supervisor/supervisor.py
def initialize_workflow(self, project_data, selected_domains=None):
    # Extract domain context
    if selected_domains:
        context = self.vision_extractor.extract_context_with_selected_domains(
            project_data, selected_domains
        )
    else:
        context = self.vision_extractor.extract_context(project_data)
    
    # Pass enhanced context to agents
    self.enhanced_context = context
```

#### B. Enhanced Agent Prompts

The system automatically provides domain-specific context to agent prompts through template variables:

```text
# In prompts/epic_strategist.txt
CONTEXT:
- Project: ${project_name}
- Domain: ${domain}
- Target Users: ${target_users}
- Domain Vocabulary: ${domain_vocabulary}

### Domain-Specific Validation:
For domain "${domain}":
- Epic titles and descriptions MUST use industry-specific terminology
- Address actual business processes and workflows from the domain
```

## Database Schema Overview

### Core Tables

1. **domains**: Main industry domains (real_estate, healthcare, etc.)
2. **subdomains**: Specialized areas within domains
3. **domain_patterns**: Keywords for domain detection
4. **domain_user_types**: Industry-specific user roles
5. **domain_vocabulary**: Domain-specific terminology
6. **project_domains**: Associates projects with selected domains
7. **domain_requests**: User requests for new domains

### Key Relationships

```
domains (1) -> (many) subdomains
domains (1) -> (many) domain_patterns
domains (1) -> (many) domain_user_types
domains (1) -> (many) domain_vocabulary
projects (many) -> (many) domains (via project_domains)
```

## API Endpoints

| Endpoint | Method | Description |
|----------|---------|-------------|
| `/api/domains` | GET | Get all available domains |
| `/api/projects/{id}/domains` | GET/POST | Get/set project domain selections |
| `/api/domain-requests` | GET/POST | Manage domain requests |
| `/api/domains/search` | GET | Search domains by keyword |

## Usage Examples

### 1. Basic Domain Selection

```typescript
// User selects Real Estate domain for a property management project
const selections = [
  {
    domain_id: 7,
    domain_key: 'real_estate',
    subdomain_id: 3,
    subdomain_key: 'property_management',
    is_primary: true,
    weight: 1.0
  }
];
```

### 2. Multi-Domain Project

```typescript
// User selects both Real Estate and Finance for a proptech fintech project
const selections = [
  {
    domain_id: 7,
    domain_key: 'real_estate',
    is_primary: true,
    weight: 0.7
  },
  {
    domain_id: 3,
    domain_key: 'finance',
    is_primary: false,
    weight: 0.3
  }
];
```

### 3. Requesting New Domain

```typescript
const newDomainRequest = {
  request_type: 'new_domain',
  requested_domain_key: 'aerospace',
  requested_display_name: 'Aerospace & Defense',
  justification: 'We work with aerospace companies and need domain-specific work items for flight systems, safety regulations, and certification processes.',
  proposed_patterns: ['aircraft', 'aviation', 'aerospace', 'flight', 'pilot', 'maintenance'],
  proposed_user_types: [
    {
      name: 'pilots',
      patterns: ['pilot', 'captain', 'first officer', 'flight crew']
    }
  ],
  proposed_vocabulary: ['flight operations', 'aircraft maintenance', 'safety protocols'],
  priority: 'high'
};
```

## Benefits

### For Users
- **Better Relevance**: Work items use industry-specific terminology
- **Faster Setup**: Pre-configured domain patterns eliminate manual specification
- **Multi-Domain Support**: Complex projects can span multiple industries
- **Extensible**: Can request new domains as business needs evolve

### For Development
- **Maintainable**: Domain data is in database, not hardcoded
- **Scalable**: Easy to add new domains without code changes
- **Auditable**: Track which domains are used by which projects
- **Flexible**: Support for subdomains and weighted multi-domain projects

## Migration from Hardcoded Patterns

The system automatically migrates existing domain patterns:

| Old (Hardcoded) | New (Database) |
|-----------------|----------------|
| `self.industry_patterns['real_estate']` | `domain_patterns` table |
| `self.user_type_patterns['real_estate_professionals']` | `domain_user_types` table |
| Hardcoded vocabulary lists | `domain_vocabulary` table |

Existing functionality continues to work, but now pulls from the database.

## Performance Considerations

- **Caching**: Domain data is cached in `VisionContextExtractor` for performance
- **Indexes**: Database indexes on key lookup fields
- **Lazy Loading**: Subdomains loaded only when needed
- **Search Optimization**: Full-text search capabilities for domain discovery

## Future Enhancements

1. **Admin Interface**: Web UI for managing domains without code changes
2. **Analytics**: Track domain usage and effectiveness
3. **Auto-Detection Improvement**: ML-based domain classification
4. **Domain Templates**: Pre-built templates for common domain combinations
5. **Integration APIs**: Export domain data for other tools

## Troubleshooting

### Common Issues

1. **Migration Errors**: Ensure database permissions allow table creation
2. **Missing Imports**: Verify all new modules are properly imported
3. **Frontend Integration**: Check that React components have proper TypeScript types
4. **Cache Issues**: Use `extractor.refresh_domains()` if domain data seems stale

### Logging

Enable domain-specific logging:

```python
import logging
logging.getLogger('VisionContextExtractor').setLevel(logging.DEBUG)
```

This will show domain detection and context extraction details in the logs.