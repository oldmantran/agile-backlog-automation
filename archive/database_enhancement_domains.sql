-- Database Enhancement for Domain Management System
-- This script defines the new tables and relationships for managing domains, subdomains, and their associated patterns

-- =====================================================
-- CORE DOMAIN TABLES
-- =====================================================

-- Main domains table (e.g., real_estate, healthcare, finance)
CREATE TABLE IF NOT EXISTS domains (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    domain_key TEXT NOT NULL UNIQUE,  -- e.g., 'real_estate', 'healthcare'
    display_name TEXT NOT NULL,       -- e.g., 'Real Estate', 'Healthcare'
    description TEXT,                 -- Brief description of the domain
    icon_name TEXT,                   -- Icon identifier for UI
    color_code TEXT,                  -- Hex color for UI theming
    is_active BOOLEAN DEFAULT TRUE,   -- Whether domain is available for selection
    is_system_default BOOLEAN DEFAULT FALSE,  -- System-provided vs user-created
    sort_order INTEGER DEFAULT 0,    -- Display order in UI
    created_by TEXT,                  -- User who created custom domain
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Subdomains table (e.g., 'residential_sales', 'commercial_leasing' under real_estate)
CREATE TABLE IF NOT EXISTS subdomains (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    domain_id INTEGER NOT NULL,
    subdomain_key TEXT NOT NULL,      -- e.g., 'residential_sales', 'commercial_leasing'
    display_name TEXT NOT NULL,       -- e.g., 'Residential Sales', 'Commercial Leasing'
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    sort_order INTEGER DEFAULT 0,
    created_by TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (domain_id) REFERENCES domains (id) ON DELETE CASCADE,
    UNIQUE(domain_id, subdomain_key)
);

-- =====================================================
-- DOMAIN PATTERN TABLES
-- =====================================================

-- Industry-specific patterns/keywords for domain detection
CREATE TABLE IF NOT EXISTS domain_patterns (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    domain_id INTEGER NOT NULL,
    subdomain_id INTEGER,            -- Optional: pattern specific to subdomain
    pattern_type TEXT NOT NULL CHECK (pattern_type IN ('keyword', 'phrase', 'regex')),
    pattern_value TEXT NOT NULL,     -- The actual pattern/keyword
    weight DECIMAL(3,2) DEFAULT 1.0, -- Scoring weight for domain detection
    is_active BOOLEAN DEFAULT TRUE,
    created_by TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (domain_id) REFERENCES domains (id) ON DELETE CASCADE,
    FOREIGN KEY (subdomain_id) REFERENCES subdomains (id) ON DELETE CASCADE
);

-- User types specific to domains (e.g., 'real_estate_agent', 'buyer', 'seller')
CREATE TABLE IF NOT EXISTS domain_user_types (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    domain_id INTEGER NOT NULL,
    subdomain_id INTEGER,
    user_type_key TEXT NOT NULL,     -- e.g., 'real_estate_agent', 'property_buyer'
    display_name TEXT NOT NULL,      -- e.g., 'Real Estate Agent', 'Property Buyer'
    description TEXT,
    user_patterns TEXT NOT NULL,     -- JSON array of detection patterns
    is_active BOOLEAN DEFAULT TRUE,
    sort_order INTEGER DEFAULT 0,
    created_by TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (domain_id) REFERENCES domains (id) ON DELETE CASCADE,
    FOREIGN KEY (subdomain_id) REFERENCES subdomains (id) ON DELETE CASCADE,
    UNIQUE(domain_id, subdomain_id, user_type_key)
);

-- Domain-specific vocabulary and terminology
CREATE TABLE IF NOT EXISTS domain_vocabulary (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    domain_id INTEGER NOT NULL,
    subdomain_id INTEGER,
    category TEXT NOT NULL,          -- e.g., 'processes', 'tools', 'outcomes', 'regulations'
    term TEXT NOT NULL,             -- The vocabulary term
    definition TEXT,                -- Optional definition/explanation
    synonyms TEXT,                  -- JSON array of synonyms
    usage_context TEXT,             -- When/how to use this term
    is_active BOOLEAN DEFAULT TRUE,
    created_by TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (domain_id) REFERENCES domains (id) ON DELETE CASCADE,
    FOREIGN KEY (subdomain_id) REFERENCES subdomains (id) ON DELETE CASCADE
);

-- =====================================================
-- PROJECT DOMAIN ASSOCIATIONS
-- =====================================================

-- Many-to-many relationship between projects and domains
CREATE TABLE IF NOT EXISTS project_domains (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id TEXT NOT NULL,        -- References projects (stored elsewhere)
    domain_id INTEGER NOT NULL,
    subdomain_id INTEGER,            -- Optional: specific subdomain selection
    is_primary BOOLEAN DEFAULT FALSE, -- Primary domain for the project
    weight DECIMAL(3,2) DEFAULT 1.0, -- Influence weight for multi-domain projects
    selected_by TEXT,                -- User who selected this domain
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (domain_id) REFERENCES domains (id) ON DELETE CASCADE,
    FOREIGN KEY (subdomain_id) REFERENCES subdomains (id) ON DELETE CASCADE,
    UNIQUE(project_id, domain_id, subdomain_id)
);

-- =====================================================
-- USER DOMAIN REQUESTS
-- =====================================================

-- User requests for new domains or enhancements
CREATE TABLE IF NOT EXISTS domain_requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    requested_by TEXT NOT NULL,      -- User ID who made the request
    request_type TEXT NOT NULL CHECK (request_type IN ('new_domain', 'new_subdomain', 'enhancement', 'pattern_addition')),
    parent_domain_id INTEGER,        -- For subdomain requests
    requested_domain_key TEXT,       -- Proposed domain key
    requested_display_name TEXT,     -- Proposed display name
    justification TEXT NOT NULL,     -- Why this domain is needed
    proposed_patterns TEXT,          -- JSON array of proposed patterns
    proposed_user_types TEXT,        -- JSON array of proposed user types
    proposed_vocabulary TEXT,        -- JSON array of proposed vocabulary
    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected', 'implemented')),
    admin_response TEXT,             -- Admin response/feedback
    priority TEXT DEFAULT 'medium' CHECK (priority IN ('low', 'medium', 'high', 'critical')),
    reviewed_by TEXT,                -- Admin who reviewed
    reviewed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (parent_domain_id) REFERENCES domains (id) ON DELETE SET NULL
);

