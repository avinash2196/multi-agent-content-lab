import json
import re
from typing import Dict, Any, Optional, List
import logging


class ResponseParser:
    """Parse and extract structured data from LLM responses."""
    
    def __init__(self):
        self.logger = logging.getLogger("response_parser")
    
    def parse_json_response(self, response: str) -> Optional[Dict[str, Any]]:
        """Extract and parse JSON from response text."""
        try:
            # Try direct parsing first
            return json.loads(response)
        except json.JSONDecodeError:
            # Try to extract JSON from markdown code blocks
            json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group(1))
                except json.JSONDecodeError:
                    pass
            
            # Try to find JSON object in text
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group(0))
                except json.JSONDecodeError:
                    pass
            
            self.logger.warning("Failed to parse JSON from response")
            return None
    
    def extract_code_blocks(self, response: str, language: Optional[str] = None) -> List[str]:
        """Extract code blocks from markdown response."""
        if language:
            pattern = rf'```{language}\s*(.*?)```'
        else:
            pattern = r'```(?:\w+)?\s*(.*?)```'
        
        return re.findall(pattern, response, re.DOTALL)
    
    def extract_sections(self, response: str) -> Dict[str, str]:
        """Extract sections based on markdown headers."""
        sections = {}
        
        # Split by headers
        parts = re.split(r'\n##\s+', response)
        
        # First part might not have a header
        if parts[0].strip():
            sections["introduction"] = parts[0].strip()
        
        # Process remaining sections
        for part in parts[1:]:
            lines = part.split('\n', 1)
            if len(lines) == 2:
                header = lines[0].strip()
                content = lines[1].strip()
                sections[header.lower().replace(' ', '_')] = content
        
        return sections
    
    def extract_list_items(self, response: str) -> List[str]:
        """Extract list items from response."""
        # Match both ordered and unordered lists
        items = []
        
        # Unordered lists
        items.extend(re.findall(r'^\s*[-*+]\s+(.+)$', response, re.MULTILINE))
        
        # Ordered lists
        items.extend(re.findall(r'^\s*\d+\.\s+(.+)$', response, re.MULTILINE))
        
        return items
    
    def extract_metadata(self, response: str) -> Dict[str, Any]:
        """Extract metadata from structured response."""
        metadata = {}
        
        # Extract title
        title_match = re.search(r'^#\s+(.+)$', response, re.MULTILINE)
        if title_match:
            metadata['title'] = title_match.group(1).strip()
        
        # Extract meta description
        meta_match = re.search(r'(?:meta\s+description|description):\s*(.+)', response, re.IGNORECASE)
        if meta_match:
            metadata['description'] = meta_match.group(1).strip()
        
        # Extract keywords/tags
        keywords_match = re.search(r'(?:keywords|tags):\s*(.+)', response, re.IGNORECASE)
        if keywords_match:
            keywords_str = keywords_match.group(1).strip()
            metadata['keywords'] = [k.strip() for k in keywords_str.split(',')]
        
        return metadata
    
    def clean_response(self, response: str) -> str:
        """Clean response by removing artifacts and normalizing."""
        # Remove thinking tags if present
        response = re.sub(r'<thinking>.*?</thinking>', '', response, flags=re.DOTALL)
        
        # Remove excessive newlines
        response = re.sub(r'\n{3,}', '\n\n', response)
        
        # Strip leading/trailing whitespace
        response = response.strip()
        
        return response
    
    def extract_key_value_pairs(self, response: str) -> Dict[str, str]:
        """Extract key-value pairs from response."""
        pairs = {}
        
        # Match patterns like "Key: Value" or "Key - Value"
        matches = re.findall(r'^([^:\-\n]+)[\:\-]\s*(.+)$', response, re.MULTILINE)
        
        for key, value in matches:
            clean_key = key.strip().lower().replace(' ', '_')
            pairs[clean_key] = value.strip()
        
        return pairs
    
    def parse_structured_output(self, response: str, expected_fields: List[str]) -> Dict[str, Any]:
        """Parse response expecting specific fields."""
        result = {}
        
        # Try JSON first
        json_data = self.parse_json_response(response)
        if json_data:
            for field in expected_fields:
                if field in json_data:
                    result[field] = json_data[field]
            return result
        
        # Fall back to key-value extraction
        kv_pairs = self.extract_key_value_pairs(response)
        for field in expected_fields:
            if field in kv_pairs:
                result[field] = kv_pairs[field]
        
        return result
