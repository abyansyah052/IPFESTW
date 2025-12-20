Project Requirement: Streamlit Financial Scenario Testing Application

Saya ingin membuat aplikasi Streamlit untuk menguji berbagai skenario terbaik dari konsep rancangan finansial proyek. Berikut requirement lengkapnya:

contoh proses bisnis aplikasi: 
user Input CAPEX per Kategori
Tim akan melakukan input CAPEX per kategori dengan sistem pemilihan item sebagai berikut:

Kategori Production:

CCUS + CO2 EGR
CCUS + CO2 EOR
Supersonic Separator

Kategori Power:

Combined Cycle Power Plant (CCPP): (asumsi /10000 KW)

Floating Wind Turbine (FWT):  per unit

Kategori Transportation:
Pilih metode terlebih dahulu (Shipping atau Pipeline), kemudian pilih item:

Pipeline:

Pipeline (CO₂/Utility): per satu project (30km)

Shipping:

Stern Tube System (STS):  per vessel

Oil Water Separator (OWS):per process separation unit

Very Large Gas Carriers (VLGC):  per unit

Kategori Flaring:

Flare Gas Recovery System (FGRS):  per flare gas recovery skid

Flexibilitas Pemilihan:
User dapat memilih 1 item, 2 item, atau semua item dalam setiap kategori CAPEX sesuai kebutuhan skenario yang ingin diuji. User juga dapat menentukan jumlah unit/quantity untuk setiap item yang dipilih.

Auto-Generate OPEX
Sistem secara otomatis menghasilkan OPEX yang sesuai berdasarkan CAPEX yang telah dipilih oleh user.

Kalkulasi Finansial
Sistem melakukan proses kalkulasi finansial seperti yang ada di tab "Calculation Example" dengan output:

Data hasil per tahun

Data total

Visualisasi dalam bentuk grafik

Perbandingan Skenario
User dapat membandingkan semua skenario atau hanya beberapa skenario yang dipilih. Sistem akan:

Memberikan rekomendasi skenario terbaik

Menjelaskan alasan mengapa skenario tersebut adalah yang terbaik

Menyajikan hasil perbandingan dalam format yang mudah dipahami

Export Hasil
Hasil analisis dapat diunduh dalam format:
Excel
PDF

nah itu adalah overview, untuk detail perinci dari tiap data capex dan opex juga elemen finansial yang lain ada dibawah ini 


## Tech Stack Final

**Backend & Database:**
- PostgreSQL (hosted di Neon/Supabase/Railway free tier)
- SQLAlchemy untuk ORM
- Psycopg2 untuk database driver

**Frontend:**
- Streamlit (deployed di Streamlit Community Cloud)
- Plotly untuk charting
- Pandas untuk data manipulation

**Deployment:**
- Streamlit Community Cloud (gratis)
- PostgreSQL di Neon.tech (gratis 0.5GB)

## Database Schema - Complete

```sql
-- ====================================
-- DROP TABLES (untuk reset)
-- ====================================

DROP TABLE IF EXISTS audit_log CASCADE;
DROP TABLE IF EXISTS comparison_scenarios CASCADE;
DROP TABLE IF EXISTS scenario_comparisons CASCADE;
DROP TABLE IF EXISTS scenario_metrics CASCADE;
DROP TABLE IF EXISTS calculation_results CASCADE;
DROP TABLE IF EXISTS scenario_opex CASCADE;
DROP TABLE IF EXISTS scenario_capex CASCADE;
DROP TABLE IF EXISTS scenarios CASCADE;
DROP TABLE IF EXISTS production_data CASCADE;
DROP TABLE IF EXISTS production_profiles CASCADE;
DROP TABLE IF EXISTS production_enhancement CASCADE;
DROP TABLE IF EXISTS pricing_assumptions CASCADE;
DROP TABLE IF EXISTS fiscal_terms CASCADE;
DROP TABLE IF EXISTS opex_mapping CASCADE;
DROP TABLE IF EXISTS capex_items CASCADE;
DROP TABLE IF EXISTS capex_subcategories CASCADE;
DROP TABLE IF EXISTS capex_categories CASCADE;

-- ====================================
-- MASTER DATA TABLES
-- ====================================

CREATE TABLE capex_categories (
    id SERIAL PRIMARY KEY,
    code VARCHAR(20) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    sort_order INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE capex_subcategories (
    id SERIAL PRIMARY KEY,
    category_id INTEGER REFERENCES capex_categories(id),
    code VARCHAR(20) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    sort_order INTEGER
);

CREATE TABLE capex_items (
    id SERIAL PRIMARY KEY,
    category_id INTEGER REFERENCES capex_categories(id),
    subcategory_id INTEGER REFERENCES capex_subcategories(id),
    code VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(200) NOT NULL,
    unit VARCHAR(50) NOT NULL,
    unit_cost DECIMAL(15,2) NOT NULL,
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE opex_mapping (
    id SERIAL PRIMARY KEY,
    capex_item_id INTEGER REFERENCES capex_items(id),
    opex_name VARCHAR(200) NOT NULL,
    opex_calculation_method VARCHAR(50),
    opex_rate DECIMAL(10,6),
    opex_unit VARCHAR(50),
    year_start INTEGER,
    year_end INTEGER,
    notes TEXT
);

-- ====================================
-- FISCAL & PRICING PARAMETERS
-- ====================================

CREATE TABLE fiscal_terms (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    version VARCHAR(20),
    gov_oil_pretax DECIMAL(6,4) DEFAULT 0.3277,
    gov_gas_pretax DECIMAL(6,4) DEFAULT 0.3277,
    contractor_oil_pretax DECIMAL(6,4) DEFAULT 0.6723,
    contractor_gas_pretax DECIMAL(6,4) DEFAULT 0.6723,
    gov_oil_posttax DECIMAL(6,4) DEFAULT 0.60,
    gov_gas_posttax DECIMAL(6,4) DEFAULT 0.60,
    contractor_oil_posttax DECIMAL(6,4) DEFAULT 0.40,
    contractor_gas_posttax DECIMAL(6,4) DEFAULT 0.40,
    contractor_tax_rate DECIMAL(6,4) DEFAULT 0.405,
    dmo_volume DECIMAL(6,4) DEFAULT 0.25,
    dmo_fee DECIMAL(6,4) DEFAULT 1.00,
    dmo_holiday INTEGER DEFAULT 0,
    discount_rate DECIMAL(6,4) DEFAULT 0.13,
    depreciation_life INTEGER DEFAULT 5,
    depreciation_method VARCHAR(20) DEFAULT 'DDB',
    depreciation_factor DECIMAL(6,4) DEFAULT 0.25,
    asr_rate DECIMAL(6,4) DEFAULT 0.05,
    salvage_value DECIMAL(15,2) DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE pricing_assumptions (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    version VARCHAR(20),
    oil_price DECIMAL(10,2) DEFAULT 60.00,
    gas_price DECIMAL(10,2) DEFAULT 5.50,
    usd_to_idr DECIMAL(10,2) DEFAULT 16500,
    gross_heating_value DECIMAL(10,2) DEFAULT 1200,
    mmscf_to_mmbtu DECIMAL(10,4) DEFAULT 1027,
    co2_production_rate DECIMAL(6,4) DEFAULT 0.20,
    carbon_tax DECIMAL(10,2) DEFAULT 2.00,
    emission_factor DECIMAL(10,2) DEFAULT 53.06,
    ghv_condensate DECIMAL(6,2) DEFAULT 5.8,
    barrel_to_liter DECIMAL(10,2) DEFAULT 158.987,
    working_days INTEGER DEFAULT 220,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE production_enhancement (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    eor_rate DECIMAL(6,4) DEFAULT 0.20,
    egr_rate DECIMAL(6,4) DEFAULT 0.25,
    is_active BOOLEAN DEFAULT TRUE
);

-- ====================================
-- PRODUCTION DATA
-- ====================================

CREATE TABLE production_profiles (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    project_start_year INTEGER NOT NULL,
    project_duration INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE production_data (
    id SERIAL PRIMARY KEY,
    profile_id INTEGER REFERENCES production_profiles(id),
    year INTEGER NOT NULL,
    condensate_rate_bopd DECIMAL(12,2),
    gas_rate_mmscfd DECIMAL(12,4),
    UNIQUE(profile_id, year)
);

-- ====================================
-- SCENARIO MANAGEMENT
-- ====================================

CREATE TABLE scenarios (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    production_profile_id INTEGER REFERENCES production_profiles(id),
    fiscal_terms_id INTEGER REFERENCES fiscal_terms(id),
    pricing_id INTEGER REFERENCES pricing_assumptions(id),
    enhancement_id INTEGER REFERENCES production_enhancement(id),
    project_duration INTEGER DEFAULT 12,
    created_by VARCHAR(100),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE
);

CREATE TABLE scenario_capex (
    id SERIAL PRIMARY KEY,
    scenario_id INTEGER REFERENCES scenarios(id) ON DELETE CASCADE,
    capex_item_id INTEGER REFERENCES capex_items(id),
    quantity DECIMAL(10,2) DEFAULT 1,
    multiplier DECIMAL(10,2) DEFAULT 1,
    total_cost DECIMAL(15,2),
    year_incurred INTEGER,
    notes TEXT,
    UNIQUE(scenario_id, capex_item_id)
);

CREATE TABLE scenario_opex (
    id SERIAL PRIMARY KEY,
    scenario_id INTEGER REFERENCES scenarios(id) ON DELETE CASCADE,
    year INTEGER NOT NULL,
    opex_name VARCHAR(200),
    opex_amount DECIMAL(15,2),
    source_capex_id INTEGER REFERENCES scenario_capex(id),
    calculation_note TEXT
);

-- ====================================
-- CALCULATION RESULTS
-- ====================================

CREATE TABLE calculation_results (
    id SERIAL PRIMARY KEY,
    scenario_id INTEGER REFERENCES scenarios(id) ON DELETE CASCADE,
    year INTEGER NOT NULL,
    oil_production_bbl DECIMAL(15,2),
    gas_production_mmscf DECIMAL(15,4),
    gas_production_mmbtu DECIMAL(15,2),
    oil_revenue DECIMAL(18,2),
    gas_revenue DECIMAL(18,2),
    total_revenue DECIMAL(18,2),
    capex DECIMAL(18,2),
    opex DECIMAL(18,2),
    depreciation DECIMAL(18,2),
    operating_profit DECIMAL(18,2),
    contractor_pretax DECIMAL(18,2),
    contractor_tax DECIMAL(18,2),
    contractor_aftertax DECIMAL(18,2),
    government_pretax DECIMAL(18,2),
    government_tax DECIMAL(18,2),
    government_total DECIMAL(18,2),
    net_cash_flow DECIMAL(18,2),
    cumulative_cash_flow DECIMAL(18,2),
    UNIQUE(scenario_id, year)
);

CREATE TABLE scenario_metrics (
    id SERIAL PRIMARY KEY,
    scenario_id INTEGER REFERENCES scenarios(id) ON DELETE CASCADE,
    total_capex DECIMAL(18,2),
    total_opex DECIMAL(18,2),
    total_revenue DECIMAL(18,2),
    total_contractor_aftertax DECIMAL(18,2),
    total_government_take DECIMAL(18,2),
    total_tax_paid DECIMAL(18,2),
    npv DECIMAL(18,2),
    irr DECIMAL(8,4),
    payback_period DECIMAL(6,2),
    asr_amount DECIMAL(18,2),
    calculated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(scenario_id)
);

-- ====================================
-- COMPARISON & RANKING
-- ====================================

CREATE TABLE scenario_comparisons (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    created_by VARCHAR(100),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE comparison_scenarios (
    id SERIAL PRIMARY KEY,
    comparison_id INTEGER REFERENCES scenario_comparisons(id) ON DELETE CASCADE,
    scenario_id INTEGER REFERENCES scenarios(id),
    rank INTEGER,
    rank_reason TEXT,
    UNIQUE(comparison_id, scenario_id)
);

-- ====================================
-- AUDIT TRAIL
-- ====================================

CREATE TABLE audit_log (
    id SERIAL PRIMARY KEY,
    table_name VARCHAR(100),
    record_id INTEGER,
    action VARCHAR(20),
    changed_by VARCHAR(100),
    changed_at TIMESTAMP DEFAULT NOW(),
    old_values JSONB,
    new_values JSONB
);

-- ====================================
-- INDEXES for Performance
-- ====================================

CREATE INDEX idx_capex_items_category ON capex_items(category_id);
CREATE INDEX idx_capex_items_active ON capex_items(is_active) WHERE is_active = TRUE;
CREATE INDEX idx_scenario_capex_scenario ON scenario_capex(scenario_id);
CREATE INDEX idx_scenario_opex_scenario ON scenario_opex(scenario_id);
CREATE INDEX idx_calculation_results_scenario ON calculation_results(scenario_id);
CREATE INDEX idx_production_data_profile ON production_data(profile_id);
CREATE INDEX idx_scenarios_active ON scenarios(is_active) WHERE is_active = TRUE;
```

