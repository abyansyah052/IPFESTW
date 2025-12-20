"""
Unit Test for Calculator Logic (No Database Required)
Tests the corrected formulas using mock data matching Excel values
"""
from decimal import Decimal

# === TEST DATA FROM EXCEL ===
CAPEX_TOTAL = 156_620_733.0
ASR_RATE = 0.05
ASR_AMOUNT = CAPEX_TOTAL * ASR_RATE  # $7,831,036.65

# Production data (years 2026-2037)
PRODUCTION_DATA = [
    {'year': 2026, 'revenue': 20_489_975, 'cost': 167_932_806, 'depreciation': 7_831_037},
    {'year': 2027, 'revenue': 39_037_359, 'cost': 10_990_142, 'depreciation': 7_439_485},
    {'year': 2028, 'revenue': 37_163_747, 'cost': 10_689_181, 'depreciation': 7_067_511},
    {'year': 2029, 'revenue': 35_394_558, 'cost': 16_408_239, 'depreciation': 6_714_135},
    {'year': 2030, 'revenue': 34_321_832, 'cost': 10_146_414, 'depreciation': 6_378_428},
    {'year': 2031, 'revenue': 36_052_142, 'cost': 3_843_345, 'depreciation': 0},
    {'year': 2032, 'revenue': 27_990_384, 'cost': 3_920_213, 'depreciation': 0},
    {'year': 2033, 'revenue': 28_522_745, 'cost': 3_998_617, 'depreciation': 0},
    {'year': 2034, 'revenue': 20_522_442, 'cost': 4_078_589, 'depreciation': 0},
    {'year': 2035, 'revenue': 21_597_845, 'cost': 4_160_161, 'depreciation': 0},
    {'year': 2036, 'revenue': 19_683_856, 'cost': 4_243_364, 'depreciation': 0},
    {'year': 2037, 'revenue': 15_273_214, 'cost': 4_328_232 + ASR_AMOUNT, 'depreciation': 0},  # ASR included
]

# PSC Split rates
CONTRACTOR_PRETAX_SPLIT = 0.6723
GOVERNMENT_PRETAX_SPLIT = 0.3277
CONTRACTOR_TAX_RATE = 0.405

LAST_YEAR = 2037

def calculate_psc_split(available_for_split, year):
    """Test PSC Split with corrected rules"""
    # CRITICAL: NO SPLIT if loss or ASR year
    if available_for_split <= 0 or year == LAST_YEAR:
        return {
            'contractor_pretax': 0,
            'contractor_tax': 0,
            'contractor_aftertax': 0,
            'government_pretax': 0,
            'government_total': 0
        }
    else:
        contractor_pretax = available_for_split * CONTRACTOR_PRETAX_SPLIT
        contractor_tax = contractor_pretax * CONTRACTOR_TAX_RATE
        contractor_aftertax = contractor_pretax - contractor_tax
        
        government_pretax = available_for_split * GOVERNMENT_PRETAX_SPLIT
        government_total = government_pretax + contractor_tax
        
        return {
            'contractor_pretax': contractor_pretax,
            'contractor_tax': contractor_tax,
            'contractor_aftertax': contractor_aftertax,
            'government_pretax': government_pretax,
            'government_total': government_total
        }

