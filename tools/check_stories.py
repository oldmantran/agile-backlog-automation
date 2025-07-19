#!/usr/bin/env python3
"""Check the story titles in the existing backlog."""

import json

def check_stories():
    """Check if the existing backlog has generic stories."""
    
    try:
        with open('output/backlog_20250716_090012.json', 'r') as f:
            data = json.load(f)
        
        # Extract all user stories
        stories = []
        for epic in data['epics']:
            for feature in epic['features']:
                for story in feature['user_stories']:
                    stories.append(story)
        
        print(f"Total stories: {len(stories)}")
        print("\nFirst 10 story titles:")
        for i, story in enumerate(stories[:10]):
            print(f"  {i+1}. {story['title']}")
        
        # Check for generic patterns
        generic_count = 0
        for story in stories:
            if "Process Feature Requirements" in story['title']:
                generic_count += 1
        
        print(f"\nGeneric 'Process Feature Requirements' stories: {generic_count}")
        
        return stories
        
    except Exception as e:
        print(f"Error reading backlog: {e}")
        return None

if __name__ == "__main__":
    check_stories()
