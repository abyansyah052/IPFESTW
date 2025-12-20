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
        
        # Display key metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total CAPEX", f"${metrics.total_capex:,.0f}")
        with col2:
            st.metric("Total OPEX", f"${metrics.total_opex:,.0f}")
        with col3:
            st.metric("Total Revenue", f"${metrics.total_revenue:,.0f}")
        with col4:
            npv_color = "normal" if metrics.npv > 0 else "inverse"
            st.metric("NPV (13%)", f"${metrics.npv:,.0f}", delta_color=npv_color)
        
        col5, col6, col7, col8 = st.columns(4)
        
        with col5:
            st.metric("Contractor Share", f"${metrics.total_contractor_share:,.0f}")
        with col6:
            st.metric("Government Take", f"${metrics.total_government_take:,.0f}")
        with col7:
            st.metric("ASR (5%)", f"${metrics.asr_amount:,.0f}")
        with col8:
            roi = ((metrics.total_contractor_share - metrics.total_capex) / metrics.total_capex * 100) if metrics.total_capex > 0 else 0
            st.metric("ROI", f"{roi:.2f}%")
        
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
            st.plotly_chart(fig1, use_container_width=True)
            
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
            st.plotly_chart(fig2, use_container_width=True)
            
            # PSC Split
            total_contractor = sum(r.contractor_share_aftertax for r in results)
            total_government = sum(r.government_total_take for r in results)
            
            fig3 = go.Figure(data=[go.Pie(
                labels=['Contractor (After-tax)', 'Government Total Take'],
                values=[total_contractor, total_government],
                hole=.3
            )])
            fig3.update_layout(title='Production Sharing Split', height=400)
            st.plotly_chart(fig3, use_container_width=True)
        
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
    """Scenario comparison page"""
    st.title("Compare Scenarios")
    
    with get_db_session() as session:
        scenarios = session.query(Scenario).filter_by(is_active=True).all()
        
        if len(scenarios) < 2:
            st.warning("You need at least 2 scenarios to compare. Please create more scenarios first.")
            return
        
        # Scenario selection
        scenario_options = {f"{s.name} (ID: {s.id})": s.id for s in scenarios}
        selected_names = st.multiselect(
            "Select scenarios to compare:",
            options=list(scenario_options.keys()),
            default=list(scenario_options.keys())[:2] if len(scenario_options) >= 2 else []
        )
        
        if len(selected_names) < 2:
            st.info("Please select at least 2 scenarios to compare.")
            return
        
        selected_ids = [scenario_options[name] for name in selected_names]
        
        if st.button("Compare Scenarios", type="primary"):
            comparator = ScenarioComparator(session)
            comparison = comparator.compare_scenarios_detailed(selected_ids)
            
            # Display best recommendation
            st.success("### Best Scenario Recommendation")
            best = comparison['best_scenario']
            
            st.markdown(f"""
            **{best['summary']}**
            
            **Scenario:** {best['scenario_name']}  
            **Score:** {best['score']:.2f}/100  
            **Rank:** #{best['rank']}
            
            **Key Metrics:**
            - NPV: ${best['npv']:,.2f}
            - Total CAPEX: ${best['total_capex']:,.2f}
            - Total Revenue: ${best['total_revenue']:,.2f}
            - Contractor Share: ${best['total_contractor_share']:,.2f}
            
            **Reasons:**
            """)
            
            for reason in best['reasons']:
                st.markdown(f"- {reason}")
            
            # Comparison table
            st.markdown("### Detailed Comparison")
            ranked_df = pd.DataFrame(comparison['ranked_scenarios'])[
                ['rank', 'scenario_name', 'total_score', 'npv', 'total_capex', 
                 'total_opex', 'total_revenue', 'total_contractor_share']
            ]
            ranked_df.columns = ['Rank', 'Scenario', 'Score', 'NPV', 'CAPEX', 
                                'OPEX', 'Revenue', 'Contractor Share']
            
            st.dataframe(ranked_df, width='stretch')
            
            # Visualizations
            st.markdown("### Comparison Charts")
            
            col1, col2 = st.columns(2)
            
            with col1:
                # NPV Comparison
                fig1 = px.bar(
                    ranked_df,
                    x='Scenario',
                    y='NPV',
                    title='NPV Comparison',
                    color='NPV',
                    color_continuous_scale='RdYlGn'
                )
                st.plotly_chart(fig1, use_container_width=True)  # TODO: Update to width='stretch' when Streamlit updates plotly
            
            with col2:
                # Score Comparison
                fig2 = px.bar(
                    ranked_df,
                    x='Scenario',
                    y='Score',
                    title='Overall Score Comparison',
                    color='Score',
                    color_continuous_scale='Blues'
                )
                st.plotly_chart(fig2, use_container_width=True)  # TODO: Update to width='stretch' when Streamlit updates plotly
            
            # CAPEX vs Revenue
            fig3 = go.Figure()
            fig3.add_trace(go.Bar(name='CAPEX', x=ranked_df['Scenario'], y=ranked_df['CAPEX']))
            fig3.add_trace(go.Bar(name='OPEX', x=ranked_df['Scenario'], y=ranked_df['OPEX']))
            fig3.add_trace(go.Bar(name='Revenue', x=ranked_df['Scenario'], y=ranked_df['Revenue']))
            fig3.update_layout(
                title='CAPEX, OPEX, and Revenue Comparison',
                barmode='group',
                height=400
            )
            st.plotly_chart(fig3, use_container_width=True)
            
            # Export comparison
            if st.button("Export Comparison to Excel"):
                ensure_export_directory()
                filename = generate_filename("scenario_comparison")
                filepath = os.path.join('exports', filename)
                
                exporter = ExcelExporter(session)
                exporter.export_comparison(selected_ids, filepath)
                
                with open(filepath, 'rb') as f:
                    st.download_button(
                        label="Download Comparison Excel",
                        data=f,
                        file_name=filename,
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
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
            ["Home", "Create Scenario", "View Scenarios", "Manage Scenarios", "Compare Scenarios", "About"],
            index=["Home", "Create Scenario", "View Scenarios", "Manage Scenarios", "Compare Scenarios", "About"].index(default_page) if default_page in ["Home", "Create Scenario", "View Scenarios", "Manage Scenarios", "Compare Scenarios", "About"] else 0,
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
    
    elif page == "Manage Scenarios":
        st.title("Manage Scenarios")
        
        with get_db_session() as session:
            scenarios = session.query(Scenario).filter_by(is_active=True).order_by(Scenario.created_at.desc()).all()
            
            if not scenarios:
                st.warning("No scenarios found. Create a new scenario to get started.")
            else:
                st.markdown(f"**Total Active Scenarios:** {len(scenarios)}")
                st.markdown("---")
                
                # Display scenarios in a table with actions
                for scenario in scenarios:
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
                        col_a, col_b, col_c, col_d = st.columns(4)
                        
                        with col_a:
                            if st.button("Edit", key=f"edit_{scenario.id}"):
                                st.session_state.editing_scenario_id = scenario.id
                                st.session_state.page = "Create Scenario"
                                st.rerun()
                        
                        with col_b:
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
                        
                        with col_c:
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
                        
                        with col_d:
                            if st.button("View Details", key=f"view_{scenario.id}"):
                                st.session_state.selected_scenario_id = scenario.id
                                st.session_state.page = "View Scenarios"
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
                    if st.button("Export this Scenario to Excel"):
                        ensure_export_directory()
                        scenario = session.query(Scenario).filter_by(id=scenario_id).first()
                        filename = generate_filename(scenario.name)
                        filepath = os.path.join('exports', filename)
                        
                        exporter = ExcelExporter(session)
                        exporter.export_scenario(scenario_id, filepath)
                        
                        with open(filepath, 'rb') as f:
                            st.download_button(
                                label="Download Excel Report",
                                data=f,
                                file_name=filename,
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
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
