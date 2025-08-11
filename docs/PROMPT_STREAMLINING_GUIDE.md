# Prompt Streamlining Guide

This document explains the prompt streamlining approach implemented across all agents and provides guidance for future prompt improvements.

## Overview

On August 10, 2025, all agent prompts were streamlined following a consistent pattern that dramatically improved output quality while reducing prompt complexity.

## Results

| Agent | Lines Reduced | Quality Improvement |
|-------|---------------|-------------------|
| Epic Strategist | 111 → 42 (62% reduction) | 65/100 → 86/100 |
| Feature Decomposer | 76 → 56 (26% reduction) | Improved structure |
| User Story Decomposer | 78 → 60 (23% reduction) | All achieve 75+/100 |
| Developer Agent | 93 → 46 (51% reduction) | Clear technical structure |

## Streamlining Pattern

### 1. Response Format First
```
RESPONSE FORMAT: ONLY valid JSON array. NO text, NO markdown, NO explanations.
```
- Place this at the very top
- Makes expectations crystal clear
- Prevents LLMs from adding explanations

### 2. Minimal Context Section
```
CONTEXT:
Project: ${project_name}
Domain: ${domain}
Tech Stack: ${tech_stack}
```
- List only essential variables
- Use simple key-value format
- No verbose explanations

### 3. Concrete Example (Critical!)
```
EXAMPLE EPIC (your output must match this structure exactly):
{
  "title": "One-Tap Ride Request & Real-Time Dispatch",
  "description": "Enable Urban Commuters and College Students to request...",
  "priority": "High",
  "estimated_complexity": "L",
  "category": "core_platform"
}
```
- Provide ONE complete, realistic example
- Show ALL required fields
- Use domain-specific content
- Add comment: "your output must match this structure exactly"

### 4. Simple Requirements List
```
REQUIREMENTS (3-5 epics total):
1. Vision alignment - directly address product vision goals
2. User-specific - mention target users by name
3. Technical clarity - include platform/technology details
4. Domain terminology - use industry-specific language
5. Measurable outcomes - quantifiable benefits
6. Independent scope - can be developed separately
7. Clear priority - High/Medium/Low based on user value
```
- Maximum 7 requirements
- One line each
- Focus on practical criteria
- No philosophical explanations

### 5. Direct Final Instruction
```
Generate epics that transform "${product_vision}" into actionable development work.
```
- Single line
- References the main goal
- No repetition of earlier instructions

## Technical Considerations

### Template Variable Naming
Python's Template class doesn't support dots in variable names:
```python
# ❌ Won't work
${user_story.title}

# ✅ Use underscores
${user_story_title}
```

### List Handling
When flattening objects for templates, format lists appropriately:
```python
if isinstance(value, list):
    if key == 'acceptance_criteria':
        # Format as numbered list
        formatted = '\n'.join(f"{i+1}. {item}" for i, item in enumerate(value))
        context[f'user_story_{key}'] = formatted
```

### Quality Integration
Streamlined prompts work seamlessly with existing quality assessors:
- Maintain the same output structure
- Quality assessors remain unchanged
- Scores improve due to clearer instructions

## Benefits

1. **Higher Quality Output**
   - Clear examples guide LLM behavior
   - Less confusion from verbose instructions
   - Better adherence to required format

2. **Easier Maintenance**
   - Less text to update
   - Clear structure is self-documenting
   - Consistent pattern across agents

3. **Better Performance**
   - Fewer tokens to process
   - Faster response times
   - Lower API costs

## Applying to New Agents

When creating new agent prompts:

1. Start with the standard template
2. Adapt the example to your domain
3. Keep requirements under 7 items
4. Test with quality assessment
5. Iterate on the example if needed

## Common Pitfalls to Avoid

1. **Over-explaining** - Trust the LLM to understand simple instructions
2. **Multiple examples** - One good example is better than three mediocre ones
3. **Nested requirements** - Keep the list flat and simple
4. **Philosophical context** - Stick to practical, actionable criteria
5. **Redundant instructions** - Say it once, clearly

## Testing Streamlined Prompts

Use the test pattern from our implementation:
```python
# 1. Set up test context with all required variables
# 2. Generate output using the agent
# 3. Run quality assessment
# 4. Verify scores meet threshold (75+)
```

## Conclusion

The streamlined approach proves that less is more when it comes to LLM prompts. By providing clear structure, concrete examples, and simple requirements, we achieve better results with less complexity.