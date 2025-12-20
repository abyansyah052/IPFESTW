"""
Main Streamlit Application for Financial Scenario Testing
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.connection import get_db_session
from database.models import (
    Scenario, CapexCategory, CapexItem, CapexSubcategory, ScenarioCapex,
    FiscalTerms, PricingAssumptions, ProductionProfile, ProductionData, ProductionEnhancement,
    ScenarioOpex, CalculationResult, ScenarioMetrics
)
from engine.calculator import FinancialCalculator
from engine.opex_generator import OpexGenerator
from engine.comparator import ScenarioComparator
from utils.export import ExcelExporter, ensure_export_directory, generate_filename

# Page config
st.set_page_config(
    page_title="Financial Scenario Testing",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .stButton>button {
        width: 100%;
    }
    /* Fix sidebar navigation to not look like bullet points */
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] ul {
        list-style-type: none;
        padding-left: 0;
    }
    [data-testid="stSidebar"] .row-widget.stRadio > div {
        gap: 0.5rem;
    }
    [data-testid="stSidebar"] .row-widget.stRadio > div > label {
        padding: 0.5rem 1rem;
        border-radius: 0.5rem;
        width: 100%;
        cursor: pointer;
    }
    [data-testid="stSidebar"] .row-widget.stRadio > div > label:hover {
        background-color: #f0f2f6;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'current_scenario' not in st.session_state:
    st.session_state.current_scenario = None
if 'selected_capex' not in st.session_state:
    st.session_state.selected_capex = {}
if 'scenarios_list' not in st.session_state:
    st.session_state.scenarios_list = []
if 'comparison_data' not in st.session_state:
    st.session_state.comparison_data = None
if 'scenarios_page' not in st.session_state:
    st.session_state.scenarios_page = 0

@st.cache_data(ttl=300)
def get_categories_cached():
    """Cached query for CAPEX categories"""
    with get_db_session() as session:
        return [(cat.id, cat.code, cat.name, cat.sort_order) 
                for cat in session.query(CapexCategory).order_by(CapexCategory.sort_order).all()]

@st.cache_data(ttl=300)
def get_items_for_category_cached(category_id):
    """Cached query for CAPEX items"""
    with get_db_session() as session:
        items = session.query(CapexItem).filter_by(
            category_id=category_id, is_active=True
        ).all()
        return [(item.id, item.code, item.name, item.unit, item.unit_cost, 
                 item.subcategory.name if item.subcategory else "General")
                for item in items]

@st.cache_data(ttl=60)
def get_scenarios_list_cached(page: int = 0, per_page: int = 50):
    """Cached paginated query for scenarios - optimized for hundreds of scenarios"""
    with get_db_session() as session:
        total = session.query(Scenario).filter_by(is_active=True).count()
        scenarios = session.query(Scenario).filter_by(is_active=True)\
            .order_by(Scenario.created_at.desc())\
            .offset(page * per_page).limit(per_page).all()
        return {
            'total': total,
            'page': page,
            'per_page': per_page,
            'total_pages': (total + per_page - 1) // per_page,
            'scenarios': [(s.id, s.name, s.description, s.created_at) for s in scenarios]
        }

@st.cache_data(ttl=60)
def get_scenario_metrics_cached(scenario_id: int):
    """Cached query for scenario metrics"""
    with get_db_session() as session:
        from sqlalchemy import text
        metrics = session.query(ScenarioMetrics).filter_by(scenario_id=scenario_id).first()
        if metrics:
            ptcf = session.execute(text(
                'SELECT SUM(contractor_tax) FROM calculation_results WHERE scenario_id = :sid'
            ), {'sid': scenario_id}).fetchone()[0] or 0
            return {
                'npv': float(metrics.npv) if metrics.npv else 0,
                'irr': float(metrics.irr) if metrics.irr else 0,
                'payback': float(metrics.payback_period_years) if metrics.payback_period_years else 0,
                'total_revenue': float(metrics.total_revenue) if metrics.total_revenue else 0,
                'total_capex': float(metrics.total_capex) if metrics.total_capex else 0,
                'total_opex': float(metrics.total_opex) if metrics.total_opex else 0,
                'contractor_share': float(metrics.total_contractor_share) if metrics.total_contractor_share else 0,
                'government_take': float(metrics.total_government_take) if metrics.total_government_take else 0,
                'asr': float(metrics.asr_amount) if metrics.asr_amount else 0,
                'contractor_ptcf': float(ptcf)
            }
        return None

def initialize_default_data(session):
    """Initialize default fiscal terms, pricing, and production profile if not exists"""
    # Check if fiscal terms exist
    fiscal = session.query(FiscalTerms).filter_by(is_active=True).first()
    if not fiscal:
        fiscal = FiscalTerms(
            name='Default PSC Terms',
            version='v1.0',
            gov_oil_pretax=0.3277,
            gov_gas_pretax=0.3277,
            contractor_oil_pretax=0.6723,
            contractor_gas_pretax=0.6723,
            gov_oil_posttax=0.60,
            gov_gas_posttax=0.60,
            contractor_oil_posttax=0.40,
            contractor_gas_posttax=0.40,
            contractor_tax_rate=0.405,
            dmo_volume=0.25,
            dmo_fee=1.00,
            dmo_holiday=0,
            discount_rate=0.13,
            depreciation_life=5,
            depreciation_method='DDB',
            depreciation_factor=0.25,
            asr_rate=0.05,
            salvage_value=0,
            opex_escalation_rate=0.02,
            project_start_year=2026,
            project_end_year=2037,
            is_active=True
        )
        session.add(fiscal)
    
    # Check if pricing exists
    pricing = session.query(PricingAssumptions).filter_by(is_active=True).first()
    if not pricing:
        pricing = PricingAssumptions(
            name='Base Case Pricing',
            version='v1.0',
            oil_price=60.0,
            gas_price=5.5,
            usd_to_idr=16500,
            gross_heating_value=1200,
            mmscf_to_mmbtu=1027,
            co2_production_rate=0.20,
            carbon_tax=2.00,
            emission_factor=53.06,
            ghv_condensate=5.8,
            barrel_to_liter=158.987,
            working_days=220,
            currency='USD',
            is_active=True
        )
        session.add(pricing)
    
    # Check if enhancement exists
    enhancement = session.query(ProductionEnhancement).filter_by(is_active=True).first()
    if not enhancement:
        enhancement = ProductionEnhancement(
            name='Default Enhancement Rates',
            eor_enhancement_rate=0.20,
            egr_enhancement_rate=0.25,
            is_active=True
        )
        session.add(enhancement)
    
    # Check if production profile exists
    profile = session.query(ProductionProfile).filter_by(is_active=True).first()
    if not profile:
        profile = ProductionProfile(
            name='Base Production Profile',
            description='Actual production profile 2026-2037 from data',
            project_start_year=2026,
            project_duration=12,
            is_active=True
        )
        session.add(profile)
        session.flush()
        
        # Add actual production data from revised dataset (BOPD and MMSCFD)
        production_data_list = [
            ProductionData(profile_id=profile.id, year=2026, condensate_rate_bopd=1257.49, gas_rate_mmscfd=0.36781),
            ProductionData(profile_id=profile.id, year=2027, condensate_rate_bopd=2394.10, gas_rate_mmscfd=0.71769),
            ProductionData(profile_id=profile.id, year=2028, condensate_rate_bopd=2199.95, gas_rate_mmscfd=1.49133),
            ProductionData(profile_id=profile.id, year=2029, condensate_rate_bopd=2063.88, gas_rate_mmscfd=1.73993),
            ProductionData(profile_id=profile.id, year=2030, condensate_rate_bopd=1949.47, gas_rate_mmscfd=2.21602),
            ProductionData(profile_id=profile.id, year=2031, condensate_rate_bopd=2052.16, gas_rate_mmscfd=2.28278),
            ProductionData(profile_id=profile.id, year=2032, condensate_rate_bopd=1622.27, gas_rate_mmscfd=1.47658),
            ProductionData(profile_id=profile.id, year=2033, condensate_rate_bopd=1636.66, gas_rate_mmscfd=1.67256),
            ProductionData(profile_id=profile.id, year=2034, condensate_rate_bopd=1142.45, gas_rate_mmscfd=1.56182),
            ProductionData(profile_id=profile.id, year=2035, condensate_rate_bopd=1258.40, gas_rate_mmscfd=1.07175),
            ProductionData(profile_id=profile.id, year=2036, condensate_rate_bopd=1158.71, gas_rate_mmscfd=0.85615),
            ProductionData(profile_id=profile.id, year=2037, condensate_rate_bopd=888.79, gas_rate_mmscfd=0.76917),
        ]
        session.add_all(production_data_list)
    
    session.commit()
    return fiscal, pricing, enhancement, profile

def render_capex_selection():
    """Render CAPEX selection interface"""
    st.subheader("CAPEX Selection")
    st.markdown("Select items to include in your scenario. All costs are in USD.")
    st.markdown("---")
    
    with get_db_session() as session:
        categories = session.query(CapexCategory).order_by(CapexCategory.sort_order).all()
        
        selected_items = {}
        
        for category in categories:
            with st.expander(f"**{category.name}**", expanded=True):
                # Get items for this category
                items = session.query(CapexItem).filter_by(
                    category_id=category.id,
                    is_active=True
                ).all()
                
                # Group by subcategory
                items_by_subcat = {}
                for item in items:
                    subcat_name = item.subcategory.name if item.subcategory else "General"
                    if subcat_name not in items_by_subcat:
                        items_by_subcat[subcat_name] = []
                    items_by_subcat[subcat_name].append(item)
                
                # Special handling for Transportation
                if category.code == 'TRANS':
                    transport_methods = st.multiselect(
                        "Select Transportation Method(s):",
                        ["Pipeline", "Shipping"],
                        default=["Pipeline"],
                        key=f"transport_{category.id}",
                        help="You can select both Pipeline and Shipping"
                    )
                    
                    # Collect items from all selected methods
                    items_to_show = []
                    for method in transport_methods:
                        items_to_show.extend(items_by_subcat.get(method, []))
                    
                    for item in items_to_show:
                        col1, col2 = st.columns([3, 1])
                        with col1:
                            st.markdown(f"**{item.name}**")
                            st.caption(f"Unit: {item.unit} | Cost: ${item.unit_cost:,.2f}")
                        with col2:
                            # Special multiplier for pipeline (30km)
                            if item.code == 'PIPELINE_CO2':
                                default_qty = 30
                                qty = st.number_input(
                                    "km",
                                    min_value=0,
                                    value=default_qty,
                                    step=1,
                                    key=f"qty_{item.id}",
                                    help="Pipeline length in kilometers"
                                )
                            else:
                                qty = st.number_input(
                                    "Qty",
                                    min_value=0,
                                    value=1,
                                    step=1,
                                    key=f"qty_{item.id}"
                                )
                            if qty > 0:
                                selected_items[item.id] = qty
                        st.markdown("")
                else:
                    # Normal display for other categories
                    for subcat_name, items_list in items_by_subcat.items():
                        if len(items_by_subcat) > 1:
                            st.markdown(f"**{subcat_name}**")
                        
                        for item in items_list:
                            col1, col2 = st.columns([3, 1])
                            with col1:
                                st.markdown(f"**{item.name}**")
                                st.caption(f"Unit: {item.unit} | Cost: ${item.unit_cost:,.2f}")
                            with col2:
                                qty = st.number_input(
                                    "Qty",
                                    min_value=0,
                                    value=1,
                                    step=1,
                                    key=f"qty_{item.id}"
                                )
                                if qty > 0:
                                    selected_items[item.id] = qty
                            st.markdown("")
        
        return selected_items

def create_scenario_from_selection(session, scenario_name, description, selected_items):
    """Create a new scenario from selected CAPEX items"""
    # Get default parameters
    fiscal, pricing, enhancement, profile = initialize_default_data(session)
    
    # Create scenario
    scenario = Scenario(
        name=scenario_name,
        description=description,
        production_profile_id=profile.id,
        fiscal_terms_id=fiscal.id,
        pricing_assumptions_id=pricing.id,
        production_enhancement_id=enhancement.id,
        created_by='User',
        is_active=True
    )
    session.add(scenario)
    session.flush()
    
    # Add CAPEX items
    for item_id, quantity in selected_items.items():
        capex_item = session.query(CapexItem).filter_by(id=item_id).first()
        if capex_item:
            total_cost = capex_item.unit_cost * quantity
            scenario_capex = ScenarioCapex(
                scenario_id=scenario.id,
                capex_item_id=item_id,
                quantity=quantity,
                unit_cost=capex_item.unit_cost,
                total_cost=total_cost
            )
            session.add(scenario_capex)
    
    session.commit()
    
    # Generate OPEX with 2% escalation
    opex_gen = OpexGenerator(session)
    opex_gen.save_opex_for_scenario(scenario.id, fiscal.project_start_year, fiscal.project_end_year, escalation_rate=0.02)
    
    # Calculate financials
    calculator = FinancialCalculator(scenario, session)
    calculator.save_calculations()
    
    return scenario

def display_scenario_results(scenario_id):
    """Display scenario calculation results"""
    with get_db_session() as session:
        scenario = session.query(Scenario).filter_by(id=scenario_id).first()
        
        if not scenario:
            st.error("Scenario not found")
            return
        
        st.subheader(f"Results: {scenario.name}")
        
        if scenario.description:
            st.info(scenario.description)
        
        # Get metrics
        from database.models import ScenarioMetrics, CalculationResult
        metrics = session.query(ScenarioMetrics).filter_by(scenario_id=scenario_id).first()
        
        if not metrics:
            st.warning("No calculation results available. Please calculate first.")
            return
        
        # Get Contractor PTCF (total tax paid)
        from sqlalchemy import text
        ptcf_result = session.execute(text(
            'SELECT SUM(contractor_tax) FROM calculation_results WHERE scenario_id = :sid'
        ), {'sid': scenario_id}).fetchone()
        contractor_ptcf = float(ptcf_result[0]) if ptcf_result[0] else 0
        
        # Display key metrics - Row 1
        st.markdown("### 📊 Key Financial Metrics")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            npv_color = "normal" if metrics.npv > 0 else "inverse"
            st.metric("NPV (13%)", f"${metrics.npv:,.0f}", delta_color=npv_color)
        with col2:
            irr_val = metrics.irr * 100 if metrics.irr else 0
            irr_color = "normal" if irr_val > 0 else "inverse"
            st.metric("IRR", f"{irr_val:.2f}%", delta_color=irr_color)
        with col3:
            payback = metrics.payback_period_years if metrics.payback_period_years else 0
            st.metric("Payback Period", f"{payback:.3f} years")
        with col4:
            st.metric("Gross Revenue", f"${metrics.total_revenue:,.0f}")
        
        # Row 2 - Contractor & Government
        col5, col6, col7, col8 = st.columns(4)
        
        with col5:
            st.metric("Contractor Take", f"${metrics.total_contractor_share:,.0f}")
        with col6:
            st.metric("Government Take", f"${metrics.total_government_take:,.0f}")
        with col7:
            st.metric("Contractor PTCF (Tax)", f"${contractor_ptcf:,.0f}")
        with col8:
            roi = ((metrics.total_contractor_share - metrics.total_capex) / metrics.total_capex * 100) if metrics.total_capex > 0 else 0
            st.metric("ROI", f"{roi:.2f}%")
        
        # Row 3 - Investment Details
        col9, col10, col11, col12 = st.columns(4)
        
        with col9:
            st.metric("Total CAPEX", f"${metrics.total_capex:,.0f}")
        with col10:
            st.metric("Total OPEX", f"${metrics.total_opex:,.0f}")
        with col11:
            st.metric("ASR (5%)", f"${metrics.asr_amount:,.0f}")
        with col12:
            # Profit margin
            profit_margin = (metrics.total_contractor_share / metrics.total_revenue * 100) if metrics.total_revenue > 0 else 0
            st.metric("Profit Margin", f"{profit_margin:.2f}%")
        
        # Tabs for detailed results
        tab1, tab2, tab3, tab4 = st.tabs(["Annual Results", "CAPEX/OPEX", "Visualizations", "Summary"])
        
        with tab1:
            st.subheader("Annual Financial Results")
            results = session.query(CalculationResult).filter_by(
                scenario_id=scenario_id
            ).order_by(CalculationResult.year).all()
            
            results_data = []
            for r in results:
                results_data.append({
                    'Year': r.year,
                    'Oil (bbl)': f"{r.oil_production:,.0f}",
                    'Gas (MMBTU)': f"{r.gas_production_mmbtu:,.0f}",
                    'Revenue': f"${r.total_revenue:,.0f}",
                    'Depreciation': f"${r.depreciation:,.0f}",
                    'OPEX': f"${r.opex_total:,.0f}",
                    'Operating Profit': f"${r.operating_profit:,.0f}",
                    'Contractor (After-tax)': f"${r.contractor_share_aftertax:,.0f}",
                    'Government Take': f"${r.government_total_take:,.0f}",
                    'Cumulative CF': f"${r.cumulative_cash_flow:,.0f}"
                })
            
            st.dataframe(pd.DataFrame(results_data), width='stretch', height=400)
        
        with tab2:
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("CAPEX Breakdown")
                capex_items = session.query(ScenarioCapex, CapexItem).join(
                    CapexItem
                ).filter(
                    ScenarioCapex.scenario_id == scenario_id
                ).all()
                
                capex_data = []
                for capex, item in capex_items:
                    capex_data.append({
                        'Item': item.name,
                        'Quantity': capex.quantity,
                        'Unit Cost': f"${capex.unit_cost:,.2f}",
                        'Total': f"${capex.total_cost:,.0f}"
                    })
                
                st.dataframe(pd.DataFrame(capex_data), width='stretch')
            
            with col2:
                st.subheader("OPEX Summary by Year")
                opex_gen = OpexGenerator(session)
                opex_summary = opex_gen.get_opex_summary_by_year(scenario_id)
                
                opex_data = [{'Year': year, 'Total OPEX': f"${amount:,.0f}"} 
                            for year, amount in sorted(opex_summary.items())]
                
                st.dataframe(pd.DataFrame(opex_data), width='stretch', height=400)
        
        with tab3:
            st.subheader("Financial Visualizations")
            
            results = session.query(CalculationResult).filter_by(
                scenario_id=scenario_id
            ).order_by(CalculationResult.year).all()
            
            # Revenue vs Costs
            fig1 = go.Figure()
            years = [r.year for r in results]
            fig1.add_trace(go.Bar(name='Revenue', x=years, y=[r.total_revenue for r in results]))
            fig1.add_trace(go.Bar(name='OPEX', x=years, y=[r.opex_total for r in results]))
            fig1.add_trace(go.Bar(name='Depreciation', x=years, y=[r.depreciation for r in results]))
            fig1.update_layout(
                title='Revenue vs Costs',
                xaxis_title='Year',
                yaxis_title='USD',
                barmode='group',
                height=400
            )
            st.plotly_chart(fig1, width="stretch")
            
            # Cumulative Cash Flow
            fig2 = go.Figure()
            fig2.add_trace(go.Scatter(
                x=years,
                y=[r.cumulative_cash_flow for r in results],
                mode='lines+markers',
                name='Cumulative Cash Flow',
                line=dict(color='green', width=3)
            ))
            fig2.update_layout(
                title='Cumulative Cash Flow',
                xaxis_title='Year',
                yaxis_title='USD',
                height=400
            )
            st.plotly_chart(fig2, width="stretch")
            
            # PSC Split
            total_contractor = sum(r.contractor_share_aftertax for r in results)
            total_government = sum(r.government_total_take for r in results)
            
            fig3 = go.Figure(data=[go.Pie(
                labels=['Contractor (After-tax)', 'Government Total Take'],
                values=[total_contractor, total_government],
                hole=.3
            )])
            fig3.update_layout(title='Production Sharing Split', height=400)
            st.plotly_chart(fig3, width="stretch")
        
        with tab4:
            st.subheader("Scenario Summary Report")
            
            st.markdown(f"""
            **Scenario:** {scenario.name}
            
            **Description:** {scenario.description or 'N/A'}
            
            **Created:** {scenario.created_at.strftime('%Y-%m-%d %H:%M') if scenario.created_at else 'N/A'}
            
            ---
            
            ### Financial Summary
            
            - **Total CAPEX:** ${metrics.total_capex:,.2f}
            - **Total OPEX:** ${metrics.total_opex:,.2f}
            - **Total Revenue:** ${metrics.total_revenue:,.2f}
            - **Net Present Value (NPV @ 13%):** ${metrics.npv:,.2f}
            - **Abandonment Security Reserve (ASR):** ${metrics.asr_amount:,.2f}
            
            ### Stakeholder Distribution
            
            - **Total Contractor Share (After-tax):** ${metrics.total_contractor_share:,.2f}
            - **Total Government Take:** ${metrics.total_government_take:,.2f}
            
            ### Performance Indicators
            
            - **Return on Investment (ROI):** {((metrics.total_contractor_share - metrics.total_capex) / metrics.total_capex * 100):.2f}%
            - **CAPEX/OPEX Ratio:** {(metrics.total_capex / metrics.total_opex):.2f}x
            - **Revenue/CAPEX Ratio:** {(metrics.total_revenue / metrics.total_capex):.2f}x
            """)

def compare_scenarios_page():
    """Scenario comparison page with bulk compare support"""
    st.title("Compare Scenarios")
    
    with get_db_session() as session:
        from sqlalchemy import func
        
        scenarios = session.query(Scenario).filter_by(is_active=True).order_by(Scenario.id).all()
        
        if len(scenarios) < 2:
            st.warning("You need at least 2 scenarios to compare. Please create more scenarios first.")
            return
        
        # Bulk selection options
        st.subheader("Select Scenarios to Compare")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            select_mode = st.radio(
                "Selection Mode",
                ["Manual Select", "Select Range", "Select All"],
                horizontal=True
            )
        
        selected_scenarios = []
        
        if select_mode == "Select All":
            selected_scenarios = scenarios
            st.success(f"All {len(scenarios)} scenarios selected")
            
        elif select_mode == "Select Range":
            col_a, col_b = st.columns(2)
            with col_a:
                start_idx = st.number_input(
                    "From Scenario #", 
                    min_value=1, 
                    max_value=len(scenarios),
                    value=1
                )
            with col_b:
                end_idx = st.number_input(
                    "To Scenario #", 
                    min_value=1, 
                    max_value=len(scenarios),
                    value=min(10, len(scenarios))
                )
            
            if start_idx <= end_idx:
                selected_scenarios = scenarios[start_idx-1:end_idx]
                st.success(f"{len(selected_scenarios)} scenarios selected (#{start_idx} to #{end_idx})")
            else:
                st.error("Start must be <= End")
                
        else:  # Manual Select
            # Quick filter
            filter_text = st.text_input("Filter scenarios by name", "")
            
            filtered_scenarios = scenarios
            if filter_text:
                filtered_scenarios = [s for s in scenarios if filter_text.lower() in s.name.lower()]
            
            # Pagination for large lists
            items_per_page = 50
            total_pages = max(1, (len(filtered_scenarios) - 1) // items_per_page + 1)
            
            if total_pages > 1:
                page_num = st.selectbox(
                    f"Page (showing {items_per_page} per page)",
                    range(1, total_pages + 1),
                    format_func=lambda x: f"Page {x} of {total_pages}"
                )
                start = (page_num - 1) * items_per_page
                end = start + items_per_page
                display_scenarios = filtered_scenarios[start:end]
            else:
                display_scenarios = filtered_scenarios
            
            scenario_options = {f"{s.name} (ID: {s.id})": s for s in display_scenarios}
            
            selected_names = st.multiselect(
                f"Select Scenarios ({len(filtered_scenarios)} available)",
                list(scenario_options.keys()),
                help="Hold Ctrl/Cmd to select multiple"
            )
            selected_scenarios = [scenario_options[name] for name in selected_names]
        
        # Check if enough scenarios selected
        if len(selected_scenarios) < 2:
            st.info("Please select at least 2 scenarios to compare.")
            return
        
        selected_ids = [s.id for s in selected_scenarios]
        
        st.divider()
        
        # Run comparison
        if st.button("Run Comparison", type="primary"):
            st.session_state.run_comparison = True
        
        if st.session_state.get('run_comparison', False) or select_mode in ["Select All", "Select Range"]:
            st.subheader(f"Comparison Results ({len(selected_scenarios)} scenarios)")
            
            # OPTIMIZED: Batch query instead of N+1 queries
            progress_bar = st.progress(0, text="Loading scenarios...")
            
            selected_ids = [s.id for s in selected_scenarios]
            
            # Single batch query for all metrics using JOIN
            progress_bar.progress(20, text="Fetching metrics...")
            metrics_results = session.query(
                Scenario.id,
                Scenario.name,
                ScenarioMetrics.npv,
                ScenarioMetrics.irr,
                ScenarioMetrics.payback_period_years,
                ScenarioMetrics.total_revenue,
                ScenarioMetrics.total_contractor_share,
                ScenarioMetrics.total_government_take,
                ScenarioMetrics.total_capex,
                ScenarioMetrics.total_opex
            ).join(
                ScenarioMetrics, Scenario.id == ScenarioMetrics.scenario_id
            ).filter(
                Scenario.id.in_(selected_ids)
            ).all()
            
            progress_bar.progress(60, text="Calculating PTCF...")
            
            # Batch query for PTCF (sum of contractor_tax per scenario)
            ptcf_results = session.query(
                CalculationResult.scenario_id,
                func.sum(CalculationResult.contractor_tax)
            ).filter(
                CalculationResult.scenario_id.in_(selected_ids),
                CalculationResult.contractor_tax > 0
            ).group_by(CalculationResult.scenario_id).all()
            
            ptcf_dict = {r[0]: r[1] for r in ptcf_results}
            
            progress_bar.progress(90, text="Building comparison table...")
            
            # Build comparison data
            comparison_data = []
            for r in metrics_results:
                scenario_id = r[0]
                comparison_data.append({
                    'ID': scenario_id,
                    'Scenario': r[1][:50] + "..." if len(r[1]) > 50 else r[1],
                    'NPV (13%)': r[2],
                    'IRR (%)': r[3] * 100 if r[3] else None,
                    'Payback (years)': r[4],
                    'Gross Revenue': r[5],
                    'Contractor Take': r[6],
                    'Gov Take': r[7],
                    'Contractor PTCF': ptcf_dict.get(scenario_id, 0),
                    'Total CAPEX': r[8],
                    'Total OPEX': r[9]
                })
            
            progress_bar.progress(100, text="Done!")
            progress_bar.empty()
            
            if not comparison_data:
                st.warning("No metrics found for selected scenarios. Please recalculate them.")
                return
                
            df = pd.DataFrame(comparison_data)
            
            # Summary stats
            st.markdown("### Summary Statistics")
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                best_npv = df.loc[df['NPV (13%)'].idxmax()]
                st.metric("Best NPV", f"${best_npv['NPV (13%)']:,.0f}", f"ID: {int(best_npv['ID'])}")
            with col2:
                if df['IRR (%)'].notna().any():
                    best_irr = df.loc[df['IRR (%)'].idxmax()]
                    st.metric("Best IRR", f"{best_irr['IRR (%)']:.2f}%", f"ID: {int(best_irr['ID'])}")
                else:
                    st.metric("Best IRR", "N/A")
            with col3:
                positive_npv = len(df[df['NPV (13%)'] > 0])
                st.metric("Positive NPV", f"{positive_npv}/{len(df)}", f"{positive_npv/len(df)*100:.1f}%")
            with col4:
                avg_payback = df['Payback (years)'].mean()
                st.metric("Avg Payback", f"{avg_payback:.2f} yrs" if pd.notna(avg_payback) else "N/A")
            
            # Detailed Comparison - sorted by NPV descending (no user sort options)
            st.markdown("### Detailed Comparison")
            
            # Sort by NPV descending by default
            df_sorted = df.sort_values(by='NPV (13%)', ascending=False, na_position='last')
            
            # Format for display
            df_display = df_sorted.copy()
            for col in ['NPV (13%)', 'Gross Revenue', 'Contractor Take', 'Gov Take', 'Contractor PTCF', 'Total CAPEX', 'Total OPEX']:
                if col in df_display.columns:
                    df_display[col] = df_display[col].apply(lambda x: f"${x:,.0f}" if pd.notna(x) else "N/A")
            if 'IRR (%)' in df_display.columns:
                df_display['IRR (%)'] = df_display['IRR (%)'].apply(lambda x: f"{x:.2f}%" if pd.notna(x) else "N/A")
            if 'Payback (years)' in df_display.columns:
                df_display['Payback (years)'] = df_display['Payback (years)'].apply(lambda x: f"{x:.3f}" if pd.notna(x) else "N/A")
            
            st.dataframe(df_display, use_container_width=True, hide_index=True)
            
            # Charts for bulk comparison
            st.markdown("### Visual Comparison")
            
            tab1, tab2, tab3 = st.tabs(["NPV Distribution", "Top/Bottom Performers", "Scatter Plot"])
            
            with tab1:
                fig_npv = px.histogram(
                    df, x='NPV (13%)', 
                    nbins=min(30, len(df)),
                    title="NPV Distribution",
                    labels={'NPV (13%)': 'NPV ($)'}
                )
                fig_npv.add_vline(x=0, line_dash="dash", line_color="red", annotation_text="Break-even")
                st.plotly_chart(fig_npv, use_container_width=True)
            
            with tab2:
                # Top 10 and Bottom 10
                top_10 = df.nlargest(min(10, len(df)), 'NPV (13%)')
                bottom_10 = df.nsmallest(min(10, len(df)), 'NPV (13%)')
                
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("**🏆 Top 10 by NPV**")
                    fig_top = px.bar(
                        top_10, x='Scenario', y='NPV (13%)',
                        color='NPV (13%)',
                        color_continuous_scale='Greens'
                    )
                    fig_top.update_layout(showlegend=False, xaxis_tickangle=-45)
                    st.plotly_chart(fig_top, use_container_width=True)
                
                with col2:
                    st.markdown("**📉 Bottom 10 by NPV**")
                    fig_bottom = px.bar(
                        bottom_10, x='Scenario', y='NPV (13%)',
                        color='NPV (13%)',
                        color_continuous_scale='Reds_r'
                    )
                    fig_bottom.update_layout(showlegend=False, xaxis_tickangle=-45)
                    st.plotly_chart(fig_bottom, use_container_width=True)
            
            with tab3:
                fig_scatter = px.scatter(
                    df, x='Total CAPEX', y='NPV (13%)',
                    color='IRR (%)',
                    size='Gross Revenue',
                    hover_name='Scenario',
                    title="CAPEX vs NPV (size = Revenue, color = IRR)"
                )
                fig_scatter.add_hline(y=0, line_dash="dash", line_color="red")
                st.plotly_chart(fig_scatter, use_container_width=True)
            
            # Export
            st.markdown("### Export Comparison")
            
            col1, col2 = st.columns(2)
            with col1:
                # CSV export
                csv_data = df_sorted.to_csv(index=False)
                st.download_button(
                    "Download CSV",
                    csv_data,
                    f"comparison_{len(selected_scenarios)}_scenarios.csv",
                    "text/csv",
                    key="csv_download"
                )
            
            with col2:
                # Excel export with full details
                from io import BytesIO
                output = BytesIO()
                exporter = ExcelExporter(session)
                exporter.export_comparison(selected_ids, output)
                output.seek(0)
                filename = generate_filename(f"comparison_{len(selected_scenarios)}_scenarios")
                st.download_button(
                    label="Download Excel Report",
                    data=output,
                    file_name=filename,
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    key="excel_download",
                    type="primary"
                )
            
            # ============================================
            # LEADERBOARD TOP 100 WITH SCORING
            # ============================================
            st.markdown("---")
            st.markdown("### Scenario Leaderboard (Top 100)")
            st.caption("""
            **Scoring Weights:** NPV (30%) | Contractor Share (25%) | IRR (15%) | Payback Period (10%) | CAPEX (10%) | OPEX (10%)
            """)
            
            # Use comparator for scoring
            comparator = ScenarioComparator(session)
            
            # Progress bar for leaderboard calculation
            lb_progress = st.progress(0, text="Calculating leaderboard scores...")
            ranked = comparator.rank_scenarios(selected_ids)
            lb_progress.progress(100, text="Leaderboard calculation complete!")
            lb_progress.empty()
            
            if ranked:
                # Limit to top 100
                top_100 = ranked[:100]
                
                # Pagination - 10 per page
                items_per_page = 10
                total_items = len(top_100)
                total_pages = (total_items - 1) // items_per_page + 1
                
                # Page selector
                col1, col2, col3 = st.columns([1, 2, 1])
                with col2:
                    if 'leaderboard_page' not in st.session_state:
                        st.session_state.leaderboard_page = 1
                    
                    page_num = st.selectbox(
                        "Page",
                        range(1, total_pages + 1),
                        index=st.session_state.leaderboard_page - 1,
                        format_func=lambda x: f"Page {x} of {total_pages} (Rank {(x-1)*10+1}-{min(x*10, total_items)})",
                        key="leaderboard_page_select"
                    )
                    st.session_state.leaderboard_page = page_num
                
                # Get current page items
                start_idx = (page_num - 1) * items_per_page
                end_idx = start_idx + items_per_page
                page_items = top_100[start_idx:end_idx]
                
                # Create leaderboard dataframe
                leaderboard_data = []
                for r in page_items:
                    irr_val = r.get('irr') * 100 if r.get('irr') else None
                    leaderboard_data.append({
                        'Rank': r['rank'],
                        'Score': r['total_score'],
                        'Scenario': r['scenario_name'][:60],
                        'NPV': r['npv'],
                        'IRR (%)': irr_val,
                        'Payback': r.get('payback_period'),
                        'Contractor': r['total_contractor_share'],
                        'CAPEX': r['total_capex'],
                        'OPEX': r['total_opex']
                    })
                
                lb_df = pd.DataFrame(leaderboard_data)
                
                # Format for display
                lb_display = lb_df.copy()
                lb_display['Score'] = lb_display['Score'].apply(lambda x: f"{x:.2f}")
                lb_display['NPV'] = lb_display['NPV'].apply(lambda x: f"${x:,.0f}")
                lb_display['Contractor'] = lb_display['Contractor'].apply(lambda x: f"${x:,.0f}")
                lb_display['CAPEX'] = lb_display['CAPEX'].apply(lambda x: f"${x:,.0f}")
                lb_display['OPEX'] = lb_display['OPEX'].apply(lambda x: f"${x:,.0f}")
                lb_display['IRR (%)'] = lb_display['IRR (%)'].apply(lambda x: f"{x:.2f}%" if pd.notna(x) else "N/A")
                lb_display['Payback'] = lb_display['Payback'].apply(lambda x: f"{x:.2f} yrs" if pd.notna(x) else "N/A")
                
                # Display with styling
                st.dataframe(
                    lb_display,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "Rank": st.column_config.NumberColumn("Rank", width="small"),
                        "Score": st.column_config.TextColumn("Score", width="small"),
                        "Scenario": st.column_config.TextColumn("Scenario", width="large"),
                        "NPV": st.column_config.TextColumn("NPV", width="medium"),
                        "IRR (%)": st.column_config.TextColumn("IRR", width="small"),
                        "Payback": st.column_config.TextColumn("Payback", width="small"),
                    }
                )
                
                # Quick navigation buttons
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    if st.button("<< First", disabled=(page_num == 1), key="lb_first"):
                        st.session_state.leaderboard_page = 1
                        st.rerun()
                with col2:
                    if st.button("< Prev", disabled=(page_num == 1), key="lb_prev"):
                        st.session_state.leaderboard_page = page_num - 1
                        st.rerun()
                with col3:
                    if st.button("Next >", disabled=(page_num == total_pages), key="lb_next"):
                        st.session_state.leaderboard_page = page_num + 1
                        st.rerun()
                with col4:
                    if st.button("Last >>", disabled=(page_num == total_pages), key="lb_last"):
                        st.session_state.leaderboard_page = total_pages
                        st.rerun()
                
                # Show #1 highlight
                if page_num == 1 and top_100:
                    best = top_100[0]
                    st.success(f"""
                    **BEST SCENARIO: {best['scenario_name']}**
                    
                    Score: **{best['total_score']:.2f}/100** | NPV: **${best['npv']:,.0f}** | IRR: **{best.get('irr', 0)*100:.2f}%** | Payback: **{best.get('payback_period', 0):.2f} years**
                    """)
                
                # Export leaderboard
                st.markdown("#### Export Leaderboard")
                leaderboard_full = []
                for r in top_100:
                    irr_val = r.get('irr') * 100 if r.get('irr') else None
                    leaderboard_full.append({
                        'Rank': r['rank'],
                        'Score': r['total_score'],
                        'Scenario': r['scenario_name'],
                        'NPV': r['npv'],
                        'IRR (%)': irr_val,
                        'Payback (years)': r.get('payback_period'),
                        'Contractor Share': r['total_contractor_share'],
                        'CAPEX': r['total_capex'],
                        'OPEX': r['total_opex']
                    })
                lb_export_df = pd.DataFrame(leaderboard_full)
                csv_lb = lb_export_df.to_csv(index=False)
                st.download_button(
                    "Download Top 100 Leaderboard (CSV)",
                    csv_lb,
                    "leaderboard_top_100.csv",
                    "text/csv",
                    key="lb_csv_download"
                )

def main():
    """Main application"""
    
    # Main navigation
    with st.sidebar:
        st.title("Navigation")
        # Check if page override exists in session state
        if 'page' in st.session_state:
            default_page = st.session_state.page
            del st.session_state.page
        else:
            default_page = 'Home'
        
        page = st.radio(
            "Select Page",
            ["Home", "Create Scenario", "Bulk Import", "View Scenarios", "Manage Scenarios", "Compare Scenarios", "About"],
            index=["Home", "Create Scenario", "Bulk Import", "View Scenarios", "Manage Scenarios", "Compare Scenarios", "About"].index(default_page) if default_page in ["Home", "Create Scenario", "Bulk Import", "View Scenarios", "Manage Scenarios", "Compare Scenarios", "About"] else 0,
            label_visibility="collapsed"
        )
    
    if page == "Home":
        st.markdown("""
        ## Welcome to Financial Scenario Testing Application
        
        This application helps you test various financial scenarios for project investments based on:
        - **Production Sharing Contract (PSC)** fiscal model
        - **CAPEX** and **OPEX** analysis
        - **NPV** calculation with 13% discount rate
        - **Production enhancement** with CCUS (EOR/EGR)
        
        ### How to Use:
        1. **Create Scenario**: Select CAPEX items
        2. **Auto-generate OPEX**: System automatically calculates OPEX
        3. **Calculate**: View financial results and visualizations
        4. **Compare**: Compare multiple scenarios to find the best option
        5. **Export**: Download results in Excel format
        
        ### Key Features:
        - Flexible CAPEX selection (Production, Power, Transportation, Flaring)
        - Auto-generated OPEX based on CAPEX
        - Comprehensive financial calculations
        - Scenario comparison with recommendations
        - Export to Excel and PDF
        
        **Get started by creating a new scenario!**
        """)
        
        with get_db_session() as session:
            scenario_count = session.query(Scenario).filter_by(is_active=True).count()
            st.info(f"You currently have **{scenario_count}** active scenario(s).")
    
    elif page == "Create Scenario":
        st.title("Create New Scenario")
        st.markdown("Select CAPEX items and the system will automatically calculate OPEX and financial metrics.")
        
        # Scenario details
        col1, col2 = st.columns([2, 1])
        with col1:
            scenario_name = st.text_input("Scenario Name *", placeholder="e.g., CCUS with CCPP")
        with col2:
            auto_name = st.checkbox("Auto-generate name", value=False)
        
        scenario_desc = st.text_area("Description (optional)", placeholder="Describe this scenario...")
        
        # Render CAPEX selection
        selected_items = render_capex_selection()
        
        # Display selection summary
        if selected_items:
            st.markdown("---")
            st.subheader("Selected Items Summary")
            with get_db_session() as session:
                total_capex = 0
                summary_data = []
                
                for item_id, quantity in selected_items.items():
                    item = session.query(CapexItem).filter_by(id=item_id).first()
                    if item:
                        total_cost = item.unit_cost * quantity
                        total_capex += total_cost
                        summary_data.append({
                            'Item': item.name,
                            'Quantity': quantity,
                            'Unit Cost': f"${item.unit_cost:,.2f}",
                            'Total': f"${total_cost:,.2f}"
                        })
                
                st.dataframe(pd.DataFrame(summary_data), width='stretch')
                st.metric("Total CAPEX", f"${total_capex:,.2f}")
        
        # Create scenario button
        if st.button("Create & Calculate Scenario", type="primary", disabled=not selected_items):
            if not scenario_name and not auto_name:
                st.error("Please provide a scenario name or enable auto-generate.")
            else:
                with st.spinner("Creating scenario and calculating financials..."):
                    try:
                        with get_db_session() as session:
                            # Auto-generate name if needed
                            if auto_name or not scenario_name:
                                item_names = []
                                for item_id in list(selected_items.keys())[:3]:
                                    item = session.query(CapexItem).filter_by(id=item_id).first()
                                    if item:
                                        item_names.append(item.code)
                                scenario_name = f"Scenario_{'+'.join(item_names)}_{datetime.now().strftime('%Y%m%d_%H%M')}"
                            
                            # Create scenario
                            scenario = create_scenario_from_selection(
                                session, 
                                scenario_name, 
                                scenario_desc, 
                                selected_items
                            )
                            
                            st.success(f"Scenario '{scenario.name}' created successfully!")
                            st.session_state.current_scenario = scenario.id
                            
                            # Display results
                            st.markdown("---")
                            display_scenario_results(scenario.id)
                            
                            # Export option
                            if st.button("Export to Excel"):
                                ensure_export_directory()
                                filename = generate_filename(scenario.name)
                                filepath = os.path.join('exports', filename)
                                
                                exporter = ExcelExporter(session)
                                exporter.export_scenario(scenario.id, filepath)
                                
                                with open(filepath, 'rb') as f:
                                    st.download_button(
                                        label="Download Excel Report",
                                        data=f,
                                        file_name=filename,
                                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                                    )
                    
                    except Exception as e:
                        st.error(f"Error creating scenario: {str(e)}")
                        st.exception(e)
        
        elif not selected_items:
            st.info("Please select CAPEX items to continue.")
    
    elif page == "Bulk Import":
        st.title("📥 Bulk Import Scenarios")
        st.markdown("""
        Import multiple scenarios from an Excel file. The system will automatically:
        - Parse CAPEX selections from Excel
        - Generate OPEX for each scenario
        - Calculate all financial metrics (NPV, IRR, Payback, etc.)
        """)
        
        # Download template button
        with st.expander("📄 Download Excel Template", expanded=False):
            st.markdown("""
            **Excel Format (sesuai 512_scenarios.xlsx):**
            
            | Scenario ID | Production | Power | Transportation | Flaring |
            |-------------|------------|-------|----------------|---------|
            | 1 | | | Pipeline | FGRS ON |
            | 2 | CO2 EOR | CCPP | Pipeline | FGRS ON |
            | 3 | CO2 EOR, CO2 EGR | CCPP, FWT | VLGC | FGRS OFF |
            
            **Nilai yang valid:**
            - **Production**: CO2 EOR, CO2 EGR, Supersonic Separator (bisa dikombinasi dengan koma)
            - **Power**: CCPP, FWT (bisa dikombinasi dengan koma)  
            - **Transportation**: Pipeline, VLGC, OWS, STS (bisa dikombinasi dengan koma)
            - **Flaring**: FGRS ON atau FGRS OFF
            """)
            
            # Generate sample template for download
            sample_df = pd.DataFrame({
                'Scenario ID': [1, 2, 3, 4, 5],
                'Production': ['', 'CO2 EOR', 'CO2 EGR', 'CO2 EOR, CO2 EGR', 'CO2 EOR, CO2 EGR, Supersonic Separator'],
                'Power': ['', 'CCPP', 'FWT', 'CCPP, FWT', 'CCPP, FWT'],
                'Transportation': ['Pipeline', 'Pipeline', 'VLGC', 'VLGC, OWS', 'Pipeline'],
                'Flaring': ['FGRS ON', 'FGRS ON', 'FGRS OFF', 'FGRS ON', 'FGRS ON']
            })
            
            from io import BytesIO
            output = BytesIO()
            sample_df.to_excel(output, index=False, sheet_name='Sheet1')
            output.seek(0)
            
            st.download_button(
                label="📥 Download Template Excel",
                data=output,
                file_name="scenario_template.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        
        # File uploader
        uploaded_file = st.file_uploader(
            "Upload Excel file with scenario configurations",
            type=['xlsx', 'xls'],
            help="Excel should have columns: Scenario ID, Production, Power, Transportation, Flaring"
        )
        
        if uploaded_file:
            import tempfile
            import os as os_module
            
            # Save uploaded file temporarily
            with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp_file:
                tmp_file.write(uploaded_file.getvalue())
                tmp_path = tmp_file.name
            
            try:
                # Preview
                df = pd.read_excel(tmp_path)
                st.success(f"✅ File loaded: **{len(df)} scenarios** found")
                
                # Show column mapping info
                with st.expander("📋 Column Mapping Reference", expanded=False):
                    st.markdown("""
                    | Excel Column | CAPEX Items |
                    |--------------|-------------|
                    | **Production** | CO2 EOR, CO2 EGR, Supersonic Separator |
                    | **Power** | CCPP, FWT |
                    | **Transportation** | Pipeline, VLGC, OWS, STS |
                    | **Flaring** | FGRS ON, FGRS OFF |
                    
                    *Multiple items can be comma-separated (e.g., "CO2 EOR, CO2 EGR")*
                    """)
                
                # Preview section
                st.subheader("Preview")
                with get_db_session() as session:
                    from engine.bulk_importer import BulkScenarioImporter
                    importer = BulkScenarioImporter(session)
                    preview_df = importer.preview_import(tmp_path, limit=10)
                    st.dataframe(preview_df, use_container_width=True)
                    
                    if len(df) > 10:
                        st.info(f"Showing first 10 of {len(df)} scenarios")
                
                st.markdown("---")
                
                # Import options
                st.subheader("Import Options")
                col1, col2 = st.columns(2)
                
                with col1:
                    import_mode = st.radio(
                        "Import Mode",
                        ["All scenarios", "Select range", "Specific IDs"],
                        help="Choose which scenarios to import"
                    )
                
                with col2:
                    if import_mode == "Select range":
                        start_id = st.number_input("Start ID", min_value=1, max_value=len(df), value=1)
                        end_id = st.number_input("End ID", min_value=1, max_value=len(df), value=min(10, len(df)))
                        selected_ids = list(range(int(start_id), int(end_id) + 1))
                        st.info(f"Will import {len(selected_ids)} scenarios (ID {start_id} to {end_id})")
                    elif import_mode == "Specific IDs":
                        ids_input = st.text_input("Enter IDs (comma-separated)", "1, 2, 3")
                        selected_ids = [int(x.strip()) for x in ids_input.split(',') if x.strip().isdigit()]
                        st.info(f"Will import {len(selected_ids)} scenarios")
                    else:
                        selected_ids = None
                        st.info(f"Will import all {len(df)} scenarios")
                
                # Calculate financials option
                calc_financials = st.checkbox("Calculate financial metrics", value=True, 
                    help="Uncheck to import faster (you can calculate later)")
                
                # Import button
                if st.button("🚀 Start Import", type="primary"):
                    with get_db_session() as session:
                        from engine.bulk_importer import BulkScenarioImporter
                        importer = BulkScenarioImporter(session)
                        
                        progress_bar = st.progress(0)
                        status_text = st.empty()
                        
                        def update_progress(current, total, message):
                            progress_bar.progress(current / total)
                            status_text.text(f"{message} ({current}/{total})")
                        
                        results = importer.import_from_excel(
                            tmp_path,
                            scenario_ids=selected_ids,
                            calculate=calc_financials,
                            progress_callback=update_progress
                        )
                        
                        progress_bar.progress(1.0)
                        status_text.text("Import complete!")
                        
                        # Show results
                        st.markdown("---")
                        st.subheader("Import Results")
                        
                        col1, col2, col3, col4 = st.columns(4)
                        col1.metric("Total", results['total'])
                        col2.metric("Created", results['created'], delta_color="normal")
                        col3.metric("Skipped", results['skipped'], delta_color="off")
                        col4.metric("Errors", results['errors'], delta_color="inverse" if results['errors'] > 0 else "off")
                        
                        if results['created'] > 0:
                            st.success(f"✅ Successfully imported {results['created']} scenarios!")
                            
                            # Show created scenarios
                            with st.expander("View created scenarios", expanded=True):
                                created = [s for s in results['scenarios'] if s['status'] == 'created']
                                for s in created[:20]:  # Show first 20
                                    st.write(f"• **{s['name']}** (ID: {s['scenario_id']}) - CAPEX: ${s['total_capex']:,.0f}")
                                if len(created) > 20:
                                    st.info(f"... and {len(created) - 20} more")
                        
                        if results['errors'] > 0:
                            with st.expander("View errors", expanded=True):
                                errors = [s for s in results['scenarios'] if s['status'] == 'error']
                                for e in errors:
                                    st.error(f"Scenario {e['scenario_id']}: {e['error']}")
                
            finally:
                # Cleanup temp file
                if os_module.path.exists(tmp_path):
                    os_module.remove(tmp_path)
        
        else:
            # Show template info
            st.info("👆 Upload an Excel file to get started")
            
            st.markdown("### Excel Template Format")
            st.markdown("""
            Your Excel file should have these columns:
            
            | Column | Description | Example Values |
            |--------|-------------|----------------|
            | Scenario ID | Unique identifier | 1, 2, 3, ... |
            | Production | Production enhancement | CO2 EOR, CO2 EGR, Supersonic Separator |
            | Power | Power generation | CCPP, FWT |
            | Transportation | Transport method | Pipeline, VLGC, OWS, STS |
            | Flaring | Flare gas recovery | FGRS ON, FGRS OFF |
            
            **Tips:**
            - Leave cells empty if no selection for that category
            - Use comma-separated values for multiple selections (e.g., "CO2 EOR, CO2 EGR")
            - Pipeline uses default quantity of 30 km
            """)
    
    elif page == "Manage Scenarios":
        st.title("📋 Manage Scenarios")
        
        with get_db_session() as session:
            # Sorting options
            col1, col2 = st.columns([2, 1])
            with col1:
                sort_order = st.radio(
                    "Sort by",
                    ["Newest First", "Oldest First"],
                    horizontal=True,
                    key="manage_sort"
                )
            
            # Query with sorting
            if sort_order == "Newest First":
                scenarios = session.query(Scenario).filter_by(is_active=True).order_by(Scenario.created_at.desc()).all()
            else:
                scenarios = session.query(Scenario).filter_by(is_active=True).order_by(Scenario.created_at.asc()).all()
            
            if not scenarios:
                st.warning("No scenarios found. Create a new scenario to get started.")
            else:
                st.markdown(f"**Total Active Scenarios:** {len(scenarios)}")
                
                # Pagination - 10 per page
                items_per_page = 10
                total_items = len(scenarios)
                total_pages = max(1, (total_items - 1) // items_per_page + 1)
                
                # Page selector
                with col2:
                    if 'manage_page' not in st.session_state:
                        st.session_state.manage_page = 1
                    
                    page_num = st.selectbox(
                        "Page",
                        range(1, total_pages + 1),
                        index=min(st.session_state.manage_page - 1, total_pages - 1),
                        format_func=lambda x: f"Page {x}/{total_pages}",
                        key="manage_page_select"
                    )
                    st.session_state.manage_page = page_num
                
                # Get current page items
                start_idx = (page_num - 1) * items_per_page
                end_idx = start_idx + items_per_page
                page_scenarios = scenarios[start_idx:end_idx]
                
                st.caption(f"Showing {start_idx + 1}-{min(end_idx, total_items)} of {total_items} scenarios")
                st.markdown("---")
                
                # Display scenarios in a table with actions
                for scenario in page_scenarios:
                    with st.expander(f"**{scenario.name}** - Created: {scenario.created_at.strftime('%Y-%m-%d %H:%M')}"):
                        if scenario.description:
                            st.write(f"**Description:** {scenario.description}")
                        
                        # Get metrics
                        from database.models import ScenarioMetrics
                        metrics = session.query(ScenarioMetrics).filter_by(scenario_id=scenario.id).first()
                        
                        if metrics:
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric("Total CAPEX", f"${metrics.total_capex:,.0f}")
                            with col2:
                                st.metric("NPV", f"${metrics.npv:,.0f}")
                            with col3:
                                st.metric("Total Revenue", f"${metrics.total_revenue:,.0f}")
                        
                        st.markdown("---")
                        col_a, col_b, col_c, col_d, col_e = st.columns(5)
                        
                        with col_a:
                            if st.button("Edit", key=f"edit_{scenario.id}"):
                                st.session_state.editing_scenario_id = scenario.id
                                st.session_state.page = "Create Scenario"
                                st.rerun()
                        
                        with col_b:
                            if st.button("Download", key=f"download_{scenario.id}"):
                                ensure_export_directory()
                                filename = generate_filename(scenario.name)
                                filepath = os.path.join('exports', filename)
                                
                                exporter = ExcelExporter(session)
                                exporter.export_scenario(scenario.id, filepath)
                                
                                with open(filepath, 'rb') as f:
                                    file_data = f.read()
                                
                                st.download_button(
                                    label=f"📥 {filename}",
                                    data=file_data,
                                    file_name=filename,
                                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                    key=f"dl_btn_{scenario.id}"
                                )
                        
                        with col_c:
                            if st.button("Duplicate", key=f"dup_{scenario.id}"):
                                # Duplicate scenario
                                new_name = f"{scenario.name} (Copy)"
                                new_scenario = Scenario(
                                    name=new_name,
                                    description=scenario.description,
                                    production_profile_id=scenario.production_profile_id,
                                    fiscal_terms_id=scenario.fiscal_terms_id,
                                    pricing_assumptions_id=scenario.pricing_assumptions_id,
                                    production_enhancement_id=scenario.production_enhancement_id,
                                    created_by=scenario.created_by,
                                    is_active=True
                                )
                                session.add(new_scenario)
                                session.flush()
                                
                                # Copy CAPEX items
                                capex_items = session.query(ScenarioCapex).filter_by(scenario_id=scenario.id).all()
                                for capex in capex_items:
                                    new_capex = ScenarioCapex(
                                        scenario_id=new_scenario.id,
                                        capex_item_id=capex.capex_item_id,
                                        quantity=capex.quantity,
                                        unit_cost=capex.unit_cost,
                                        total_cost=capex.total_cost
                                    )
                                    session.add(new_capex)
                                
                                session.commit()
                                
                                # Generate OPEX and calculations
                                fiscal = session.query(FiscalTerms).filter_by(id=new_scenario.fiscal_terms_id).first()
                                opex_gen = OpexGenerator(session)
                                opex_gen.save_opex_for_scenario(
                                    new_scenario.id, 
                                    fiscal.project_start_year, 
                                    fiscal.project_end_year, 
                                    escalation_rate=0.02
                                )
                                
                                calculator = FinancialCalculator(new_scenario, session)
                                calculator.save_calculations()
                                
                                st.success(f"Scenario '{new_name}' created successfully!")
                                st.rerun()
                        
                        with col_d:
                            if st.button("Delete", key=f"del_{scenario.id}", type="secondary"):
                                if st.session_state.get(f"confirm_delete_{scenario.id}", False):
                                    # Delete related data
                                    session.query(ScenarioCapex).filter_by(scenario_id=scenario.id).delete()
                                    session.query(ScenarioOpex).filter_by(scenario_id=scenario.id).delete()
                                    session.query(CalculationResult).filter_by(scenario_id=scenario.id).delete()
                                    session.query(ScenarioMetrics).filter_by(scenario_id=scenario.id).delete()
                                    session.delete(scenario)
                                    session.commit()
                                    
                                    st.success(f"Scenario '{scenario.name}' deleted successfully!")
                                    if f"confirm_delete_{scenario.id}" in st.session_state:
                                        del st.session_state[f"confirm_delete_{scenario.id}"]
                                    st.rerun()
                                else:
                                    st.session_state[f"confirm_delete_{scenario.id}"] = True
                                    st.warning("Click Delete again to confirm")
                        
                        with col_e:
                            if st.button("View Details", key=f"view_{scenario.id}"):
                                st.session_state.selected_scenario_id = scenario.id
                                st.session_state.page = "View Scenarios"
                                st.rerun()
                
                # Pagination navigation buttons
                st.markdown("---")
                col1, col2, col3, col4, col5 = st.columns(5)
                with col1:
                    if st.button("⏮️ First", disabled=(page_num == 1), key="manage_first"):
                        st.session_state.manage_page = 1
                        st.rerun()
                with col2:
                    if st.button("◀️ Prev", disabled=(page_num == 1), key="manage_prev"):
                        st.session_state.manage_page = page_num - 1
                        st.rerun()
                with col3:
                    st.markdown(f"<center>Page {page_num} of {total_pages}</center>", unsafe_allow_html=True)
                with col4:
                    if st.button("Next ▶️", disabled=(page_num == total_pages), key="manage_next"):
                        st.session_state.manage_page = page_num + 1
                        st.rerun()
                with col5:
                    if st.button("Last ⏭️", disabled=(page_num == total_pages), key="manage_last"):
                        st.session_state.manage_page = total_pages
                        st.rerun()
    
    elif page == "View Scenarios":
        st.title("View Existing Scenarios")
        
        with get_db_session() as session:
            scenarios = session.query(Scenario).filter_by(is_active=True).order_by(Scenario.created_at.desc()).all()
            
            if not scenarios:
                st.warning("No scenarios found. Create a new scenario to get started.")
            else:
                # Check if a specific scenario was selected from Manage Scenarios
                if 'selected_scenario_id' in st.session_state:
                    scenario_id = st.session_state.selected_scenario_id
                    del st.session_state.selected_scenario_id
                    display_scenario_results(scenario_id)
                else:
                    # Scenario selector
                    scenario_options = {f"{s.name} (Created: {s.created_at.strftime('%Y-%m-%d')})": s.id 
                                       for s in scenarios}
                    selected_name = st.selectbox("Select a scenario to view:", list(scenario_options.keys()))
                    
                    if selected_name:
                        scenario_id = scenario_options[selected_name]
                        display_scenario_results(scenario_id)
                    
                    # Export option
                    st.markdown("---")
                    if st.button("Export this Scenario to Excel", key="export_scenario_btn"):
                        ensure_export_directory()
                        scenario = session.query(Scenario).filter_by(id=scenario_id).first()
                        filename = generate_filename(scenario.name)
                        filepath = os.path.join('exports', filename)
                        
                        exporter = ExcelExporter(session)
                        exporter.export_scenario(scenario_id, filepath)
                        
                        with open(filepath, 'rb') as f:
                            file_data = f.read()
                        
                        st.download_button(
                            label="Download Excel Report",
                            data=file_data,
                            file_name=filename,
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            key="download_scenario_btn"
                        )
    
    elif page == "Compare Scenarios":
        compare_scenarios_page()
    
    elif page == "About":
        st.markdown("""
        ## About This Application
        
        ### Financial Model
        
        This application implements a **Production Sharing Contract (PSC)** financial model with the following parameters:
        
        **Fiscal Terms:**
        - Contractor Pre-tax Split: **67.23%**
        - Government Pre-tax Split: **32.77%**
        - Contractor Tax Rate: **40.5%**
        - Discount Rate: **13%**
        
        **Pricing Assumptions:**
        - Oil Price: **$60/bbl**
        - Gas Price: **$5.5/MMBTU**
        - Gas Conversion: **1027 MMSCF to MMBTU**
        
        **Production Enhancement (CCUS):**
        - EOR (Enhanced Oil Recovery): **+20%**
        - EGR (Enhanced Gas Recovery): **+25%**
        
        **Depreciation:**
        - Method: **Declining Balance (DDB)**
        - Life: **5 years**
        - Factor: **25%**
        - Salvage Value: **$0**
        
        **Other Parameters:**
        - Project Period: **2026-2037** (12 years)
        - Abandonment Security Reserve (ASR): **5% of CAPEX**
        
        ### Technical Stack
        
        - **Backend:** PostgreSQL, SQLAlchemy
        - **Frontend:** Streamlit
        - **Visualization:** Plotly
        - **Export:** Excel (openpyxl)
        
        ### Version
        **v1.0.0** - December 2024
        
        ---
        
        For questions or support, please contact the development team.
        """)

if __name__ == "__main__":
    main()
