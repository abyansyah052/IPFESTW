saya lihat ada kesalahan di CAPEX dan OPEX. Saya revisi sekarang berdasarkan data yang kamu berikan.

## Hardcoded Data - REVISED COMPLETE INSERT

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
-- INSERT CAPEX ITEMS - CORRECTED
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

-- Power - CORRECTED
((SELECT id FROM capex_categories WHERE code = 'POWER'), 
 NULL, 
 'CCPP', 'Combined Cycle Power Plant (CCPP)', '/unit', 8400000.00, 'Combined Cycle Power Plant', TRUE),

((SELECT id FROM capex_categories WHERE code = 'POWER'), 
 NULL, 
 'FWT', 'Floating Wind Turbine (FWT)', '/unit', 15300000.00, 'Offshore wind turbine', TRUE),

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
-- INSERT OPEX MAPPING - CORRECTED BASED ON ACTUAL DATA
-- ====================================

-- CCUS EGR - OPEX sekitar $1,020,518.33 tahun pertama, kemudian naik sekitar 2% per tahun
-- Ini adalah 5% dari CAPEX ($20,410,366.50 * 0.05 = $1,020,518.33)
INSERT INTO opex_mapping (capex_item_id, opex_name, opex_calculation_method, opex_rate, opex_unit, year_start, year_end, notes) VALUES
((SELECT id FROM capex_items WHERE code = 'CCUS_EGR'), 
 'CCUS EGR Operations & Maintenance', 'PERCENTAGE', 0.05, 'per year', 1, NULL, '5% of CAPEX annually');

-- CCUS EOR - OPEX sekitar $825,518.33 tahun pertama, kemudian naik sekitar 2% per tahun
-- Ini adalah 5% dari CAPEX ($16,510,366.50 * 0.05 = $825,518.33)
INSERT INTO opex_mapping (capex_item_id, opex_name, opex_calculation_method, opex_rate, opex_unit, year_start, year_end, notes) VALUES
((SELECT id FROM capex_items WHERE code = 'CCUS_EOR'), 
 'CCUS EOR Operations & Maintenance', 'PERCENTAGE', 0.05, 'per year', 1, NULL, '5% of CAPEX annually');

-- Supersonic Separator - OPEX $150,000 flat per tahun
INSERT INTO opex_mapping (capex_item_id, opex_name, opex_calculation_method, opex_rate, opex_unit, year_start, year_end, notes) VALUES
((SELECT id FROM capex_items WHERE code = 'SUPERSONIC'), 
 'Supersonic Separator Maintenance', 'FIXED', 150000.00, 'USD/year', 1, NULL, 'Fixed annual maintenance cost');

-- CCPP - OPEX $420,000 tahun pertama, kemudian naik sedikit
-- Ini adalah 5% dari CAPEX ($8,400,000 * 0.05 = $420,000)
INSERT INTO opex_mapping (capex_item_id, opex_name, opex_calculation_method, opex_rate, opex_unit, year_start, year_end, notes) VALUES
((SELECT id FROM capex_items WHERE code = 'CCPP'), 
 'CCPP Operations & Maintenance', 'PERCENTAGE', 0.05, 'per year', 1, NULL, '5% of CAPEX annually');

-- FWT - OPEX $765,000 tahun pertama
-- Ini adalah 5% dari CAPEX ($15,300,000 * 0.05 = $765,000)
INSERT INTO opex_mapping (capex_item_id, opex_name, opex_calculation_method, opex_rate, opex_unit, year_start, year_end, notes) VALUES
((SELECT id FROM capex_items WHERE code = 'FWT'), 
 'FWT Operations & Maintenance', 'PERCENTAGE', 0.05, 'per year', 1, NULL, '5% of CAPEX annually');

-- Pipeline - OPEX $150,000 per tahun flat
-- Untuk 30km: CAPEX = $90,000,000 (30 * $3,000,000)
-- OPEX = $150,000 adalah sekitar 0.167% dari CAPEX total atau $5,000 per km
INSERT INTO opex_mapping (capex_item_id, opex_name, opex_calculation_method, opex_rate, opex_unit, year_start, year_end, notes) VALUES
((SELECT id FROM capex_items WHERE code = 'PIPELINE_CO2'), 
 'Pipeline Maintenance', 'FIXED', 150000.00, 'USD/year', 1, NULL, 'Fixed maintenance for 30km pipeline');

