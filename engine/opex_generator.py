"""
OPEX Generator
Automatically generates OPEX based on selected CAPEX items
"""
from typing import List, Dict
from database.models import ScenarioCapex, ScenarioOpex, OpexMapping, CapexItem

class OpexGenerator:
    """
    Generates OPEX based on CAPEX selections and mapping rules
    """
    
    def __init__(self, session):
        self.session = session
    
    def generate_opex_for_scenario(self, scenario_id: int, start_year: int, end_year: int, escalation_rate: float = 0.02) -> List[ScenarioOpex]:
        """
        Generate OPEX for a scenario based on its CAPEX selections
        Includes 2% annual escalation rate
        
        Args:
            scenario_id: ID of the scenario
            start_year: Project start year
            end_year: Project end year
            escalation_rate: Annual OPEX escalation rate (default 2%)
            
        Returns:
            List of ScenarioOpex objects
        """
        # Get scenario CAPEX items
        scenario_capex = self.session.query(ScenarioCapex).filter_by(
            scenario_id=scenario_id
        ).all()
        
        opex_list = []
        
        for capex in scenario_capex:
            # Get OPEX mappings for this CAPEX item
            opex_mappings = self.session.query(OpexMapping).filter_by(
                capex_item_id=capex.capex_item_id
            ).all()
            
            for mapping in opex_mappings:
                # Determine year range
                year_start = start_year + (mapping.year_start - 1) if mapping.year_start else start_year
                year_end = start_year + (mapping.year_end - 1) if mapping.year_end else end_year
                
                # Calculate base OPEX amount
                if mapping.opex_calculation_method == 'PERCENTAGE':
                    # OPEX = CAPEX × percentage
                    base_opex_amount = capex.total_cost * mapping.opex_rate
                    calc_base_note = f"{mapping.opex_rate*100}% of CAPEX (${capex.total_cost:,.2f})"
                elif mapping.opex_calculation_method == 'FIXED':
                    # FIXED: flat rate per year regardless of quantity (e.g., Pipeline maintenance)
                    # This matches Excel where Pipeline OPEX is $150,000/year regardless of km
                    base_opex_amount = mapping.opex_rate
                    calc_base_note = f"Fixed rate ${mapping.opex_rate:,.2f}/year"
                elif mapping.opex_calculation_method == 'FIXED_PER_UNIT':
                    # FIXED_PER_UNIT: rate × quantity (e.g., OWS at $1,250 × units)
                    base_opex_amount = mapping.opex_rate * capex.quantity
                    calc_base_note = f"Fixed rate ${mapping.opex_rate:,.2f} × {capex.quantity} units"
                else:
                    base_opex_amount = 0
                    calc_base_note = "Unknown method"
                
                # Generate OPEX for each year with escalation
                for year in range(year_start, year_end + 1):
                    year_offset = year - start_year
                    
                    # Apply escalation: OPEX_year = OPEX_base × (1 + escalation)^year_offset
                    escalation_factor = (1 + escalation_rate) ** year_offset
                    opex_amount = base_opex_amount * escalation_factor
                    
                    calc_note = f"{calc_base_note}, escalated {year_offset} years at {escalation_rate*100}%"
                    
                    opex = ScenarioOpex(
                        scenario_id=scenario_id,
                        year=year,
                        opex_name=f"{mapping.opex_name} ({capex.capex_item.name})",
                        opex_amount=opex_amount,
                        calculation_note=calc_note
                    )
                    opex_list.append(opex)
        
        return opex_list
    
    def save_opex_for_scenario(self, scenario_id: int, start_year: int, end_year: int, escalation_rate: float = 0.02):
        """
        Generate and save OPEX to database with escalation
        
        Args:
            scenario_id: ID of the scenario
            start_year: Project start year
            end_year: Project end year
            escalation_rate: Annual OPEX escalation rate (default 2%)
        """
        # Delete existing OPEX
        self.session.query(ScenarioOpex).filter_by(scenario_id=scenario_id).delete()
        
        # Generate new OPEX with escalation
        opex_list = self.generate_opex_for_scenario(scenario_id, start_year, end_year, escalation_rate)
        
        # Save to database
        self.session.add_all(opex_list)
        self.session.commit()
        
        return opex_list
    
    def get_opex_summary_by_year(self, scenario_id: int) -> Dict[int, float]:
        """
        Get OPEX summary grouped by year
        
        Args:
            scenario_id: ID of the scenario
            
        Returns:
            Dictionary with year as key and total OPEX as value
        """
        opex_items = self.session.query(ScenarioOpex).filter_by(
            scenario_id=scenario_id
        ).all()
        
        summary = {}
        for item in opex_items:
            if item.year not in summary:
                summary[item.year] = 0
            summary[item.year] += item.opex_amount
        
        return summary
    
    def get_opex_breakdown(self, scenario_id: int) -> List[Dict]:
        """
        Get detailed OPEX breakdown
        
        Args:
            scenario_id: ID of the scenario
            
        Returns:
            List of dictionaries with OPEX details
        """
        opex_items = self.session.query(ScenarioOpex).filter_by(
            scenario_id=scenario_id
        ).order_by(ScenarioOpex.year, ScenarioOpex.opex_name).all()
        
        breakdown = []
        for item in opex_items:
            breakdown.append({
                'year': item.year,
                'opex_name': item.opex_name,
                'amount': item.opex_amount,
                'calculation_note': item.calculation_note
            })
        
        return breakdown
