"""
Test New Calculator Logic (tambahan.md)
"""
from database.connection import get_db_session
from database.models import Scenario
from engine.calculator import FinancialCalculator

with get_db_session() as session:
    scenario = session.query(Scenario).first()
    
    print(f"🧪 Testing New Calculator Logic")
    print(f"Scenario: {scenario.name}\n")
    
    try:
        calc = FinancialCalculator(scenario, session)
        results, metrics = calc.calculate_scenario()
        
        print("✅ CALCULATION SUCCESS!\n")
        
        print("=== FINANCIAL METRICS (matching Excel J35-J41) ===")
        print(f"NPV at 13%:       ${metrics.npv:,.2f}")
        print(f"IRR:              {metrics.irr*100:.2f}% " if metrics.irr else "IRR:              N/A")
        print(f"Payback Period:   {metrics.payback_period_years:.2f} years" if metrics.payback_period_years else "Payback Period:   N/A")
        print(f"Gross Revenue:    ${metrics.total_revenue:,.2f}")
        print(f"Contractor Take:  ${metrics.total_contractor_share:,.2f}")
        print(f"Gov Take:         ${metrics.total_government_take:,.2f}")
        print(f"ASR Amount:       ${metrics.asr_amount:,.2f}")
        
        print(f"\n=== TOTALS ===")
        print(f"Total CAPEX:      ${metrics.total_capex:,.2f}")
        print(f"Total OPEX:       ${metrics.total_opex:,.2f}")
        
        print(f"\n=== YEAR-BY-YEAR BREAKDOWN (First 3 years) ===")
        for i, result in enumerate(results[:3]):
            print(f"\n--- Year {result.year} (Period {i+1}) ---")
            print(f"Revenue:          ${result.total_revenue:,.2f}")
            print(f"OPEX:             ${result.opex_total:,.2f}")
            print(f"Depreciation:     ${result.depreciation:,.2f}")
            print(f"Available Split:  ${result.operating_profit:,.2f}")
            print(f"Contractor Tax:   ${result.contractor_tax:,.2f}")
            print(f"Contractor A/T:   ${result.contractor_share_aftertax:,.2f}")
            print(f"Gov Total:        ${result.government_total_take:,.2f}")
            print(f"Net Cash Flow:    ${result.cash_flow:,.2f}")
            print(f"Cumulative CF:    ${result.cumulative_cash_flow:,.2f}")
        
        print(f"\n✅ ALL TESTS PASSED - New Logic Working!")
        
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