## Hardcoded Data - Complete INSERT

```sql
-- ====================================
-- INSERT CAPEX CATEGORIES
-- ====================================

INSERT INTO capex_categories (code, name, description, sort_order) VALUES
('PROD', 'Production', 'Production facilities and equipment', 1),
('POWER', 'Power', 'Power generation systems', 2),
('TRANS', 'Transportation', 'Transportation infrastructure', 3),
('FLARE', 'Flaring', 'Flare gas recovery systems', 4);

-- ====================================
-- INSERT CAPEX SUBCATEGORIES
-- ====================================

INSERT INTO capex_subcategories (category_id, code, name, description, sort_order) VALUES
((SELECT id FROM capex_categories WHERE code = 'PROD'), 'CCUS', 'CCUS Systems', 'Carbon Capture, Utilization and Storage', 1),
((SELECT id FROM capex_categories WHERE code = 'PROD'), 'SEP', 'Separators', 'Separation equipment', 2),
((SELECT id FROM capex_categories WHERE code = 'TRANS'), 'PIPE', 'Pipeline', 'Pipeline infrastructure', 1),
((SELECT id FROM capex_categories WHERE code = 'TRANS'), 'SHIP', 'Shipping', 'Shipping equipment', 2);

-- ====================================
-- INSERT CAPEX ITEMS
-- ====================================

INSERT INTO capex_items (category_id, subcategory_id, code, name, unit, unit_cost, description, is_active) VALUES
-- Production - CCUS
((SELECT id FROM capex_categories WHERE code = 'PROD'), 
 (SELECT id FROM capex_subcategories WHERE code = 'CCUS'), 
 'CCUS_EGR', 'CCUS + CO2 EGR', '/unit.well', 20410366.50, 'Enhanced Gas Recovery with CCUS', TRUE),

((SELECT id FROM capex_categories WHERE code = 'PROD'), 
 (SELECT id FROM capex_subcategories WHERE code = 'CCUS'), 
 'CCUS_EOR', 'CCUS + CO2 EOR', '/unit.well', 16510366.50, 'Enhanced Oil Recovery with CCUS', TRUE),

-- Production - Separator
((SELECT id FROM capex_categories WHERE code = 'PROD'), 
 (SELECT id FROM capex_subcategories WHERE code = 'SEP'), 
 'SUPERSONIC', 'Supersonic Separator', '/unit', 3000000.00, 'Supersonic gas separator', TRUE),

-- Power
((SELECT id FROM capex_categories WHERE code = 'POWER'), 
 NULL, 
 'CCPP', 'Combined Cycle Power Plant (CCPP)', '/kW', 1131.00, 'Assume 100000 KW', TRUE),

((SELECT id FROM capex_categories WHERE code = 'POWER'), 
 NULL, 
 'FWT', 'Floating Wind Turbine (FWT)', '/kW', 5317.00, 'Offshore wind turbine', TRUE),

-- Transportation - Pipeline
((SELECT id FROM capex_categories WHERE code = 'TRANS'), 
 (SELECT id FROM capex_subcategories WHERE code = 'PIPE'), 
 'PIPELINE_CO2', 'Pipeline (CO2/Utility)', '/kM', 3000000.00, 'CO2 and utility pipeline', TRUE),

-- Transportation - Shipping
((SELECT id FROM capex_categories WHERE code = 'TRANS'), 
 (SELECT id FROM capex_subcategories WHERE code = 'SHIP'), 
 'STS', 'Stern Tube System (STS)', '/vessel', 2000000.00, 'Stern tube system for vessels', TRUE),

((SELECT id FROM capex_categories WHERE code = 'TRANS'), 
 (SELECT id FROM capex_subcategories WHERE code = 'SHIP'), 
 'OWS', 'Oil Water Separator (OWS)', '/ Process separation unit', 25000.00, 'Oil water separation unit', TRUE),

((SELECT id FROM capex_categories WHERE code = 'TRANS'), 
 (SELECT id FROM capex_subcategories WHERE code = 'SHIP'), 
 'VLGC', 'Very Large Gas Carriers (VLGC)', '/ unit', 110000000.00, 'Very large gas carrier ship', TRUE),

-- Flaring
((SELECT id FROM capex_categories WHERE code = 'FLARE'), 
 NULL, 
 'FGRS', 'Flare Gas Recovery System (FGRS)', '/flare gas recovery skid', 3000000.00, 'Flare gas recovery system', TRUE);

-- ====================================
-- INSERT OPEX MAPPING
-- ====================================

INSERT INTO opex_mapping (capex_item_id, opex_name, opex_calculation_method, opex_rate, opex_unit, year_start, year_end, notes) VALUES
((SELECT id FROM capex_items WHERE code = 'CCUS_EGR'), 'CCUS EGR Annual Maintenance', 'PERCENTAGE', 0.02, 'per year', 1, NULL, '2% of CAPEX annually'),
((SELECT id FROM capex_items WHERE code = 'CCUS_EGR'), 'CCUS EGR Operations', 'FIXED', 500000.00, 'USD/year', 1, NULL, 'Fixed operations cost'),
((SELECT id FROM capex_items WHERE code = 'CCUS_EOR'), 'CCUS EOR Annual Maintenance', 'PERCENTAGE', 0.02, 'per year', 1, NULL, '2% of CAPEX annually'),
((SELECT id FROM capex_items WHERE code = 'CCUS_EOR'), 'CCUS EOR Operations', 'FIXED', 450000.00, 'USD/year', 1, NULL, 'Fixed operations cost'),
((SELECT id FROM capex_items WHERE code = 'SUPERSONIC'), 'Supersonic Separator Maintenance', 'PERCENTAGE', 0.03, 'per year', 1, NULL, '3% of CAPEX annually'),
((SELECT id FROM capex_items WHERE code = 'CCPP'), 'CCPP Operations & Maintenance', 'PERCENTAGE', 0.025, 'per year', 1, NULL, '2.5% of CAPEX annually'),
((SELECT id FROM capex_items WHERE code = 'FWT'), 'FWT Operations & Maintenance', 'PERCENTAGE', 0.03, 'per year', 1, NULL, '3% of CAPEX annually'),
((SELECT id FROM capex_items WHERE code = 'PIPELINE_CO2'), 'Pipeline Maintenance', 'PERCENTAGE', 0.015, 'per year', 1, NULL, '1.5% of CAPEX annually'),
((SELECT id FROM capex_items WHERE code = 'STS'), 'STS Maintenance', 'PERCENTAGE', 0.02, 'per year', 1, NULL, '2% of CAPEX annually'),
((SELECT id FROM capex_items WHERE code = 'OWS'), 'OWS Operations', 'PERCENTAGE', 0.04, 'per year', 1, NULL, '4% of CAPEX annually'),
((SELECT id FROM capex_items WHERE code = 'VLGC'), 'VLGC Operations', 'PERCENTAGE', 0.05, 'per year', 1, NULL, '5% of CAPEX annually'),
((SELECT id FROM capex_items WHERE code = 'VLGC'), 'VLGC Crew & Insurance', 'FIXED', 2000000.00, 'USD/year', 1, NULL, 'Fixed annual cost'),
((SELECT id FROM capex_items WHERE code = 'FGRS'), 'FGRS Operations', 'PERCENTAGE', 0.025, 'per year', 1, NULL, '2.5% of CAPEX annually');

-- ====================================
-- INSERT FISCAL TERMS
-- ====================================

INSERT INTO fiscal_terms (
    name, version,
    gov_oil_pretax, gov_gas_pretax,
    contractor_oil_pretax, contractor_gas_pretax,
    gov_oil_posttax, gov_gas_posttax,
    contractor_oil_posttax, contractor_gas_posttax,
    contractor_tax_rate,
    dmo_volume, dmo_fee, dmo_holiday,
    discount_rate,
    depreciation_life, depreciation_method, depreciation_factor,
    asr_rate, salvage_value,
    is_active
) VALUES (
    'Default PSC Terms', 'v1.0',
    0.3277, 0.3277,
    0.6723, 0.6723,
    0.60, 0.60,
    0.40, 0.40,
    0.405,
    0.25, 1.00, 0,
    0.13,
    5, 'DDB', 0.25,
    0.05, 0,
    TRUE
);

-- ====================================
-- INSERT PRICING ASSUMPTIONS
-- ====================================

INSERT INTO pricing_assumptions (
    name, version,
    oil_price, gas_price,
    usd_to_idr,
    gross_heating_value, mmscf_to_mmbtu,
    co2_production_rate, carbon_tax,
    emission_factor, ghv_condensate,
    barrel_to_liter,
    working_days,
    is_active
) VALUES (
    'Base Case Pricing', 'v1.0',
    60.00, 5.50,
    16500,
    1200, 1027,
    0.20, 2.00,
    53.06, 5.8,
    158.987,
    220,
    TRUE
);

-- ====================================
-- INSERT PRODUCTION ENHANCEMENT
-- ====================================

INSERT INTO production_enhancement (name, eor_rate, egr_rate, is_active) VALUES
('Standard CCUS Enhancement', 0.20, 0.25, TRUE),
('No Enhancement', 0.00, 0.00, TRUE),
('Aggressive Enhancement', 0.30, 0.35, TRUE);

-- ====================================
-- INSERT PRODUCTION PROFILE
-- ====================================

INSERT INTO production_profiles (name, description, project_start_year, project_duration) VALUES
('Base Production Profile', 'Default production profile from existing data', 2026, 12);

-- ====================================
-- INSERT PRODUCTION DATA
-- ====================================

INSERT INTO production_data (profile_id, year, condensate_rate_bopd, gas_rate_mmscfd) VALUES
((SELECT id FROM production_profiles WHERE name = 'Base Production Profile'), 2026, 1257.49, 0.36781),
((SELECT id FROM production_profiles WHERE name = 'Base Production Profile'), 2027, 2394.10, 0.71769),
((SELECT id FROM production_profiles WHERE name = 'Base Production Profile'), 2028, 2199.95, 1.49133),
((SELECT id FROM production_profiles WHERE name = 'Base Production Profile'), 2029, 2063.88, 1.73993),
((SELECT id FROM production_profiles WHERE name = 'Base Production Profile'), 2030, 1949.47, 2.21602),
((SELECT id FROM production_profiles WHERE name = 'Base Production Profile'), 2031, 2052.16, 2.28278),
((SELECT id FROM production_profiles WHERE name = 'Base Production Profile'), 2032, 1622.27, 1.47658),
((SELECT id FROM production_profiles WHERE name = 'Base Production Profile'), 2033, 1636.66, 1.67256),
((SELECT id FROM production_profiles WHERE name = 'Base Production Profile'), 2034, 1142.45, 1.56182),
((SELECT id FROM production_profiles WHERE name = 'Base Production Profile'), 2035, 1258.40, 1.07175),
((SELECT id FROM production_profiles WHERE name = 'Base Production Profile'), 2036, 1158.71, 0.85615),
((SELECT id FROM production_profiles WHERE name = 'Base Production Profile'), 2037, 888.79, 0.76917);
```

