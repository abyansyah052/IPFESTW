"""
Database Models for Financial Scenario Testing Application
"""
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, Text, 
    DateTime, ForeignKey, UniqueConstraint, Index, JSON
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

# ====================================
# MASTER DATA TABLES
# ====================================

class CapexCategory(Base):
    __tablename__ = 'capex_categories'
    
    id = Column(Integer, primary_key=True)
    code = Column(String(50), unique=True, nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    sort_order = Column(Integer)
    created_at = Column(DateTime, default=datetime.now)
    
    items = relationship("CapexItem", back_populates="category")
    subcategories = relationship("CapexSubcategory", back_populates="category")

class CapexSubcategory(Base):
    __tablename__ = 'capex_subcategories'
    
    id = Column(Integer, primary_key=True)
    category_id = Column(Integer, ForeignKey('capex_categories.id'))
    code = Column(String(50), unique=True, nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    sort_order = Column(Integer)
    
    category = relationship("CapexCategory", back_populates="subcategories")
    items = relationship("CapexItem", back_populates="subcategory")

class CapexItem(Base):
    __tablename__ = 'capex_items'
    
    id = Column(Integer, primary_key=True)
    category_id = Column(Integer, ForeignKey('capex_categories.id'))
    subcategory_id = Column(Integer, ForeignKey('capex_subcategories.id'), nullable=True)
    code = Column(String(50), unique=True, nullable=False)
    name = Column(String(200), nullable=False)
    unit = Column(String(100), nullable=False)
    unit_cost = Column(Float, nullable=False)
    description = Column(Text)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    category = relationship("CapexCategory", back_populates="items")
    subcategory = relationship("CapexSubcategory", back_populates="items")
    opex_mappings = relationship("OpexMapping", back_populates="capex_item")
    scenario_capex = relationship("ScenarioCapex", back_populates="capex_item")

class OpexMapping(Base):
    __tablename__ = 'opex_mapping'
    
    id = Column(Integer, primary_key=True)
    capex_item_id = Column(Integer, ForeignKey('capex_items.id'))
    opex_name = Column(String(200), nullable=False)
    opex_calculation_method = Column(String(50), nullable=False)  # PERCENTAGE, FIXED
    opex_rate = Column(Float, nullable=False)
    opex_unit = Column(String(100))
    year_start = Column(Integer)
    year_end = Column(Integer, nullable=True)
    notes = Column(Text)
    
    capex_item = relationship("CapexItem", back_populates="opex_mappings")

# ====================================
# FISCAL & PRICING PARAMETERS
# ====================================

class FiscalTerms(Base):
    __tablename__ = 'fiscal_terms'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    version = Column(String(50), default='v1.0')
    # Pre-tax splits
    gov_oil_pretax = Column(Float, nullable=False, default=0.3277)
    gov_gas_pretax = Column(Float, nullable=False, default=0.3277)
    contractor_oil_pretax = Column(Float, nullable=False, default=0.6723)
    contractor_gas_pretax = Column(Float, nullable=False, default=0.6723)
    # Post-tax splits
    gov_oil_posttax = Column(Float, nullable=False, default=0.60)
    gov_gas_posttax = Column(Float, nullable=False, default=0.60)
    contractor_oil_posttax = Column(Float, nullable=False, default=0.40)
    contractor_gas_posttax = Column(Float, nullable=False, default=0.40)
    # Tax
    contractor_tax_rate = Column(Float, nullable=False, default=0.405)
    # DMO
    dmo_volume = Column(Float, default=0.25)
    dmo_fee = Column(Float, default=1.00)
    dmo_holiday = Column(Integer, default=0)
    # Discount
    discount_rate = Column(Float, nullable=False, default=0.13)
    # Depreciation
    depreciation_life = Column(Integer, default=5)
    depreciation_method = Column(String(50), default='DDB')
    depreciation_factor = Column(Float, default=0.25)
    # Other
    asr_rate = Column(Float, default=0.05)
    salvage_value = Column(Float, default=0)
    opex_escalation_rate = Column(Float, default=0.02)  # 2% per year
    project_start_year = Column(Integer, default=2026)
    project_end_year = Column(Integer, default=2037)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)

class PricingAssumptions(Base):
    __tablename__ = 'pricing_assumptions'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    version = Column(String(50), default='v1.0')
    oil_price = Column(Float, nullable=False, default=60.0)
    gas_price = Column(Float, nullable=False, default=5.5)
    usd_to_idr = Column(Float, default=16500)
    gross_heating_value = Column(Float, default=1200)
    mmscf_to_mmbtu = Column(Float, default=1027)
    co2_production_rate = Column(Float, default=0.20)
    carbon_tax = Column(Float, default=2.00)
    emission_factor = Column(Float, default=53.06)
    ghv_condensate = Column(Float, default=5.8)
    barrel_to_liter = Column(Float, default=158.987)
    working_days = Column(Integer, default=220)
    currency = Column(String(10), default='USD')
    effective_date = Column(DateTime)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)

