#!/usr/bin/env python3
"""
Database migration script to add domain management tables and migrate existing domain data.
"""

import sqlite3
import json
import logging
from datetime import datetime
from typing import Dict, List, Any
from pathlib import Path

logger = logging.getLogger(__name__)

class DomainMigration:
    def __init__(self, db_path: str = "backlog_jobs.db"):
        self.db_path = db_path
        
    def run_migration(self):
        """Execute the complete domain migration."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Step 1: Create new domain tables
                print("🔧 Creating domain management tables...")
                self._create_domain_tables(cursor)
                
                # Step 2: Migrate existing domain data
                print("📦 Migrating existing domain data...")
                self._migrate_existing_domains(cursor)
                
                # Step 3: Create indexes and views
                print("🚀 Creating indexes and views...")
                self._create_indexes_and_views(cursor)
                
                conn.commit()
                print("✅ Domain migration completed successfully!")
                
        except Exception as e:
            logger.error(f"Migration failed: {e}")
            print(f"❌ Migration failed: {e}")
            raise
    
    def _create_domain_tables(self, cursor):
        """Create all domain management tables."""
        
        # Read and execute the domain schema
        schema_file = Path(__file__).parent / "database_enhancement_domains.sql"
        with open(schema_file, 'r') as f:
            schema_sql = f.read()
        
        # Split by double newlines to get individual statements
        statements = [stmt.strip() for stmt in schema_sql.split(';\n') if stmt.strip() and not stmt.strip().startswith('--')]
        
        for statement in statements:
            if statement and not statement.startswith('INSERT') and not statement.startswith('CREATE VIEW'):
                try:
                    cursor.execute(statement + ';')
                except sqlite3.Error as e:
                    if "already exists" not in str(e):
                        logger.warning(f"Schema statement failed: {e}")
    
    def _migrate_existing_domains(self, cursor):
        """Migrate existing VisionContextExtractor domain data to database."""
        
        # Import the enhanced VisionContextExtractor to get all domain data
        from utils.vision_context_extractor import VisionContextExtractor
        extractor = VisionContextExtractor()
        
        # Define comprehensive domain metadata with descriptions
        domain_metadata = {
            'oil_gas': {'display_name': 'Oil & Gas', 'description': 'Petroleum industry including drilling, production, and field operations'},
            'healthcare': {'display_name': 'Healthcare', 'description': 'Medical industry including clinical operations, patient care, and healthcare management'},
            'finance': {'display_name': 'Finance', 'description': 'Financial services including banking, trading, investment, and fintech'},
            'retail': {'display_name': 'Retail', 'description': 'Retail industry including e-commerce, inventory management, and customer service'},
            'education': {'display_name': 'Education', 'description': 'Educational sector including learning management, curriculum, and academic administration'},
            'manufacturing': {'display_name': 'Manufacturing', 'description': 'Manufacturing industry including production, assembly, and supply chain'},
            'real_estate': {'display_name': 'Real Estate', 'description': 'Real estate industry including property transactions, listings, and property management'},
            'logistics': {'display_name': 'Logistics', 'description': 'Logistics and supply chain industry including shipping, warehousing, and distribution'},
            'agriculture': {'display_name': 'Agriculture', 'description': 'Agricultural industry including farming, livestock, and food production'},
            'technology': {'display_name': 'Technology', 'description': 'Technology sector including software development, IT services, and digital innovation'},
            'telecommunications': {'display_name': 'Telecommunications', 'description': 'Telecommunications industry including network infrastructure, wireless communications, and connectivity services'},
            'energy': {'display_name': 'Energy', 'description': 'Energy sector including renewable energy, power generation, and utility services'},
            'transportation': {'display_name': 'Transportation', 'description': 'Transportation industry including public transit, logistics, and mobility services'},
            'hospitality_tourism': {'display_name': 'Hospitality & Tourism', 'description': 'Hospitality and tourism industry including hotels, restaurants, and travel services'},
            'entertainment_media': {'display_name': 'Entertainment & Media', 'description': 'Entertainment and media industry including content creation, broadcasting, and digital media'},
            'construction': {'display_name': 'Construction', 'description': 'Construction industry including building, infrastructure development, and project management'},
            'automotive': {'display_name': 'Automotive', 'description': 'Automotive industry including vehicle manufacturing, dealerships, and maintenance services'},
            'aerospace_defense': {'display_name': 'Aerospace & Defense', 'description': 'Aerospace and defense industry including aircraft manufacturing, military systems, and space technology'},
            'pharmaceuticals_biotech': {'display_name': 'Pharmaceuticals & Biotech', 'description': 'Pharmaceutical and biotechnology industry including drug development, clinical research, and medical innovation'},
            'consumer_goods': {'display_name': 'Consumer Goods', 'description': 'Consumer goods industry including product development, brand management, and retail distribution'},
            'environmental_services': {'display_name': 'Environmental Services', 'description': 'Environmental services industry including sustainability, waste management, and conservation'},
            'government_public_sector': {'display_name': 'Government & Public Sector', 'description': 'Government and public sector including public administration, policy development, and citizen services'},
            'insurance': {'display_name': 'Insurance', 'description': 'Insurance industry including policy management, claims processing, and risk assessment'},
            'professional_services': {'display_name': 'Professional Services', 'description': 'Professional services industry including consulting, advisory services, and business expertise'},
            'nonprofit_social_impact': {'display_name': 'Nonprofit & Social Impact', 'description': 'Nonprofit and social impact sector including charitable organizations, community services, and social change'},
            'mining_natural_resources': {'display_name': 'Mining & Natural Resources', 'description': 'Mining and natural resources industry including extraction, mineral processing, and resource management'},
            'food_beverage': {'display_name': 'Food & Beverage', 'description': 'Food and beverage industry including restaurants, food service, and culinary operations'},
            'ecommerce': {'display_name': 'E-commerce', 'description': 'E-commerce industry including online retail, digital marketplaces, and online customer experience'},
            'sports_fitness': {'display_name': 'Sports & Fitness', 'description': 'Sports and fitness industry including athletic training, wellness programs, and sports management'},
            'workforce_management': {'display_name': 'Workforce Management', 'description': 'Workforce management industry including human resources, talent management, and employee engagement'},
            'security_safety': {'display_name': 'Security & Safety', 'description': 'Security and safety industry including risk management, surveillance, and protection services'}
        }
        
        # Get vocabulary mapping from the extractor
        vocabulary_mapping = extractor._extract_domain_vocabulary.__defaults__[0] if hasattr(extractor, '_extract_domain_vocabulary') else {}
        
        # Process each domain from the extractor
        for domain_key in extractor.industry_patterns.keys():
            if domain_key in domain_metadata:
                metadata = domain_metadata[domain_key]
                patterns = extractor.industry_patterns[domain_key]
                
                # Insert domain
                cursor.execute('''
                    INSERT OR REPLACE INTO domains (domain_key, display_name, description, is_system_default, is_active)
                    VALUES (?, ?, ?, TRUE, TRUE)
                ''', (domain_key, metadata['display_name'], metadata['description']))
                
                domain_id = cursor.lastrowid or cursor.execute('SELECT id FROM domains WHERE domain_key = ?', (domain_key,)).fetchone()[0]
                
                # Insert patterns
                for pattern in patterns:
                    cursor.execute('''
                        INSERT OR REPLACE INTO domain_patterns (domain_id, pattern_type, pattern_value, weight)
                        VALUES (?, 'keyword', ?, 1.0)
                    ''', (domain_id, pattern))
                
                # Insert user types for this domain
                domain_user_types = {}
                for user_type_key, user_patterns in extractor.user_type_patterns.items():
                    # Group user types by domain based on naming patterns
                    if (domain_key == 'oil_gas' and ('field' in user_type_key or 'petroleum' in user_type_key)) or \
                       (domain_key == 'healthcare' and 'healthcare' in user_type_key) or \
                       (domain_key == 'finance' and 'financial' in user_type_key) or \
                       (domain_key == 'real_estate' and 'real_estate' in user_type_key) or \
                       (domain_key == 'retail' and ('retail' in user_type_key or 'suppliers' in user_type_key)) or \
                       (domain_key == 'education' and ('education' in user_type_key or 'educators' in user_type_key or 'students' in user_type_key)) or \
                       (domain_key == 'manufacturing' and ('production' in user_type_key or 'quality' in user_type_key or 'plant' in user_type_key)) or \
                       user_type_key in ['managers', 'analysts', 'end_users']:  # Generic types for all domains
                        
                        display_name = user_type_key.replace('_', ' ').title()
                        cursor.execute('''
                            INSERT OR REPLACE INTO domain_user_types (domain_id, user_type_key, display_name, user_patterns)
                            VALUES (?, ?, ?, ?)
                        ''', (domain_id, user_type_key, display_name, json.dumps(user_patterns)))
                
                # Insert vocabulary terms (use vocabulary mapping if available)
                vocab_terms = []
                if hasattr(extractor, '_extract_domain_vocabulary'):
                    # Extract vocabulary based on domain triggers
                    test_text = ' '.join(patterns)  # Create test text with domain patterns
                    vocab_terms = extractor._extract_domain_vocabulary(test_text)
                
                # If no specific vocabulary found, add some generic domain terms
                if not vocab_terms:
                    vocab_terms = [f"{metadata['display_name']} operations", f"{metadata['display_name']} management", 
                                 f"{metadata['display_name']} analytics", f"{metadata['display_name']} optimization"]
                
                for vocab_term in vocab_terms[:10]:  # Limit to 10 terms
                    cursor.execute('''
                        INSERT OR REPLACE INTO domain_vocabulary (domain_id, category, term)
                        VALUES (?, 'processes', ?)
                    ''', (domain_id, vocab_term))
        
        print(f"✅ Migrated {len(extractor.industry_patterns)} domains with patterns, user types, and vocabulary")
                    }
                },
                'vocabulary': [
                    'patient care', 'clinical workflow', 'medical records', 'diagnosis', 'treatment plan',
                    'healthcare delivery', 'patient safety', 'clinical decision support', 'medical imaging', 'laboratory results'
                ]
            },
            'finance': {
                'display_name': 'Finance',
                'description': 'Financial services including banking, trading, investment, and fintech',
                'patterns': ['financial', 'banking', 'trading', 'investment', 'portfolio', 'risk', 'compliance', 'fintech'],
                'user_types': {
                    'financial_advisors': {
                        'display_name': 'Financial Advisors',
                        'patterns': ['financial advisor', 'investment advisor', 'wealth manager', 'financial planner']
                    },
                    'traders': {
                        'display_name': 'Traders',
                        'patterns': ['trader', 'portfolio manager', 'analyst', 'fund manager']
                    },
                    'customers': {
                        'display_name': 'Financial Customers',
                        'patterns': ['client', 'investor', 'account holder', 'customer']
                    }
                },
                'vocabulary': [
                    'portfolio management', 'risk assessment', 'financial planning', 'investment strategy',
                    'market analysis', 'compliance reporting', 'transaction processing', 'account management', 'financial modeling', 'regulatory compliance'
                ]
            },
            'retail': {
                'display_name': 'Retail',
                'description': 'Retail industry including e-commerce, inventory management, and customer service',
                'patterns': ['retail', 'ecommerce', 'shopping', 'customer', 'inventory', 'sales', 'merchandise'],
                'user_types': {
                    'retailers': {
                        'display_name': 'Retailers',
                        'patterns': ['retailer', 'store manager', 'sales associate', 'merchandiser']
                    },
                    'customers': {
                        'display_name': 'Retail Customers',
                        'patterns': ['customer', 'shopper', 'buyer', 'consumer']
                    },
                    'suppliers': {
                        'display_name': 'Suppliers',
                        'patterns': ['supplier', 'vendor', 'distributor', 'manufacturer']
                    }
                },
                'vocabulary': [
                    'inventory management', 'point of sale', 'customer experience', 'supply chain',
                    'merchandising', 'sales analytics', 'customer loyalty', 'product catalog', 'order fulfillment', 'retail operations'
                ]
            },
            'education': {
                'display_name': 'Education',
                'description': 'Educational sector including learning management, curriculum, and academic administration',
                'patterns': ['education', 'learning', 'student', 'teacher', 'curriculum', 'academic', 'school'],
                'user_types': {
                    'educators': {
                        'display_name': 'Educators',
                        'patterns': ['teacher', 'instructor', 'professor', 'educator', 'faculty']
                    },
                    'students': {
                        'display_name': 'Students',
                        'patterns': ['student', 'learner', 'pupil', 'trainee']
                    },
                    'administrators': {
                        'display_name': 'Education Administrators',
                        'patterns': ['administrator', 'principal', 'dean', 'academic coordinator']
                    }
                },
                'vocabulary': [
                    'curriculum design', 'learning outcomes', 'student assessment', 'educational technology',
                    'lesson planning', 'academic performance', 'learning management', 'educational resources', 'student engagement', 'academic analytics'
                ]
            },
            'manufacturing': {
                'display_name': 'Manufacturing',
                'description': 'Manufacturing industry including production, assembly, and supply chain',
                'patterns': ['manufacturing', 'production', 'assembly', 'quality', 'supply chain', 'inventory'],
                'user_types': {
                    'production_workers': {
                        'display_name': 'Production Workers',
                        'patterns': ['production worker', 'assembly worker', 'machine operator', 'technician']
                    },
                    'quality_inspectors': {
                        'display_name': 'Quality Inspectors',
                        'patterns': ['quality inspector', 'quality control', 'quality assurance', 'QA specialist']
                    },
                    'plant_managers': {
                        'display_name': 'Plant Managers',
                        'patterns': ['plant manager', 'production manager', 'operations manager', 'supervisor']
                    }
                },
                'vocabulary': [
                    'production planning', 'quality control', 'supply chain management', 'manufacturing process',
                    'assembly line', 'production efficiency', 'quality assurance', 'inventory control', 'lean manufacturing', 'process optimization'
                ]
            },
            'real_estate': {
                'display_name': 'Real Estate',
                'description': 'Real estate industry including property transactions, listings, and property management',
                'patterns': ['real estate', 'property', 'listing', 'mls', 'agent', 'broker', 'buyer', 'seller', 'home', 'house', 'apartment', 'rent', 'sale', 'mortgage', 'appraisal', 'inspection', 'closing', 'lease', 'tenant', 'landlord', 'commission', 'escrow', 'title', 'realtor', 'homeowner', 'transaction', 'property management', 'residential', 'commercial', 'market analysis', 'comparable sales', 'home value', 'property search', 'offer', 'negotiation'],
                'user_types': {
                    'real_estate_professionals': {
                        'display_name': 'Real Estate Professionals',
                        'patterns': ['real estate agent', 'broker', 'realtor', 'listing agent', 'property manager', 'home inspector', 'appraiser', 'mortgage broker', 'escrow officer']
                    },
                    'property_stakeholders': {
                        'display_name': 'Property Stakeholders',
                        'patterns': ['buyer', 'seller', 'homeowner', 'tenant', 'landlord', 'investor', 'first-time buyer', 'home seller']
                    }
                },
                'vocabulary': [
                    'property transactions', 'home buying process', 'listing management', 'market analysis',
                    'property valuation', 'closing process', 'mortgage approval', 'property search',
                    'offer negotiation', 'inspection scheduling', 'escrow management', 'title verification',
                    'comparative market analysis', 'property showing', 'buyer qualification', 'commission tracking',
                    'mls integration', 'property marketing', 'transaction coordination', 'client relationship management'
                ]
            }
        }
        
        # Insert domains
        for domain_key, domain_data in existing_domains.items():
            # Insert domain
            cursor.execute('''
                INSERT OR REPLACE INTO domains (domain_key, display_name, description, is_system_default, is_active)
                VALUES (?, ?, ?, TRUE, TRUE)
            ''', (domain_key, domain_data['display_name'], domain_data['description']))
            
            domain_id = cursor.lastrowid
            
            # Insert patterns
            for pattern in domain_data['patterns']:
                cursor.execute('''
                    INSERT OR REPLACE INTO domain_patterns (domain_id, pattern_type, pattern_value, weight)
                    VALUES (?, 'keyword', ?, 1.0)
                ''', (domain_id, pattern))
            
            # Insert user types
            for user_type_key, user_type_data in domain_data.get('user_types', {}).items():
                cursor.execute('''
                    INSERT OR REPLACE INTO domain_user_types (domain_id, user_type_key, display_name, user_patterns)
                    VALUES (?, ?, ?, ?)
                ''', (domain_id, user_type_key, user_type_data['display_name'], json.dumps(user_type_data['patterns'])))
            
            # Insert vocabulary
            for vocab_term in domain_data.get('vocabulary', []):
                cursor.execute('''
                    INSERT OR REPLACE INTO domain_vocabulary (domain_id, category, term)
                    VALUES (?, 'processes', ?)
                ''', (domain_id, vocab_term))
            
        print(f"✅ Migrated {len(existing_domains)} domains with patterns, user types, and vocabulary")
    
    def _create_indexes_and_views(self, cursor):
        """Create indexes and views for performance."""
        
        # Create the views from the schema
        cursor.execute('''
            CREATE VIEW IF NOT EXISTS v_domain_complete AS
            SELECT 
                d.id as domain_id,
                d.domain_key,
                d.display_name as domain_name,
                d.description as domain_description,
                d.is_active as domain_active,
                s.id as subdomain_id,
                s.subdomain_key,
                s.display_name as subdomain_name,
                s.description as subdomain_description,
                s.is_active as subdomain_active
            FROM domains d
            LEFT JOIN subdomains s ON d.id = s.domain_id
            WHERE d.is_active = TRUE
            ORDER BY d.sort_order, d.display_name, s.sort_order, s.display_name
        ''')
        
        cursor.execute('''
            CREATE VIEW IF NOT EXISTS v_domain_patterns_summary AS
            SELECT 
                d.domain_key,
                d.display_name as domain_name,
                COUNT(dp.id) as pattern_count,
                GROUP_CONCAT(dp.pattern_value, '|') as patterns
            FROM domains d
            LEFT JOIN domain_patterns dp ON d.id = dp.domain_id AND dp.is_active = TRUE
            WHERE d.is_active = TRUE
            GROUP BY d.id, d.domain_key, d.display_name
        ''')

def main():
    """Run the domain migration."""
    print("🚀 Starting domain migration...")
    migration = DomainMigration()
    migration.run_migration()
    print("🎉 Migration completed successfully!")

if __name__ == "__main__":
    main()