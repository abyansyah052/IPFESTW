"""
Export Functionality - Excel and PDF
"""
import pandas as pd
from datetime import datetime
from typing import List, Dict
import os
from database.models import (
    Scenario, ScenarioCapex, ScenarioOpex, CalculationResult, 
    ScenarioMetrics, CapexItem
)

class ExcelExporter:
    """Export scenario results to Excel"""
    
    def __init__(self, session):
        self.session = session
    
    def export_scenario(self, scenario_id: int, output_path: str):
        """
        Export scenario to Excel with multiple sheets
        
        Args:
            scenario_id: ID of the scenario
            output_path: Output file path
        """
        scenario = self.session.query(Scenario).filter_by(id=scenario_id).first()
        
        if not scenario:
            raise ValueError(f"Scenario {scenario_id} not found")
        
        # Create Excel writer
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            # Sheet 1: Scenario Summary
            summary_df = self._create_summary_sheet(scenario)
            summary_df.to_excel(writer, sheet_name='Summary', index=False)
            
            # Sheet 2: CAPEX Details
            capex_df = self._create_capex_sheet(scenario_id)
            capex_df.to_excel(writer, sheet_name='CAPEX', index=False)
            
            # Sheet 3: OPEX Details
            opex_df = self._create_opex_sheet(scenario_id)
            opex_df.to_excel(writer, sheet_name='OPEX', index=False)
            
            # Sheet 4: Annual Calculations
            calc_df = self._create_calculations_sheet(scenario_id)
            calc_df.to_excel(writer, sheet_name='Annual Results', index=False)
            
            # Sheet 5: Metrics
            metrics_df = self._create_metrics_sheet(scenario_id)
            metrics_df.to_excel(writer, sheet_name='Metrics', index=False)
        
        return output_path
    
    def _create_summary_sheet(self, scenario: Scenario) -> pd.DataFrame:
        """Create summary information sheet"""
        metrics = self.session.query(ScenarioMetrics).filter_by(scenario_id=scenario.id).first()
        
        data = {
            'Item': [
                'Scenario Name',
                'Description',
                'Created At',
                'Total CAPEX',
                'Total OPEX',
                'Total Revenue',
                'Total Contractor Share',
                'Total Government Take',
                'NPV (13%)',
                'ASR Amount'
            ],
            'Value': [
                scenario.name,
                scenario.description or '-',
                scenario.created_at.strftime('%Y-%m-%d %H:%M:%S') if scenario.created_at else '-',
                f"${metrics.total_capex:,.2f}" if metrics else '-',
                f"${metrics.total_opex:,.2f}" if metrics else '-',
                f"${metrics.total_revenue:,.2f}" if metrics else '-',
                f"${metrics.total_contractor_share:,.2f}" if metrics else '-',
                f"${metrics.total_government_take:,.2f}" if metrics else '-',
                f"${metrics.npv:,.2f}" if metrics else '-',
                f"${metrics.asr_amount:,.2f}" if metrics else '-'
            ]
        }
        
        return pd.DataFrame(data)
    
    def _create_capex_sheet(self, scenario_id: int) -> pd.DataFrame:
        """Create CAPEX details sheet"""
        capex_items = self.session.query(
            ScenarioCapex, CapexItem
        ).join(
            CapexItem
        ).filter(
            ScenarioCapex.scenario_id == scenario_id
        ).all()
        
        data = []
        for capex, item in capex_items:
            data.append({
                'Category': item.category.name,
                'Subcategory': item.subcategory.name if item.subcategory else '-',
                'Item': item.name,
                'Unit': item.unit,
                'Quantity': capex.quantity,
                'Unit Cost': capex.unit_cost,
                'Total Cost': capex.total_cost,
                'Notes': capex.notes or '-'
            })
        
        df = pd.DataFrame(data)
        if not df.empty:
            # Add total row
            total_row = pd.DataFrame([{
                'Category': 'TOTAL',
                'Subcategory': '',
                'Item': '',
                'Unit': '',
                'Quantity': '',
                'Unit Cost': '',
                'Total Cost': df['Total Cost'].sum(),
                'Notes': ''
            }])
            df = pd.concat([df, total_row], ignore_index=True)
        
        return df
    
    def _create_opex_sheet(self, scenario_id: int) -> pd.DataFrame:
        """Create OPEX details sheet"""
        opex_items = self.session.query(ScenarioOpex).filter_by(
            scenario_id=scenario_id
        ).order_by(ScenarioOpex.year, ScenarioOpex.opex_name).all()
        
        data = []
        for opex in opex_items:
            data.append({
                'Year': opex.year,
                'OPEX Item': opex.opex_name,
                'Amount': opex.opex_amount,
                'Calculation Note': opex.calculation_note or '-'
            })
        
        df = pd.DataFrame(data)
        return df
    
    def _create_calculations_sheet(self, scenario_id: int) -> pd.DataFrame:
        """Create annual calculations sheet"""
        results = self.session.query(CalculationResult).filter_by(
            scenario_id=scenario_id
        ).order_by(CalculationResult.year).all()
        
        data = []
        for r in results:
            data.append({
                'Year': r.year,
                'Oil Production (bbl)': r.oil_production,
                'Gas Production (MMSCF)': r.gas_production_mmscf,
                'Gas Production (MMBTU)': r.gas_production_mmbtu,
                'Oil Revenue': r.oil_revenue,
                'Gas Revenue': r.gas_revenue,
                'Total Revenue': r.total_revenue,
                'Depreciation': r.depreciation,
                'OPEX': r.opex_total,
                'Operating Profit': r.operating_profit,
                'Contractor Share (Pre-tax)': r.contractor_share_pretax,
                'Contractor Tax': r.contractor_tax,
                'Contractor Share (After-tax)': r.contractor_share_aftertax,
                'Government Share (Pre-tax)': r.government_share_pretax,
                'Government Total Take': r.government_total_take,
                'Cash Flow': r.cash_flow,
                'Cumulative Cash Flow': r.cumulative_cash_flow
            })
        
        return pd.DataFrame(data)
    
    def _create_metrics_sheet(self, scenario_id: int) -> pd.DataFrame:
        """Create metrics summary sheet"""
        metrics = self.session.query(ScenarioMetrics).filter_by(scenario_id=scenario_id).first()
        
        if not metrics:
            return pd.DataFrame()
        
        data = {
            'Metric': [
                'Total CAPEX',
                'Total OPEX',
                'Total Revenue',
                'Total Contractor Share (After-tax)',
                'Total Government Take',
                'Net Present Value (NPV)',
                'Abandonment Security Reserve (ASR)',
                'Calculated At'
            ],
            'Value': [
                metrics.total_capex,
                metrics.total_opex,
                metrics.total_revenue,
                metrics.total_contractor_share,
                metrics.total_government_take,
                metrics.npv,
                metrics.asr_amount,
                metrics.calculated_at.strftime('%Y-%m-%d %H:%M:%S') if metrics.calculated_at else '-'
            ]
        }
        
        return pd.DataFrame(data)
    
    def export_comparison(self, scenario_ids: List[int], output_path: str):
        """
        Export scenario comparison to Excel
        
        Args:
            scenario_ids: List of scenario IDs to compare
            output_path: Output file path
        """
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            # Summary comparison
            comparison_df = self._create_comparison_sheet(scenario_ids)
            comparison_df.to_excel(writer, sheet_name='Comparison', index=False)
            
            # Individual scenario sheets
            for scenario_id in scenario_ids:
                scenario = self.session.query(Scenario).filter_by(id=scenario_id).first()
                if scenario:
                    calc_df = self._create_calculations_sheet(scenario_id)
                    sheet_name = f"Scenario {scenario_id}"[:31]  # Excel sheet name limit
                    calc_df.to_excel(writer, sheet_name=sheet_name, index=False)
        
        return output_path
    
    def _create_comparison_sheet(self, scenario_ids: List[int]) -> pd.DataFrame:
        """Create comparison summary sheet"""
        data = []
        
        for scenario_id in scenario_ids:
            scenario = self.session.query(Scenario).filter_by(id=scenario_id).first()
            metrics = self.session.query(ScenarioMetrics).filter_by(scenario_id=scenario_id).first()
            
            if scenario and metrics:
                data.append({
                    'Scenario ID': scenario.id,
                    'Scenario Name': scenario.name,
                    'Total CAPEX': metrics.total_capex,
                    'Total OPEX': metrics.total_opex,
                    'Total Revenue': metrics.total_revenue,
                    'Contractor Share': metrics.total_contractor_share,
                    'Government Take': metrics.total_government_take,
                    'NPV': metrics.npv,
                    'ASR': metrics.asr_amount
                })
        
        return pd.DataFrame(data)


def ensure_export_directory():
    """Ensure export directory exists"""
    export_dir = 'exports'
    if not os.path.exists(export_dir):
        os.makedirs(export_dir)
    return export_dir


def generate_filename(scenario_name: str, file_type: str = 'xlsx') -> str:
    """Generate unique filename for export"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    safe_name = "".join(c for c in scenario_name if c.isalnum() or c in (' ', '-', '_')).strip()
    safe_name = safe_name.replace(' ', '_')
    return f"{safe_name}_{timestamp}.{file_type}"