## Python Database Module

```python
# database.py
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import List, Dict, Optional, Any
import os

class Database:
    def __init__(self):
        self.conn = None
        self.connect()
    
    def connect(self):
        """Connect to PostgreSQL database"""
        try:
            self.conn = psycopg2.connect(
                host=os.getenv('DB_HOST', 'localhost'),
                database=os.getenv('DB_NAME', 'financial_scenarios'),
                user=os.getenv('DB_USER', 'postgres'),
                password=os.getenv('DB_PASSWORD', 'password'),
                port=os.getenv('DB_PORT', '5432')
            )
        except Exception as e:
            raise Exception(f"Database connection failed: {e}")
    
    def execute(self, query: str, params: tuple = None) -> None:
        """Execute a query without returning results"""
        cursor = self.conn.cursor()
        try:
            cursor.execute(query, params)
            self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            raise Exception(f"Query execution failed: {e}")
        finally:
            cursor.close()
    
    def fetch_one(self, query: str, params: tuple = None) -> Optional[Dict]:
        """Fetch single row as dictionary"""
        cursor = self.conn.cursor(cursor_factory=RealDictCursor)
        try:
            cursor.execute(query, params)
            result = cursor.fetchone()
            return dict(result) if result else None
        finally:
            cursor.close()
    
    def fetch_all(self, query: str, params: tuple = None) -> List[Dict]:
        """Fetch all rows as list of dictionaries"""
        cursor = self.conn.cursor(cursor_factory=RealDictCursor)
        try:
            cursor.execute(query, params)
            results = cursor.fetchall()
            return [dict(row) for row in results]
        finally:
            cursor.close()
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()

class ScenarioManager:
    def __init__(self, db: Database):
        self.db = db
    
    def create_scenario(
        self, 
        name: str, 
        description: str,
        production_profile_id: int,
        fiscal_terms_id: int,
        pricing_id: int,
        enhancement_id: int,
        project_duration: int = 12,
        created_by: str = 'system'
    ) -> int:
        """Create new scenario"""
        query = """
            INSERT INTO scenarios (
                name, description, 
                production_profile_id, fiscal_terms_id, 
                pricing_id, enhancement_id,
                project_duration, created_by
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """
        cursor = self.db.conn.cursor()
        try:
            cursor.execute(query, (
                name, description,
                production_profile_id, fiscal_terms_id,
                pricing_id, enhancement_id,
                project_duration, created_by
            ))
            self.db.conn.commit()
            scenario_id = cursor.fetchone()[0]
            return scenario_id
        except Exception as e:
            self.db.conn.rollback()
            raise Exception(f"Failed to create scenario: {e}")
        finally:
            cursor.close()
    
    def duplicate_scenario(self, source_scenario_id: int, new_name: str) -> int:
        """Duplicate existing scenario with all its CAPEX selections"""
        # Get source scenario
        source = self.db.fetch_one(
            "SELECT * FROM scenarios WHERE id = %s",
            (source_scenario_id,)
        )
        
        if not source:
            raise Exception(f"Source scenario {source_scenario_id} not found")
        
        # Create new scenario
        new_scenario_id = self.create_scenario(
            name=new_name,
            description=f"Duplicated from: {source['name']}",
            production_profile_id=source['production_profile_id'],
            fiscal_terms_id=source['fiscal_terms_id'],
            pricing_id=source['pricing_id'],
            enhancement_id=source['enhancement_id'],
            project_duration=source['project_duration'],
            created_by=source['created_by']
        )
        
        # Copy CAPEX items
        capex_items = self.db.fetch_all(
            "SELECT * FROM scenario_capex WHERE scenario_id = %s",
            (source_scenario_id,)
        )
        
        for item in capex_items:
            self.db.execute(
                """
                INSERT INTO scenario_capex (
                    scenario_id, capex_item_id, quantity, 
                    multiplier, total_cost, year_incurred, notes
                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    new_scenario_id, item['capex_item_id'], 
                    item['quantity'], item['multiplier'],
                    item['total_cost'], item['year_incurred'], 
                    item['notes']
                )
            )
        
        # Copy OPEX items
        opex_items = self.db.fetch_all(
            "SELECT * FROM scenario_opex WHERE scenario_id = %s",
            (source_scenario_id,)
        )
        
        for item in opex_items:
            self.db.execute(
                """
                INSERT INTO scenario_opex (
                    scenario_id, year, opex_name, 
                    opex_amount, calculation_note
                ) VALUES (%s, %s, %s, %s, %s)
                """,
                (
                    new_scenario_id, item['year'], item['opex_name'],
                    item['opex_amount'], item['calculation_note']
                )
            )
        
        return new_scenario_id
    
    def delete_scenario(self, scenario_id: int) -> bool:
        """Delete scenario and all related data (CASCADE)"""
        try:
            self.db.execute(
                "DELETE FROM scenarios WHERE id = %s",
                (scenario_id,)
            )
            return True
        except Exception as e:
            raise Exception(f"Failed to delete scenario: {e}")
    
    def get_all_scenarios(self) -> List[Dict]:
        """Get all scenarios"""
        return self.db.fetch_all(
            """
            SELECT 
                s.*,
                pp.name as production_profile_name,
                ft.name as fiscal_terms_name,
                pa.name as pricing_name,
                pe.name as enhancement_name
            FROM scenarios s
            LEFT JOIN production_profiles pp ON pp.id = s.production_profile_id
            LEFT JOIN fiscal_terms ft ON ft.id = s.fiscal_terms_id
            LEFT JOIN pricing_assumptions pa ON pa.id = s.pricing_id
            LEFT JOIN production_enhancement pe ON pe.id = s.enhancement_id
            WHERE s.is_active = TRUE
            ORDER BY s.created_at DESC
            """
        )
    
    def get_scenario(self, scenario_id: int) -> Optional[Dict]:
        """Get single scenario"""
        return self.db.fetch_one(
            """
            SELECT 
                s.*,
                pp.name as production_profile_name,
                ft.name as fiscal_terms_name,
                pa.name as pricing_name,
                pe.name as enhancement_name
            FROM scenarios s
            LEFT JOIN production_profiles pp ON pp.id = s.production_profile_id
            LEFT JOIN fiscal_terms ft ON ft.id = s.fiscal_terms_id
            LEFT JOIN pricing_assumptions pa ON pa.id = s.pricing_id
            LEFT JOIN production_enhancement pe ON pe.id = s.enhancement_id
            WHERE s.id = %s
            """,
            (scenario_id,)
        )
    
    def add_capex_to_scenario(
        self, 
        scenario_id: int, 
        capex_item_id: int,
        quantity: float = 1.0,
        multiplier: float = 1.0,
        year_incurred: int = 2026,
        notes: str = ''
    ) -> None:
        """Add CAPEX item to scenario"""
        # Get unit cost
        capex_item = self.db.fetch_one(
            "SELECT unit_cost FROM capex_items WHERE id = %s",
            (capex_item_id,)
        )
        
        total_cost = float(capex_item['unit_cost']) * quantity * multiplier
        
        self.db.execute(
            """
            INSERT INTO scenario_capex (
                scenario_id, capex_item_id, quantity, 
                multiplier, total_cost, year_incurred, notes
            ) VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (scenario_id, capex_item_id) DO UPDATE
            SET quantity = EXCLUDED.quantity,
                multiplier = EXCLUDED.multiplier,
                total_cost = EXCLUDED.total_cost,
                year_incurred = EXCLUDED.year_incurred,
                notes = EXCLUDED.notes
            """,
            (scenario_id, capex_item_id, quantity, multiplier, 
             total_cost, year_incurred, notes)
        )
    
    def remove_capex_from_scenario(
        self, 
        scenario_id: int, 
        capex_item_id: int
    ) -> None:
        """Remove CAPEX item from scenario"""
        self.db.execute(
            """
            DELETE FROM scenario_capex 
            WHERE scenario_id = %s AND capex_item_id = %s
            """,
            (scenario_id, capex_item_id)
        )
    
    def get_scenario_capex(self, scenario_id: int) -> List[Dict]:
        """Get all CAPEX items for a scenario"""
        return self.db.fetch_all(
            """
            SELECT 
                sc.*,
                ci.code, ci.name, ci.unit, ci.unit_cost,
                cat.name as category_name
            FROM scenario_capex sc
            JOIN capex_items ci ON ci.id = sc.capex_item_id
            JOIN capex_categories cat ON cat.id = ci.category_id
            WHERE sc.scenario_id = %s
            ORDER BY cat.sort_order, ci.name
            """,
            (scenario_id,)
        )
```

