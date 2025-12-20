from database.connection import get_db_session
from database.models import Scenario
from engine.calculator import FinancialCalculator

with get_db_session() as session:
    scenario = session.query(Scenario).first()
    
    print(f"Testing: {scenario.name}")
    calc = FinancialCalculator(scenario, session)
    results, metrics = calc.calculate_scenario()
    
    print(f"NPV: ${metrics.npv:,.0f}")
    print(f"CAPEX: ${metrics.total_capex:,.0f}")
    print(f"Revenue: ${metrics.total_revenue:,.0f}")
    print("✅ Calculator works!")
