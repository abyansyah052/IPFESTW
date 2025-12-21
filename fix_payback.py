"""
Quick fix to recalculate payback period for all scenarios
"""
from database.connection import get_session
from database.models import ScenarioMetrics, CalculationResult

def calculate_payback(results):
    """Calculate payback period from calculation results"""
    for i, result in enumerate(results):
        if result.cumulative_cash_flow >= 0:
            if i == 0:
                # First year already positive
                if result.cash_flow > 0:
                    return abs(result.cumulative_cash_flow - result.cash_flow) / result.cash_flow
                return 1.0
            
            prev_cumulative = results[i-1].cumulative_cash_flow  # Still negative
            current_year_cf = result.cash_flow  # Annual CF this year
            
            if current_year_cf <= 0:
                return float(i + 1)
            
            year_number = i + 1
            fraction_into_year = abs(prev_cumulative) / current_year_cf
            return float(year_number) - fraction_into_year
    
    return None

print("Fixing payback periods for all scenarios...")
print()

with get_session() as session:
    # Get all scenario metrics
    all_metrics = session.query(ScenarioMetrics).all()
    total = len(all_metrics)
    fixed = 0
    
    for i, metrics in enumerate(all_metrics, 1):
        # Get calculation results for this scenario
        results = session.query(CalculationResult).filter(
            CalculationResult.scenario_id == metrics.scenario_id
        ).order_by(CalculationResult.year).all()
        
        if results:
            old_payback = metrics.payback_period_years
            new_payback = calculate_payback(results)
            
            if new_payback is not None:
                metrics.payback_period_years = new_payback
                fixed += 1
                
                if old_payback != new_payback:
                    if abs(old_payback - new_payback) > 10:  # Show big differences
                        print(f"Scenario {metrics.scenario_id}: {old_payback:.3f} → {new_payback:.3f} years")
        
        if i % 100 == 0:
            print(f"Progress: {i}/{total}")
            session.commit()
    
    session.commit()
    print(f"\n✅ Fixed {fixed} scenarios out of {total} total")
    
    # Verify S66
    s66 = session.query(ScenarioMetrics).filter(ScenarioMetrics.scenario_id == 83).first()
    print(f"\n=== S66 Verification ===")
    print(f"New Payback: {s66.payback_period_years:.3f} years (was 67.083)")