## Python Calculation Engine - Complete

```python
# calculator.py
from decimal import Decimal
from typing import List, Dict, Tuple, Optional
import numpy_financial as npf
from dataclasses import dataclass
from database import Database

@dataclass
class FiscalTerms:
    gov_oil_pretax: Decimal = Decimal('0.3277')
    gov_gas_pretax: Decimal = Decimal('0.3277')
    contractor_oil_pretax: Decimal = Decimal('0.6723')
    contractor_gas_pretax: Decimal = Decimal('0.6723')
    contractor_tax_rate: Decimal = Decimal('0.405')
    discount_rate: Decimal = Decimal('0.13')
    depreciation_life: int = 5
    depreciation_factor: Decimal = Decimal('0.25')
    asr_rate: Decimal = Decimal('0.05')
    salvage_value: Decimal = Decimal('0')

@dataclass
class PricingAssumptions:
    oil_price: Decimal = Decimal('60.00')
    gas_price: Decimal = Decimal('5.50')
    mmscf_to_mmbtu: Decimal = Decimal('1027')
    working_days: int = 220

@dataclass
class ProductionEnhancement:
    eor_rate: Decimal = Decimal('0.20')
    egr_rate: Decimal = Decimal('0.25')

class FinancialCalculator:
    
    def __init__(self, db: Database):
        self.db = db
    
    def calculate_scenario(self, scenario_id: int) -> Tuple[List[Dict], Dict]:
        """Main calculation engine"""
        
        scenario = self.load_scenario(scenario_id)
        production_data = self.load_production_data(scenario['production_profile_id'])
        capex_items = self.load_scenario_capex(scenario_id)
        fiscal = self.load_fiscal_terms(scenario['fiscal_terms_id'])
        pricing = self.load_pricing(scenario['pricing_id'])
        enhancement = self.load_enhancement(scenario['enhancement_id'])
        
        self.generate_opex(scenario_id, capex_items, scenario)
        opex_data = self.load_scenario_opex(scenario_id)
        
        total_capex = sum(Decimal(str(item['total_cost'])) for item in capex_items)
        
        results = []
        cumulative_cf = Decimal('0')
        
        for idx, prod_year in enumerate(production_data):
            period = idx + 1
            year = prod_year['year']
            
            base_oil_bbl = Decimal(str(prod_year['condensate_rate_bopd'])) * Decimal(str(pricing.working_days))
            base_gas_mmscf = Decimal(str(prod_year['gas_rate_mmscfd'])) * Decimal(str(pricing.working_days))
            
            enhanced_oil_bbl = base_oil_bbl * (Decimal('1') + enhancement.eor_rate)
            enhanced_gas_mmscf = base_gas_mmscf * (Decimal('1') + enhancement.egr_rate)
            enhanced_gas_mmbtu = enhanced_gas_mmscf * pricing.mmscf_to_mmbtu
            
            oil_revenue = enhanced_oil_bbl * pricing.oil_price
            gas_revenue = enhanced_gas_mmbtu * pricing.gas_price
            total_revenue = oil_revenue + gas_revenue
            
            year_capex = self.get_capex_for_year(capex_items, year)
            year_opex = self.get_opex_for_year(opex_data, year)
            
            depreciation = self.calculate_depreciation_ddb(
                cost=total_capex,
                salvage=fiscal.salvage_value,
                life=fiscal.depreciation_life,
                period=period,
                factor=fiscal.depreciation_factor
            )
            
            operating_profit = total_revenue - depreciation
            
            contractor_pretax = operating_profit * fiscal.contractor_oil_pretax
            contractor_tax = contractor_pretax * fiscal.contractor_tax_rate
            contractor_aftertax = contractor_pretax - contractor_tax
            
            government_pretax = operating_profit * fiscal.gov_oil_pretax
            government_tax = contractor_tax
            government_total = government_pretax + government_tax
            
            net_cf = total_revenue - year_opex - year_capex
            cumulative_cf += net_cf
            
            year_result = {
                'scenario_id': scenario_id,
                'year': year,
                'oil_production_bbl': float(enhanced_oil_bbl),
                'gas_production_mmscf': float(enhanced_gas_mmscf),
                'gas_production_mmbtu': float(enhanced_gas_mmbtu),
                'oil_revenue': float(oil_revenue),
                'gas_revenue': float(gas_revenue),
                'total_revenue': float(total_revenue),
                'capex': float(year_capex),
                'opex': float(year_opex),
                'depreciation': float(depreciation),
                'operating_profit': float(operating_profit),
                'contractor_pretax': float(contractor_pretax),
                'contractor_tax': float(contractor_tax),
                'contractor_aftertax': float(contractor_aftertax),
                'government_pretax': float(government_pretax),
                'government_tax': float(government_tax),
                'government_total': float(government_total),
                'net_cash_flow': float(net_cf),
                'cumulative_cash_flow': float(cumulative_cf)
            }
            
            results.append(year_result)
        
        self.save_calculation_results(results)
        metrics = self.calculate_metrics(scenario_id, results, fiscal, total_capex)
        self.save_scenario_metrics(scenario_id, metrics)
        
        return results, metrics
    
    def calculate_depreciation_ddb(
        self, cost: Decimal, salvage: Decimal, life: int, period: int, factor: Decimal
    ) -> Decimal:
        """Declining Balance Depreciation"""
        if period > life or period < 1:
            return Decimal('0')
        
        rate = factor / Decimal(life)
        depreciation = Decimal('0')
        remaining_value = cost
        
        for p in range(1, period + 1):
            year_depreciation = remaining_value * rate
            
            periods_remaining = Decimal(life - p + 1)
            if periods_remaining > 0:
                straight_line = (remaining_value - salvage) / periods_remaining
            else:
                straight_line = Decimal('0')
            
            if straight_line > year_depreciation:
                year_depreciation = straight_line
            
            if p == period:
                depreciation = year_depreciation
            
            remaining_value -= year_depreciation
            
            if remaining_value < salvage:
                remaining_value = salvage
                break
        
        return depreciation
    
    def calculate_metrics(
        self, scenario_id: int, results: List[Dict], fiscal: FiscalTerms, total_capex: Decimal
    ) -> Dict:
        """Calculate NPV, IRR, Payback Period"""
        
        cash_flows = [float(r['net_cash_flow']) for r in results]
        
        try:
            npv = Decimal(str(npf.npv(float(fiscal.discount_rate), cash_flows)))
        except:
            npv = None
        
        try:
            irr = Decimal(str(npf.irr(cash_flows)))
        except:
            irr = None
        
        payback = self.calculate_payback_period(results)
        
        total_opex = sum(Decimal(str(r['opex'])) for r in results)
        total_revenue = sum(Decimal(str(r['total_revenue'])) for r in results)
        total_contractor_aftertax = sum(Decimal(str(r['contractor_aftertax'])) for r in results)
        total_government_take = sum(Decimal(str(r['government_total'])) for r in results)
        total_tax_paid = sum(Decimal(str(r['contractor_tax'])) for r in results)
        
        asr_amount = total_capex * fiscal.asr_rate
        
        return {
            'total_capex': float(total_capex),
            'total_opex': float(total_opex),
            'total_revenue': float(total_revenue),
            'total_contractor_aftertax': float(total_contractor_aftertax),
            'total_government_take': float(total_government_take),
            'total_tax_paid': float(total_tax_paid),
            'npv': float(npv) if npv else None,
            'irr': float(irr) if irr else None,
            'payback_period': float(payback) if payback else None,
            'asr_amount': float(asr_amount)
        }
    
    def calculate_payback_period(self, results: List[Dict]) -> Optional[Decimal]:
        """Calculate payback period"""
        for i, r in enumerate(results):
            if Decimal(str(r['cumulative_cash_flow'])) >= 0:
                if i == 0:
                    return Decimal('1')
                
                prev_cf = Decimal(str(results[i-1]['cumulative_cash_flow']))
                curr_cf = Decimal(str(r['cumulative_cash_flow']))
                
                if curr_cf == prev_cf:
                    return Decimal(i + 1)
                
                fraction = abs(prev_cf) / (curr_cf - prev_cf)
                return Decimal(i) + fraction
        
        return None
    
    def generate_opex(self, scenario_id: int, capex_items: List[Dict], scenario: Dict):
        """Auto-generate OPEX"""
        
        self.db.execute("DELETE FROM scenario_opex WHERE scenario_id = %s", (scenario_id,))
        
        project_duration = scenario['project_duration']
        project_start_year = self.get_project_start_year(scenario['production_profile_id'])
        
        for capex_item in capex_items:
            opex_mappings = self.db.fetch_all(
                "SELECT * FROM opex_mapping WHERE capex_item_id = %s",
                (capex_item['capex_item_id'],)
            )
            
            for opex_map in opex_mappings:
                year_start = opex_map['year_start'] if opex_map['year_start'] else 1
                year_end = opex_map['year_end'] if opex_map['year_end'] else project_duration
                
                for year_offset in range(year_start - 1, year_end):
                    year = project_start_year + year_offset
                    
                    if opex_map['opex_calculation_method'] == 'PERCENTAGE':
                        opex_amount = Decimal(str(capex_item['total_cost'])) * Decimal(str(opex_map['opex_rate']))
                    elif opex_map['opex_calculation_method'] == 'FIXED':
                        opex_amount = Decimal(str(opex_map['opex_rate']))
                    elif opex_map['opex_calculation_method'] == 'PER_UNIT':
                        opex_amount = Decimal(str(capex_item['quantity'])) * Decimal(str(opex_map['opex_rate']))
                    else:
                        opex_amount = Decimal('0')
                    
                    self.db.execute(
                        """
                        INSERT INTO scenario_opex 
                        (scenario_id, year, opex_name, opex_amount, calculation_note)
                        VALUES (%s, %s, %s, %s, %s)
                        """,
                        (scenario_id, year, opex_map['opex_name'], float(opex_amount),
                         f"{opex_map['opex_calculation_method']}: {opex_map['opex_rate']}")
                    )
    
    def get_capex_for_year(self, capex_items: List[Dict], year: int) -> Decimal:
        """Get total CAPEX for year"""
        total = Decimal('0')
        for item in capex_items:
            if item.get('year_incurred') == year:
                total += Decimal(str(item['total_cost']))
        return total
    
    def get_opex_for_year(self, opex_data: List[Dict], year: int) -> Decimal:
        """Get total OPEX for year"""
        total = Decimal('0')
        for opex in opex_data:
            if opex['year'] == year:
                total += Decimal(str(opex['opex_amount']))
        return total
    
    def load_scenario(self, scenario_id: int) -> Dict:
        return self.db.fetch_one("SELECT * FROM scenarios WHERE id = %s", (scenario_id,))
    
    def load_production_data(self, profile_id: int) -> List[Dict]:
        return self.db.fetch_all(
            "SELECT year, condensate_rate_bopd, gas_rate_mmscfd FROM production_data WHERE profile_id = %s ORDER BY year",
            (profile_id,)
        )
    
    def load_scenario_capex(self, scenario_id: int) -> List[Dict]:
        return self.db.fetch_all(
            "SELECT sc.*, ci.code, ci.name, ci.unit, ci.unit_cost FROM scenario_capex sc JOIN capex_items ci ON ci.id = sc.capex_item_id WHERE sc.scenario_id = %s",
            (scenario_id,)
        )
    
    def load_scenario_opex(self, scenario_id: int) -> List[Dict]:
        return self.db.fetch_all(
            "SELECT * FROM scenario_opex WHERE scenario_id = %s ORDER BY year",
            (scenario_id,)
        )
    
    def load_fiscal_terms(self, fiscal_id: int) -> FiscalTerms:
        data = self.db.fetch_one("SELECT * FROM fiscal_terms WHERE id = %s", (fiscal_id,))
        return FiscalTerms(
            gov_oil_pretax=Decimal(str(data['gov_oil_pretax'])),
            gov_gas_pretax=Decimal(str(data['gov_gas_pretax'])),
            contractor_oil_pretax=Decimal(str(data['contractor_oil_pretax'])),
            contractor_gas_pretax=Decimal(str(data['contractor_gas_pretax'])),
            contractor_tax_rate=Decimal(str(data['contractor_tax_rate'])),
            discount_rate=Decimal(str(data['discount_rate'])),
            depreciation_life=data['depreciation_life'],
            depreciation_factor=Decimal(str(data['depreciation_factor'])),
            asr_rate=Decimal(str(data['asr_rate'])),
            salvage_value=Decimal(str(data['salvage_value']))
        )
    
    def load_pricing(self, pricing_id: int) -> PricingAssumptions:
        data = self.db.fetch_one("SELECT * FROM pricing_assumptions WHERE id = %s", (pricing_id,))
        return PricingAssumptions(
            oil_price=Decimal(str(data['oil_price'])),
            gas_price=Decimal(str(data['gas_price'])),
            mmscf_to_mmbtu=Decimal(str(data['mmscf_to_mmbtu'])),
            working_days=data['working_days']
        )
    
    def load_enhancement(self, enhancement_id: int) -> ProductionEnhancement:
        data = self.db.fetch_one("SELECT * FROM production_enhancement WHERE id = %s", (enhancement_id,))
        return ProductionEnhancement(
            eor_rate=Decimal(str(data['eor_rate'])),
            egr_rate=Decimal(str(data['egr_rate']))
        )
    
    def get_project_start_year(self, profile_id: int) -> int:
        result = self.db.fetch_one(
            "SELECT project_start_year FROM production_profiles WHERE id = %s",
            (profile_id,)
        )
        return result['project_start_year']
    
    def save_calculation_results(self, results: List[Dict]):
        """Save results"""
        for result in results:
            self.db.execute(
                """
                INSERT INTO calculation_results (
                    scenario_id, year, oil_production_bbl, gas_production_mmscf, gas_production_mmbtu,
                    oil_revenue, gas_revenue, total_revenue, capex, opex, depreciation, operating_profit,
                    contractor_pretax, contractor_tax, contractor_aftertax,
                    government_pretax, government_tax, government_total,
                    net_cash_flow, cumulative_cash_flow
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (scenario_id, year) DO UPDATE SET
                    oil_production_bbl = EXCLUDED.oil_production_bbl,
                    gas_production_mmscf = EXCLUDED.gas_production_mmscf,
                    gas_production_mmbtu = EXCLUDED.gas_production_mmbtu,
                    oil_revenue = EXCLUDED.oil_revenue,
                    gas_revenue = EXCLUDED.gas_revenue,
                    total_revenue = EXCLUDED.total_revenue,
                    capex = EXCLUDED.capex,
                    opex = EXCLUDED.opex,
                    depreciation = EXCLUDED.depreciation,
                    operating_profit = EXCLUDED.operating_profit,
                    contractor_pretax = EXCLUDED.contractor_pretax,
                    contractor_tax = EXCLUDED.contractor_tax,
                    contractor_aftertax = EXCLUDED.contractor_aftertax,
                    government_pretax = EXCLUDED.government_pretax,
                    government_tax = EXCLUDED.government_tax,
                    government_total = EXCLUDED.government_total,
                    net_cash_flow = EXCLUDED.net_cash_flow,
                    cumulative_cash_flow = EXCLUDED.cumulative_cash_flow
                """,
                tuple(result.values())
            )
    
    def save_scenario_metrics(self, scenario_id: int, metrics: Dict):
        """Save metrics"""
        self.db.execute(
            """
            INSERT INTO scenario_metrics (
                scenario_id, total_capex, total_opex, total_revenue,
                total_contractor_aftertax, total_government_take, total_tax_paid,
                npv, irr, payback_period, asr_amount, calculated_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
            ON CONFLICT (scenario_id) DO UPDATE SET
                total_capex = EXCLUDED.total_capex,
                total_opex = EXCLUDED.total_opex,
                total_revenue = EXCLUDED.total_revenue,
                total_contractor_aftertax = EXCLUDED.total_contractor_aftertax,
                total_government_take = EXCLUDED.total_government_take,
                total_tax_paid = EXCLUDED.total_tax_paid,
                npv = EXCLUDED.npv,
                irr = EXCLUDED.irr,
                payback_period = EXCLUDED.payback_period,
                asr_amount = EXCLUDED.asr_amount,
                calculated_at = NOW()
            """,
            (scenario_id, metrics['total_capex'], metrics['total_opex'], metrics['total_revenue'],
             metrics['total_contractor_aftertax'], metrics['total_government_take'], metrics['total_tax_paid'],
             metrics['npv'], metrics['irr'], metrics['payback_period'], metrics['asr_amount'])
        )
```