-- STS - OPEX $100,000 tahun pertama, kemudian naik sekitar 2% per tahun
-- Ini adalah 5% dari CAPEX ($2,000,000 * 0.05 = $100,000)
INSERT INTO opex_mapping (capex_item_id, opex_name, opex_calculation_method, opex_rate, opex_unit, year_start, year_end, notes) VALUES
((SELECT id FROM capex_items WHERE code = 'STS'), 
 'STS Maintenance', 'PERCENTAGE', 0.05, 'per year', 1, NULL, '5% of CAPEX annually');

-- OWS - OPEX $1,250 flat per tahun
INSERT INTO opex_mapping (capex_item_id, opex_name, opex_calculation_method, opex_rate, opex_unit, year_start, year_end, notes) VALUES
((SELECT id FROM capex_items WHERE code = 'OWS'), 
 'OWS Operations', 'FIXED', 1250.00, 'USD/year', 1, NULL, 'Fixed annual operations cost');

-- VLGC - OPEX $5,500,000 tahun pertama
-- Ini adalah 5% dari CAPEX ($110,000,000 * 0.05 = $5,500,000)
INSERT INTO opex_mapping (capex_item_id, opex_name, opex_calculation_method, opex_rate, opex_unit, year_start, year_end, notes) VALUES
((SELECT id FROM capex_items WHERE code = 'VLGC'), 
 'VLGC Operations', 'PERCENTAGE', 0.05, 'per year', 1, NULL, '5% of CAPEX annually');

-- FGRS - OPEX $150,000 flat per tahun
INSERT INTO opex_mapping (capex_item_id, opex_name, opex_calculation_method, opex_rate, opex_unit, year_start, year_end, notes) VALUES
((SELECT id FROM capex_items WHERE code = 'FGRS'), 
 'FGRS Operations', 'FIXED', 150000.00, 'USD/year', 1, NULL, 'Fixed annual operations cost');

-- ====================================
-- INSERT FISCAL TERMS - CORRECTED
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
-- INSERT PRICING ASSUMPTIONS - CORRECTED
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
    60.0, 5.5,
    16500,
    1200, 1027,
    0.20, 2.00,
    53.06, 5.8,
    158.987,
    220,
    TRUE
);

-- ====================================
-- INSERT PRODUCTION ENHANCEMENT - CORRECTED
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
-- INSERT PRODUCTION DATA - CORRECTED FROM IMAGES
-- ====================================

-- Data dari gambar menunjukkan Total Bbl dan MMSCF (bukan BOPD dan MMSCFD)
-- Jadi perlu dibagi dengan working days (220) untuk dapat rate per day

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

## Summary Perubahan CAPEX:

1. **CCPP**: $1,131.00 /kW → **$8,400,000.00 /unit** (CORRECTED)
2. **FWT**: $5,317.00 /kW → **$15,300,000.00 /unit** (CORRECTED)
3. Semua item lain sudah benar

## Summary Perubahan OPEX:

Mayoritas OPEX adalah **5% dari CAPEX** per tahun, kecuali:
- **Supersonic Separator**: $150,000 fixed
- **Pipeline**: $150,000 fixed (untuk 30km project)
- **OWS**: $1,250 fixed
- **FGRS**: $150,000 fixed

Total CAPEX jika semua dipilih: **$268,645,733.00** (sesuai dengan gambar)

Dengan formula OPEX 5% untuk items yang percentage-based dan fixed amount untuk yang lainnya, maka:
- CCUS EGR: $20,410,366.50 × 0.05 = **$1,020,518.33** ✓
- CCUS EOR: $16,510,366.50 × 0.05 = **$825,518.33** ✓
- CCPP: $8,400,000 × 0.05 = **$420,000** ✓
- FWT: $15,300,000 × 0.05 = **$765,000** ✓
- VLGC: $110,000,000 × 0.05 = **$5,500,000** ✓
- STS: $2,000,000 × 0.05 = **$100,000** ✓