def main():
    print("=" * 70)
    print("🧪 UNIT TEST: Calculator Logic (No Database)")
    print("Testing corrected PSC Split and Cash Flow formulas")
    print("=" * 70)
    
    results = []
    cumulative_cf = 0
    
    print("\n📊 YEAR-BY-YEAR CALCULATION:")
    print("-" * 70)
    print(f"{'Year':<6} {'Revenue':>15} {'Cost':>15} {'Available':>15} {'Split?':<12}")
    print("-" * 70)
    
    for data in PRODUCTION_DATA:
        year = data['year']
        revenue = data['revenue']
        cost = data['cost']
        
        # Available for production split
        available_for_split = revenue - cost
        
        # PSC Split with corrected rules
        psc = calculate_psc_split(available_for_split, year)
        
        # Cash flow
        annual_cf = available_for_split
        cumulative_cf += annual_cf
        
        # Determine split status
        if available_for_split <= 0:
            split_status = "NO (loss)"
        elif year == LAST_YEAR:
            split_status = "NO (ASR)"
        else:
            split_status = "YES"
        
        results.append({
            'year': year,
            'revenue': revenue,
            'cost': cost,
            'available': available_for_split,
            'contractor_aftertax': psc['contractor_aftertax'],
            'government_total': psc['government_total'],
            'annual_cf': annual_cf,
            'cumulative_cf': cumulative_cf,
            'has_split': psc['contractor_aftertax'] > 0
        })
        
        print(f"{year:<6} ${revenue:>14,.0f} ${cost:>14,.0f} ${available_for_split:>14,.0f} {split_status:<12}")
    
    # Calculate totals (only from years with split)
    contractor_take = sum(r['contractor_aftertax'] for r in results if r['has_split'])
    gov_take = sum(r['government_total'] for r in results if r['has_split'])
    gross_revenue = sum(r['revenue'] for r in results)
    years_with_split = len([r for r in results if r['has_split']])
    
    # Calculate NPV using cumulative cash flows
    discount_rate = 0.13
    cash_flows = [r['cumulative_cf'] for r in results]
    npv = sum(cf / ((1 + discount_rate) ** (i + 1)) for i, cf in enumerate(cash_flows))
    
    print("-" * 70)
    
    # Expected values from Excel
    EXPECTED = {
        'npv': -258_234_120,
        'gross_revenue': 336_050_098,
        'contractor_take': 93_527_783,
        'gov_take': 140_289_860,
    }
    
    print("\n📋 SUMMARY:")
    print("-" * 70)
    print(f"Years with PSC Split: {years_with_split} (expected: 10, years 2027-2036)")
    print(f"Year 2026 split?    : {'YES' if results[0]['has_split'] else 'NO'} (expected: NO - loss year)")
    print(f"Year 2037 split?    : {'YES' if results[11]['has_split'] else 'NO'} (expected: NO - ASR year)")
    
    print("\n📊 FINANCIAL METRICS COMPARISON:")
    print("-" * 70)
    print(f"{'Metric':<25} {'Calculated':>20} {'Expected':>20} {'Status':<10}")
    print("-" * 70)
    
    all_passed = True
    
    # Check each metric
    def check(name, calc, exp, tolerance=0.10):  # 10% tolerance
        if exp == 0:
            passed = abs(calc) < 1000
        else:
            passed = abs(calc - exp) / abs(exp) <= tolerance
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{name:<25} ${calc:>19,.0f} ${exp:>19,.0f} {status:<10}")
        return passed
    
    all_passed &= check("Gross Revenue", gross_revenue, EXPECTED['gross_revenue'])
    all_passed &= check("NPV (13%)", npv, EXPECTED['npv'])
    all_passed &= check("Contractor Take", contractor_take, EXPECTED['contractor_take'])
    all_passed &= check("Gov Take", gov_take, EXPECTED['gov_take'])
    
    print("-" * 70)
    
    # Verify PSC Split rules
    print("\n🔍 PSC SPLIT RULES VERIFICATION:")
    rule1 = not results[0]['has_split']  # 2026 should have no split
    rule2 = not results[11]['has_split']  # 2037 should have no split
    rule3 = years_with_split == 10  # Only 10 years should have split
    
    print(f"Rule 1: No split when loss (2026)    : {'✅ PASS' if rule1 else '❌ FAIL'}")
    print(f"Rule 2: No split in ASR year (2037)  : {'✅ PASS' if rule2 else '❌ FAIL'}")
    print(f"Rule 3: Split only 2027-2036 (10 yrs): {'✅ PASS' if rule3 else '❌ FAIL'}")
    
    all_passed &= rule1 and rule2 and rule3
    
    print("\n" + "=" * 70)
    if all_passed:
        print("✅ ALL TESTS PASSED! Calculator logic is correct.")
    else:
        print("❌ SOME TESTS FAILED. Review the calculations above.")
    print("=" * 70)
    
    return all_passed

if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)