## Streamlit App - Complete

```python
# app.py
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from database import Database, ScenarioManager
from calculator import FinancialCalculator
from io import BytesIO
import xlsxwriter

st.set_page_config(page_title="Financial Scenario Analyzer", layout="wide", initial_sidebar_state="expanded")

@st.cache_resource
def init_database():
    return Database()

@st.cache_resource
def init_managers(_db):
    return ScenarioManager(_db), FinancialCalculator(_db)

db = init_database()
scenario_mgr, calculator = init_managers(db)

st.sidebar.title("Navigation")
page = st.sidebar.radio("Menu", [
    "Dashboard",
    "Manage Scenarios",
    "Configure CAPEX",
    "Calculate Results",
    "Compare Scenarios",
    "Export Results"
])

if page == "Dashboard":
    st.title("Financial Scenario Analyzer - Dashboard")
    
    scenarios = scenario_mgr.get_all_scenarios()
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Scenarios", len(scenarios))
    
    calculated_scenarios = db.fetch_all(
        "SELECT COUNT(*) as count FROM scenario_metrics"
    )
    col2.metric("Calculated Scenarios", calculated_scenarios[0]['count'])
    
    if scenarios:
        st.subheader("All Scenarios")
        df_scenarios = pd.DataFrame(scenarios)
        st.dataframe(df_scenarios[['id', 'name', 'description', 'created_at']], use_container_width=True)

elif page == "Manage Scenarios":
    st.title("Manage Scenarios")
    
    tab1, tab2, tab3 = st.tabs(["Create New", "Duplicate", "Delete"])
    
    with tab1:
        st.subheader("Create New Scenario")
        
        col1, col2 = st.columns(2)
        
        with col1:
            scenario_name = st.text_input("Scenario Name", key="new_name")
            description = st.text_area("Description", key="new_desc")
            
            production_profiles = db.fetch_all("SELECT * FROM production_profiles WHERE 1=1")
            prod_profile = st.selectbox(
                "Production Profile",
                options=production_profiles,
                format_func=lambda x: x['name'],
                key="new_prod"
            )
        
        with col2:
            fiscal_terms = db.fetch_all("SELECT * FROM fiscal_terms WHERE is_active = TRUE")
            fiscal = st.selectbox(
                "Fiscal Terms",
                options=fiscal_terms,
                format_func=lambda x: x['name'],
                key="new_fiscal"
            )
            
            pricing = db.fetch_all("SELECT * FROM pricing_assumptions WHERE is_active = TRUE")
            price = st.selectbox(
                "Pricing Assumptions",
                options=pricing,
                format_func=lambda x: x['name'],
                key="new_price"
            )
            
            enhancements = db.fetch_all("SELECT * FROM production_enhancement WHERE is_active = TRUE")
            enhancement = st.selectbox(
                "Production Enhancement",
                options=enhancements,
                format_func=lambda x: f"{x['name']} (EOR: {float(x['eor_rate'])*100}%, EGR: {float(x['egr_rate'])*100}%)",
                key="new_enh"
            )
        
        if st.button("Create Scenario", type="primary"):
            if scenario_name:
                new_id = scenario_mgr.create_scenario(
                    name=scenario_name,
                    description=description,
                    production_profile_id=prod_profile['id'],
                    fiscal_terms_id=fiscal['id'],
                    pricing_id=price['id'],
                    enhancement_id=enhancement['id']
                )
                st.success(f"Scenario created successfully with ID: {new_id}")
                st.rerun()
            else:
                st.error("Please enter scenario name")
    
    with tab2:
        st.subheader("Duplicate Existing Scenario")
        
        scenarios = scenario_mgr.get_all_scenarios()
        
        if scenarios:
            source_scenario = st.selectbox(
                "Select Scenario to Duplicate",
                options=scenarios,
                format_func=lambda x: f"{x['name']} (ID: {x['id']})",
                key="dup_source"
            )
            
            new_name = st.text_input(
                "New Scenario Name",
                value=f"{source_scenario['name']} - Copy",
                key="dup_name"
            )
            
            if st.button("Duplicate Scenario", type="primary"):
                if new_name:
                    new_id = scenario_mgr.duplicate_scenario(
                        source_scenario_id=source_scenario['id'],
                        new_name=new_name
                    )
                    st.success(f"Scenario duplicated successfully with ID: {new_id}")
                    st.rerun()
                else:
                    st.error("Please enter new scenario name")
        else:
            st.info("No scenarios available to duplicate")
    
    with tab3:
        st.subheader("Delete Scenario")
        
        scenarios = scenario_mgr.get_all_scenarios()
        
        if scenarios:
            delete_scenario = st.selectbox(
                "Select Scenario to Delete",
                options=scenarios,
                format_func=lambda x: f"{x['name']} (ID: {x['id']})",
                key="del_scenario"
            )
            
            st.warning("This action cannot be undone. All related data will be permanently deleted.")
            
            confirm = st.checkbox("I understand and want to delete this scenario")
            
            if st.button("Delete Scenario", type="primary", disabled=not confirm):
                scenario_mgr.delete_scenario(delete_scenario['id'])
                st.success("Scenario deleted successfully")
                st.rerun()
        else:
            st.info("No scenarios available to delete")

elif page == "Configure CAPEX":
    st.title("Configure CAPEX Items")
    
    scenarios = scenario_mgr.get_all_scenarios()
    
    if not scenarios:
        st.warning("Please create a scenario first")
    else:
        selected_scenario = st.selectbox(
            "Select Scenario",
            options=scenarios,
            format_func=lambda x: x['name']
        )
        
        st.divider()
        
        categories = db.fetch_all("SELECT * FROM capex_categories ORDER BY sort_order")
        
        for category in categories:
            with st.expander(f"{category['name']}", expanded=True):
                items = db.fetch_all(
                    "SELECT * FROM capex_items WHERE category_id = %s AND is_active = TRUE",
                    (category['id'],)
                )
                
                existing_capex = scenario_mgr.get_scenario_capex(selected_scenario['id'])
                existing_ids = [c['capex_item_id'] for c in existing_capex]
                
                for item in items:
                    col1, col2, col3, col4, col5 = st.columns([3, 1, 1, 1, 1])
                    
                    is_selected = item['id'] in existing_ids
                    
                    with col1:
                        st.write(f"**{item['name']}**")
                        st.caption(f"${float(item['unit_cost']):,.2f} {item['unit']}")
                    
                    with col2:
                        qty = st.number_input(
                            "Qty",
                            min_value=0.0,
                            value=1.0 if is_selected else 0.0,
                            step=1.0,
                            key=f"qty_{item['id']}_{selected_scenario['id']}"
                        )
                    
                    with col3:
                        mult = st.number_input(
                            "Mult",
                            min_value=0.0,
                            value=1.0,
                            step=1.0,
                            key=f"mult_{item['id']}_{selected_scenario['id']}"
                        )
                    
                    with col4:
                        year = st.number_input(
                            "Year",
                            min_value=2026,
                            max_value=2037,
                            value=2026,
                            step=1,
                            key=f"year_{item['id']}_{selected_scenario['id']}"
                        )
                    
                    with col5:
                        if qty > 0:
                            if st.button("Add", key=f"add_{item['id']}_{selected_scenario['id']}"):
                                scenario_mgr.add_capex_to_scenario(
                                    scenario_id=selected_scenario['id'],
                                    capex_item_id=item['id'],
                                    quantity=qty,
                                    multiplier=mult,
                                    year_incurred=year
                                )
                                st.success("Added")
                                st.rerun()
                        elif is_selected:
                            if st.button("Remove", key=f"rem_{item['id']}_{selected_scenario['id']}"):
                                scenario_mgr.remove_capex_from_scenario(
                                    scenario_id=selected_scenario['id'],
                                    capex_item_id=item['id']
                                )
                                st.success("Removed")
                                st.rerun()
        
        st.divider()
        st.subheader("Selected CAPEX Items")
        current_capex = scenario_mgr.get_scenario_capex(selected_scenario['id'])
        
        if current_capex:
            df_capex = pd.DataFrame(current_capex)
            df_capex['Total Cost'] = df_capex['total_cost'].apply(lambda x: f"${float(x):,.2f}")
            st.dataframe(
                df_capex[['name', 'quantity', 'multiplier', 'Total Cost', 'year_incurred']],
                use_container_width=True
            )
            
            total = sum(float(c['total_cost']) for c in current_capex)
            st.metric("Total CAPEX", f"${total:,.2f}")
        else:
            st.info("No CAPEX items selected yet")

elif page == "Calculate Results":
    st.title("Calculate Financial Results")
    
    scenarios = scenario_mgr.get_all_scenarios()
    
    if not scenarios:
        st.warning("Please create a scenario first")
    else:
        selected_scenario = st.selectbox(
            "Select Scenario",
            options=scenarios,
            format_func=lambda x: x['name']
        )
        
        capex_count = db.fetch_one(
            "SELECT COUNT(*) as count FROM scenario_capex WHERE scenario_id = %s",
            (selected_scenario['id'],)
        )
        
        if capex_count['count'] == 0:
            st.warning("Please configure CAPEX items first")
        else:
            if st.button("Run Calculation", type="primary"):
                with st.spinner("Calculating financial metrics..."):
                    try:
                        results, metrics = calculator.calculate_scenario(selected_scenario['id'])
                        st.success("Calculation completed successfully")
                        
                        st.subheader("Financial Metrics")
                        col1, col2, col3, col4 = st.columns(4)
                        
                        col1.metric("NPV", f"${metrics['npv']:,.2f}" if metrics['npv'] else "N/A")
                        col2.metric("IRR", f"{metrics['irr']*100:.2f}%" if metrics['irr'] else "N/A")
                        col3.metric("Payback Period", f"{metrics['payback_period']:.2f} years" if metrics['payback_period'] else "N/A")
                        col4.metric("Total CAPEX", f"${metrics['total_capex']:,.2f}")
                        
                        st.divider()
                        
                        col1, col2 = st.columns(2)
                        col1.metric("Total Revenue", f"${metrics['total_revenue']:,.2f}")
                        col2.metric("Total OPEX", f"${metrics['total_opex']:,.2f}")
                        
                        col1.metric("Contractor Take (After Tax)", f"${metrics['total_contractor_aftertax']:,.2f}")
                        col2.metric("Government Take", f"${metrics['total_government_take']:,.2f}")
                        
                        st.subheader("Yearly Results")
                        df_results = pd.DataFrame(results)
                        st.dataframe(df_results, use_container_width=True)
                        
                        st.subheader("Charts")
                        
                        tab1, tab2, tab3 = st.tabs(["Revenue", "Cash Flow", "PSC Split"])
                        
                        with tab1:
                            fig = px.bar(
                                df_results,
                                x='year',
                                y=['oil_revenue', 'gas_revenue'],
                                title="Annual Revenue Breakdown",
                                labels={'value': 'Revenue (USD)', 'year': 'Year'},
                                barmode='stack'
                            )
                            st.plotly_chart(fig, use_container_width=True)
                        
                        with tab2:
                            fig = go.Figure()
                            fig.add_trace(go.Scatter(
                                x=df_results['year'],
                                y=df_results['net_cash_flow'],
                                mode='lines+markers',
                                name='Net Cash Flow',
                                line=dict(color='blue')
                            ))
                            fig.add_trace(go.Scatter(
                                x=df_results['year'],
                                y=df_results['cumulative_cash_flow'],
                                mode='lines+markers',
                                name='Cumulative Cash Flow',
                                line=dict(color='green')
                            ))
                            fig.update_layout(title="Cash Flow Analysis", xaxis_title="Year", yaxis_title="Cash Flow (USD)")
                            st.plotly_chart(fig, use_container_width=True)
                        
                        with tab3:
                            fig = px.bar(
                                df_results,
                                x='year',
                                y=['contractor_aftertax', 'government_total'],
                                title="PSC Split - Contractor vs Government",
                                labels={'value': 'Amount (USD)', 'year': 'Year'},
                                barmode='group'
                            )
                            st.plotly_chart(fig, use_container_width=True)
                        
                    except Exception as e:
                        st.error(f"Calculation failed: {str(e)}")
            
            existing_results = db.fetch_one(
                "SELECT * FROM scenario_metrics WHERE scenario_id = %s",
                (selected_scenario['id'],)
            )
            
            if existing_results:
                st.info(f"Last calculated: {existing_results['calculated_at']}")
                
                if st.button("View Previous Results"):
                    results = db.fetch_all(
                        "SELECT * FROM calculation_results WHERE scenario_id = %s ORDER BY year",
                        (selected_scenario['id'],)
                    )
                    
                    df_results = pd.DataFrame(results)
                    st.dataframe(df_results, use_container_width=True)

elif page == "Compare Scenarios":
    st.title("Compare Scenarios")
    
    calculated = db.fetch_all(
        """
        SELECT s.*, sm.npv, sm.irr, sm.payback_period
        FROM scenarios s
        JOIN scenario_metrics sm ON sm.scenario_id = s.id
        WHERE s.is_active = TRUE
        ORDER BY sm.npv DESC
        """
    )
    
    if len(calculated) < 2:
        st.warning("Please calculate at least 2 scenarios for comparison")
    else:
        selected_scenarios = st.multiselect(
            "Select Scenarios to Compare",
            options=calculated,
            format_func=lambda x: x['name'],
            default=calculated[:3] if len(calculated) >= 3 else calculated
        )
        
        if len(selected_scenarios) > 0:
            rank_by = st.selectbox("Rank By", ["NPV", "IRR", "Payback Period"])
            
            st.subheader("Comparison Table")
            
            comparison_data = []
            for scenario in selected_scenarios:
                metrics = db.fetch_one(
                    "SELECT * FROM scenario_metrics WHERE scenario_id = %s",
                    (scenario['id'],)
                )
                comparison_data.append({
                    'Scenario': scenario['name'],
                    'NPV': f"${float(metrics['npv']):,.2f}" if metrics['npv'] else "N/A",
                    'IRR': f"{float(metrics['irr'])*100:.2f}%" if metrics['irr'] else "N/A",
                    'Payback': f"{float(metrics['payback_period']):.2f} yrs" if metrics['payback_period'] else "N/A",
                    'Total CAPEX': f"${float(metrics['total_capex']):,.2f}",
                    'Total Revenue': f"${float(metrics['total_revenue']):,.2f}",
                    'Contractor Take': f"${float(metrics['total_contractor_aftertax']):,.2f}",
                    'Government Take': f"${float(metrics['total_government_take']):,.2f}"
                })
            
            df_comparison = pd.DataFrame(comparison_data)
            st.dataframe(df_comparison, use_container_width=True)
            
            st.subheader("Visual Comparison")
            
            metrics_data = []
            for scenario in selected_scenarios:
                metrics = db.fetch_one(
                    "SELECT * FROM scenario_metrics WHERE scenario_id = %s",
                    (scenario['id'],)
                )
                metrics_data.append({
                    'Scenario': scenario['name'],
                    'NPV': float(metrics['npv']) if metrics['npv'] else 0,
                    'Total Revenue': float(metrics['total_revenue']),
                    'Total CAPEX': float(metrics['total_capex']),
                    'Contractor Take': float(metrics['total_contractor_aftertax']),
                    'Government Take': float(metrics['total_government_take'])
                })
            
            df_metrics = pd.DataFrame(metrics_data)
            
            fig = px.bar(
                df_metrics,
                x='Scenario',
                y=['NPV'],
                title="NPV Comparison",
                barmode='group'
            )
            st.plotly_chart(fig, use_container_width=True)
            
            fig2 = px.bar(
                df_metrics,
                x='Scenario',
                y=['Contractor Take', 'Government Take'],
                title="Take Comparison",
                barmode='group'
            )
            st.plotly_chart(fig2, use_container_width=True)
            
            best_scenario = max(selected_scenarios, key=lambda x: float(x['npv']) if x['npv'] else -999999999)
            st.success(f"Best Scenario (by NPV): {best_scenario['name']} with NPV ${float(best_scenario['npv']):,.2f}")

elif page == "Export Results":
    st.title("Export Results")
    
    calculated = db.fetch_all(
        """
        SELECT s.* FROM scenarios s
        JOIN scenario_metrics sm ON sm.scenario_id = s.id
        WHERE s.is_active = TRUE
        """
    )
    
    if not calculated:
        st.warning("No calculated scenarios available")
    else:
        export_scenario = st.selectbox(
            "Select Scenario to Export",
            options=calculated,
            format_func=lambda x: x['name']
        )
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("Export to Excel", type="primary"):
                results = db.fetch_all(
                    "SELECT * FROM calculation_results WHERE scenario_id = %s ORDER BY year",
                    (export_scenario['id'],)
                )
                metrics = db.fetch_one(
                    "SELECT * FROM scenario_metrics WHERE scenario_id = %s",
                    (export_scenario['id'],)
                )
                
                output = BytesIO()
                workbook = xlsxwriter.Workbook(output, {'in_memory': True})
                
                worksheet1 = workbook.add_worksheet("Summary")
                worksheet1.write(0, 0, "Metric")
                worksheet1.write(0, 1, "Value")
                row = 1
                for key, value in metrics.items():
                    if key not in ['id', 'scenario_id', 'calculated_at']:
                        worksheet1.write(row, 0, key)
                        worksheet1.write(row, 1, str(value))
                        row += 1
                
                worksheet2 = workbook.add_worksheet("Yearly Results")
                df_results = pd.DataFrame(results)
                for col_num, col_name in enumerate(df_results.columns):
                    worksheet2.write(0, col_num, col_name)
                for row_num, row_data in enumerate(df_results.values):
                    for col_num, cell_value in enumerate(row_data):
                        worksheet2.write(row_num + 1, col_num, str(cell_value))
                
                workbook.close()
                output.seek(0)
                
                st.download_button(
                    label="Download Excel",
                    data=output,
                    file_name=f"{export_scenario['name']}_results.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

st.sidebar.divider()
st.sidebar.caption("Financial Scenario Analyzer v1.0")
```

