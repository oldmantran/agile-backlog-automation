# Developer Agent Context Optimization Guide

## Problem Statement
Tasks are receiving FAIR ratings (45-64/100) due to:
- Insufficient technical specificity
- Missing domain context
- Generic descriptions
- Lack of implementation details

## Solution: Context Summarization

Since the full product vision (3132 characters) + epic + feature + user story context can be overwhelming, we should provide a focused context summary for the developer agent.

### Recommended Context Structure

```python
# In supervisor.py _execute_task_generation method
def _create_task_generation_context(self, base_context, epic, feature, user_story):
    """Create optimized context for task generation."""
    
    # Extract only the most relevant technical details from vision
    vision_tech_summary = self._extract_technical_summary(base_context.get('product_vision', ''))
    
    # Create focused context
    task_context = base_context.copy()
    
    # Replace full vision with technical summary
    task_context['vision_tech_summary'] = vision_tech_summary
    
    # Add hierarchical context with key details only
    task_context['epic_summary'] = f"{epic.get('title')}: {epic.get('key_deliverables', '')[:200]}"
    task_context['feature_summary'] = f"{feature.get('title')}: {feature.get('technical_approach', '')[:200]}"
    
    # Add domain-specific technical hints
    if base_context.get('domain') == 'agriculture':
        task_context['domain_tech_hints'] = [
            "Use PostGIS for spatial data",
            "Implement ISOBUS/ISO 11783 standards",
            "Include IoT sensors (LoRaWAN/MQTT)",
            "Reference precision agriculture APIs",
            "Consider offline field operations"
        ]
    
    return task_context

def _extract_technical_summary(self, vision):
    """Extract only technical implementation details from vision."""
    # Extract sections like:
    # - Technical Architecture
    # - Integration Requirements
    # - Core technical capabilities
    # Limit to 500 characters
    
    tech_keywords = ['api', 'database', 'protocol', 'integration', 'standard', 'mqtt', 'postgis']
    tech_sentences = []
    
    for sentence in vision.split('.'):
        if any(keyword in sentence.lower() for keyword in tech_keywords):
            tech_sentences.append(sentence.strip())
    
    return '. '.join(tech_sentences[:5])[:500]
```

### Enhanced Prompt Structure

1. **Focused Context** (instead of full 3K+ character vision):
   - Technical architecture summary (500 chars)
   - Key integration points
   - Domain-specific standards

2. **Clear Examples**:
   - Full technical_details object
   - Minimum 150-char descriptions
   - Specific technology mentions

3. **Quality Triggers**:
   - Mandatory technical terms per task
   - Required implementation verbs
   - Specific deliverable mentions

## Implementation Steps

1. **Update supervisor.py**:
   - Add context summarization before calling developer agent
   - Extract only technical details from vision
   - Add domain-specific hints

2. **Use enhanced prompt**:
   - Already implemented with fallback
   - Contains better examples
   - Enforces quality requirements

3. **Monitor improvements**:
   - Track task quality scores
   - Adjust context summary length if needed
   - Fine-tune domain keywords

## Expected Results
- Task scores improving from FAIR (45-64) to GOOD (65-79) or EXCELLENT (80+)
- Reduced context overhead
- More focused, technical task descriptions
- Better domain alignment