class ProductionEnhancement(Base):
    __tablename__ = 'production_enhancement'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    eor_enhancement_rate = Column(Float, default=0.20)  # 20%
    egr_enhancement_rate = Column(Float, default=0.25)  # 25%
    is_active = Column(Boolean, default=True)

# ====================================
# PRODUCTION DATA
# ====================================

class ProductionProfile(Base):
    __tablename__ = 'production_profiles'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    project_start_year = Column(Integer, default=2026)
    project_duration = Column(Integer, default=12)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)
    
    production_data = relationship("ProductionData", back_populates="profile")

class ProductionData(Base):
    __tablename__ = 'production_data'
    
    id = Column(Integer, primary_key=True)
    profile_id = Column(Integer, ForeignKey('production_profiles.id'))
    year = Column(Integer, nullable=False)
    condensate_rate_bopd = Column(Float, nullable=False)  # Barrels of oil per day
    gas_rate_mmscfd = Column(Float, nullable=False)  # Million standard cubic feet per day
    
    profile = relationship("ProductionProfile", back_populates="production_data")
    
    __table_args__ = (
        UniqueConstraint('profile_id', 'year', name='uq_profile_year'),
    )

# ====================================
# SCENARIO MANAGEMENT
# ====================================

class Scenario(Base):
    __tablename__ = 'scenarios'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    production_profile_id = Column(Integer, ForeignKey('production_profiles.id'))
    fiscal_terms_id = Column(Integer, ForeignKey('fiscal_terms.id'))
    pricing_assumptions_id = Column(Integer, ForeignKey('pricing_assumptions.id'))
    production_enhancement_id = Column(Integer, ForeignKey('production_enhancement.id'), nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    created_by = Column(String(200))
    is_active = Column(Boolean, default=True)
    
    scenario_capex = relationship("ScenarioCapex", back_populates="scenario")
    scenario_opex = relationship("ScenarioOpex", back_populates="scenario")
    calculation_results = relationship("CalculationResult", back_populates="scenario")
    metrics = relationship("ScenarioMetrics", back_populates="scenario", uselist=False)

class ScenarioCapex(Base):
    __tablename__ = 'scenario_capex'
    
    id = Column(Integer, primary_key=True)
    scenario_id = Column(Integer, ForeignKey('scenarios.id'))
    capex_item_id = Column(Integer, ForeignKey('capex_items.id'))
    quantity = Column(Float, nullable=False)
    unit_cost = Column(Float, nullable=False)
    total_cost = Column(Float, nullable=False)
    notes = Column(Text)
    
    scenario = relationship("Scenario", back_populates="scenario_capex")
    capex_item = relationship("CapexItem", back_populates="scenario_capex")
    
    __table_args__ = (
        UniqueConstraint('scenario_id', 'capex_item_id', name='uq_scenario_capex'),
    )

class ScenarioOpex(Base):
    __tablename__ = 'scenario_opex'
    
    id = Column(Integer, primary_key=True)
    scenario_id = Column(Integer, ForeignKey('scenarios.id'))
    year = Column(Integer, nullable=False)
    opex_name = Column(String(200), nullable=False)
    opex_amount = Column(Float, nullable=False)
    calculation_note = Column(Text)
    
    scenario = relationship("Scenario", back_populates="scenario_opex")

# ====================================
# CALCULATION RESULTS
# ====================================

class CalculationResult(Base):
    __tablename__ = 'calculation_results'
    
    id = Column(Integer, primary_key=True)
    scenario_id = Column(Integer, ForeignKey('scenarios.id'))
    year = Column(Integer, nullable=False)
    oil_production = Column(Float)
    gas_production_mmscf = Column(Float)
    gas_production_mmbtu = Column(Float)
    oil_revenue = Column(Float)
    gas_revenue = Column(Float)
    total_revenue = Column(Float)
    depreciation = Column(Float)
    opex_total = Column(Float)
    operating_profit = Column(Float)
    contractor_share_pretax = Column(Float)
    contractor_tax = Column(Float)
    contractor_share_aftertax = Column(Float)
    government_share_pretax = Column(Float)
    government_total_take = Column(Float)
    cash_flow = Column(Float)
    cumulative_cash_flow = Column(Float)
    
    scenario = relationship("Scenario", back_populates="calculation_results")
    
    __table_args__ = (
        UniqueConstraint('scenario_id', 'year', name='uq_scenario_year'),
    )

class ScenarioMetrics(Base):
    __tablename__ = 'scenario_metrics'
    
    id = Column(Integer, primary_key=True)
    scenario_id = Column(Integer, ForeignKey('scenarios.id'))
    total_capex = Column(Float)
    total_opex = Column(Float)
    total_revenue = Column(Float)
    total_contractor_share = Column(Float)
    total_government_take = Column(Float)
    npv = Column(Float)
    irr = Column(Float, nullable=True)
    payback_period_years = Column(Float, nullable=True)
    asr_amount = Column(Float)
    calculated_at = Column(DateTime, default=datetime.now)
    
    scenario = relationship("Scenario", back_populates="metrics")
    
    __table_args__ = (
        UniqueConstraint('scenario_id', name='uq_scenario_metrics'),
    )

# ====================================
# COMPARISON & RANKING
# ====================================

class ScenarioComparison(Base):
    __tablename__ = 'scenario_comparisons'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.now)
    
    comparison_scenarios = relationship("ComparisonScenario", back_populates="comparison")

