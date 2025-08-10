"""
Central quality configuration for work item acceptance.

This module defines the universal quality acceptance threshold and
related configurations for all agents in the system.
"""

# Universal quality acceptance threshold
# Work items must score at least this value to be accepted
# Otherwise they are discarded and regenerated
MINIMUM_QUALITY_SCORE = 75

# Quality rating thresholds
QUALITY_RATINGS = {
    "EXCELLENT": (80, 100),   # 80-100 points
    "GOOD": (70, 79),         # 70-79 points  
    "FAIR": (50, 69),         # 50-69 points
    "POOR": (0, 49)           # 0-49 points
}

def get_acceptable_ratings(minimum_score=MINIMUM_QUALITY_SCORE):
    """
    Get list of acceptable quality ratings based on minimum score.
    
    Args:
        minimum_score: The minimum quality score required (default: 75)
        
    Returns:
        List of rating names that meet the minimum score requirement
    """
    acceptable = []
    for rating, (min_val, max_val) in QUALITY_RATINGS.items():
        if max_val >= minimum_score:
            acceptable.append(rating)
    return acceptable

def is_quality_acceptable(score, minimum_score=MINIMUM_QUALITY_SCORE):
    """
    Check if a quality score meets the minimum threshold.
    
    Args:
        score: The quality score to check
        minimum_score: The minimum required score (default: 75)
        
    Returns:
        True if score meets threshold, False otherwise
    """
    return score >= minimum_score

def get_rating_from_score(score):
    """
    Get the quality rating name for a given score.
    
    Args:
        score: The quality score
        
    Returns:
        The rating name (EXCELLENT, GOOD, FAIR, or POOR)
    """
    for rating, (min_val, max_val) in QUALITY_RATINGS.items():
        if min_val <= score <= max_val:
            return rating
    return "POOR"