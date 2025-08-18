"""
Domain Knowledge Configuration

This module contains comprehensive domain knowledge for all supported domains,
including primary terms, secondary terms, user personas, systems, and problems.
Used for flexible domain relevance scoring in quality assessment.
"""

DOMAIN_KNOWLEDGE = {
    "energy": {
        "primary_terms": ["grid management", "renewable integration", "energy efficiency", "smart meters", "load balancing",
                         "power generation", "energy distribution", "grid stability", "energy storage", "microgrid"],
        "secondary_terms": ["carbon", "emissions", "GHG", "Scope 1-3", "SCADA", "DER", "sustainability", "carbon accounting", 
                          "renewable energy", "solar", "wind", "battery storage", "demand response", "peak load",
                          "energy trading", "power purchase", "grid resilience", "outage management", "voltage control",
                          "frequency regulation", "transmission", "distribution network", "energy consumption", "kilowatt",
                          "megawatt", "power quality", "grid synchronization", "energy forecasting", "load shedding",
                          "net metering", "feed-in tariff", "capacity planning", "grid modernization", "AMI", "AMR",
                          "time-of-use pricing", "critical peak pricing", "demand side management", "energy audit"],
        "user_personas": ["Grid Operators", "Energy Producers", "Sustainability Officers", "ESG Teams", 
                         "Industrial Sustainability Officers", "Environmental Services Managers", "Utility Companies",
                         "Energy Traders", "Facility Managers", "Energy Analysts", "Regulatory Compliance Officers",
                         "Renewable Energy Developers", "Energy Consumers", "Power Plant Operators"],
        "systems": ["smart meters", "SCADA/EMS", "AMI feeds", "IoT sensors", "MQTT", "OPC-UA", "renewable forecast systems",
                   "energy management systems", "distribution management systems", "outage management systems",
                   "meter data management", "grid analytics platforms", "energy trading platforms", "DERMS",
                   "virtual power plants", "battery management systems", "substation automation"],
        "problems": ["emissions tracking", "load balancing", "renewable forecasting", "regulatory compliance", 
                    "carbon reduction", "grid reliability", "energy optimization", "peak demand management",
                    "renewable intermittency", "grid congestion", "energy theft", "power quality issues",
                    "infrastructure aging", "cybersecurity threats", "regulatory reporting", "cost optimization"]
    },
    "environmental_services": {
        "primary_terms": ["waste management", "environmental compliance", "sustainability metrics", "carbon footprint", "recycling systems"],
        "secondary_terms": ["EPA regulations", "waste diversion", "circular economy", "environmental impact", "green initiatives",
                          "pollution control", "resource conservation", "environmental monitoring"],
        "user_personas": ["Environmental Managers", "Compliance Officers", "Sustainability Directors", "Waste Management Teams"],
        "systems": ["waste tracking systems", "compliance dashboards", "environmental sensors", "recycling equipment"],
        "problems": ["regulatory compliance", "waste reduction", "environmental protection", "sustainability reporting"]
    },
    "healthcare": {
        "primary_terms": ["HIPAA compliance", "patient outcomes", "clinical workflows", "EHR integration", "medical records"],
        "secondary_terms": ["patient care", "diagnosis", "treatment", "medical devices", "healthcare analytics", 
                          "telemedicine", "patient safety", "clinical trials", "pharmaceutical"],
        "user_personas": ["Physicians", "Nurses", "Hospital Administrators", "Patients", "Healthcare IT Staff", 
                         "Clinical Researchers", "Pharmacists"],
        "systems": ["EHR/EMR systems", "PACS", "laboratory systems", "medical devices", "patient portals", "HL7/FHIR"],
        "problems": ["patient care coordination", "medical errors", "healthcare costs", "clinical efficiency", "data interoperability"]
    },
    "finance": {
        "primary_terms": ["regulatory compliance", "audit trails", "transaction security", "risk management", "KYC/AML"],
        "secondary_terms": ["financial reporting", "portfolio management", "trading", "banking", "investments", 
                          "fraud detection", "payment processing", "financial analytics"],
        "user_personas": ["Retail Investors", "Wealth Managers", "Bank Tellers", "Loan Officers", "Compliance Officers", 
                         "Financial Analysts", "Traders"],
        "systems": ["core banking systems", "trading platforms", "payment gateways", "risk management systems", "ledgers"],
        "problems": ["fraud prevention", "regulatory reporting", "transaction speed", "risk assessment", "customer onboarding"]
    },
    "retail": {
        "primary_terms": ["inventory management", "customer experience", "omnichannel", "POS integration", "supply chain"],
        "secondary_terms": ["merchandising", "customer loyalty", "retail analytics", "store operations", "e-commerce",
                          "product catalog", "pricing strategy", "seasonal planning"],
        "user_personas": ["Store Managers", "Retail Associates", "Customers", "Inventory Managers", "Merchandisers",
                         "Supply Chain Managers"],
        "systems": ["POS systems", "inventory systems", "CRM", "e-commerce platforms", "supply chain management"],
        "problems": ["inventory optimization", "customer retention", "sales conversion", "supply chain efficiency"]
    },
    "technology": {
        "primary_terms": ["scalability", "API integration", "cloud architecture", "DevOps", "microservices"],
        "secondary_terms": ["software development", "infrastructure", "security", "performance", "automation",
                          "containerization", "CI/CD", "monitoring", "data pipelines"],
        "user_personas": ["Software Engineers", "DevOps Engineers", "System Administrators", "Product Managers", 
                         "Technical Architects", "QA Engineers"],
        "systems": ["cloud platforms", "container orchestration", "monitoring systems", "CI/CD pipelines", "version control"],
        "problems": ["system reliability", "deployment efficiency", "code quality", "infrastructure costs", "technical debt"]
    },
    "education": {
        "primary_terms": ["learning outcomes", "student engagement", "curriculum management", "assessment tools", "LMS integration"],
        "secondary_terms": ["online learning", "educational content", "student performance", "academic records", "course delivery",
                          "educational technology", "adaptive learning", "competency tracking"],
        "user_personas": ["Students", "Teachers", "Administrators", "Parents", "Course Designers", "Academic Advisors"],
        "systems": ["LMS platforms", "student information systems", "assessment platforms", "content management", "video conferencing"],
        "problems": ["student retention", "learning effectiveness", "administrative efficiency", "remote learning", "assessment accuracy"]
    },
    "manufacturing": {
        "primary_terms": ["production efficiency", "quality control", "supply chain", "IoT sensors", "predictive maintenance"],
        "secondary_terms": ["assembly line", "inventory control", "defect tracking", "OEE", "lean manufacturing",
                          "automation", "robotics", "workforce management"],
        "user_personas": ["Plant Managers", "Production Supervisors", "Quality Inspectors", "Maintenance Technicians",
                         "Supply Chain Coordinators", "Machine Operators"],
        "systems": ["MES", "SCADA", "ERP", "quality management systems", "industrial IoT", "robotics systems"],
        "problems": ["production downtime", "quality defects", "inventory costs", "equipment failures", "supply disruptions"]
    },
    "transportation": {
        "primary_terms": ["route optimization", "fleet management", "GPS tracking", "logistics coordination", "delivery scheduling"],
        "secondary_terms": ["vehicle tracking", "driver management", "fuel efficiency", "maintenance scheduling", "cargo management",
                          "traffic patterns", "autonomous vehicles", "last-mile delivery"],
        "user_personas": ["Fleet Managers", "Drivers", "Dispatchers", "Logistics Coordinators", "Maintenance Teams",
                         "Passengers", "Shippers"],
        "systems": ["GPS systems", "fleet management software", "routing engines", "telematics", "dispatch systems", "TMS"],
        "problems": ["delivery delays", "fuel costs", "vehicle maintenance", "route efficiency", "driver safety"]
    },
    "agriculture": {
        "primary_terms": ["crop yield optimization", "precision farming", "soil analytics", "irrigation management", "farm equipment"],
        "secondary_terms": ["harvest planning", "pest control", "weather monitoring", "livestock management", "seed selection",
                          "fertilizer optimization", "drone monitoring", "agricultural IoT"],
        "user_personas": ["Farmers", "Agronomists", "Farm Managers", "Agricultural Consultants", "Cooperative Members",
                         "Agricultural Lenders"],
        "systems": ["precision agriculture systems", "weather stations", "irrigation controllers", "farm management software", "drones"],
        "problems": ["crop yield", "water usage", "pest management", "weather risks", "market pricing"]
    },
    "real_estate": {
        "primary_terms": ["property management", "listing management", "tenant screening", "lease tracking", "maintenance requests"],
        "secondary_terms": ["property valuation", "market analysis", "virtual tours", "rental income", "property marketing",
                          "HOA management", "commercial real estate", "residential properties"],
        "user_personas": ["Property Managers", "Real Estate Agents", "Landlords", "Tenants", "Buyers", "Sellers", "Investors"],
        "systems": ["MLS systems", "property management software", "CRM", "listing platforms", "virtual tour technology"],
        "problems": ["vacancy rates", "maintenance costs", "tenant retention", "property valuation", "market competition"]
    },
    "hospitality": {
        "primary_terms": ["reservation management", "guest experience", "room inventory", "revenue optimization", "service quality"],
        "secondary_terms": ["check-in/check-out", "housekeeping", "food service", "event management", "loyalty programs",
                          "online reviews", "channel management", "dynamic pricing"],
        "user_personas": ["Hotel Managers", "Front Desk Staff", "Guests", "Housekeeping Staff", "Concierge", "Event Planners"],
        "systems": ["PMS", "reservation systems", "channel managers", "revenue management", "guest feedback platforms"],
        "problems": ["occupancy rates", "guest satisfaction", "operational efficiency", "revenue per room", "staff management"]
    },
    "insurance": {
        "primary_terms": ["claims processing", "underwriting", "risk assessment", "policy management", "actuarial analysis"],
        "secondary_terms": ["premium calculation", "fraud detection", "customer onboarding", "reinsurance", "regulatory compliance",
                          "loss prevention", "insurance analytics", "digital insurance"],
        "user_personas": ["Insurance Agents", "Underwriters", "Claims Adjusters", "Policyholders", "Actuaries", "Risk Managers"],
        "systems": ["policy administration systems", "claims management", "underwriting platforms", "actuarial software", "CRM"],
        "problems": ["claims fraud", "risk pricing", "customer acquisition", "claims efficiency", "regulatory compliance"]
    },
    "nonprofit": {
        "primary_terms": ["donor management", "fundraising campaigns", "volunteer coordination", "grant tracking", "impact measurement"],
        "secondary_terms": ["donation processing", "event management", "member engagement", "program delivery", "financial transparency",
                          "community outreach", "advocacy", "nonprofit compliance"],
        "user_personas": ["Donors", "Volunteers", "Program Directors", "Fundraisers", "Grant Writers", "Beneficiaries", "Board Members"],
        "systems": ["donor CRM", "fundraising platforms", "volunteer management", "grant management", "event systems"],
        "problems": ["donor retention", "volunteer engagement", "funding sustainability", "impact reporting", "operational efficiency"]
    },
    "government_public_sector": {
        "primary_terms": ["citizen services", "regulatory compliance", "public safety", "government transparency", "civic engagement"],
        "secondary_terms": ["permit processing", "tax collection", "public records", "emergency services", "infrastructure management",
                          "policy implementation", "constituent services", "e-governance"],
        "user_personas": ["Citizens", "Government Employees", "Public Officials", "Law Enforcement", "Emergency Responders", "Contractors"],
        "systems": ["citizen portals", "permit systems", "tax systems", "emergency management", "GIS", "case management"],
        "problems": ["service delivery", "regulatory compliance", "budget constraints", "citizen satisfaction", "data transparency"]
    },
    "legal": {
        "primary_terms": ["case management", "document automation", "billing tracking", "compliance monitoring", "litigation support"],
        "secondary_terms": ["contract management", "legal research", "time tracking", "client communication", "court filing",
                          "intellectual property", "due diligence", "legal analytics"],
        "user_personas": ["Attorneys", "Paralegals", "Legal Assistants", "Clients", "Judges", "Court Clerks", "Legal Researchers"],
        "systems": ["case management systems", "document management", "legal research platforms", "billing software", "e-discovery"],
        "problems": ["case efficiency", "billing accuracy", "document organization", "compliance deadlines", "client communication"]
    },
    "media_publishing": {
        "primary_terms": ["content management", "editorial workflow", "digital publishing", "audience analytics", "content monetization"],
        "secondary_terms": ["article creation", "multimedia content", "subscription management", "advertising", "social media integration",
                          "content distribution", "reader engagement", "print production"],
        "user_personas": ["Editors", "Writers", "Publishers", "Readers", "Advertisers", "Content Creators", "Designers"],
        "systems": ["CMS", "editorial systems", "digital asset management", "subscription platforms", "analytics tools"],
        "problems": ["content quality", "audience growth", "monetization", "distribution efficiency", "reader retention"]
    },
    "telecommunications": {
        "primary_terms": ["network management", "service provisioning", "customer billing", "network optimization", "fault management"],
        "secondary_terms": ["bandwidth management", "VoIP", "5G deployment", "fiber optics", "mobile services",
                          "network security", "service quality", "roaming management"],
        "user_personas": ["Network Engineers", "Customer Service Reps", "Subscribers", "Technical Support", "Field Technicians"],
        "systems": ["OSS/BSS", "network monitoring", "billing systems", "CRM", "provisioning systems", "network equipment"],
        "problems": ["network reliability", "service quality", "customer churn", "infrastructure costs", "regulatory compliance"]
    },
    "pharmaceutical": {
        "primary_terms": ["drug development", "clinical trials", "FDA compliance", "pharmaceutical manufacturing", "drug safety"],
        "secondary_terms": ["research protocols", "patient recruitment", "adverse events", "drug formulation", "quality assurance",
                          "supply chain integrity", "pharmacovigilance", "regulatory submissions"],
        "user_personas": ["Researchers", "Clinical Trial Managers", "Regulatory Affairs", "Quality Assurance", "Pharmacists", "Patients"],
        "systems": ["LIMS", "clinical trial management", "regulatory systems", "manufacturing execution", "pharmacovigilance systems"],
        "problems": ["regulatory approval", "trial efficiency", "drug safety", "manufacturing quality", "time to market"]
    },
    "automotive": {
        "primary_terms": ["vehicle diagnostics", "autonomous driving", "EV charging", "fleet management", "telematics"],
        "secondary_terms": ["connected cars", "ADAS", "vehicle safety", "infotainment", "predictive maintenance",
                          "electric vehicles", "battery management", "vehicle-to-grid"],
        "user_personas": ["Drivers", "Fleet Managers", "Service Technicians", "Dealerships", "OEMs", "Safety Engineers"],
        "systems": ["telematics platforms", "diagnostic tools", "ADAS systems", "charging infrastructure", "fleet software"],
        "problems": ["vehicle safety", "emissions reduction", "autonomous reliability", "charging infrastructure", "maintenance costs"]
    },
    "aerospace_defense": {
        "primary_terms": ["FAA compliance", "defense contracts", "mission-critical systems", "aviation safety", "radar systems"],
        "secondary_terms": ["flight systems", "air traffic control", "military specifications", "avionics", "satellite systems",
                          "aerospace manufacturing", "defense technology", "security clearance"],
        "user_personas": ["Pilots", "Air Traffic Controllers", "Defense Contractors", "Aerospace Engineers", "Military Personnel"],
        "systems": ["flight control systems", "radar systems", "communication systems", "navigation systems", "defense platforms"],
        "problems": ["safety compliance", "mission reliability", "system integration", "security requirements", "cost overruns"]
    },
    "construction": {
        "primary_terms": ["project management", "building codes", "safety compliance", "BIM integration", "site monitoring"],
        "secondary_terms": ["cost estimation", "subcontractor management", "materials tracking", "schedule optimization", "quality inspections",
                          "permit management", "construction documentation", "equipment management"],
        "user_personas": ["Project Managers", "Site Supervisors", "Contractors", "Architects", "Safety Officers", "Inspectors"],
        "systems": ["project management software", "BIM platforms", "scheduling tools", "safety systems", "document management"],
        "problems": ["project delays", "cost overruns", "safety incidents", "quality issues", "resource allocation"]
    },
    "consumer_goods": {
        "primary_terms": ["product lifecycle", "brand management", "supply chain optimization", "consumer insights", "quality assurance"],
        "secondary_terms": ["product development", "market research", "packaging design", "distribution channels", "brand loyalty",
                          "product launches", "competitive analysis", "sustainability"],
        "user_personas": ["Brand Managers", "Product Developers", "Supply Chain Managers", "Quality Controllers", "Consumers", "Retailers"],
        "systems": ["PLM systems", "supply chain software", "quality management", "market research tools", "ERP"],
        "problems": ["product quality", "brand perception", "supply chain efficiency", "market competition", "consumer trends"]
    },
    "ecommerce": {
        "primary_terms": ["shopping cart", "payment gateway", "conversion optimization", "customer analytics", "fulfillment logistics"],
        "secondary_terms": ["product catalog", "checkout process", "abandoned cart", "customer reviews", "recommendation engine",
                          "inventory sync", "order tracking", "return management"],
        "user_personas": ["Online Shoppers", "E-commerce Managers", "Customer Service", "Warehouse Staff", "Digital Marketers"],
        "systems": ["e-commerce platforms", "payment processors", "inventory management", "CRM", "analytics tools", "fulfillment systems"],
        "problems": ["cart abandonment", "conversion rates", "payment security", "shipping costs", "customer retention"]
    },
    "entertainment_media": {
        "primary_terms": ["content management", "streaming platforms", "audience engagement", "digital rights", "production workflow"],
        "secondary_terms": ["video streaming", "content delivery", "audience analytics", "content monetization", "social engagement",
                          "live broadcasting", "content recommendation", "media production"],
        "user_personas": ["Content Creators", "Producers", "Viewers", "Editors", "Distribution Managers", "Rights Holders"],
        "systems": ["streaming platforms", "content delivery networks", "production tools", "rights management", "analytics platforms"],
        "problems": ["content discovery", "viewer retention", "content piracy", "production costs", "platform competition"]
    },
    "food_beverage": {
        "primary_terms": ["food safety", "HACCP compliance", "inventory tracking", "recipe management", "nutritional analysis"],
        "secondary_terms": ["menu planning", "supplier management", "kitchen operations", "food cost control", "allergen management",
                          "temperature monitoring", "batch tracking", "restaurant management"],
        "user_personas": ["Chefs", "Restaurant Managers", "Food Safety Officers", "Suppliers", "Customers", "Kitchen Staff"],
        "systems": ["kitchen management systems", "POS", "inventory systems", "food safety monitoring", "recipe management"],
        "problems": ["food waste", "compliance violations", "inventory spoilage", "cost control", "customer satisfaction"]
    },
    "sports_fitness": {
        "primary_terms": ["athlete performance", "training programs", "fitness tracking", "sports analytics", "injury prevention"],
        "secondary_terms": ["workout planning", "nutrition tracking", "team management", "competition scheduling", "recovery monitoring",
                          "biomechanics analysis", "wearable integration", "coaching tools"],
        "user_personas": ["Athletes", "Coaches", "Trainers", "Fitness Enthusiasts", "Team Managers", "Sports Scientists"],
        "systems": ["performance tracking", "wearable devices", "training software", "team management platforms", "analytics tools"],
        "problems": ["performance optimization", "injury prevention", "training effectiveness", "team coordination", "data accuracy"]
    },
    "travel_tourism": {
        "primary_terms": ["booking management", "itinerary planning", "travel logistics", "customer reviews", "destination marketing"],
        "secondary_terms": ["flight booking", "hotel reservations", "activity planning", "travel insurance", "local experiences",
                          "group travel", "loyalty programs", "travel documentation"],
        "user_personas": ["Travelers", "Travel Agents", "Tour Operators", "Hotel Staff", "Airlines", "Local Guides"],
        "systems": ["booking engines", "GDS", "property management", "review platforms", "itinerary builders"],
        "problems": ["booking complexity", "price optimization", "customer satisfaction", "inventory management", "seasonality"]
    },
    "logistics_supply_chain": {
        "primary_terms": ["warehouse management", "freight tracking", "supply chain visibility", "order fulfillment", "logistics optimization"],
        "secondary_terms": ["inventory control", "shipping management", "customs clearance", "last-mile delivery", "reverse logistics",
                          "cross-docking", "carrier management", "demand forecasting"],
        "user_personas": ["Warehouse Managers", "Logistics Coordinators", "Truck Drivers", "Supply Chain Analysts", "Customs Brokers"],
        "systems": ["WMS", "TMS", "supply chain platforms", "tracking systems", "EDI", "robotics systems"],
        "problems": ["delivery delays", "inventory accuracy", "shipping costs", "supply chain disruptions", "warehouse efficiency"]
    },
    "mining_resources": {
        "primary_terms": ["resource extraction", "mining operations", "safety monitoring", "geological analysis", "equipment maintenance"],
        "secondary_terms": ["ore processing", "environmental compliance", "worker safety", "production optimization", "exploration data",
                          "mine planning", "equipment tracking", "resource estimation"],
        "user_personas": ["Mine Operators", "Geologists", "Safety Officers", "Equipment Operators", "Environmental Engineers"],
        "systems": ["mine planning software", "safety monitoring systems", "geological modeling", "equipment management", "production tracking"],
        "problems": ["worker safety", "environmental impact", "equipment downtime", "resource depletion", "operational costs"]
    },
    "oil_gas": {
        "primary_terms": ["drilling operations", "pipeline management", "refinery processes", "exploration data", "HSE compliance"],
        "secondary_terms": ["well monitoring", "production optimization", "reservoir management", "downstream operations", "upstream activities",
                          "petrochemical processing", "field operations", "asset integrity"],
        "user_personas": ["Field Engineers", "Refinery Operators", "HSE Managers", "Geologists", "Pipeline Controllers", "Executives"],
        "systems": ["SCADA systems", "drilling platforms", "pipeline monitoring", "refinery control", "exploration software"],
        "problems": ["operational safety", "environmental compliance", "production efficiency", "equipment reliability", "market volatility"]
    }
}

