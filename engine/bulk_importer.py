"""
Bulk Scenario Importer
Import scenarios from Excel template with CAPEX configurations
"""
import pandas as pd
from typing import List, Dict, Optional, Tuple
from database.models import (
    Scenario, ScenarioCapex, CapexItem, FiscalTerms, 
    PricingAssumptions, ProductionProfile, ProductionEnhancement
)
from engine.calculator import FinancialCalculator
from engine.opex_generator import OpexGenerator


class BulkScenarioImporter:
    """
    Import multiple scenarios from Excel template
    
    Excel format:
    - Scenario ID: Unique identifier
    - Production: CO2 EOR, CO2 EGR, Supersonic Separator (comma-separated for multiple)
    - Power: CCPP, FWT (comma-separated for multiple)
    - Transportation: Pipeline, VLGC, OWS, STS (comma-separated for multiple)
    - Flaring: FGRS ON, FGRS OFF
    """
    
    # Mapping from Excel values to database CAPEX codes
    CAPEX_MAPPING = {
        # Production
        'CO2 EOR': 'CCUS_EOR',
        'CO2 EGR': 'CCUS_EGR',
        'Supersonic Separator': 'SUPERSONIC',
        # Power
        'CCPP': 'CCPP',
        'FWT': 'FWT',
        # Transportation
        'Pipeline': 'PIPELINE_CO2',
        'VLGC': 'VLGC',
        'OWS': 'OWS',
        'STS': 'STS',
        # Flaring
        'FGRS ON': 'FGRS',
        'FGRS OFF': None,  # No CAPEX item selected
    }
    
    # Default quantities for each CAPEX item
    DEFAULT_QUANTITIES = {
        'CCUS_EOR': 1,
        'CCUS_EGR': 1,
        'SUPERSONIC': 1,
        'CCPP': 1,
        'FWT': 1,
        'PIPELINE_CO2': 30,  # 30 km default
        'VLGC': 1,
        'OWS': 1,
        'STS': 1,
        'FGRS': 1,
    }
    
    def __init__(self, session):
        self.session = session
        self._load_capex_items()
        self._load_defaults()
    
    def _load_capex_items(self):
        """Load CAPEX items from database"""
        self.capex_items = {}
        items = self.session.query(CapexItem).filter_by(is_active=True).all()
        for item in items:
            self.capex_items[item.code] = item
    
    def _load_defaults(self):
        """Load default fiscal terms, pricing, profile, enhancement"""
        self.fiscal_terms = self.session.query(FiscalTerms).first()
        self.pricing = self.session.query(PricingAssumptions).first()
        self.profile = self.session.query(ProductionProfile).first()
        self.enhancement = self.session.query(ProductionEnhancement).first()
        
        if not all([self.fiscal_terms, self.pricing, self.profile]):
            raise ValueError("Default fiscal terms, pricing, or production profile not found in database")
    
    def parse_excel_row(self, row: pd.Series) -> Dict[str, List[str]]:
        """
        Parse a single Excel row to extract CAPEX selections
        
        Args:
            row: pandas Series representing one scenario row
            
        Returns:
            Dictionary with category -> list of CAPEX codes
        """
        capex_selections = {
            'production': [],
            'power': [],
            'transportation': [],
            'flaring': []
        }
        
        # Parse Production column
        if pd.notna(row.get('Production')):
            items = [x.strip() for x in str(row['Production']).split(',')]
            for item in items:
                code = self.CAPEX_MAPPING.get(item)
                if code:
                    capex_selections['production'].append(code)
        
        # Parse Power column
        if pd.notna(row.get('Power')):
            items = [x.strip() for x in str(row['Power']).split(',')]
            for item in items:
                code = self.CAPEX_MAPPING.get(item)
                if code:
                    capex_selections['power'].append(code)
        
        # Parse Transportation column
        if pd.notna(row.get('Transportation')):
            items = [x.strip() for x in str(row['Transportation']).split(',')]
            for item in items:
                code = self.CAPEX_MAPPING.get(item)
                if code:
                    capex_selections['transportation'].append(code)
        
        # Parse Flaring column
        if pd.notna(row.get('Flaring')):
            flaring_val = str(row['Flaring']).strip()
            code = self.CAPEX_MAPPING.get(flaring_val)
            if code:
                capex_selections['flaring'].append(code)
        
        return capex_selections
    
    def generate_scenario_name(self, row: pd.Series, scenario_id: int) -> str:
        """Generate descriptive scenario name from selections"""
        parts = []
        
        if pd.notna(row.get('Production')):
            parts.append(str(row['Production']))
        if pd.notna(row.get('Power')):
            parts.append(str(row['Power']))
        if pd.notna(row.get('Transportation')):
            parts.append(str(row['Transportation']))
        if pd.notna(row.get('Flaring')):
            parts.append(str(row['Flaring']))
        
        if parts:
            name = f"S{scenario_id}: {' | '.join(parts)}"
        else:
            name = f"Scenario {scenario_id}"
        
        # Truncate if too long
        if len(name) > 200:
            name = name[:197] + "..."
        
        return name
    
    def create_scenario_from_row(
        self, 
        row: pd.Series, 
        custom_quantities: Optional[Dict[str, float]] = None,
        calculate: bool = True
    ) -> Tuple[Scenario, Dict]:
        """
        Create a scenario from Excel row
        
        Args:
            row: pandas Series with scenario configuration
            custom_quantities: Optional custom quantities for CAPEX items
            calculate: Whether to run financial calculations
            
        Returns:
            Tuple of (Scenario object, result info dict)
        """
        scenario_id = int(row['Scenario ID'])
        capex_selections = self.parse_excel_row(row)
        
        # Generate name and description
        name = self.generate_scenario_name(row, scenario_id)
        description = f"Bulk imported scenario #{scenario_id}"
        
        # Check if scenario with this excel_id already exists
        existing = self.session.query(Scenario).filter(
            Scenario.name.like(f"S{scenario_id}:%")
        ).first()
        
        if existing:
            return existing, {'status': 'skipped', 'reason': 'Already exists', 'scenario_id': existing.id}
        
        # Create scenario
        scenario = Scenario(
            name=name,
            description=description,
            production_profile_id=self.profile.id,
            fiscal_terms_id=self.fiscal_terms.id,
            pricing_assumptions_id=self.pricing.id,
            production_enhancement_id=self.enhancement.id if self.enhancement else None,
            created_by='BulkImporter',
            is_active=True
        )
        self.session.add(scenario)
        self.session.flush()
        
        # Add CAPEX items
        all_codes = []
        for category, codes in capex_selections.items():
            all_codes.extend(codes)
        
        total_capex = 0
        for code in all_codes:
            capex_item = self.capex_items.get(code)
            if capex_item:
                quantity = (custom_quantities or {}).get(code, self.DEFAULT_QUANTITIES.get(code, 1))
                total_cost = capex_item.unit_cost * quantity
                total_capex += total_cost
                
                scenario_capex = ScenarioCapex(
                    scenario_id=scenario.id,
                    capex_item_id=capex_item.id,
                    quantity=quantity,
                    unit_cost=capex_item.unit_cost,
                    total_cost=total_cost
                )
                self.session.add(scenario_capex)
        
        self.session.commit()
        
        # Generate OPEX
        opex_gen = OpexGenerator(self.session)
        opex_gen.save_opex_for_scenario(
            scenario.id, 
            self.fiscal_terms.project_start_year, 
            self.fiscal_terms.project_end_year, 
            escalation_rate=0.02
        )
        
        # Calculate financials if requested
        if calculate:
            calculator = FinancialCalculator(scenario, self.session)
            calculator.save_calculations()
        
        return scenario, {
            'status': 'created',
            'scenario_id': scenario.id,
            'name': name,
            'capex_items': all_codes,
            'total_capex': total_capex
        }
    
    def import_from_excel(
        self, 
        excel_path: str, 
        scenario_ids: Optional[List[int]] = None,
        limit: Optional[int] = None,
        calculate: bool = True,
        progress_callback = None
    ) -> Dict:
        """
        Import scenarios from Excel file
        
        Args:
            excel_path: Path to Excel file
            scenario_ids: Optional list of specific scenario IDs to import
            limit: Optional limit on number of scenarios to import
            calculate: Whether to run financial calculations
            progress_callback: Optional callback function for progress updates
            
        Returns:
            Dictionary with import results
        """
        df = pd.read_excel(excel_path)
        
        # Filter by scenario_ids if specified
        if scenario_ids:
            df = df[df['Scenario ID'].isin(scenario_ids)]
        
        # Apply limit
        if limit:
            df = df.head(limit)
        
        results = {
            'total': len(df),
            'created': 0,
            'skipped': 0,
            'errors': 0,
            'scenarios': []
        }
        
        for idx, row in df.iterrows():
            try:
                if progress_callback:
                    progress_callback(idx + 1, len(df), f"Processing scenario {row['Scenario ID']}")
                
                scenario, info = self.create_scenario_from_row(row, calculate=calculate)
                results['scenarios'].append(info)
                
                if info['status'] == 'created':
                    results['created'] += 1
                else:
                    results['skipped'] += 1
                    
            except Exception as e:
                results['errors'] += 1
                results['scenarios'].append({
                    'status': 'error',
                    'scenario_id': row['Scenario ID'],
                    'error': str(e)
                })
        
        return results
    
    def preview_import(self, excel_path: str, limit: int = 10) -> pd.DataFrame:
        """
        Preview what would be imported without creating scenarios
        
        Args:
            excel_path: Path to Excel file
            limit: Number of rows to preview
            
        Returns:
            DataFrame with preview information
        """
        df = pd.read_excel(excel_path).head(limit)
        
        preview_data = []
        for _, row in df.iterrows():
            capex_selections = self.parse_excel_row(row)
            all_codes = []
            for codes in capex_selections.values():
                all_codes.extend(codes)
            
            # Calculate total CAPEX
            total_capex = 0
            for code in all_codes:
                item = self.capex_items.get(code)
                if item:
                    qty = self.DEFAULT_QUANTITIES.get(code, 1)
                    total_capex += item.unit_cost * qty
            
            preview_data.append({
                'Scenario ID': row['Scenario ID'],
                'Name': self.generate_scenario_name(row, row['Scenario ID']),
                'CAPEX Items': ', '.join(all_codes) if all_codes else 'None',
                'Item Count': len(all_codes),
                'Est. Total CAPEX': f"${total_capex:,.0f}"
            })
        
        return pd.DataFrame(preview_data)


def import_scenarios_from_excel(
    excel_path: str,
    scenario_ids: Optional[List[int]] = None,
    limit: Optional[int] = None,
    calculate: bool = True
) -> Dict:
    """
    Convenience function to import scenarios from Excel
    
    Args:
        excel_path: Path to Excel file
        scenario_ids: Optional list of specific scenario IDs to import
        limit: Optional limit on number of scenarios
        calculate: Whether to run financial calculations
        
    Returns:
        Import results dictionary
    """
    from database.connection import get_db_session
    
    with get_db_session() as session:
        importer = BulkScenarioImporter(session)
        return importer.import_from_excel(
            excel_path, 
            scenario_ids=scenario_ids, 
            limit=limit,
            calculate=calculate
        )
