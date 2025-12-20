"""
Deep Validation Test - Logic Matching tambahan.md
"""
from database.connection import get_db_session
from database.models import Scenario, FiscalTerms, PricingAssumptions
from engine.calculator import FinancialCalculator

print("="*70)
print("🔬 DEEP VALIDATION TEST - Logic Matching tambahan.md")
print("="*70)

with get_db_session() as session:
    scenario = session.query(Scenario).first()
    fiscal = session.query(FiscalTerms).first()
    pricing = session.query(PricingAssumptions).first()
    
    print(f"\n📋 Scenario: {scenario.name}")
    print(f"📅 Project Period: {fiscal.project_start_year} - {fiscal.project_end_year}")
    
    calc = FinancialCalculator(scenario, session)
    results, metrics = calc.calculate_scenario()
    
    print(f"\n{'='*70}")
    print("✅ VALIDATION CHECKLIST (from tambahan.md)")
    print(f"{'='*70}")
    
    # 1. Check ASR calculation
    expected_asr = metrics.total_capex * 0.05
    print(f"\n1️⃣  ASR Calculation")
    print(f"   Total CAPEX: ${metrics.total_capex:,.2f}")
    print(f"   ASR Rate: {fiscal.asr_rate*100}%")
    print(f"   ASR Amount: ${metrics.asr_amount:,.2f}")
    print(f"   Expected: ${expected_asr:,.2f}")
    print(f"   ✅ PASS" if abs(metrics.asr_amount - expected_asr) < 0.01 else "   ❌ FAIL")
    
    # 2. Check depreciation only in first 5 years
    print(f"\n2️⃣  Depreciation (Only First 5 Years)")
    depreciation_years = [r for r in results if r.depreciation > 0]
    print(f"   Years with depreciation: {len(depreciation_years)}")
    print(f"   Expected: 5 years")
    for i, r in enumerate(results[:7]):
        status = "✓" if (i < 5 and r.depreciation > 0) or (i >= 5 and r.depreciation == 0) else "✗"
        print(f"   {status} Year {r.year}: ${r.depreciation:,.2f}")
    print(f"   ✅ PASS" if len(depreciation_years) == 5 else "   ❌ FAIL")
    
    # 3. Check Available for Split calculation
    print(f"\n3️⃣  Available for Split Calculation")
    print(f"   Formula: Revenue - (CAPEX + OPEX + Depreciation + ASR)")
    first_year = results[0]
    second_year = results[1]
    
    # Year 1 should have CAPEX
    capex_y1 = metrics.total_capex  # All CAPEX in year 1
    cost_recoverable_y1 = capex_y1 + first_year.opex_total + first_year.depreciation
    print(f"\n   Year 2026 (Period 1):")
    print(f"   Revenue: ${first_year.total_revenue:,.2f}")
    print(f"   CAPEX: ${capex_y1:,.2f}")
    print(f"   OPEX: ${first_year.opex_total:,.2f}")
    print(f"   Depreciation: ${first_year.depreciation:,.2f}")
    print(f"   Total Cost Recoverable: ${cost_recoverable_y1:,.2f}")
    print(f"   Available for Split: ${first_year.operating_profit:,.2f}")
    expected_available = first_year.total_revenue - cost_recoverable_y1
    print(f"   Expected: ${expected_available:,.2f}")
    print(f"   ✅ PASS" if abs(first_year.operating_profit - expected_available) < 0.01 else "   ❌ FAIL")
    
    # 4. Check PSC Split
    print(f"\n4️⃣  PSC Split")
    print(f"   Contractor Pre-tax: {fiscal.contractor_oil_pretax*100}%")
    print(f"   Government Pre-tax: {fiscal.gov_oil_pretax*100}%")
    print(f"   Tax Rate: {fiscal.contractor_tax_rate*100}%")
    
    available = second_year.operating_profit
    expected_contractor_pretax = available * fiscal.contractor_oil_pretax
    expected_tax = expected_contractor_pretax * fiscal.contractor_tax_rate
    expected_contractor_aftertax = expected_contractor_pretax - expected_tax
    expected_gov_pretax = available * fiscal.gov_oil_pretax
    expected_gov_total = expected_gov_pretax + expected_tax
    
    print(f"\n   Year 2027 (Period 2):")
    print(f"   Available: ${available:,.2f}")
    print(f"   Contractor Pre-tax: ${second_year.contractor_share_pretax:,.2f} (expected: ${expected_contractor_pretax:,.2f})")
    print(f"   Contractor Tax: ${second_year.contractor_tax:,.2f} (expected: ${expected_tax:,.2f})")
    print(f"   Contractor After-tax: ${second_year.contractor_share_aftertax:,.2f} (expected: ${expected_contractor_aftertax:,.2f})")
    print(f"   Gov Pre-tax: ${second_year.government_share_pretax:,.2f} (expected: ${expected_gov_pretax:,.2f})")
    print(f"   Gov Total: ${second_year.government_total_take:,.2f} (expected: ${expected_gov_total:,.2f})")
    
    psc_pass = (
        abs(second_year.contractor_share_pretax - expected_contractor_pretax) < 0.01 and
        abs(second_year.contractor_tax - expected_tax) < 0.01 and
        abs(second_year.government_total_take - expected_gov_total) < 0.01
    )
    print(f"   ✅ PASS" if psc_pass else "   ❌ FAIL")
    
    # 5. Check Cash Flow (excludes depreciation)
    print(f"\n5️⃣  Cash Flow Calculation")
    print(f"   Formula: Revenue - OPEX - CAPEX - ASR")
    print(f"   (Depreciation NOT included - non-cash)")
    
    # Check year 1
    expected_cf_y1 = first_year.total_revenue - first_year.opex_total - capex_y1
    print(f"\n   Year 2026:")
    print(f"   Cash Flow: ${first_year.cash_flow:,.2f}")
    print(f"   Expected: ${expected_cf_y1:,.2f}")
    print(f"   ✅ PASS" if abs(first_year.cash_flow - expected_cf_y1) < 0.01 else "   ❌ FAIL")
    
    # 6. Check Metrics (matching Excel J35-J41)
    print(f"\n6️⃣  Metrics (Excel J35-J41)")
    print(f"   NPV at 13%: ${metrics.npv:,.2f}")
    print(f"   IRR: {metrics.irr*100:.2f}%" if metrics.irr else "   IRR: N/A")
    print(f"   Payback Period: {metrics.payback_period_years:.2f} years" if metrics.payback_period_years else "   Payback Period: N/A")
    print(f"   Gross Revenue: ${metrics.total_revenue:,.2f}")
    print(f"   Contractor Take: ${metrics.total_contractor_share:,.2f}")
    print(f"   Gov Take: ${metrics.total_government_take:,.2f}")
    
    # Verify Contractor Take = SUM of contractor after-tax
    expected_contractor_take = sum(r.contractor_share_aftertax for r in results)
    contractor_take_pass = abs(metrics.total_contractor_share - expected_contractor_take) < 0.01
    
    # Verify Gov Take = SUM of government total
    expected_gov_take = sum(r.government_total_take for r in results)
    gov_take_pass = abs(metrics.total_government_take - expected_gov_take) < 0.01
    
    # Verify Gross Revenue = SUM of revenues
    expected_gross = sum(r.total_revenue for r in results)
    gross_pass = abs(metrics.total_revenue - expected_gross) < 0.01
    
    print(f"\n   Contractor Take matches SUM: {'✅' if contractor_take_pass else '❌'}")
    print(f"   Gov Take matches SUM: {'✅' if gov_take_pass else '❌'}")
    print(f"   Gross Revenue matches SUM: {'✅' if gross_pass else '❌'}")
    
    # 7. Check Payback Period calculation
    print(f"\n7️⃣  Payback Period")
    print(f"   Calculated: {metrics.payback_period_years:.2f} years" if metrics.payback_period_years else "   N/A")
    for i, r in enumerate(results[:8]):
        if r.cumulative_cash_flow >= 0:
            print(f"   First positive CF at Year {r.year} (Period {i+1})")
            print(f"   Cumulative CF: ${r.cumulative_cash_flow:,.2f}")
            break
    
    print(f"\n{'='*70}")
    print("🎯 VALIDATION SUMMARY")
    print(f"{'='*70}")
    
    all_pass = (
        abs(metrics.asr_amount - expected_asr) < 0.01 and
        len(depreciation_years) == 5 and
        abs(first_year.operating_profit - expected_available) < 0.01 and
        psc_pass and
        abs(first_year.cash_flow - expected_cf_y1) < 0.01 and
        contractor_take_pass and
        gov_take_pass and
        gross_pass
    )
    
    if all_pass:
        print("✅ ALL VALIDATIONS PASSED!")
        print("✅ Calculator logic matches tambahan.md specifications")
    else:
        print("⚠️  Some validations failed - review details above")
    
    print(f"\n{'='*70}")
