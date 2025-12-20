"""
Database Initialization and Setup Script
"""
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from models import Base, CapexCategory, CapexSubcategory, CapexItem, OpexMapping
from models import FiscalTerms, PricingAssumptions, ProductionEnhancement, ProductionProfile, ProductionData
import os
from dotenv import load_dotenv

load_dotenv()

def get_database_url():
    """Get database URL from environment or use default"""
    return os.getenv('DATABASE_URL', 'postgresql://user:password@localhost:5432/scenario_calc')

def create_tables(engine):
    """Create all tables in the database"""
    Base.metadata.create_all(engine)
    print("✓ Database tables created successfully")

def insert_master_data(session):
    """Insert hardcoded master data - REPLACE existing data"""
    
    # DELETE existing data to ensure clean slate
    print("Cleaning existing data...")
    session.execute(text("DELETE FROM opex_mapping"))
    session.execute(text("DELETE FROM scenario_capex"))
    session.execute(text("DELETE FROM capex_items"))
    session.execute(text("DELETE FROM capex_subcategories"))
    session.execute(text("DELETE FROM capex_categories"))
    session.commit()
    print("✓ Existing CAPEX/OPEX data cleaned")
    
    # Insert CAPEX Categories
    categories = [
        CapexCategory(code='PROD', name='Production', description='Production facilities and equipment', sort_order=1),
        CapexCategory(code='POWER', name='Power', description='Power generation systems', sort_order=2),
        CapexCategory(code='TRANS', name='Transportation', description='Transportation infrastructure', sort_order=3),
        CapexCategory(code='FLARE', name='Flaring', description='Flare gas recovery systems', sort_order=4),
    ]
    session.add_all(categories)
    session.commit()
    print("✓ CAPEX Categories inserted")
    
    # Get category IDs
    prod_cat = session.query(CapexCategory).filter_by(code='PROD').first()
    power_cat = session.query(CapexCategory).filter_by(code='POWER').first()
    trans_cat = session.query(CapexCategory).filter_by(code='TRANS').first()
    flare_cat = session.query(CapexCategory).filter_by(code='FLARE').first()
    
    # Insert CAPEX Subcategories
    subcategories = [
        CapexSubcategory(category_id=prod_cat.id, code='CCUS', name='CCUS Systems', description='Carbon Capture, Utilization and Storage', sort_order=1),
        CapexSubcategory(category_id=prod_cat.id, code='SEP', name='Separators', description='Separation equipment', sort_order=2),
        CapexSubcategory(category_id=trans_cat.id, code='PIPE', name='Pipeline', description='Pipeline infrastructure', sort_order=1),
        CapexSubcategory(category_id=trans_cat.id, code='SHIP', name='Shipping', description='Shipping equipment', sort_order=2),
    ]
    session.add_all(subcategories)
    session.commit()
    print("✓ CAPEX Subcategories inserted")
    
    # Get subcategory IDs
    ccus_sub = session.query(CapexSubcategory).filter_by(code='CCUS').first()
    sep_sub = session.query(CapexSubcategory).filter_by(code='SEP').first()
    pipe_sub = session.query(CapexSubcategory).filter_by(code='PIPE').first()
    ship_sub = session.query(CapexSubcategory).filter_by(code='SHIP').first()
    
    # Insert CAPEX Items - REVISED
    items = [
        # Production - CCUS
        CapexItem(category_id=prod_cat.id, subcategory_id=ccus_sub.id, code='CCUS_EGR', 
                 name='CCUS + CO2 EGR', unit='/unit.well', unit_cost=20410366.50, 
                 description='Enhanced Gas Recovery with CCUS', is_active=True),
        CapexItem(category_id=prod_cat.id, subcategory_id=ccus_sub.id, code='CCUS_EOR', 
                 name='CCUS + CO2 EOR', unit='/unit.well', unit_cost=16510366.50, 
                 description='Enhanced Oil Recovery with CCUS', is_active=True),
        # Production - Separator
        CapexItem(category_id=prod_cat.id, subcategory_id=sep_sub.id, code='SUPERSONIC', 
                 name='Supersonic Separator', unit='/unit', unit_cost=3000000.00, 
                 description='Supersonic gas separator', is_active=True),
        # Power - REVISED: Changed from per-kW to per-unit (assume 10000 kW)
        CapexItem(category_id=power_cat.id, subcategory_id=None, code='CCPP', 
                 name='Combined Cycle Power Plant (CCPP)', unit='/unit', unit_cost=8400000.00, 
                 description='Combined Cycle Power Plant (assume 10000 kW)', is_active=True),
        CapexItem(category_id=power_cat.id, subcategory_id=None, code='FWT', 
                 name='Floating Wind Turbine (FWT)', unit='/unit', unit_cost=15300000.00, 
                 description='Floating Wind Turbine', is_active=True),
        # Transportation - Pipeline
        CapexItem(category_id=trans_cat.id, subcategory_id=pipe_sub.id, code='PIPELINE_CO2', 
                 name='Pipeline (CO2/Utility)', unit='/km', unit_cost=3000000.00, 
                 description='CO2 and utility pipeline (30km project)', is_active=True),
        # Transportation - Shipping
        CapexItem(category_id=trans_cat.id, subcategory_id=ship_sub.id, code='STS', 
                 name='Stern Tube System (STS)', unit='/vessel', unit_cost=2000000.00, 
                 description='Stern tube system for vessels', is_active=True),
        CapexItem(category_id=trans_cat.id, subcategory_id=ship_sub.id, code='OWS', 
                 name='Oil Water Separator (OWS)', unit='/unit', unit_cost=25000.00, 
                 description='Oil water separation unit', is_active=True),
        CapexItem(category_id=trans_cat.id, subcategory_id=ship_sub.id, code='VLGC', 
                 name='Very Large Gas Carriers (VLGC)', unit='/unit', unit_cost=110000000.00, 
                 description='Very large gas carrier ship', is_active=True),
        # Flaring
        CapexItem(category_id=flare_cat.id, subcategory_id=None, code='FGRS', 
                 name='Flare Gas Recovery System (FGRS)', unit='/unit', unit_cost=3000000.00, 
                 description='Flare gas recovery system', is_active=True),
    ]
    session.add_all(items)
    session.commit()
    print("✓ CAPEX Items inserted")
    
    # Get CAPEX items for OPEX mapping
    ccus_egr = session.query(CapexItem).filter_by(code='CCUS_EGR').first()
    ccus_eor = session.query(CapexItem).filter_by(code='CCUS_EOR').first()
    supersonic = session.query(CapexItem).filter_by(code='SUPERSONIC').first()
    ccpp = session.query(CapexItem).filter_by(code='CCPP').first()
    fwt = session.query(CapexItem).filter_by(code='FWT').first()
    pipeline = session.query(CapexItem).filter_by(code='PIPELINE_CO2').first()
    sts = session.query(CapexItem).filter_by(code='STS').first()
    ows = session.query(CapexItem).filter_by(code='OWS').first()
    vlgc = session.query(CapexItem).filter_by(code='VLGC').first()
    fgrs = session.query(CapexItem).filter_by(code='FGRS').first()
    
    # Insert OPEX Mapping - REVISED: Most are 5% of CAPEX, some fixed
    opex_mappings = [
        # CCUS EGR - 5% of CAPEX annually
        OpexMapping(capex_item_id=ccus_egr.id, opex_name='CCUS EGR Operations & Maintenance', 
                   opex_calculation_method='PERCENTAGE', opex_rate=0.05, opex_unit='per year', 
                   year_start=1, notes='5% of CAPEX annually'),
        # CCUS EOR - 5% of CAPEX annually
        OpexMapping(capex_item_id=ccus_eor.id, opex_name='CCUS EOR Operations & Maintenance', 
                   opex_calculation_method='PERCENTAGE', opex_rate=0.05, opex_unit='per year', 
                   year_start=1, notes='5% of CAPEX annually'),
        # Supersonic Separator - Fixed $150,000/year
        OpexMapping(capex_item_id=supersonic.id, opex_name='Supersonic Separator Maintenance', 
                   opex_calculation_method='FIXED', opex_rate=150000.00, opex_unit='USD/year', 
                   year_start=1, notes='Fixed annual maintenance cost'),
        # CCPP - 5% of CAPEX annually
        OpexMapping(capex_item_id=ccpp.id, opex_name='CCPP Operations & Maintenance', 
                   opex_calculation_method='PERCENTAGE', opex_rate=0.05, opex_unit='per year', 
                   year_start=1, notes='5% of CAPEX annually'),
        # FWT - 5% of CAPEX annually
        OpexMapping(capex_item_id=fwt.id, opex_name='FWT Operations & Maintenance', 
                   opex_calculation_method='PERCENTAGE', opex_rate=0.05, opex_unit='per year', 
                   year_start=1, notes='5% of CAPEX annually'),
        # Pipeline - Fixed $150,000/year for 30km project
        OpexMapping(capex_item_id=pipeline.id, opex_name='Pipeline Maintenance', 
                   opex_calculation_method='FIXED', opex_rate=150000.00, opex_unit='USD/year', 
                   year_start=1, notes='Fixed maintenance for 30km pipeline'),
        # STS - 5% of CAPEX annually
        OpexMapping(capex_item_id=sts.id, opex_name='STS Maintenance', 
                   opex_calculation_method='PERCENTAGE', opex_rate=0.05, opex_unit='per year', 
                   year_start=1, notes='5% of CAPEX annually'),
        # OWS - Fixed $1,250/year
        OpexMapping(capex_item_id=ows.id, opex_name='OWS Operations', 
                   opex_calculation_method='FIXED', opex_rate=1250.00, opex_unit='USD/year', 
                   year_start=1, notes='Fixed annual operations cost'),
        # VLGC - 5% of CAPEX annually
        OpexMapping(capex_item_id=vlgc.id, opex_name='VLGC Operations', 
                   opex_calculation_method='PERCENTAGE', opex_rate=0.05, opex_unit='per year', 
                   year_start=1, notes='5% of CAPEX annually'),
        # FGRS - Fixed $150,000/year
        OpexMapping(capex_item_id=fgrs.id, opex_name='FGRS Operations', 
                   opex_calculation_method='FIXED', opex_rate=150000.00, opex_unit='USD/year', 
                   year_start=1, notes='Fixed annual operations cost'),
    ]
    session.add_all(opex_mappings)
    session.commit()
    print("✓ OPEX Mappings inserted")
    
    # Insert Default Fiscal Terms - REVISED
    fiscal = FiscalTerms(
        name='Default PSC Terms',
        version='v1.0',
        gov_oil_pretax=0.3277,
        gov_gas_pretax=0.3277,
        contractor_oil_pretax=0.6723,
        contractor_gas_pretax=0.6723,
        gov_oil_posttax=0.60,
        gov_gas_posttax=0.60,
        contractor_oil_posttax=0.40,
        contractor_gas_posttax=0.40,
        contractor_tax_rate=0.405,
        dmo_volume=0.25,
        dmo_fee=1.00,
        dmo_holiday=0,
        discount_rate=0.13,
        depreciation_life=5,
        depreciation_method='DDB',
        depreciation_factor=0.25,
        asr_rate=0.05,
        salvage_value=0,
        opex_escalation_rate=0.02,  # 2% per year
        project_start_year=2026,
        project_end_year=2037,
        is_active=True
    )
    session.add(fiscal)
    session.commit()
    print("✓ Fiscal Terms inserted")
    
    # Insert Default Pricing Assumptions - REVISED
    pricing = PricingAssumptions(
        name='Base Case Pricing',
        version='v1.0',
        oil_price=60.0,
        gas_price=5.5,
        usd_to_idr=16500,
        gross_heating_value=1200,
        mmscf_to_mmbtu=1027,
        co2_production_rate=0.20,
        carbon_tax=2.00,
        emission_factor=53.06,
        ghv_condensate=5.8,
        barrel_to_liter=158.987,
        working_days=220,
        currency='USD',
        is_active=True
    )
    session.add(pricing)
    session.commit()
    print("✓ Pricing Assumptions inserted")
    
    # Insert Production Enhancement
    enhancement = ProductionEnhancement(
        name='Default Enhancement Rates',
        eor_enhancement_rate=0.20,
        egr_enhancement_rate=0.25,
        is_active=True
    )
    session.add(enhancement)
    session.commit()
    print("✓ Production Enhancement rates inserted")

def initialize_database():
    """Main initialization function"""
    try:
        # Create engine
        database_url = get_database_url()
        engine = create_engine(database_url)
        print(f"Connecting to database...")
        
        # Create tables
        create_tables(engine)
        
        # Create session
        Session = sessionmaker(bind=engine)
        session = Session()
        
        # Insert master data
        insert_master_data(session)
        
        session.close()
        print("\n✅ Database initialization completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Error during database initialization: {str(e)}")
        raise

if __name__ == "__main__":
    print("=" * 60)
    print("Financial Scenario Testing - Database Setup")
    print("=" * 60)
    initialize_database()