[
tapi khusus fiscalterms ikuti update terbaru ini 
Ya ada! Saya menemukan ada **OPEX Escalation Rate 2% per tahun** yang belum saya masukkan.

Dari analisis OPEX di gambar:
- 2026: $9,082,286.65
- 2027: $9,263,932.38 (naik 2%)
- 2028: $9,449,211.03 (naik 2%)
- dst...

Ini yang perlu ditambahkan:

## Updated Fiscal Terms Table

```sql
ALTER TABLE fiscal_terms ADD COLUMN opex_escalation_rate DECIMAL(6,4) DEFAULT 0.02;

-- Update existing data
UPDATE fiscal_terms SET opex_escalation_rate = 0.02 WHERE name = 'Default PSC Terms';
```

## Updated INSERT for Fiscal Terms

```sql
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
    opex_escalation_rate,
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
    0.02,
    TRUE
);
```

## Updated Python Dataclass

```python
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
    opex_escalation_rate: Decimal = Decimal('0.02')  # NEW
```

## Updated Calculator - Generate OPEX Function

```python
def generate_opex(self, scenario_id: int, capex_items: List[Dict], scenario: Dict):
    """Auto-generate OPEX with 2% escalation per year"""
    
    self.db.execute("DELETE FROM scenario_opex WHERE scenario_id = %s", (scenario_id,))
    
    project_duration = scenario['project_duration']
    project_start_year = self.get_project_start_year(scenario['production_profile_id'])
    
    # Get fiscal terms for escalation rate
    fiscal = self.load_fiscal_terms(scenario['fiscal_terms_id'])
    
    for capex_item in capex_items:
        opex_mappings = self.db.fetch_all(
            "SELECT * FROM opex_mapping WHERE capex_item_id = %s",
            (capex_item['capex_item_id'],)
        )
        
        for opex_map in opex_mappings:
            year_start = opex_map['year_start'] if opex_map['year_start'] else 1
            year_end = opex_map['year_end'] if opex_map['year_end'] else project_duration
            
            # Base OPEX calculation
            if opex_map['opex_calculation_method'] == 'PERCENTAGE':
                base_opex_amount = Decimal(str(capex_item['total_cost'])) * Decimal(str(opex_map['opex_rate']))
            elif opex_map['opex_calculation_method'] == 'FIXED':
                base_opex_amount = Decimal(str(opex_map['opex_rate']))
            elif opex_map['opex_calculation_method'] == 'PER_UNIT':
                base_opex_amount = Decimal(str(capex_item['quantity'])) * Decimal(str(opex_map['opex_rate']))
            else:
                base_opex_amount = Decimal('0')
            
            for year_offset in range(year_start - 1, year_end):
                year = project_start_year + year_offset
                
                # Apply escalation: OPEX_year = OPEX_base * (1 + escalation_rate)^year_offset
                escalation_factor = (Decimal('1') + fiscal.opex_escalation_rate) ** year_offset
                opex_amount = base_opex_amount * escalation_factor
                
                self.db.execute(
                    """
                    INSERT INTO scenario_opex 
                    (scenario_id, year, opex_name, opex_amount, calculation_note)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (scenario_id, year, opex_map['opex_name'], float(opex_amount),
                     f"{opex_map['opex_calculation_method']}: {opex_map['opex_rate']} (escalated {year_offset} years at {float(fiscal.opex_escalation_rate)*100}%)")
                )
```

## Updated Load Fiscal Terms Function

```python
def load_fiscal_terms(self, fiscal_id: int) -> FiscalTerms:
    """Load fiscal terms"""
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
        salvage_value=Decimal(str(data['salvage_value'])),
        opex_escalation_rate=Decimal(str(data['opex_escalation_rate']))  # NEW
    )
```

Ini adalah perubahan yang diperlukan untuk match dengan data Excel kamu. OPEX sekarang akan otomatis naik 2% per tahun sesuai dengan data yang ada di screenshot.

**Summary semua parameter yang benar:**
- Pre-tax split: Gov 32.77%, Contractor 67.23% ✓
- Post-tax split: Gov 60%, Contractor 40% ✓
- Tax rate: 40.5% ✓
- Discount rate: 13% ✓
- Depreciation: 5 years, DDB, 25% factor ✓
- ASR: 5% ✓
- Oil price: $60/bbl ✓
- Gas price: $5.5/MMBTU ✓
- MMSCF to MMBTU: 1027 ✓
- Working days: 220 ✓
- EOR: 20% ✓
- EGR: 25% ✓
- **OPEX Escalation: 2% per year** ✓ (BARU DITAMBAHKAN)