def get_domain_knowledge(domain_key: str) -> dict:
    """Get domain knowledge for a specific domain."""
    return DOMAIN_KNOWLEDGE.get(domain_key, {})

def get_all_domain_terms(domain_key: str) -> list:
    """Get all terms (primary and secondary) for a domain."""
    domain = get_domain_knowledge(domain_key)
    return domain.get('primary_terms', []) + domain.get('secondary_terms', [])

def get_domain_personas(domain_key: str) -> list:
    """Get user personas for a domain."""
    domain = get_domain_knowledge(domain_key)
    return domain.get('user_personas', [])

def is_infrastructure_work_item(title: str, description: str) -> bool:
    """Check if a work item is infrastructure/platform related and domain-agnostic."""
    combined_text = f"{title} {description}".lower()
    
    # First check if it has clear infrastructure keywords
    clear_infrastructure_keywords = [
        'authentication system', 'access control system', 'api gateway',
        'microservices architecture', 'database optimization', 'monitoring infrastructure',
        'logging system', 'message queue', 'event bus',
        # Energy-specific infrastructure
        'grid infrastructure', 'smart grid infrastructure', 'metering infrastructure',
        'data integration platform', 'telemetry system', 'communication infrastructure',
        'integration framework', 'data pipeline', 'streaming platform'
    ]
    if any(keyword in combined_text for keyword in clear_infrastructure_keywords):
        return True
    
    # Exclude if it's clearly domain-specific functionality
    domain_functional_indicators = [
        'grid operator', 'energy producer', 'customer portal', 'patient care',
        'trading platform', 'shopping cart', 'course delivery', 'fleet management'
    ]
    if any(indicator in combined_text for indicator in domain_functional_indicators):
        return False
    
    # More specific infrastructure patterns
    infrastructure_patterns = [
        # Security & Access (but not domain-specific security)
        r'\b(authentication|authorization|login|oauth|sso|jwt|token)\s+(system|framework|service|implementation)',
        r'\buser\s+(authentication|management|access\s+control)\b',
        
        # Architecture & Infrastructure
        r'\b(microservice|infrastructure|deployment|devops|ci/cd|containerization)',
        r'\b(docker|kubernetes|cloud\s+migration|serverless)\b',
        
        # Database & Storage (generic)
        r'\b(database|data\s+migration|schema|indexing)\s+(optimization|design|architecture)',
        r'\b(backup|disaster\s+recovery|data\s+retention)\s+(system|strategy)',
        
        # Performance & Reliability (system-wide)
        r'\bsystem\s+(performance|optimization|scaling)',
        r'\b(high\s+availability|fault\s+tolerance|load\s+balancing)\b',
        
        # Core platform services
        r'\b(api\s+gateway|message\s+queue|event\s+bus|notification\s+system)',
        r'\b(logging|monitoring|telemetry)\s+(infrastructure|system|framework)',
        
        # Development infrastructure
        r'\b(testing\s+framework|test\s+automation|code\s+quality)',
        r'\b(developer\s+tools|sdk|library)\b',
        
        # General infrastructure indicators
        r'\bauthentication\s+system\s+implementation\b',
        r'\bapi\s+gateway\b'
    ]
    
    import re
    return any(re.search(pattern, combined_text, re.IGNORECASE) for pattern in infrastructure_patterns)

