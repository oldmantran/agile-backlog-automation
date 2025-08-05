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
            'healthcare': ['healthcare', 'medical', 'patient', 'clinical', 'diagnosis', 'treatment', 'hospital', 'physician', 'nurse', 'surgery', 'therapy', 'prescription'],
            'finance': ['financial', 'banking', 'trading', 'investment', 'portfolio', 'risk', 'compliance', 'fintech', 'insurance', 'loan', 'credit', 'wealth management'],
            'retail': ['retail', 'ecommerce', 'shopping', 'customer', 'inventory', 'sales', 'merchandise', 'storefront', 'checkout', 'pricing', 'product catalog'],
            'education': ['education', 'learning', 'student', 'teacher', 'curriculum', 'academic', 'school', 'university', 'training', 'classroom', 'assessment', 'graduation'],
            'manufacturing': ['manufacturing', 'production', 'assembly', 'quality', 'supply chain', 'inventory', 'factory', 'machinery', 'fabrication', 'tooling', 'lean manufacturing'],
            'real_estate': ['real estate', 'property', 'listing', 'mls', 'agent', 'broker', 'buyer', 'seller', 'home', 'house', 'apartment', 'rent', 'sale', 'mortgage', 'appraisal', 'inspection', 'closing', 'lease', 'tenant', 'landlord', 'commission', 'escrow', 'title', 'realtor', 'homeowner', 'transaction', 'property management', 'residential', 'commercial', 'market analysis', 'comparable sales', 'home value', 'property search', 'offer', 'negotiation'],
            'logistics': ['logistics', 'shipping', 'freight', 'supply chain', 'distribution', 'warehousing', 'transportation', 'delivery', 'cargo', 'fleet management', 'tracking', 'fulfillment', 'inventory management', 'route optimization'],
            'agriculture': ['agriculture', 'farming', 'crops', 'livestock', 'harvest', 'irrigation', 'soil', 'fertilizer', 'pesticide', 'agricultural equipment', 'yield', 'farm management', 'agribusiness', 'sustainable farming'],
            'technology': ['technology', 'software', 'hardware', 'programming', 'development', 'IT', 'tech stack', 'cloud computing', 'artificial intelligence', 'machine learning', 'cybersecurity', 'data science', 'DevOps', 'digital transformation'],
            'telecommunications': ['telecommunications', 'telecom', 'network', 'wireless', 'broadband', 'cellular', 'fiber optic', 'communication', '5G', 'infrastructure', 'bandwidth', 'connectivity', 'telecommunications equipment'],
            'energy': ['energy', 'renewable energy', 'solar', 'wind', 'hydroelectric', 'nuclear', 'power generation', 'grid', 'electricity', 'energy storage', 'smart grid', 'energy efficiency', 'utility'],
            'transportation': ['transportation', 'transit', 'public transport', 'railways', 'aviation', 'maritime', 'logistics', 'traffic management', 'vehicle', 'infrastructure', 'mobility', 'freight transport'],
            'hospitality_tourism': ['hospitality', 'tourism', 'hotel', 'restaurant', 'travel', 'accommodation', 'guest services', 'booking', 'reservation', 'tourism management', 'hospitality management', 'customer experience'],
            'entertainment_media': ['entertainment', 'media', 'television', 'film', 'music', 'gaming', 'streaming', 'content creation', 'broadcasting', 'digital media', 'production', 'publishing', 'social media'],
            'construction': ['construction', 'building', 'architecture', 'engineering', 'contractor', 'project management', 'blueprint', 'infrastructure', 'renovation', 'development', 'construction materials', 'safety'],
            'automotive': ['automotive', 'vehicle', 'car', 'truck', 'manufacturing', 'assembly line', 'automotive parts', 'dealership', 'maintenance', 'repair', 'electric vehicle', 'autonomous driving'],
            'aerospace_defense': ['aerospace', 'defense', 'aircraft', 'aviation', 'military', 'satellite', 'space', 'flight', 'missile', 'radar', 'navigation', 'aerospace engineering', 'defense contractor'],
            'pharmaceuticals_biotech': ['pharmaceuticals', 'biotech', 'drug', 'medicine', 'clinical trials', 'research', 'FDA', 'regulatory', 'laboratory', 'biotechnology', 'pharmaceutical manufacturing'],
            'consumer_goods': ['consumer goods', 'products', 'retail', 'brand', 'marketing', 'packaging', 'distribution', 'consumer behavior', 'product development', 'fast-moving consumer goods', 'FMCG'],
            'environmental_services': ['environmental', 'sustainability', 'waste management', 'recycling', 'renewable', 'green technology', 'carbon footprint', 'environmental compliance', 'pollution control', 'conservation'],
            'government_public_sector': ['government', 'public sector', 'civil service', 'policy', 'regulation', 'public administration', 'citizen services', 'municipal', 'federal', 'state', 'local government'],
            'insurance': ['insurance', 'policy', 'premium', 'claims', 'underwriting', 'risk assessment', 'actuarial', 'coverage', 'deductible', 'insurance broker', 'life insurance', 'health insurance'],
            'professional_services': ['professional services', 'consulting', 'advisory', 'legal', 'accounting', 'auditing', 'tax', 'human resources', 'recruitment', 'business consulting', 'management consulting'],
            'nonprofit_social_impact': ['nonprofit', 'social impact', 'charity', 'foundation', 'community', 'volunteer', 'social services', 'fundraising', 'grant', 'social change', 'philanthropy'],
            'mining_natural_resources': ['mining', 'natural resources', 'extraction', 'minerals', 'ore', 'quarry', 'geology', 'mining equipment', 'exploration', 'environmental impact', 'resource management'],
            'food_beverage': ['food', 'beverage', 'restaurant', 'culinary', 'catering', 'food service', 'nutrition', 'recipe', 'menu', 'food safety', 'food production', 'culinary arts'],
            'ecommerce': ['ecommerce', 'online shopping', 'digital commerce', 'marketplace', 'payment processing', 'shopping cart', 'order management', 'customer experience', 'digital marketing', 'online retail'],
            'sports_fitness': ['sports', 'fitness', 'athletics', 'training', 'gym', 'exercise', 'wellness', 'health', 'coaching', 'sports management', 'fitness equipment', 'athletic performance'],
            'workforce_management': ['workforce management', 'human resources', 'employee', 'talent management', 'recruiting', 'payroll', 'performance management', 'workforce planning', 'employee engagement'],
            'security_safety': ['security', 'safety', 'surveillance', 'protection', 'risk management', 'emergency response', 'cybersecurity', 'physical security', 'compliance', 'threat assessment']
        }
        
        self.user_type_patterns = {
            # Oil & Gas
            'field_operators': ['field operator', 'field personnel', 'on-site personnel', 'technician', 'operator', 'drilling operator', 'production operator'],
            'petroleum_engineers': ['petroleum engineer', 'reservoir engineer', 'drilling engineer', 'production engineer', 'completion engineer'],
            
            # Healthcare
            'healthcare_providers': ['doctor', 'physician', 'nurse', 'clinician', 'medical staff', 'healthcare provider', 'practitioner', 'surgeon', 'therapist'],
            'patients': ['patient', 'client', 'individual', 'person receiving care', 'healthcare consumer'],
            'healthcare_administrators': ['healthcare administrator', 'medical director', 'hospital administrator', 'clinic manager'],
            
            # Finance
            'financial_advisors': ['financial advisor', 'investment advisor', 'wealth manager', 'financial planner', 'portfolio manager'],
            'traders': ['trader', 'portfolio manager', 'analyst', 'fund manager', 'investment banker', 'broker'],
            'financial_customers': ['client', 'investor', 'account holder', 'customer', 'policyholder'],
            'compliance_officers': ['compliance officer', 'risk manager', 'auditor', 'regulatory specialist'],
            
            # Retail
            'retailers': ['retailer', 'store manager', 'sales associate', 'merchandiser', 'cashier', 'inventory specialist'],
            'retail_customers': ['customer', 'shopper', 'buyer', 'consumer', 'client'],
            'suppliers': ['supplier', 'vendor', 'distributor', 'manufacturer', 'wholesaler'],
            
            # Education
            'educators': ['teacher', 'instructor', 'professor', 'educator', 'faculty', 'tutor', 'lecturer'],
            'students': ['student', 'learner', 'pupil', 'trainee', 'participant'],
            'education_administrators': ['administrator', 'principal', 'dean', 'academic coordinator', 'registrar'],
            
            # Manufacturing
            'production_workers': ['production worker', 'assembly worker', 'machine operator', 'technician', 'line worker'],
            'quality_inspectors': ['quality inspector', 'quality control', 'quality assurance', 'QA specialist', 'QC analyst'],
            'plant_managers': ['plant manager', 'production manager', 'operations manager', 'supervisor', 'floor supervisor'],
            
            # Real Estate
            'real_estate_professionals': ['real estate agent', 'broker', 'realtor', 'listing agent', 'property manager', 'home inspector', 'appraiser', 'mortgage broker', 'escrow officer'],
            'property_stakeholders': ['buyer', 'seller', 'homeowner', 'tenant', 'landlord', 'investor', 'first-time buyer', 'home seller'],
            
            # Logistics
            'logistics_coordinators': ['logistics coordinator', 'supply chain manager', 'warehouse manager', 'shipping coordinator', 'freight forwarder'],
            'drivers': ['driver', 'truck driver', 'delivery driver', 'courier', 'transport operator'],
            'warehouse_workers': ['warehouse worker', 'picker', 'packer', 'forklift operator', 'inventory clerk'],
            
            # Agriculture
            'farmers': ['farmer', 'rancher', 'agricultural producer', 'grower', 'livestock farmer'],
            'agricultural_specialists': ['agronomist', 'veterinarian', 'agricultural engineer', 'farm advisor', 'extension agent'],
            'farm_workers': ['farm worker', 'field worker', 'harvest worker', 'equipment operator'],
            
            # Technology
            'developers': ['developer', 'programmer', 'engineer', 'technical', 'software engineer', 'web developer', 'mobile developer'],
            'tech_professionals': ['system administrator', 'DevOps engineer', 'data scientist', 'cybersecurity specialist', 'IT manager'],
            'tech_users': ['end user', 'system user', 'technical user', 'power user'],
            
            # Telecommunications
            'telecom_engineers': ['network engineer', 'telecommunications engineer', 'systems engineer', 'field technician'],
            'telecom_customers': ['subscriber', 'customer', 'user', 'client', 'consumer'],
            
            # Energy
            'energy_professionals': ['engineer', 'technician', 'operator', 'energy analyst', 'grid operator', 'utility worker'],
            'energy_customers': ['customer', 'consumer', 'ratepayer', 'utility customer'],
            
            # Transportation
            'transport_operators': ['driver', 'pilot', 'conductor', 'operator', 'captain', 'dispatcher'],
            'transport_passengers': ['passenger', 'rider', 'traveler', 'commuter', 'customer'],
            'transport_planners': ['traffic planner', 'transportation planner', 'logistics coordinator', 'route planner'],
            
            # Hospitality & Tourism
            'hospitality_staff': ['hotel staff', 'front desk', 'concierge', 'housekeeper', 'server', 'chef', 'manager'],
            'guests': ['guest', 'customer', 'visitor', 'traveler', 'tourist', 'patron'],
            
            # Entertainment & Media
            'content_creators': ['content creator', 'producer', 'director', 'writer', 'editor', 'designer', 'artist'],
            'audience': ['audience', 'viewer', 'listener', 'reader', 'user', 'subscriber', 'fan'],
            
            # Construction
            'construction_workers': ['construction worker', 'contractor', 'builder', 'tradesperson', 'foreman', 'project manager'],
            'architects_engineers': ['architect', 'engineer', 'designer', 'planner', 'surveyor'],
            'construction_clients': ['client', 'property owner', 'developer', 'investor'],
            
            # Automotive
            'automotive_workers': ['assembly worker', 'technician', 'mechanic', 'engineer', 'quality inspector'],
            'automotive_customers': ['customer', 'buyer', 'car owner', 'driver', 'fleet manager'],
            
            # Aerospace & Defense
            'aerospace_engineers': ['aerospace engineer', 'flight engineer', 'systems engineer', 'test pilot', 'mission specialist'],
            'defense_personnel': ['military personnel', 'contractor', 'analyst', 'technician', 'operator'],
            
            # Pharmaceuticals & Biotech
            'researchers': ['researcher', 'scientist', 'clinical researcher', 'lab technician', 'biotech specialist'],
            'regulatory_professionals': ['regulatory affairs', 'compliance specialist', 'quality assurance', 'FDA liaison'],
            
            # Consumer Goods
            'brand_managers': ['brand manager', 'product manager', 'marketing manager', 'merchandiser'],
            'consumers': ['consumer', 'customer', 'shopper', 'buyer', 'end user'],
            
            # Environmental Services
            'environmental_specialists': ['environmental scientist', 'sustainability specialist', 'waste manager', 'conservation specialist'],
            'environmental_stakeholders': ['community member', 'regulator', 'environmental advocate', 'stakeholder'],
            
            # Government & Public Sector
            'government_employees': ['civil servant', 'government employee', 'public administrator', 'policy maker', 'regulator'],
            'citizens': ['citizen', 'resident', 'taxpayer', 'community member', 'constituent'],
            
            # Insurance
            'insurance_professionals': ['insurance agent', 'underwriter', 'claims adjuster', 'actuary', 'insurance broker'],
            'insurance_customers': ['policyholder', 'insured', 'client', 'customer', 'beneficiary'],
            
            # Professional Services
            'consultants': ['consultant', 'advisor', 'specialist', 'expert', 'professional'],
            'service_clients': ['client', 'customer', 'business owner', 'organization', 'stakeholder'],
            
            # Nonprofit & Social Impact
            'nonprofit_staff': ['program manager', 'social worker', 'volunteer coordinator', 'fundraiser', 'community organizer'],
            'beneficiaries': ['beneficiary', 'client', 'community member', 'participant', 'recipient'],
            'donors': ['donor', 'supporter', 'volunteer', 'contributor', 'philanthropist'],
            
            # Mining & Natural Resources
            'mining_workers': ['miner', 'equipment operator', 'geologist', 'mining engineer', 'safety specialist'],
            'environmental_monitors': ['environmental monitor', 'compliance officer', 'safety inspector', 'regulator'],
            
            # Food & Beverage
            'food_service_staff': ['chef', 'cook', 'server', 'bartender', 'food service worker', 'manager'],
            'diners': ['customer', 'diner', 'guest', 'patron', 'consumer'],
            
            # E-commerce
            'ecommerce_professionals': ['ecommerce manager', 'digital marketer', 'customer service', 'fulfillment specialist'],
            'online_shoppers': ['customer', 'shopper', 'buyer', 'user', 'online consumer'],
            
            # Sports & Fitness
            'fitness_professionals': ['trainer', 'coach', 'instructor', 'fitness professional', 'athletic trainer'],
            'athletes': ['athlete', 'player', 'participant', 'member', 'client', 'trainee'],
            
            # Workforce Management
            'hr_professionals': ['HR professional', 'recruiter', 'talent manager', 'HR coordinator', 'payroll specialist'],
            'employees': ['employee', 'worker', 'staff member', 'team member', 'personnel'],
            
            # Security & Safety
            'security_professionals': ['security officer', 'safety specialist', 'security analyst', 'guard', 'safety coordinator'],
            'protected_individuals': ['employee', 'resident', 'visitor', 'stakeholder', 'community member'],
            
            # Generic roles (apply to all domains)
            'managers': ['manager', 'leader', 'supervisor', 'executive', 'director'],
            'analysts': ['analyst', 'data analyst', 'engineer', 'specialist', 'researcher'],
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
        
        # Extract user types (pass detected domain for filtering)
        detected_domain = enhanced_context.get('domain')
        user_types = self._extract_user_types(vision_statement, target_audience, detected_domain)
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
    
    def _get_domain_user_types(self, domain: str) -> List[str]:
        """Get user types relevant to a specific domain."""
        if not domain:
            return ['managers', 'analysts', 'end_users']  # Generic fallback
        
        domain_mappings = {
            'logistics': ['logistics_coordinators', 'drivers', 'warehouse_workers', 'managers', 'end_users'],
            'healthcare': ['healthcare_providers', 'patients', 'healthcare_administrators', 'managers'],
            'finance': ['financial_advisors', 'traders', 'financial_customers', 'compliance_officers', 'analysts'],
            'retail': ['retailers', 'retail_customers', 'suppliers', 'managers'],
            'education': ['educators', 'students', 'education_administrators', 'managers'],
            'manufacturing': ['production_workers', 'quality_inspectors', 'plant_managers', 'managers'],
            'real_estate': ['real_estate_professionals', 'property_stakeholders', 'managers'],
            'oil_gas': ['field_operators', 'petroleum_engineers', 'managers'],
            'agriculture': ['farmers', 'agricultural_specialists', 'farm_workers', 'managers'],
            'technology': ['developers', 'tech_professionals', 'tech_users', 'managers'],
            'telecommunications': ['telecom_engineers', 'telecom_customers', 'managers'],
            'energy': ['energy_professionals', 'energy_customers', 'managers'],
            'transportation': ['transport_operators', 'transport_passengers', 'transport_planners', 'managers'],
            'hospitality_tourism': ['hospitality_staff', 'guests', 'managers'],
            'entertainment_media': ['content_creators', 'audience', 'managers'],
            'construction': ['construction_workers', 'architects_engineers', 'construction_clients', 'managers'],
            'automotive': ['automotive_workers', 'automotive_customers', 'managers'],
            'aerospace_defense': ['aerospace_engineers', 'defense_personnel', 'managers'],
            'pharmaceuticals_biotech': ['researchers', 'regulatory_professionals', 'managers'],
            'consumer_goods': ['brand_managers', 'consumers', 'managers'],
            'environmental_services': ['environmental_specialists', 'environmental_stakeholders', 'managers'],
            'government_public_sector': ['government_employees', 'citizens', 'managers'],
            'insurance': ['insurance_professionals', 'insurance_customers', 'managers'],
            'professional_services': ['consultants', 'service_clients', 'managers'],
            'nonprofit_social_impact': ['nonprofit_staff', 'beneficiaries', 'donors', 'managers'],
            'mining_natural_resources': ['mining_workers', 'environmental_monitors', 'managers'],
            'food_beverage': ['food_service_staff', 'diners', 'managers'],
            'ecommerce': ['ecommerce_professionals', 'online_shoppers', 'managers'],
            'sports_fitness': ['fitness_professionals', 'athletes', 'managers'],
            'workforce_management': ['hr_professionals', 'employees', 'managers'],
            'security_safety': ['security_professionals', 'protected_individuals', 'managers']
        }
        
        return domain_mappings.get(domain, ['managers', 'analysts', 'end_users'])
    
    def _get_domain_default_users(self, domain: str) -> str:
        """Get default users for a domain when no specific types are detected."""
        if not domain:
            return 'end users'
        
        domain_defaults = {
            'logistics': 'warehouse managers, logistics coordinators',
            'healthcare': 'healthcare providers, patients',
            'finance': 'financial advisors, clients',
            'retail': 'store managers, customers',
            'education': 'educators, students',
            'manufacturing': 'production managers, workers',
            'real_estate': 'real estate agents, clients',
            'oil_gas': 'field operators, engineers',
            'agriculture': 'farmers, agricultural specialists',
            'technology': 'developers, end users',
            'telecommunications': 'network engineers, customers',
            'energy': 'energy professionals, customers',
            'transportation': 'transport operators, passengers',
            'hospitality_tourism': 'hospitality staff, guests',
            'entertainment_media': 'content creators, audience',
            'construction': 'construction workers, clients',
            'automotive': 'automotive workers, customers',
            'aerospace_defense': 'aerospace engineers, personnel',
            'pharmaceuticals_biotech': 'researchers, regulatory professionals',
            'consumer_goods': 'brand managers, consumers',
            'environmental_services': 'environmental specialists',
            'government_public_sector': 'government employees, citizens',
            'insurance': 'insurance professionals, customers',
            'professional_services': 'consultants, clients',
            'nonprofit_social_impact': 'nonprofit staff, beneficiaries',
            'mining_natural_resources': 'mining workers, specialists',
            'food_beverage': 'food service staff, customers',
            'ecommerce': 'ecommerce professionals, online shoppers',
            'sports_fitness': 'fitness professionals, athletes',
            'workforce_management': 'HR professionals, employees',
            'security_safety': 'security professionals, protected individuals'
        }
        
        return domain_defaults.get(domain, 'end users')
    
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
    
    def _extract_user_types(self, text: str, target_audience: str = None, detected_domain: str = None) -> str:
        """Extract specific user types from the text, filtered by domain."""
        text_lower = text.lower()
        
        # Check target audience first
        if target_audience and target_audience != 'end users':
            return target_audience
        
        # Get relevant user types based on detected domain
        domain_user_types = self._get_domain_user_types(detected_domain)
        
        detected_types = []
        for user_type, patterns in self.user_type_patterns.items():
            # Only check user types relevant to the detected domain
            if user_type in domain_user_types:
                if any(pattern in text_lower for pattern in patterns):
                    detected_types.append(user_type)
        
        if detected_types:
            return ', '.join(detected_types).replace('_', ' ')
        
        # Domain-specific fallback
        return self._get_domain_default_users(detected_domain)
    
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
        domain_vocabulary_mapping = {
            'oil_gas': {
                'triggers': ['oil', 'gas', 'field', 'well', 'drilling'],
                'terms': [
                    'field operations', 'well longevity', 'stimulation jobs', 'non-productive time',
                    'operational efficiency', 'job completion', 'field operators', 'drilling',
                    'production optimization', 'downhole', 'reservoir', 'completion'
                ]
            },
            'healthcare': {
                'triggers': ['healthcare', 'medical', 'patient', 'clinical', 'hospital'],
                'terms': [
                    'patient care', 'clinical workflow', 'medical records', 'diagnosis', 'treatment plan',
                    'healthcare delivery', 'patient safety', 'clinical decision support', 'medical imaging', 'laboratory results'
                ]
            },
            'finance': {
                'triggers': ['financial', 'banking', 'trading', 'investment', 'portfolio'],
                'terms': [
                    'portfolio management', 'risk assessment', 'financial planning', 'investment strategy',
                    'market analysis', 'compliance reporting', 'transaction processing', 'account management', 'financial modeling', 'regulatory compliance'
                ]
            },
            'retail': {
                'triggers': ['retail', 'ecommerce', 'shopping', 'customer', 'inventory'],
                'terms': [
                    'inventory management', 'point of sale', 'customer experience', 'supply chain',
                    'merchandising', 'sales analytics', 'customer loyalty', 'product catalog', 'order fulfillment', 'retail operations'
                ]
            },
            'education': {
                'triggers': ['education', 'learning', 'student', 'teacher', 'curriculum'],
                'terms': [
                    'curriculum design', 'learning outcomes', 'student assessment', 'educational technology',
                    'lesson planning', 'academic performance', 'learning management', 'educational resources', 'student engagement', 'academic analytics'
                ]
            },
            'manufacturing': {
                'triggers': ['manufacturing', 'production', 'assembly', 'quality', 'factory'],
                'terms': [
                    'production planning', 'quality control', 'supply chain management', 'manufacturing process',
                    'assembly line', 'production efficiency', 'quality assurance', 'inventory control', 'lean manufacturing', 'process optimization'
                ]
            },
            'real_estate': {
                'triggers': ['real estate', 'property', 'home', 'buyer', 'seller', 'listing'],
                'terms': [
                    'property transactions', 'home buying process', 'listing management', 'market analysis',
                    'property valuation', 'closing process', 'mortgage approval', 'property search',
                    'offer negotiation', 'inspection scheduling', 'escrow management', 'title verification',
                    'comparative market analysis', 'property showing', 'buyer qualification', 'commission tracking',
                    'mls integration', 'property marketing', 'transaction coordination', 'client relationship management'
                ]
            },
            'logistics': {
                'triggers': ['logistics', 'shipping', 'freight', 'supply chain', 'distribution'],
                'terms': [
                    'supply chain optimization', 'freight management', 'warehouse operations', 'route planning',
                    'inventory tracking', 'shipment coordination', 'delivery scheduling', 'cargo handling', 'fleet optimization', 'logistics analytics'
                ]
            },
            'agriculture': {
                'triggers': ['agriculture', 'farming', 'crops', 'livestock', 'harvest'],
                'terms': [
                    'crop management', 'livestock care', 'farm planning', 'agricultural production',
                    'soil analysis', 'irrigation management', 'harvest optimization', 'farm equipment', 'sustainable agriculture', 'yield optimization'
                ]
            },
            'technology': {
                'triggers': ['technology', 'software', 'development', 'IT', 'programming'],
                'terms': [
                    'software development', 'system architecture', 'cloud infrastructure', 'data analytics',
                    'cybersecurity', 'DevOps', 'digital transformation', 'technology stack', 'API development', 'system integration'
                ]
            },
            'telecommunications': {
                'triggers': ['telecommunications', 'network', 'wireless', 'broadband', 'connectivity'],
                'terms': [
                    'network management', 'telecommunications infrastructure', 'wireless communications', 'broadband services',
                    'network optimization', 'connectivity solutions', 'telecommunications planning', 'signal processing', 'network security', 'telecom operations'
                ]
            },
            'energy': {
                'triggers': ['energy', 'renewable', 'solar', 'wind', 'electricity'],
                'terms': [
                    'energy management', 'renewable energy', 'power generation', 'grid operations',
                    'energy efficiency', 'utility management', 'energy storage', 'smart grid', 'power distribution', 'energy analytics'
                ]
            },
            'transportation': {
                'triggers': ['transportation', 'transit', 'traffic', 'vehicle', 'logistics'],
                'terms': [
                    'transportation planning', 'traffic management', 'route optimization', 'fleet management',
                    'transit operations', 'mobility solutions', 'transportation analytics', 'vehicle tracking', 'logistics coordination', 'transport efficiency'
                ]
            },
            'hospitality_tourism': {
                'triggers': ['hospitality', 'tourism', 'hotel', 'travel', 'guest'],
                'terms': [
                    'guest experience', 'hospitality management', 'reservation systems', 'tourism planning',
                    'customer service', 'hotel operations', 'travel coordination', 'guest satisfaction', 'hospitality analytics', 'tourism marketing'
                ]
            },
            'entertainment_media': {
                'triggers': ['entertainment', 'media', 'content', 'production', 'streaming'],
                'terms': [
                    'content management', 'media production', 'entertainment planning', 'audience engagement',
                    'content distribution', 'media analytics', 'production workflow', 'content strategy', 'digital media', 'entertainment marketing'
                ]
            },
            'construction': {
                'triggers': ['construction', 'building', 'architecture', 'contractor', 'development'],
                'terms': [
                    'project management', 'construction planning', 'building design', 'contractor coordination',
                    'construction safety', 'project scheduling', 'construction materials', 'building inspection', 'construction analytics', 'development planning'
                ]
            },
            'automotive': {
                'triggers': ['automotive', 'vehicle', 'car', 'manufacturing', 'assembly'],
                'terms': [
                    'vehicle manufacturing', 'automotive design', 'assembly operations', 'quality control',
                    'automotive testing', 'production planning', 'vehicle development', 'automotive analytics', 'manufacturing efficiency', 'vehicle maintenance'
                ]
            },
            'aerospace_defense': {
                'triggers': ['aerospace', 'defense', 'aircraft', 'aviation', 'flight'],
                'terms': [
                    'aerospace engineering', 'flight operations', 'defense systems', 'aircraft maintenance',
                    'mission planning', 'aerospace manufacturing', 'flight safety', 'defense analytics', 'aerospace testing', 'aviation management'
                ]
            },
            'pharmaceuticals_biotech': {
                'triggers': ['pharmaceuticals', 'biotech', 'drug', 'clinical', 'research'],
                'terms': [
                    'drug development', 'clinical research', 'pharmaceutical manufacturing', 'regulatory compliance',
                    'biotech research', 'clinical trials', 'drug testing', 'pharmaceutical analytics', 'research management', 'regulatory affairs'
                ]
            },
            'consumer_goods': {
                'triggers': ['consumer goods', 'products', 'brand', 'marketing', 'retail'],
                'terms': [
                    'product development', 'brand management', 'consumer analytics', 'market research',
                    'product marketing', 'consumer behavior', 'product lifecycle', 'brand strategy', 'consumer insights', 'product innovation'
                ]
            },
            'environmental_services': {
                'triggers': ['environmental', 'sustainability', 'waste', 'recycling', 'conservation'],
                'terms': [
                    'environmental management', 'sustainability planning', 'waste management', 'environmental compliance',
                    'conservation efforts', 'environmental monitoring', 'green technology', 'environmental analytics', 'sustainability reporting', 'environmental assessment'
                ]
            },
            'government_public_sector': {
                'triggers': ['government', 'public sector', 'citizen', 'policy', 'administration'],
                'terms': [
                    'public administration', 'citizen services', 'policy development', 'government operations',
                    'public sector management', 'civic engagement', 'government analytics', 'public service delivery', 'regulatory compliance', 'public policy'
                ]
            },
            'insurance': {
                'triggers': ['insurance', 'policy', 'claims', 'underwriting', 'coverage'],
                'terms': [
                    'insurance underwriting', 'claims processing', 'policy management', 'risk assessment',
                    'insurance analytics', 'coverage planning', 'claims investigation', 'insurance operations', 'actuarial analysis', 'policy administration'
                ]
            },
            'professional_services': {
                'triggers': ['consulting', 'advisory', 'professional services', 'business'],
                'terms': [
                    'consulting services', 'business advisory', 'professional expertise', 'client management',
                    'service delivery', 'consulting analytics', 'business consulting', 'advisory services', 'professional development', 'client engagement'
                ]
            },
            'nonprofit_social_impact': {
                'triggers': ['nonprofit', 'charity', 'social impact', 'community', 'volunteer'],
                'terms': [
                    'program management', 'community engagement', 'social impact', 'nonprofit operations',
                    'volunteer coordination', 'fundraising', 'grant management', 'social services', 'community development', 'impact measurement'
                ]
            },
            'mining_natural_resources': {
                'triggers': ['mining', 'extraction', 'natural resources', 'geology', 'minerals'],
                'terms': [
                    'resource extraction', 'mining operations', 'geological analysis', 'mineral processing',
                    'environmental monitoring', 'mining safety', 'resource management', 'extraction planning', 'mining analytics', 'environmental compliance'
                ]
            },
            'food_beverage': {
                'triggers': ['food', 'beverage', 'restaurant', 'culinary', 'nutrition'],
                'terms': [
                    'food service', 'culinary operations', 'nutrition planning', 'food safety',
                    'restaurant management', 'menu development', 'food production', 'beverage service', 'culinary analytics', 'food quality'
                ]
            },
            'ecommerce': {
                'triggers': ['ecommerce', 'online shopping', 'digital commerce', 'marketplace'],
                'terms': [
                    'ecommerce operations', 'online retail', 'digital marketing', 'customer experience',
                    'order management', 'payment processing', 'inventory management', 'ecommerce analytics', 'digital commerce', 'online customer service'
                ]
            },
            'sports_fitness': {
                'triggers': ['sports', 'fitness', 'athletics', 'training', 'wellness'],
                'terms': [
                    'athletic training', 'fitness management', 'sports performance', 'wellness programs',
                    'exercise planning', 'sports analytics', 'fitness tracking', 'athletic development', 'health monitoring', 'performance optimization'
                ]
            },
            'workforce_management': {
                'triggers': ['workforce', 'human resources', 'employee', 'talent', 'hr'],
                'terms': [
                    'talent management', 'employee engagement', 'workforce planning', 'performance management',
                    'recruitment', 'human resources', 'employee development', 'workforce analytics', 'talent acquisition', 'HR operations'
                ]
            },
            'security_safety': {
                'triggers': ['security', 'safety', 'surveillance', 'protection', 'risk'],
                'terms': [
                    'security management', 'safety protocols', 'risk assessment', 'threat analysis',
                    'security operations', 'safety compliance', 'protection services', 'security analytics', 'emergency response', 'safety management'
                ]
            }
        }
        
        # Check each domain for vocabulary terms
        for domain_key, domain_data in domain_vocabulary_mapping.items():
            if any(trigger in text_lower for trigger in domain_data['triggers']):
                for term in domain_data['terms']:
                    if term.lower() in text_lower:
                        vocabulary.append(term)
        
        return vocabulary[:10]  # Limit to top 10 terms
