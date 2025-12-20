#!/usr/bin/env python3
"""
Regenerate OPEX for scenario based on selected CAPEX items
OPEX is calculated dynamically from CAPEX selections using OpexMapping rules
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection import get_db_session
from database.models import Scenario, ScenarioCapex, ScenarioOpex, FiscalTerms, OpexMapping, CapexItem
from engine.opex_generator import OpexGenerator

def regenerate_opex_for_scenario(scenario_id: int):
    """Regenerate OPEX for a scenario based on its CAPEX selections"""
    
    with get_db_session() as session:
        # Get scenario
        scenario = session.query(Scenario).filter_by(id=scenario_id).first()
        if not scenario:
            print(f"❌ Scenario {scenario_id} not found")
            return False
        
        print(f"📊 Scenario: {scenario.name} (ID: {scenario.id})")
        
        # Get fiscal terms for year range
        fiscal = session.query(FiscalTerms).first()
        start_year = fiscal.project_start_year
        end_year = fiscal.project_end_year
        
        print(f"📅 Year range: {start_year} - {end_year}")
        
        # Show selected CAPEX items
        capex_items = session.query(ScenarioCapex).filter_by(scenario_id=scenario_id).all()
        print(f"\n📦 Selected CAPEX items ({len(capex_items)}):")
        
        total_capex = 0
        for capex in capex_items:
            item = session.query(CapexItem).filter_by(id=capex.capex_item_id).first()
            print(f"   - {item.name}: qty={capex.quantity}, total=${capex.total_cost:,.0f}")
            total_capex += capex.total_cost
            
            # Show OPEX mapping for this item
            mappings = session.query(OpexMapping).filter_by(capex_item_id=capex.capex_item_id).all()
            for m in mappings:
                if m.opex_calculation_method == 'PERCENTAGE':
                    opex_base = capex.total_cost * m.opex_rate
                    print(f"     └─ OPEX: {m.opex_name} = {m.opex_rate*100}% × ${capex.total_cost:,.0f} = ${opex_base:,.0f}/year")
                elif m.opex_calculation_method == 'FIXED':
                    print(f"     └─ OPEX: {m.opex_name} = ${m.opex_rate:,.0f}/year (flat)")
                elif m.opex_calculation_method == 'FIXED_PER_UNIT':
                    opex_base = m.opex_rate * capex.quantity
                    print(f"     └─ OPEX: {m.opex_name} = ${m.opex_rate:,.0f} × {capex.quantity} = ${opex_base:,.0f}/year")
        
        print(f"\n💰 Total CAPEX: ${total_capex:,.0f}")
        
        # Delete existing OPEX
        deleted = session.query(ScenarioOpex).filter_by(scenario_id=scenario_id).delete()
        print(f"\n🗑️  Deleted {deleted} existing OPEX records")
        
        # Generate new OPEX using OpexGenerator
        generator = OpexGenerator(session)
        opex_list = generator.generate_opex_for_scenario(
            scenario_id=scenario_id,
            start_year=start_year,
            end_year=end_year,
            escalation_rate=0.02  # 2% annual escalation
        )
        
        # Save new OPEX
        session.add_all(opex_list)
        session.commit()
        
        print(f"✅ Generated {len(opex_list)} new OPEX records")
        
        # Summary by year
        opex_by_year = {}
        for o in opex_list:
            if o.year not in opex_by_year:
                opex_by_year[o.year] = 0
            opex_by_year[o.year] += o.opex_amount
        
        print(f"\n📈 OPEX by Year (with 2% escalation):")
        for year, amount in sorted(opex_by_year.items()):
            print(f"   {year}: ${amount:,.2f}")
        
        # Expected Year 2026 OPEX calculation
        print(f"\n🔍 Expected OPEX Year {start_year} breakdown:")
        expected_total = 0
        for capex in capex_items:
            item = session.query(CapexItem).filter_by(id=capex.capex_item_id).first()
            mappings = session.query(OpexMapping).filter_by(capex_item_id=capex.capex_item_id).all()
            for m in mappings:
                if m.opex_calculation_method == 'PERCENTAGE':
                    opex_base = capex.total_cost * m.opex_rate
                elif m.opex_calculation_method == 'FIXED':
                    opex_base = m.opex_rate
                elif m.opex_calculation_method == 'FIXED_PER_UNIT':
                    opex_base = m.opex_rate * capex.quantity
                else:
                    opex_base = 0
                expected_total += opex_base
                print(f"   {item.name}: ${opex_base:,.2f}")
        
        print(f"   ─────────────────────────")
        print(f"   Total: ${expected_total:,.2f}")
        print(f"   Actual Year {start_year}: ${opex_by_year.get(start_year, 0):,.2f}")
        
        return True

def main():
    print("=" * 60)
    print("REGENERATE OPEX FROM CAPEX SELECTIONS")
    print("=" * 60)
    
    with get_db_session() as session:
        # Get active scenario or first available
        scenario = session.query(Scenario).filter_by(is_active=True).first()
        if not scenario:
            scenario = session.query(Scenario).first()
        
        if scenario:
            regenerate_opex_for_scenario(scenario.id)
        else:
            print("❌ No scenario found")

if __name__ == "__main__":
    main()