-- =====================================================
-- INDEXES FOR PERFORMANCE
-- =====================================================

-- Domain lookup indexes
CREATE INDEX IF NOT EXISTS idx_domains_active ON domains (is_active, sort_order);
CREATE INDEX IF NOT EXISTS idx_domains_key ON domains (domain_key);

-- Subdomain lookup indexes
CREATE INDEX IF NOT EXISTS idx_subdomains_domain ON subdomains (domain_id, is_active);
CREATE INDEX IF NOT EXISTS idx_subdomains_key ON subdomains (domain_id, subdomain_key);

-- Pattern matching indexes
CREATE INDEX IF NOT EXISTS idx_domain_patterns_lookup ON domain_patterns (domain_id, pattern_type, is_active);
CREATE INDEX IF NOT EXISTS idx_domain_patterns_value ON domain_patterns (pattern_value);

-- User type lookup indexes
CREATE INDEX IF NOT EXISTS idx_domain_user_types_lookup ON domain_user_types (domain_id, subdomain_id, is_active);

-- Vocabulary search indexes
CREATE INDEX IF NOT EXISTS idx_domain_vocabulary_lookup ON domain_vocabulary (domain_id, subdomain_id, category, is_active);
CREATE INDEX IF NOT EXISTS idx_domain_vocabulary_term ON domain_vocabulary (term);

-- Project domain associations
CREATE INDEX IF NOT EXISTS idx_project_domains_project ON project_domains (project_id);
CREATE INDEX IF NOT EXISTS idx_project_domains_domain ON project_domains (domain_id, subdomain_id);

-- Domain requests management
CREATE INDEX IF NOT EXISTS idx_domain_requests_status ON domain_requests (status, priority, created_at);
CREATE INDEX IF NOT EXISTS idx_domain_requests_user ON domain_requests (requested_by, created_at);

-- =====================================================
-- SAMPLE DATA INSERTION
-- =====================================================

-- Insert existing domains from VisionContextExtractor
INSERT OR IGNORE INTO domains (domain_key, display_name, description, is_system_default) VALUES
('oil_gas', 'Oil & Gas', 'Petroleum industry including drilling, production, and field operations', TRUE),
('healthcare', 'Healthcare', 'Medical industry including clinical operations, patient care, and healthcare management', TRUE),
('finance', 'Finance', 'Financial services including banking, trading, investment, and fintech', TRUE),
('retail', 'Retail', 'Retail industry including e-commerce, inventory management, and customer service', TRUE),
('education', 'Education', 'Educational sector including learning management, curriculum, and academic administration', TRUE),
('manufacturing', 'Manufacturing', 'Manufacturing industry including production, assembly, and supply chain', TRUE),
('real_estate', 'Real Estate', 'Real estate industry including property transactions, listings, and property management', TRUE);

-- Insert real estate subdomains as examples
INSERT OR IGNORE INTO subdomains (domain_id, subdomain_key, display_name, description) VALUES
((SELECT id FROM domains WHERE domain_key = 'real_estate'), 'residential_sales', 'Residential Sales', 'Home buying and selling for residential properties'),
((SELECT id FROM domains WHERE domain_key = 'real_estate'), 'commercial_leasing', 'Commercial Leasing', 'Commercial property leasing and management'),
((SELECT id FROM domains WHERE domain_key = 'real_estate'), 'property_management', 'Property Management', 'Rental property management and maintenance'),
((SELECT id FROM domains WHERE domain_key = 'real_estate'), 'real_estate_investment', 'Real Estate Investment', 'Investment property analysis and portfolio management');

-- =====================================================
-- VIEWS FOR EASY QUERYING
-- =====================================================

-- Complete domain information view
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
ORDER BY d.sort_order, d.display_name, s.sort_order, s.display_name;

-- Domain patterns aggregated view
CREATE VIEW IF NOT EXISTS v_domain_patterns_summary AS
SELECT 
    d.domain_key,
    d.display_name as domain_name,
    COUNT(dp.id) as pattern_count,
    GROUP_CONCAT(dp.pattern_value, '|') as patterns
FROM domains d
LEFT JOIN domain_patterns dp ON d.id = dp.domain_id AND dp.is_active = TRUE
WHERE d.is_active = TRUE
GROUP BY d.id, d.domain_key, d.display_name;