class ComparisonScenario(Base):
    __tablename__ = 'comparison_scenarios'
    
    id = Column(Integer, primary_key=True)
    comparison_id = Column(Integer, ForeignKey('scenario_comparisons.id'))
    scenario_id = Column(Integer, ForeignKey('scenarios.id'))
    rank = Column(Integer)
    score = Column(Float)
    
    comparison = relationship("ScenarioComparison", back_populates="comparison_scenarios")
    
    __table_args__ = (
        UniqueConstraint('comparison_id', 'scenario_id', name='uq_comparison_scenario'),
    )

# ====================================
# AUDIT TRAIL
# ====================================

class AuditLog(Base):
    __tablename__ = 'audit_log'
    
    id = Column(Integer, primary_key=True)
    table_name = Column(String(100), nullable=False)
    record_id = Column(Integer, nullable=False)
    action = Column(String(50), nullable=False)  # INSERT, UPDATE, DELETE
    user_name = Column(String(200))
    timestamp = Column(DateTime, default=datetime.now)
    old_values = Column(JSON)
    new_values = Column(JSON)

# ====================================
# INDEXES
# ====================================
Index('idx_capex_items_category', CapexItem.category_id)
Index('idx_capex_items_active', CapexItem.is_active)
Index('idx_scenario_capex_scenario', ScenarioCapex.scenario_id)
Index('idx_scenario_opex_scenario', ScenarioOpex.scenario_id)
Index('idx_calculation_results_scenario', CalculationResult.scenario_id)
Index('idx_production_data_profile', ProductionData.profile_id)
Index('idx_scenarios_active', Scenario.is_active)