def is_non_functional_requirement(title: str, description: str) -> bool:
    """Check if a work item is a non-functional requirement."""
    combined_text = f"{title} {description}".lower()
    
    # Exclude if it's clearly functional implementation
    if is_infrastructure_work_item(title, description):
        return False
    
    # Check for NFR patterns
    nfr_patterns = [
        # Performance requirements
        r'\b(performance|speed|response\s+time|latency)\s+(requirement|optimization|target)',
        r'\b\d+\s*(second|ms|millisecond|concurrent\s+user)',
        
        # Reliability requirements  
        r'\b(reliability|availability|uptime|sla)\s+(requirement|target)',
        r'\b\d+(\.\d+)?%\s+(uptime|availability)',
        
        # Security requirements
        r'\b(security|vulnerability|penetration\s+testing)\s+(requirement|assessment|audit)',
        r'\b(nerc\s+cip|sox|hipaa|gdpr|pci)\s+(compliance|requirement|implementation)',
        # Energy-specific compliance
        r'\b(ferc|iso|rto|nerc)\s+(compliance|standards|requirements)',
        r'\bgrid\s+code\s+compliance',
        
        # Scalability requirements
        r'\b(scalability|capacity|growth)\s+(requirement|planning|target)',
        
        # Other NFRs
        r'\b(usability|accessibility|maintainability)\s+(requirement|standard)',
        r'\b(browser|device|platform)\s+(support|compatibility)',
        
        # Additional NFR patterns
        r'\buptime\s+requirement',
        r'\bcompliance\s+implementation\b'
    ]
    
    import re
    return any(re.search(pattern, combined_text, re.IGNORECASE) for pattern in nfr_patterns)