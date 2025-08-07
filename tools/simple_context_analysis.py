#!/usr/bin/env python3

# Read the detailed epic strategist prompt
with open('prompts/epic_strategist.txt', 'r', encoding='utf-8') as f:
    prompt_template = f.read()

# Sample context variables (typical size)
sample_product_vision = """Create an AI-powered loading dock asset health monitoring system for distribution centers. 

Target Users: Dock supervisors, maintenance teams, and operations managers need real-time visibility into equipment health.

Core Problem: Loading dock doors, hydraulic lift gates, and conveyor motors frequently fail without warning, causing 2-4 hour delays and $50K daily losses from missed shipments.

Solution Requirements:
- Computer vision inspection of dock door seals, lift gate hydraulics, and motor vibration patterns
- Predictive analytics to forecast failures 48-72 hours in advance  
- Mobile alerts to maintenance crews with specific part recommendations
- Integration with existing WMS and maintenance scheduling systems
- Real-time dashboard showing health scores for all 24 loading dock positions

Success Metrics: Reduce unplanned downtime by 80%, improve dock utilization to 95%, decrease maintenance costs by 30%.

Technical Environment: Edge computing devices with industrial cameras, connected to cloud analytics platform, deployed across 12 distribution centers initially."""

# Substitute variables into template
final_prompt = prompt_template.replace('${product_vision}', sample_product_vision)
final_prompt = final_prompt.replace('${project_name}', 'DockSentry')
final_prompt = final_prompt.replace('${domain}', 'logistics')
final_prompt = final_prompt.replace('${target_users}', 'dock supervisors, maintenance teams, operations managers')
final_prompt = final_prompt.replace('${timeline}', '9 months')
final_prompt = final_prompt.replace('${budget_constraints}', '$2M development budget')
final_prompt = final_prompt.replace('${methodology}', 'Agile/Scrum')
final_prompt = final_prompt.replace('${max_epics}', '2')

# Calculate sizes
template_chars = len(prompt_template)
final_chars = len(final_prompt)
vision_chars = len(sample_product_vision)

# Token approximation: ~4 chars per token
template_tokens = template_chars // 4
final_tokens = final_chars // 4
vision_tokens = vision_chars // 4

print('=== CONTEXT WINDOW ANALYSIS ===')
print()
print('[AI] MODEL CONTEXT WINDOWS:')
print('  qwen2.5:32b: 32,768 tokens (32K)')
print('  llama3.1:70b: 131,072 tokens (128K)')
print('  gpt-4: 8,192 tokens (8K)')
print()
print('[STATS] PROMPT SIZE ANALYSIS:')
print(f'  Template: {template_chars:,} chars (~{template_tokens:,} tokens)')
print(f'  Product vision: {vision_chars:,} chars (~{vision_tokens:,} tokens)') 
print(f'  Final prompt: {final_chars:,} chars (~{final_tokens:,} tokens)')
print()

qwen_usage = (final_tokens / 32768) * 100
llama_usage = (final_tokens / 131072) * 100
gpt4_usage = (final_tokens / 8192) * 100

print('[STATS] CONTEXT USAGE:')
print(f'  qwen2.5:32b: {qwen_usage:.1f}% of context used')
print(f'  llama3.1:70b: {llama_usage:.1f}% of context used')
print(f'  gpt-4: {gpt4_usage:.1f}% of context used')
print()

# Response capacity
qwen_remaining = 32768 - final_tokens
llama_remaining = 131072 - final_tokens
gpt4_remaining = 8192 - final_tokens

print('[WARNING] RESPONSE CAPACITY:')
print(f'  qwen2.5:32b: {qwen_remaining:,} tokens left for response')
print(f'  llama3.1:70b: {llama_remaining:,} tokens left for response')
print(f'  gpt-4: {gpt4_remaining:,} tokens left for response')
print()

# Typical response size
response_chars = 1200  # Typical 2-epic JSON response
response_tokens = response_chars // 4

print('[REQUEST] TYPICAL RESPONSE SIZE:')
print(f'  Epic JSON response: ~{response_chars:,} chars (~{response_tokens:,} tokens)')
print()

print('[SUCCESS] SAFETY MARGINS:')
if qwen_remaining > response_tokens:
    buffer = ((qwen_remaining - response_tokens) / 32768) * 100
    print(f'  qwen2.5:32b: {buffer:.1f}% buffer remaining [SAFE]')
else:
    shortage = response_tokens - qwen_remaining
    print(f'  qwen2.5:32b: [ERROR] INSUFFICIENT SPACE (short {shortage:,} tokens)')

if llama_remaining > response_tokens:
    buffer = ((llama_remaining - response_tokens) / 131072) * 100
    print(f'  llama3.1:70b: {buffer:.1f}% buffer remaining [SAFE]')

if gpt4_remaining > response_tokens:
    buffer = ((gpt4_remaining - response_tokens) / 8192) * 100
    print(f'  gpt-4: {buffer:.1f}% buffer remaining [SAFE]')
else:
    shortage = response_tokens - gpt4_remaining
    print(f'  gpt-4: [ERROR] INSUFFICIENT SPACE (short {shortage:,} tokens)')

print()
print('[CONFIG] ANALYSIS:')
if qwen_usage > 50:
    print('  [WARNING] qwen2.5:32b is using >50% of context - may impact performance')
if qwen_usage > 80:
    print('  [ALERT] qwen2.5:32b is using >80% of context - consider prompt optimization')

print(f'  [CONFIG] Template overhead: {template_tokens:,} tokens ({(template_tokens/final_tokens)*100:.1f}% of final prompt)')
print(f'  [CONFIG] Context data: {final_tokens - template_tokens:,} tokens ({((final_tokens - template_tokens)/final_tokens)*100:.1f}% of final prompt)')