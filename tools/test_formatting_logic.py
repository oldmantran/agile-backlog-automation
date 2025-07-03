#!/usr/bin/env python3
"""
Test the formatting logic to ensure it properly handles the section headers and bullet points.
"""

import re

def fix_description(description: str) -> str:
    """Fix formatting issues in description."""
    if not description:
        return description
    
    # Skip if already HTML formatted
    if description.strip().startswith('<'):
        return description
    
    # Start with the original description
    fixed_description = description
    
    # Step 1: Handle any remaining escaped newlines
    fixed_description = fixed_description.replace('\\n', '\n')
    
    # Debug: Show what we're looking for
    print(f"DEBUG: Looking for **section**: pattern in: {repr(fixed_description)}")
    
    # Step 2: Add proper spacing before section headers like **Acceptance Criteria**:
    # Pattern 1: sentence. **Section**: -> sentence.\n\n**Section**:
    fixed_description = re.sub(
        r'([a-z]\.)\s+(\*\*[A-Z][^*]*\*\*:)',
        r'\1\n\n\2',
        fixed_description
    )
    
    # Pattern 2: word **Section**: -> word\n\n**Section**: (no period, just word ending)
    fixed_description = re.sub(
        r'([a-z])\s+(\*\*[A-Z][^*]*\*\*:)',
        r'\1\n\n\2',
        fixed_description
    )
    
    print(f"DEBUG: After section header fix: {repr(fixed_description)}")
    
    # Step 3: Add line breaks before bullet points that follow section headers
    # Pattern: **Section**: - bullet -> **Section**:\n- bullet
    fixed_description = re.sub(
        r'(\*\*[^*]+\*\*:)\s+(-\s)',
        r'\1\n\2',
        fixed_description
    )
    
    print(f"DEBUG: After bullet fix: {repr(fixed_description)}")
    
    # Step 4: Add line breaks between bullet points that are run together
    # Pattern: bullet. - next bullet -> bullet.\n- next bullet
    fixed_description = re.sub(
        r'([a-z]\.)\s+(-\s[A-Z])',
        r'\1\n\2',
        fixed_description
    )
    
    print(f"DEBUG: After bullet separation: {repr(fixed_description)}")
    
    # Step 5: Convert to HTML format
    # Split into paragraphs (double newlines)
    paragraphs = fixed_description.split('\n\n')
    html_paragraphs = []
    
    for paragraph in paragraphs:
        if paragraph.strip():
            # Replace single newlines with <br> tags within paragraphs
            paragraph_html = paragraph.replace('\n', '<br>')
            html_paragraphs.append(f'<p>{paragraph_html}</p>')
    
    # Join paragraphs
    html_description = ''.join(html_paragraphs)
    
    # If we don't have any paragraphs, wrap the whole thing in a div
    if not html_paragraphs:
        html_description = f'<div>{fixed_description.replace("\n", "<br>")}</div>'
    
    return html_description

# Test with the example you provided
test_description = """A user-friendly dashboard that displays AI/ML-predicted shipment delays with actionable insights, allowing logistics managers to monitor potential disruptions in real-time and take preventive actions. **Acceptance Criteria:** - Dashboard loads in under 3 seconds with up-to-date predictions for all active shipments. - Predictions are visually prioritized by severity (e.g., color-coded risk levels)."""

print("Original:")
print(repr(test_description))
print("\nOriginal (rendered):")
print(test_description)

print("\n" + "="*60)

fixed = fix_description(test_description)
print("\nFixed:")
print(repr(fixed))
print("\nFixed (rendered):")
print(fixed)

print("\n" + "="*60)
print("HTML Preview (what Azure DevOps will show):")
# Simulate how HTML would render
html_preview = fixed.replace('<p>', '').replace('</p>', '\n').replace('<br>', '\n').replace('<div>', '').replace('</div>', '')
print(html_preview)
