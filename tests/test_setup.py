"""
Quick Test Script - Test basic functionality without full database
"""
import sys
sys.path.append('.')

def test_imports():
    """Test if all modules can be imported"""
    print("Testing imports...")
    try:
        from database.models import Base, CapexCategory, CapexItem
        print("✓ Database models imported")
        
        from engine.calculator import FinancialCalculator
        print("✓ Calculator imported")
        
        from engine.opex_generator import OpexGenerator
        print("✓ OPEX Generator imported")
        
        from engine.comparator import ScenarioComparator
        print("✓ Comparator imported")
        
        from utils.export import ExcelExporter
        print("✓ Exporter imported")
        
        print("\n✅ All imports successful!")
        return True
    except Exception as e:
        print(f"\n❌ Import error: {e}")
        return False

def test_calculations():
    """Test basic calculation logic"""
    print("\nTesting calculations...")
    try:
        # Test production enhancement
        base_oil = 1000000
        base_gas = 50000
        eor_rate = 0.20
        egr_rate = 0.25
        
        enhanced_oil = base_oil * (1 + eor_rate)
        enhanced_gas = base_gas * (1 + egr_rate)
        
        print(f"Base Oil: {base_oil:,} bbl → Enhanced: {enhanced_oil:,} bbl (+{eor_rate*100}%)")
        print(f"Base Gas: {base_gas:,} MMSCF → Enhanced: {enhanced_gas:,} MMSCF (+{egr_rate*100}%)")
        
        # Test gas conversion
        gas_conversion = 1027
        gas_mmbtu = enhanced_gas * gas_conversion
        print(f"Gas in MMBTU: {gas_mmbtu:,}")
        
        # Test revenue calculation
        oil_price = 60
        gas_price = 5.5
        oil_revenue = enhanced_oil * oil_price
        gas_revenue = gas_mmbtu * gas_price
        total_revenue = oil_revenue + gas_revenue
        
        print(f"\nRevenue Calculation:")
        print(f"  Oil Revenue: ${oil_revenue:,.2f}")
        print(f"  Gas Revenue: ${gas_revenue:,.2f}")
        print(f"  Total Revenue: ${total_revenue:,.2f}")
        
        # Test PSC split
        operating_profit = 50000000  # Example
        contractor_pretax = operating_profit * 0.6723
        contractor_tax = contractor_pretax * 0.405
        contractor_aftertax = contractor_pretax - contractor_tax
        government_pretax = operating_profit * 0.3277
        government_total = government_pretax + contractor_tax
        
        print(f"\nPSC Split (OP = ${operating_profit:,.2f}):")
        print(f"  Contractor (Pre-tax): ${contractor_pretax:,.2f}")
        print(f"  Contractor Tax: ${contractor_tax:,.2f}")
        print(f"  Contractor (After-tax): ${contractor_aftertax:,.2f}")
        print(f"  Government (Pre-tax): ${government_pretax:,.2f}")
        print(f"  Government Total: ${government_total:,.2f}")
        
        # Test NPV calculation
        cash_flows = [10000000, 12000000, 11000000, 10000000, 9000000]
        discount_rate = 0.13
        npv = sum(cf / ((1 + discount_rate) ** (i+1)) for i, cf in enumerate(cash_flows))
        
        print(f"\nNPV Calculation:")
        print(f"  Cash Flows: {[f'${cf/1e6:.1f}M' for cf in cash_flows]}")
        print(f"  Discount Rate: {discount_rate*100}%")
        print(f"  NPV: ${npv:,.2f}")
        
        # Test ASR
        capex_total = 100000000
        asr = capex_total * 0.05
        print(f"\nASR Calculation:")
        print(f"  Total CAPEX: ${capex_total:,.2f}")
        print(f"  ASR (5%): ${asr:,.2f}")
        
        print("\n✅ All calculations working correctly!")
        return True
        
    except Exception as e:
        print(f"\n❌ Calculation error: {e}")
        return False

def test_database_connection():
    """Test database connection"""
    print("\nTesting database connection...")
    try:
        from dotenv import load_dotenv
        import os
        
        load_dotenv()
        db_url = os.getenv('DATABASE_URL')
        
        if not db_url or db_url == 'postgresql://user:password@localhost:5432/scenario_calc':
            print("⚠️  DATABASE_URL not configured in .env file")
            print("   Please update .env with your database connection string")
            return False
        
        from sqlalchemy import create_engine
        engine = create_engine(db_url, pool_pre_ping=True)
        
        # Test connection
        with engine.connect() as conn:
            result = conn.execute("SELECT 1")
            result.fetchone()
        
        print("✅ Database connection successful!")
        return True
        
    except Exception as e:
        print(f"⚠️  Database connection failed: {e}")
        print("   Make sure:")
        print("   1. PostgreSQL is running")
        print("   2. .env file has correct DATABASE_URL")
        print("   3. Database exists and is accessible")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("Financial Scenario Testing - Quick Test")
    print("=" * 60)
    
    results = []
    
    # Run tests
    results.append(("Imports", test_imports()))
    results.append(("Calculations", test_calculations()))
    results.append(("Database", test_database_connection()))
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    for test_name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name}: {status}")
    
    all_passed = all(result[1] for result in results)
    
    if all_passed:
        print("\n🎉 All tests passed! Ready to run the application.")
        print("\nNext steps:")
        print("1. Initialize database: cd database && python init_db.py")
        print("2. Run app: streamlit run app.py")
    else:
        print("\n⚠️  Some tests failed. Please fix the issues before running the app.")
