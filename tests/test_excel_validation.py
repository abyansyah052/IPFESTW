"""
Excel Validation Test
Compares calculator output against known Excel values from Scenario 1
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection import get_db_session
from database.models import Scenario, CalculationResult
from engine.calculator import FinancialCalculator

# Expected values from Excel (Screenshot)
EXPECTED = {
    'total_capex': 156_620_733,
    'npv': -258_234_120,  # Negative value (parentheses in Excel)
    'gross_revenue': 336_050_098,
    'contractor_take': 93_527_783,
    'gov_take': 140_289_860,
    'payback_period': 7.923,
    # Additional checks
    'year_2026_contractor_aftertax': 0,  # NO SPLIT (loss year)
    'year_2037_contractor_aftertax': 0,  # NO SPLIT (ASR year)
}

TOLERANCE = 0.05  # 5% tolerance for floating point differences

def check_value(name, actual, expected, tolerance=TOLERANCE):
    """Check if actual value is within tolerance of expected"""
    if expected == 0:
        passed = actual == 0
    else:
        passed = abs(actual - expected) / abs(expected) <= tolerance
    
    status = "✅ PASS" if passed else "❌ FAIL"
    diff_pct = ((actual - expected) / expected * 100) if expected != 0 else 0
    
    print(f"{status} {name}:")
    print(f"       Expected: {expected:,.2f}")
    print(f"       Actual:   {actual:,.2f}")
    print(f"       Diff:     {diff_pct:+.2f}%")
    
    return passed

def main():
    print("=" * 60)
    print("EXCEL VALIDATION TEST")
    print("Comparing calculator output with Scenario 1 Excel values")
    print("=" * 60)
    
    with get_db_session() as session:
        # Get scenario "All Solutions Combined" or first available
        scenario = session.query(Scenario).filter_by(is_active=True).first()
        
        if not scenario:
            print("❌ No active scenario found!")
            return False
        
        print(f"\nTesting: {scenario.name}")
        print("-" * 60)
        
        # Run calculation
        calc = FinancialCalculator(scenario, session)
        results, metrics = calc.calculate_scenario()
        
        all_passed = True
        
        # Test key metrics
        print("\n📊 FINANCIAL METRICS:")
        all_passed &= check_value("NPV (13%)", metrics.npv, EXPECTED['npv'])
        all_passed &= check_value("Gross Revenue", metrics.total_revenue, EXPECTED['gross_revenue'])
        all_passed &= check_value("Contractor Take", metrics.total_contractor_share, EXPECTED['contractor_take'])
        all_passed &= check_value("Gov Take", metrics.total_government_take, EXPECTED['gov_take'])
        
        # Test PSC Split rules
        print("\n📋 PSC SPLIT RULES:")
        year_2026 = next((r for r in results if r.year == 2026), None)
        year_2037 = next((r for r in results if r.year == 2037), None)
        
        if year_2026:
            all_passed &= check_value("Year 2026 Contractor After-tax (should be 0)", 
                                       year_2026.contractor_share_aftertax, 
                                       EXPECTED['year_2026_contractor_aftertax'])
            print(f"       Available for Split: ${year_2026.operating_profit:,.2f}")
            print(f"       (Negative = loss, so NO SPLIT)")
        
        if year_2037:
            all_passed &= check_value("Year 2037 Contractor After-tax (should be 0)", 
                                       year_2037.contractor_share_aftertax, 
                                       EXPECTED['year_2037_contractor_aftertax'])
            print(f"       Available for Split: ${year_2037.operating_profit:,.2f}")
            print(f"       (ASR year, so NO SPLIT even though positive)")
        
        # Count years with actual split
        years_with_split = [r for r in results if r.contractor_share_aftertax > 0]
        print(f"\n📅 Years with PSC Split: {len(years_with_split)}")
        print(f"   Expected: 10 years (2027-2036)")
        
        for r in results:
            split_status = "✓ SPLIT" if r.contractor_share_aftertax > 0 else "✗ NO SPLIT"
            print(f"   {r.year}: {split_status} (Available: ${r.operating_profit:,.0f})")
        
        # Summary
        print("\n" + "=" * 60)
        if all_passed:
            print("✅ ALL TESTS PASSED!")
        else:
            print("❌ SOME TESTS FAILED")
        print("=" * 60)
        
        return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
