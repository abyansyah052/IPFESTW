"""
Comprehensive Testing Script for ScenarioCalc Application
"""
from database.connection import get_db_session
from database.models import (
    Scenario, CapexCategory, CapexItem, ScenarioCapex, 
    FiscalTerms, PricingAssumptions, ProductionProfile, ProductionData,
    ScenarioOpex, CalculationResult, ScenarioMetrics
)
from engine.calculator import FinancialCalculator
from engine.opex_generator import OpexGenerator

def test_database_connection():
    """Test database connection"""
    print("\n=== TEST 1: Database Connection ===")
    try:
        with get_db_session() as session:
            count = session.query(Scenario).count()
            print(f"✅ Database connected - {count} scenarios found")
            return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

def test_data_integrity():
    """Test data integrity and field names"""
    print("\n=== TEST 2: Data Integrity ===")
    try:
        with get_db_session() as session:
            # Test FiscalTerms
            fiscal = session.query(FiscalTerms).first()
            assert hasattr(fiscal, 'contractor_oil_pretax'), "Missing contractor_oil_pretax"
            assert hasattr(fiscal, 'contractor_gas_pretax'), "Missing contractor_gas_pretax"
            assert hasattr(fiscal, 'salvage_value'), "Missing salvage_value"
            assert hasattr(fiscal, 'asr_rate'), "Missing asr_rate"
            print(f"✅ FiscalTerms fields verified")
            
            # Test PricingAssumptions
            pricing = session.query(PricingAssumptions).first()
            assert hasattr(pricing, 'oil_price'), "Missing oil_price"
            assert hasattr(pricing, 'gas_price'), "Missing gas_price"
            assert hasattr(pricing, 'mmscf_to_mmbtu'), "Missing mmscf_to_mmbtu"
            assert hasattr(pricing, 'working_days'), "Missing working_days"
            print(f"✅ PricingAssumptions fields verified")
            
            # Test ProductionData
            prod_data = session.query(ProductionData).first()
            if prod_data:
                assert hasattr(prod_data, 'condensate_rate_bopd'), "Missing condensate_rate_bopd"
                assert hasattr(prod_data, 'gas_rate_mmscfd'), "Missing gas_rate_mmscfd"
                assert hasattr(prod_data, 'profile_id'), "Missing profile_id"
                print(f"✅ ProductionData fields verified")
            
            return True
    except Exception as e:
        print(f"❌ Data integrity check failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_calculator():
    """Test financial calculator"""
    print("\n=== TEST 3: Financial Calculator ===")
    try:
        with get_db_session() as session:
            scenario = session.query(Scenario).first()
            if not scenario:
                print("⚠️  No scenario found to test")
                return False
            
            print(f"Testing scenario: {scenario.name}")
            calc = FinancialCalculator(scenario, session)
            results, metrics = calc.calculate_scenario()
            
            print(f"✅ Calculator executed successfully")
            print(f"   NPV: ${metrics.npv:,.2f}")
            print(f"   CAPEX: ${metrics.total_capex:,.2f}")
            print(f"   Revenue: ${metrics.total_revenue:,.2f}")
            
            return True
    except Exception as e:
        print(f"❌ Calculator test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_capex_items():
    """Test CAPEX items and categories"""
    print("\n=== TEST 4: CAPEX Items ===")
    try:
        with get_db_session() as session:
            categories = session.query(CapexCategory).all()
            items = session.query(CapexItem).all()
            
            print(f"✅ Found {len(categories)} categories and {len(items)} items")
            
            # Check for specific items
            ccpp = session.query(CapexItem).filter_by(code='CCPP').first()
            fwt = session.query(CapexItem).filter_by(code='FWT').first()
            
            if ccpp:
                print(f"   CCPP unit cost: ${ccpp.unit_cost:,.2f}")
                assert ccpp.unit_cost == 8400000, f"CCPP cost should be $8.4M, got ${ccpp.unit_cost:,.0f}"
            
            if fwt:
                print(f"   FWT unit cost: ${fwt.unit_cost:,.2f}")
                assert fwt.unit_cost == 15300000, f"FWT cost should be $15.3M, got ${fwt.unit_cost:,.0f}"
            
            print(f"✅ CAPEX values correct")
            return True
    except Exception as e:
        print(f"❌ CAPEX test failed: {e}")
        return False

def test_opex_generation():
    """Test OPEX generation"""
    print("\n=== TEST 5: OPEX Generation ===")
    try:
        with get_db_session() as session:
            scenario = session.query(Scenario).first()
            if not scenario:
                print("⚠️  No scenario found to test")
                return False
            
            opex_items = session.query(ScenarioOpex).filter_by(scenario_id=scenario.id).all()
            print(f"✅ Found {len(opex_items)} OPEX items for scenario")
            
            if opex_items:
                total_opex = sum(item.opex_amount for item in opex_items)
                print(f"   Total OPEX: ${total_opex:,.2f}")
            
            return True
    except Exception as e:
        print(f"❌ OPEX test failed: {e}")
        return False

def test_scenario_creation():
    """Test scenario creation workflow"""
    print("\n=== TEST 6: Scenario Creation ===")
    try:
        with get_db_session() as session:
            # Count existing scenarios
            initial_count = session.query(Scenario).count()
            
            # Create test scenario
            new_scenario = Scenario(
                name="Test Scenario",
                description="Automated test scenario",
                production_profile_id=1,
                fiscal_terms_id=1,
                pricing_assumptions_id=1,
                production_enhancement_id=1,
                created_by="test_script",
                is_active=True
            )
            session.add(new_scenario)
            session.flush()
            
            # Add CAPEX item
            ccpp = session.query(CapexItem).filter_by(code='CCPP').first()
            if ccpp:
                scenario_capex = ScenarioCapex(
                    scenario_id=new_scenario.id,
                    capex_item_id=ccpp.id,
                    quantity=1,
                    unit_cost=ccpp.unit_cost,
                    total_cost=ccpp.unit_cost
                )
                session.add(scenario_capex)
            
            session.commit()
            
            final_count = session.query(Scenario).count()
            assert final_count == initial_count + 1, "Scenario not created"
            
            # Clean up
            session.delete(new_scenario)
            session.commit()
            
            print(f"✅ Scenario creation workflow successful")
            return True
    except Exception as e:
        print(f"❌ Scenario creation test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def run_all_tests():
    """Run all tests"""
    print("="*60)
    print("🧪 SCENARIOCALC COMPREHENSIVE TESTING")
    print("="*60)
    
    tests = [
        test_database_connection,
        test_data_integrity,
        test_capex_items,
        test_opex_generation,
        test_calculator,
        test_scenario_creation
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"❌ Test crashed: {e}")
            results.append(False)
    
    print("\n" + "="*60)
    print(f"📊 TEST RESULTS: {sum(results)}/{len(results)} PASSED")
    print("="*60)
    
    if all(results):
        print("\n✅ ALL TESTS PASSED! Application is ready to use.")
    else:
        print("\n⚠️  Some tests failed. Check errors above.")
    
    return all(results)

if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)
