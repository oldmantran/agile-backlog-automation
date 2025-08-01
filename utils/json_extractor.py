#!/usr/bin/env python3
"""
JSON Extraction Utility for LLM Responses.

This module provides robust JSON extraction from verbose LLM responses,
specifically designed to handle CodeLlama's tendency to be explanatory.
"""

import json
import re
import logging
from typing import Optional, Dict, List, Any

logger = logging.getLogger(__name__)

class JSONExtractor:
    """Robust JSON extractor for LLM responses."""
    
    @staticmethod
    def extract_json_from_response(response: str) -> Optional[str]:
        """
        Extract JSON content from LLM response using multiple strategies.
        
        Args:
            response: Raw LLM response text
            
        Returns:
            Cleaned JSON string or None if no valid JSON found
        """
        if not response or not response.strip():
            return None
            
        # Strategy 1: Find JSON array/object in code blocks
        json_content = JSONExtractor._extract_from_code_blocks(response)
        if json_content:
            return json_content
            
        # Strategy 2: Find JSON by bracket matching
        json_content = JSONExtractor._extract_by_bracket_matching(response)
        if json_content:
            return json_content
            
        # Strategy 3: Extract from "```json" blocks specifically  
        json_content = JSONExtractor._extract_from_json_blocks(response)
        if json_content:
            return json_content
            
        # Strategy 4: Look for JSON-like patterns
        json_content = JSONExtractor._extract_json_patterns(response)
        if json_content:
            return json_content
            
        # Strategy 5: Try to parse the entire response as JSON
        try:
            json.loads(response.strip())
            return response.strip()
        except:
            pass
            
        return None
    
    @staticmethod
    def _extract_from_code_blocks(response: str) -> Optional[str]:
        """Extract JSON from markdown code blocks."""
        # Look for ```json or ``` blocks
        patterns = [
            r'```json\s*\n(.*?)\n```',
            r'```\s*\n(\[.*?\])\s*\n```',
            r'```\s*\n(\{.*?\})\s*\n```',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, response, re.DOTALL)
            for match in matches:
                try:
                    json.loads(match.strip())
                    return match.strip()
                except:
                    continue
        return None
    
    @staticmethod
    def _extract_from_json_blocks(response: str) -> Optional[str]:
        """Extract specifically from ```json blocks."""
        pattern = r'```json\s*\n(.*?)\n```'
        matches = re.findall(pattern, response, re.DOTALL | re.IGNORECASE)
        
        for match in matches:
            try:
                json.loads(match.strip())
                return match.strip()
            except:
                continue
        return None
    
    @staticmethod
    def _extract_by_bracket_matching(response: str) -> Optional[str]:
        """Extract JSON by matching brackets."""
        # Find JSON arrays
        array_match = JSONExtractor._find_balanced_brackets(response, '[', ']')
        if array_match:
            try:
                json.loads(array_match)
                return array_match
            except:
                pass
        
        # Find JSON objects
        object_match = JSONExtractor._find_balanced_brackets(response, '{', '}')
        if object_match:
            try:
                json.loads(object_match)
                return object_match
            except:
                pass
                
        return None
    
    @staticmethod
    def _find_balanced_brackets(text: str, open_bracket: str, close_bracket: str) -> Optional[str]:
        """Find balanced bracket pairs and extract content."""
        start_idx = text.find(open_bracket)
        if start_idx == -1:
            return None
            
        bracket_count = 0
        for i, char in enumerate(text[start_idx:], start_idx):
            if char == open_bracket:
                bracket_count += 1
            elif char == close_bracket:
                bracket_count -= 1
                if bracket_count == 0:
                    return text[start_idx:i+1]
        return None
    
    @staticmethod
    def _extract_json_patterns(response: str) -> Optional[str]:
        """Extract using JSON-like patterns."""
        # Strategy 1: Look for complete JSON arrays with proper structure
        array_patterns = [
            r'\[\s*\{.*?"title".*?"user_story".*?\}\s*\]',  # User story specific
            r'\[\s*\{.*?\}\s*(?:,\s*\{.*?\}\s*)*\]',       # Multiple objects
            r'\[\s*\{.*?\}\s*\]',                          # Single object
            r'\[\s*".*?"\s*\]',                            # String array
        ]
        
        for pattern in array_patterns:
            matches = re.findall(pattern, response, re.DOTALL)
            for match in matches:
                try:
                    json.loads(match)
                    return match
                except:
                    # Try cleaning the match
                    cleaned = JSONExtractor.clean_json_string(match)
                    try:
                        json.loads(cleaned)
                        return cleaned
                    except:
                        continue
        
        # Strategy 2: Look for object patterns
        object_patterns = [
            r'\{[^{}]*"title"[^{}]*:[^{}]*"user_story"[^{}]*:[^{}]*\}',  # User story specific
            r'\{[^{}]*"[^"]*"[^{}]*:[^{}]*\}',                         # Generic object
        ]
        
        for pattern in object_patterns:
            matches = re.findall(pattern, response, re.DOTALL)
            for match in matches:
                try:
                    json.loads(match)
                    return f"[{match}]"  # Wrap single object in array
                except:
                    # Try cleaning the match
                    cleaned = JSONExtractor.clean_json_string(match)
                    try:
                        json.loads(cleaned)
                        return f"[{cleaned}]"  # Wrap single object in array
                    except:
                        continue
                    
        return None
    
    @staticmethod
    def clean_json_string(json_str: str) -> str:
        """Clean and fix common JSON formatting issues."""
        if not json_str:
            return json_str
            
        # Remove leading/trailing whitespace
        cleaned = json_str.strip()
        
        # Remove markdown formatting
        cleaned = re.sub(r'^```json\s*\n?', '', cleaned, flags=re.MULTILINE)
        cleaned = re.sub(r'\n?```\s*$', '', cleaned, flags=re.MULTILINE)
        
        # Fix common JSON issues
        # Fix unquoted property names
        cleaned = re.sub(r'(\w+):', r'"\1":', cleaned)
        
        # Fix single quotes to double quotes
        cleaned = cleaned.replace("'", '"')
        
        # Fix trailing commas
        cleaned = re.sub(r',(\s*[}\]])', r'\1', cleaned)
        
        return cleaned
    
    @staticmethod
    def validate_and_parse_json(json_str: str) -> Optional[Any]:
        """Validate and parse JSON string."""
        if not json_str:
            return None
            
        try:
            # First try parsing as-is
            return json.loads(json_str)
        except json.JSONDecodeError:
            try:
                # Try with cleaning
                cleaned = JSONExtractor.clean_json_string(json_str)
                return json.loads(cleaned)
            except json.JSONDecodeError as e:
                logger.debug(f"Failed to parse JSON: {e}")
                return None