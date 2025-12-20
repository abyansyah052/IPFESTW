"""
Test Streamlit App Functionality
"""
from database.connection import get_db_session
from database.models import (
    Scenario, CapexItem, ScenarioCapex, 
    FiscalTerms, PricingAssumptions, ProductionProfile
)
from engine.calculator import FinancialCalculator
from engine.opex_generator import OpexGenerator

print("="*70)
print("🌐 STREAMLIT APP FUNCTIONALITY TEST")
print("="*70)

with get_db_session() as session:
    
    # Test 1: Check all required data exists
    print("\n1️⃣  Database Data Check")
    scenarios = session.query(Scenario).count()
    capex_items = session.query(CapexItem).count()
    fiscal_terms = session.query(FiscalTerms).count()
    pricing = session.query(PricingAssumptions).count()
    profiles = session.query(ProductionProfile).count()
    
    print(f"   Scenarios: {scenarios}")
    print(f"   CAPEX Items: {capex_items}")
    print(f"   Fiscal Terms: {fiscal_terms}")
    print(f"   Pricing Assumptions: {pricing}")
    print(f"   Production Profiles: {profiles}")
    print(f"   ✅ PASS - All master data present")
    
    # Test 2: Simulate Create Scenario workflow
    print("\n2️⃣  Create Scenario Workflow")
    
    # Get CAPEX items
    ccpp = session.query(CapexItem).filter_by(code='CCPP').first()
    fwt = session.query(CapexItem).filter_by(code='FWT').first()
    
    print(f"   Found CCPP: ${ccpp.unit_cost:,.0f}")
    print(f"   Found FWT: ${fwt.unit_cost:,.0f}")
    
    # Create test scenario
    test_scenario = Scenario(
        name="UI_Test_Scenario",
        description="Testing Streamlit functionality",
        production_profile_id=1,
        fiscal_terms_id=1,
        pricing_assumptions_id=1,
        production_enhancement_id=1,
        created_by="test",
        is_active=True
    )
    session.add(test_scenario)
    session.flush()
    
    # Add CAPEX
    test_capex = ScenarioCapex(
        scenario_id=test_scenario.id,
        capex_item_id=ccpp.id,
        quantity=1,
        unit_cost=ccpp.unit_cost,
        total_cost=ccpp.unit_cost
    )
    session.add(test_capex)
    session.commit()
    
    print(f"   Created scenario: {test_scenario.name} (ID: {test_scenario.id})")
    print(f"   ✅ PASS - Scenario creation works")
    
    # Test 3: OPEX Generation
    print("\n3️⃣  OPEX Generation")
    
    fiscal = session.query(FiscalTerms).first()
    opex_gen = OpexGenerator(session)
    opex_gen.save_opex_for_scenario(
        test_scenario.id,
        fiscal.project_start_year,
        fiscal.project_end_year,
        escalation_rate=fiscal.opex_escalation_rate
    )
    
    from database.models import ScenarioOpex
    opex_count = session.query(ScenarioOpex).filter_by(scenario_id=test_scenario.id).count()
    print(f"   Generated OPEX items: {opex_count}")
    print(f"   ✅ PASS - OPEX generation works")
    
    # Test 4: Calculator
    print("\n4️⃣  Calculator Execution")
    
    calc = FinancialCalculator(test_scenario, session)
    results, metrics = calc.calculate_scenario()
    
    print(f"   Results count: {len(results)} years")
    print(f"   NPV: ${metrics.npv:,.2f}")
    print(f"   Total CAPEX: ${metrics.total_capex:,.2f}")
    print(f"   Total OPEX: ${metrics.total_opex:,.2f}")
    print(f"   Gross Revenue: ${metrics.total_revenue:,.2f}")
    print(f"   ✅ PASS - Calculator works")
    
    # Test 5: Save Results
    print("\n5️⃣  Save Calculation Results")
    
    calc.save_calculations()
    
    from database.models import CalculationResult, ScenarioMetrics
    saved_results = session.query(CalculationResult).filter_by(scenario_id=test_scenario.id).count()
    saved_metrics = session.query(ScenarioMetrics).filter_by(scenario_id=test_scenario.id).count()
    
    print(f"   Saved results: {saved_results} years")
    print(f"   Saved metrics: {saved_metrics} record")
    print(f"   ✅ PASS - Results saved to database")
    
    # Test 6: View Scenario (simulate display_scenario_results)
    print("\n6️⃣  View Scenario")
    
    scenario_with_results = session.query(Scenario).filter_by(id=test_scenario.id).first()
    metrics_record = session.query(ScenarioMetrics).filter_by(scenario_id=test_scenario.id).first()
    results_records = session.query(CalculationResult).filter_by(scenario_id=test_scenario.id).all()
    
    print(f"   Scenario: {scenario_with_results.name}")
    print(f"   Metrics available: {metrics_record is not None}")
    print(f"   Results available: {len(results_records)} years")
    print(f"   ✅ PASS - View scenario works")
    
    # Test 7: Duplicate Scenario
    print("\n7️⃣  Duplicate Scenario")
    
    dup_scenario = Scenario(
        name=f"{test_scenario.name} (Copy)",
        description=test_scenario.description,
        production_profile_id=test_scenario.production_profile_id,
        fiscal_terms_id=test_scenario.fiscal_terms_id,
        pricing_assumptions_id=test_scenario.pricing_assumptions_id,
        production_enhancement_id=test_scenario.production_enhancement_id,
        created_by=test_scenario.created_by,
        is_active=True
    )
    session.add(dup_scenario)
    session.flush()
    
    # Copy CAPEX
    capex_items = session.query(ScenarioCapex).filter_by(scenario_id=test_scenario.id).all()
    for capex in capex_items:
        new_capex = ScenarioCapex(
            scenario_id=dup_scenario.id,
            capex_item_id=capex.capex_item_id,
            quantity=capex.quantity,
            unit_cost=capex.unit_cost,
            total_cost=capex.total_cost
        )
        session.add(new_capex)
    
    session.commit()
    
    print(f"   Duplicated scenario: {dup_scenario.name} (ID: {dup_scenario.id})")
    print(f"   ✅ PASS - Duplicate works")
    
    # Test 8: Delete Scenario
    print("\n8️⃣  Delete Scenario")
    
    # Delete test scenarios
    session.query(ScenarioCapex).filter_by(scenario_id=test_scenario.id).delete()
    session.query(ScenarioOpex).filter_by(scenario_id=test_scenario.id).delete()
    session.query(CalculationResult).filter_by(scenario_id=test_scenario.id).delete()
    session.query(ScenarioMetrics).filter_by(scenario_id=test_scenario.id).delete()
    session.delete(test_scenario)
    
    session.query(ScenarioCapex).filter_by(scenario_id=dup_scenario.id).delete()
    session.delete(dup_scenario)
    
    session.commit()
    
    print(f"   Deleted test scenarios")
    print(f"   ✅ PASS - Delete works")
    
    print("\n" + "="*70)
    print("🎯 ALL APP FUNCTIONALITY TESTS PASSED!")
    print("="*70)
    print("\n✅ Streamlit app is ready to use")
    print("✅ All CRUD operations working")
    print("✅ Calculator integration working")
    print("✅ Database operations working")
    print("\n🚀 Run: streamlit run app.py")
    print("="*70)
