#!/usr/bin/env python3
"""Test word count of vision statement"""

vision_text = """Conversational Tutoring Assistant for Students
Product Vision
For students and academic support teams seeking on-demand help, TutorBot is a conversational AI assistant that provides real-time tutoring, study guidance, and concept reinforcement across subjects. Unlike static help centers or search-based tools, TutorBot uses natural language understanding and curriculum alignment to deliver contextual, scaffolded support.
Target Audience
    tudents (middle school to college), tutoring centers, edtech platforms
    • Needs: On-demand help, cept reinforcement, engagement
Business Goals
    Improve student comprehension scores by 25%
    2.hieve 90% helpfulness rating across sessions
    3. Integrate with 5 LMS and 3 curriculum providers
 Enable multilingual support and accessibility features
    5. Launch in 10K+ student accounts withi months
Key Metrics
    • Comprehension Improvemen• Helpfulness Rating
    • Integration Success
    • Accessibility Coverage
    • Student Adoption
Unique Value Proposition
TutorBot delivers personalized academic support—anytime, anywhere—helping students master concepts and build confidence.
t
    n 6    4. Ac1. con• S"""

# Count words using the same method as the code
word_count = len(vision_text.split())
print(f"Total word count: {word_count}")

# Let's also clean it up and count
import re
clean_text = ' '.join(vision_text.split())
clean_word_count = len(clean_text.split())
print(f"Clean word count: {clean_word_count}")

# Let's see what the split produces
words = vision_text.split()
print(f"\nFirst 20 words: {words[:20]}")
print(f"Last 20 words: {words[-20:]}")

# Count non-empty words only
non_empty_words = [w for w in words if w.strip()]
print(f"\nNon-empty word count: {len(non_empty_words)}")

# Check for any weird characters
print(f"\nSample of short 'words': {[w for w in words if len(w) <= 2][:20]}")

# Remove the garbage at the end
clean_vision = vision_text.replace("t\n    n 6    4. Ac1. con• S", "").strip()
clean_count = len(clean_vision.split())
print(f"\nWithout garbage at end: {clean_count} words")

# Count excluding bullet points and numbers
text_only = re.sub(r'[•\d\.]+', '', vision_text)
text_only_count = len(text_only.split())
print(f"Excluding bullets/numbers: {text_only_count} words")