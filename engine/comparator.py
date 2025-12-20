"""
Scenario Comparison and Ranking Engine
"""
from typing import List, Dict
import pandas as pd
from sqlalchemy import func
from database.models import Scenario, ScenarioMetrics, ScenarioComparison, ComparisonScenario, CalculationResult

class ScenarioComparator:
    """
    Compares multiple scenarios and provides recommendations
    """
    
    def __init__(self, session):
        self.session = session
    
    def get_scenario_metrics_df(self, scenario_ids: List[int]) -> pd.DataFrame:
        """
        Get scenario metrics as a DataFrame using optimized batch query
        
        Args:
            scenario_ids: List of scenario IDs to compare
            
        Returns:
            DataFrame with scenario metrics
        """
        # OPTIMIZED: Single batch query with JOIN instead of N+1 queries
        results = self.session.query(
            Scenario.id,
            Scenario.name,
            ScenarioMetrics.total_capex,
            ScenarioMetrics.total_opex,
            ScenarioMetrics.total_revenue,
            ScenarioMetrics.total_contractor_share,
            ScenarioMetrics.total_government_take,
            ScenarioMetrics.npv,
            ScenarioMetrics.irr,
            ScenarioMetrics.payback_period_years,
            ScenarioMetrics.asr_amount
        ).join(
            ScenarioMetrics, Scenario.id == ScenarioMetrics.scenario_id
        ).filter(
            Scenario.id.in_(scenario_ids)
        ).all()
        
        scenarios = []
        for r in results:
            scenarios.append({
                'scenario_id': r[0],
                'scenario_name': r[1],
                'total_capex': r[2],
                'total_opex': r[3],
                'total_revenue': r[4],
                'total_contractor_share': r[5],
                'total_government_take': r[6],
                'npv': r[7],
                'irr': r[8],
                'payback_period': r[9],
                'asr_amount': r[10]
            })
        
        return pd.DataFrame(scenarios)
    
    def calculate_scenario_score(self, metrics: ScenarioMetrics) -> float:
        """
        Calculate a weighted score for scenario ranking
        
        Scoring criteria:
        - NPV (40%): Higher is better
        - Total Contractor Share (30%): Higher is better
        - CAPEX (15%): Lower is better (inverted)
        - OPEX (15%): Lower is better (inverted)
        
        Args:
            metrics: ScenarioMetrics object
            
        Returns:
            Weighted score (0-100)
        """
        # Normalize values (will be done relative to all scenarios in comparison)
        return 0  # Placeholder - will be calculated in rank_scenarios
    
    def rank_scenarios(self, scenario_ids: List[int]) -> List[Dict]:
        """
        Rank scenarios based on multiple criteria
        
        Scoring Weights (Total = 100%):
        - NPV: 30% (Higher is better)
        - Contractor Share: 25% (Higher is better)
        - IRR: 15% (Higher is better)
        - Payback Period: 10% (Lower is better)
        - CAPEX: 10% (Lower is better)
        - OPEX: 10% (Lower is better)
        
        Args:
            scenario_ids: List of scenario IDs to compare
            
        Returns:
            List of dictionaries with ranked scenarios
        """
        df = self.get_scenario_metrics_df(scenario_ids)
        
        if df.empty:
            return []
        
        # Normalize metrics for scoring (0-1 scale)
        
        # 1. NPV - Higher is better (30%)
        if df['npv'].max() != df['npv'].min():
            df['npv_score'] = (df['npv'] - df['npv'].min()) / (df['npv'].max() - df['npv'].min())
        else:
            df['npv_score'] = 1.0
        
        # 2. Contractor Share - Higher is better (25%)
        if df['total_contractor_share'].max() != df['total_contractor_share'].min():
            df['contractor_score'] = (df['total_contractor_share'] - df['total_contractor_share'].min()) / \
                                     (df['total_contractor_share'].max() - df['total_contractor_share'].min())
        else:
            df['contractor_score'] = 1.0
        
        # 3. IRR - Higher is better (15%)
        # CAP IRR at 100% for scoring to handle extreme cases:
        # - IRR > 100% (very high returns) → capped at 100%
        # - IRR = NaN (all positive CFs, instant payback) → treated as 100%
        # This prevents scenarios with tiny CAPEX from dominating unfairly
        IRR_CAP = 1.0  # 100% cap for scoring purposes
        df['irr_capped'] = df['irr'].apply(lambda x: min(x, IRR_CAP) if pd.notna(x) and x > 0 else IRR_CAP if pd.isna(x) else 0)
        
        if df['irr_capped'].max() != df['irr_capped'].min():
            df['irr_score'] = (df['irr_capped'] - df['irr_capped'].min()) / \
                              (df['irr_capped'].max() - df['irr_capped'].min())
        else:
            df['irr_score'] = 1.0
        
        # 4. Payback Period - Lower is better (10%)
        # Handle None/NaN values by filling with maximum (worst case)
        df['payback_filled'] = df['payback_period'].fillna(df['payback_period'].max() if df['payback_period'].notna().any() else 99)
        if df['payback_filled'].max() != df['payback_filled'].min():
            df['payback_score'] = 1 - (df['payback_filled'] - df['payback_filled'].min()) / \
                                  (df['payback_filled'].max() - df['payback_filled'].min())
        else:
            df['payback_score'] = 1.0
        
        # 5. CAPEX - Lower is better (10%)
        if df['total_capex'].max() != df['total_capex'].min():
            df['capex_score'] = 1 - (df['total_capex'] - df['total_capex'].min()) / \
                                (df['total_capex'].max() - df['total_capex'].min())
        else:
            df['capex_score'] = 1.0
        
        # 6. OPEX - Lower is better (10%)
        if df['total_opex'].max() != df['total_opex'].min():
            df['opex_score'] = 1 - (df['total_opex'] - df['total_opex'].min()) / \
                               (df['total_opex'].max() - df['total_opex'].min())
        else:
            df['opex_score'] = 1.0
        
        # Calculate weighted total score (NEW WEIGHTS)
        df['total_score'] = (
            df['npv_score'] * 0.30 +         # NPV: 30%
            df['contractor_score'] * 0.25 +   # Contractor Share: 25%
            df['irr_score'] * 0.15 +          # IRR: 15%
            df['payback_score'] * 0.10 +      # Payback Period: 10%
            df['capex_score'] * 0.10 +        # CAPEX: 10%
            df['opex_score'] * 0.10           # OPEX: 10%
        ) * 100
        
        # Sort by score
        df = df.sort_values('total_score', ascending=False)
        df['rank'] = range(1, len(df) + 1)
        
        return df.to_dict('records')
    
    def get_best_scenario_recommendation(self, scenario_ids: List[int]) -> Dict:
        """
        Get the best scenario with detailed recommendation
        
        Args:
            scenario_ids: List of scenario IDs to compare
            
        Returns:
            Dictionary with recommendation details
        """
        ranked = self.rank_scenarios(scenario_ids)
        
        if not ranked:
            return None
        
        best = ranked[0]
        
        # Generate recommendation text
        reasons = []
        
        # NPV analysis
        if best['npv'] > 0:
            reasons.append(f"Memiliki NPV positif sebesar ${best['npv']:,.2f}, menunjukkan proyek ini menguntungkan dengan discount rate 13%.")
        else:
            reasons.append(f"Perhatian: NPV negatif sebesar ${best['npv']:,.2f}, menunjukkan proyek mungkin tidak menguntungkan.")
        
        # Contractor share analysis
        contractor_percentage = (best['total_contractor_share'] / best['total_revenue'] * 100) if best['total_revenue'] > 0 else 0
        reasons.append(f"Contractor share mencapai ${best['total_contractor_share']:,.2f} ({contractor_percentage:.2f}% dari total revenue).")
        
        # CAPEX efficiency
        capex_opex_ratio = best['total_capex'] / best['total_opex'] if best['total_opex'] > 0 else 0
        if capex_opex_ratio > 5:
            reasons.append(f"CAPEX relatif tinggi (${best['total_capex']:,.2f}) dibanding OPEX, namun ini adalah investasi modal intensif.")
        else:
            reasons.append(f"Rasio CAPEX/OPEX seimbang pada {capex_opex_ratio:.2f}x.")
        
        # Revenue generation
        revenue_to_capex = best['total_revenue'] / best['total_capex'] if best['total_capex'] > 0 else 0
        if revenue_to_capex > 3:
            reasons.append(f"Excellent revenue generation: ${best['total_revenue']:,.2f} revenue dari ${best['total_capex']:,.2f} CAPEX (ratio {revenue_to_capex:.2f}x).")
        
        recommendation = {
            'scenario_id': best['scenario_id'],
            'scenario_name': best['scenario_name'],
            'rank': best['rank'],
            'score': best['total_score'],
            'npv': best['npv'],
            'total_capex': best['total_capex'],
            'total_opex': best['total_opex'],
            'total_revenue': best['total_revenue'],
            'total_contractor_share': best['total_contractor_share'],
            'reasons': reasons,
            'summary': f"Skenario '{best['scenario_name']}' direkomendasikan sebagai pilihan terbaik dengan skor {best['total_score']:.2f}/100."
        }
        
        return recommendation
    
    def compare_scenarios_detailed(self, scenario_ids: List[int]) -> Dict:
        """
        Detailed comparison of scenarios
        
        Args:
            scenario_ids: List of scenario IDs to compare
            
        Returns:
            Dictionary with detailed comparison
        """
        ranked = self.rank_scenarios(scenario_ids)
        best = self.get_best_scenario_recommendation(scenario_ids)
        df = self.get_scenario_metrics_df(scenario_ids)
        
        return {
            'ranked_scenarios': ranked,
            'best_scenario': best,
            'summary_statistics': {
                'avg_npv': df['npv'].mean(),
                'max_npv': df['npv'].max(),
                'min_npv': df['npv'].min(),
                'avg_capex': df['total_capex'].mean(),
                'avg_revenue': df['total_revenue'].mean()
            }
        }
    
    def save_comparison(self, name: str, description: str, scenario_ids: List[int]) -> ScenarioComparison:
        """
        Save comparison results to database
        
        Args:
            name: Comparison name
            description: Comparison description
            scenario_ids: List of scenario IDs
            
        Returns:
            ScenarioComparison object
        """
        # Create comparison
        comparison = ScenarioComparison(
            name=name,
            description=description
        )
        self.session.add(comparison)
        self.session.flush()
        
        # Rank scenarios
        ranked = self.rank_scenarios(scenario_ids)
        
        # Add scenarios to comparison
        for item in ranked:
            comp_scenario = ComparisonScenario(
                comparison_id=comparison.id,
                scenario_id=item['scenario_id'],
                rank=item['rank'],
                score=item['total_score']
            )
            self.session.add(comp_scenario)
        
        self.session.commit()
        
        return comparison
