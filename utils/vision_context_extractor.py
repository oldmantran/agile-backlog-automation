"""
Vision Context Extractor

Extracts specific domain information from vision statements to enhance project context.
"""

import re
from typing import Dict, Any, List

class VisionContextExtractor:
    """Extracts domain-specific context from vision statements."""
    
    def __init__(self):
        self.industry_patterns = {
            'oil_gas': ['oil', 'gas', 'petroleum', 'drilling', 'fracking', 'production', 'wells', 'field operations', 'downhole', 'stimulation'],
            'healthcare': ['healthcare', 'medical', 'patient', 'clinical', 'diagnosis', 'treatment', 'hospital', 'physician'],
            'finance': ['financial', 'banking', 'trading', 'investment', 'portfolio', 'risk', 'compliance', 'fintech'],
            'retail': ['retail', 'ecommerce', 'shopping', 'customer', 'inventory', 'sales', 'merchandise'],
            'education': ['education', 'learning', 'student', 'teacher', 'curriculum', 'academic', 'school'],
            'manufacturing': ['manufacturing', 'production', 'assembly', 'quality', 'supply chain', 'inventory']
        }
        
        self.user_type_patterns = {
            'field_operators': ['field operator', 'field personnel', 'on-site personnel', 'technician', 'operator'],
            'managers': ['manager', 'leader', 'supervisor', 'executive', 'director'],
            'analysts': ['analyst', 'data analyst', 'engineer', 'specialist', 'researcher'],
            'developers': ['developer', 'programmer', 'engineer', 'technical'],
            'end_users': ['user', 'customer', 'client', 'consumer']
        }
        
    def extract_context(self, project_data: Dict[str, Any], business_objectives: List[str] = None, 
                       target_audience: str = None, domain: str = None) -> Dict[str, Any]:
        """Extract enhanced context from project data including vision statement."""
        
        enhanced_context = {}
        
        # Extract vision statement from project data
        vision_statement = project_data.get('vision_statement', '')
        if not vision_statement:
            # Fallback to description if no vision statement
            vision_statement = project_data.get('description', '')
        
        # Extract domain information
        detected_domain = self._detect_domain(vision_statement)
        if detected_domain:
            enhanced_context['domain'] = detected_domain
            enhanced_context['industry'] = detected_domain.replace('_', ' and ')
        elif domain and domain != 'software_development':
            enhanced_context['domain'] = domain
            enhanced_context['industry'] = domain.replace('_', ' ')
        
        # Extract user types
        user_types = self._extract_user_types(vision_statement, target_audience)
        if user_types:
            enhanced_context['target_users'] = user_types
        
        # Extract specific technologies and platforms
        tech_info = self._extract_technology_context(vision_statement)
        enhanced_context.update(tech_info)
        
        # Extract business goals and metrics
        goals = self._extract_business_goals(vision_statement, business_objectives)
        enhanced_context.update(goals)
        
        # Extract specific terminology and vocabulary
        vocabulary = self._extract_domain_vocabulary(vision_statement)
        enhanced_context['domain_vocabulary'] = vocabulary
        
        return enhanced_context
    
    def _detect_domain(self, text: str) -> str:
        """Detect the primary domain from the text."""
        text_lower = text.lower()
        
        domain_scores = {}
        for domain, keywords in self.industry_patterns.items():
            score = sum(1 for keyword in keywords if keyword in text_lower)
            if score > 0:
                domain_scores[domain] = score
        
        if domain_scores:
            return max(domain_scores, key=domain_scores.get)
        return None
    
    def _extract_user_types(self, text: str, target_audience: str = None) -> str:
        """Extract specific user types from the text."""
        text_lower = text.lower()
        
        # Check target audience first
        if target_audience and target_audience != 'end users':
            return target_audience
        
        detected_types = []
        for user_type, patterns in self.user_type_patterns.items():
            if any(pattern in text_lower for pattern in patterns):
                detected_types.append(user_type)
        
        if detected_types:
            return ', '.join(detected_types).replace('_', ' ')
        
        return 'end users'
    
    def _extract_technology_context(self, text: str) -> Dict[str, Any]:
        """Extract technology and platform information."""
        text_lower = text.lower()
        tech_context = {}
        
        # Platform detection
        if any(term in text_lower for term in ['web-based', 'web platform', 'web application']):
            tech_context['platform'] = 'Web-based platform'
        elif any(term in text_lower for term in ['mobile', 'mobile app']):
            tech_context['platform'] = 'Mobile application'
        elif any(term in text_lower for term in ['desktop', 'windows', 'mac']):
            tech_context['platform'] = 'Desktop application'
        else:
            tech_context['platform'] = 'Web application'
        
        # Data-related technology
        if any(term in text_lower for term in ['real-time', 'real time', 'streaming']):
            tech_context['data_processing'] = 'Real-time data processing'
        
        if any(term in text_lower for term in ['visualization', 'dashboard', 'charts', 'graphs']):
            tech_context['visualization'] = 'Data visualization and dashboards'
        
        if any(term in text_lower for term in ['api', 'integration', 'connectivity']):
            tech_context['integration'] = 'API integration and connectivity'
        
        return tech_context
    
    def _extract_business_goals(self, text: str, business_objectives: List[str] = None) -> Dict[str, Any]:
        """Extract business goals and metrics."""
        goals_context = {}
        
        # Extract percentage targets
        percentage_pattern = r'(\d+)%'
        percentages = re.findall(percentage_pattern, text)
        if percentages:
            goals_context['performance_targets'] = f"{', '.join(percentages)}% improvement targets"
        
        # Extract timeline information
        timeline_pattern = r'(\d+)\s*(month|year|quarter)s?'
        timelines = re.findall(timeline_pattern, text.lower())
        if timelines:
            timeline_str = ', '.join([f"{num} {period}s" for num, period in timelines])
            goals_context['timeline'] = timeline_str
        
        # Extract revenue/financial targets
        revenue_pattern = r'\$(\d+(?:,\d+)*)\s*(million|billion|thousand)?'
        revenue_matches = re.findall(revenue_pattern, text)
        if revenue_matches:
            goals_context['revenue_targets'] = f"${', '.join([f'{amount} {unit}' for amount, unit in revenue_matches])}"
        
        # Use business objectives if provided and not generic
        if business_objectives and business_objectives != ['TBD']:
            goals_context['business_objectives'] = business_objectives
        
        return goals_context
    
    def _extract_domain_vocabulary(self, text: str) -> List[str]:
        """Extract domain-specific vocabulary and terms."""
        # Extract technical terms and domain-specific vocabulary
        text_lower = text.lower()
        vocabulary = []
        
        # Common domain terms
        domain_terms = [
            'efficiency', 'optimization', 'performance', 'productivity', 'scalability',
            'data-driven', 'actionable insights', 'real-time', 'automation', 'integration',
            'user experience', 'workflow', 'process improvement', 'analytics', 'reporting'
        ]
        
        for term in domain_terms:
            if term in text_lower:
                vocabulary.append(term)
        
        # Industry-specific terms
        oil_gas_terms = [
            'field operations', 'well longevity', 'stimulation jobs', 'non-productive time',
            'operational efficiency', 'job completion', 'field operators', 'drilling',
            'production optimization', 'downhole', 'reservoir', 'completion'
        ]
        
        if any(term in text_lower for term in ['oil', 'gas', 'field', 'well', 'drilling']):
            for term in oil_gas_terms:
                if term in text_lower:
                    vocabulary.append(term)
        
        return vocabulary[:10]  # Limit to top 10 terms