## Requirements.txt

```
streamlit==1.29.0
psycopg2-binary==2.9.9
pandas==2.1.4
plotly==5.18.0
numpy-financial==1.0.0
xlsxwriter==3.1.9
python-dotenv==1.0.0
```

## .streamlit/secrets.toml

```toml
[database]
DB_HOST = "your-database-host.neon.tech"
DB_NAME = "financial_scenarios"
DB_USER = "your-username"
DB_PASSWORD = "your-password"
DB_PORT = "5432"
```

## Deployment Steps

1. Create GitHub repository dengan struktur:
```
financial-scenario-app/
├── app.py
├── database.py
├── calculator.py
├── requirements.txt
├── .streamlit/
│   └── secrets.toml
└── README.md
```

2. Create PostgreSQL database supabase ini ya kalo ridect connection postgresql://postgres:[YOUR-PASSWORD]@db.swkgxntzamifnmktyabo.supabase.co:5432/postgres 
passwordku Abyansyah123 atau kalau ngga bisa Abyansyah 123$ nanti tolong setupkan juga

3. Run semua SQL schema dan INSERT statements di database

4. Deploy ke Streamlit Community Cloud:
   - Connect GitHub repo
   - Set secrets dari .streamlit/secrets.toml
   - Deploy

Semua value sudah match antara SQL (0.3277, 0.6723, 0.405, 0.13, 0.25, 0.05, 60.00, 5.50, 1027, 0.20, 0.25, 220) dengan Python code. Fitur create, duplicate, delete scenario sudah lengkap.
