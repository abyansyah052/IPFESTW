# 🚀 Quick Start Guide - Financial Scenario Testing

## For Local Development

```bash
# 1. Activate environment
source venv/bin/activate  # Mac/Linux
# OR
venv\Scripts\activate  # Windows

# 2. Run application
streamlit run app.py

# 3. Open browser
# http://localhost:8501
```

## For Production Deployment

### Option 1: Streamlit Community Cloud (Recommended)
```bash
# 1. Push to GitHub
git add .
git commit -m "Production ready"
git push origin main

# 2. Deploy
# - Go to https://share.streamlit.io
# - Connect your GitHub repo
# - Add database secrets in dashboard
# - Click Deploy

# Done! App live in ~2 minutes
```

### Option 2: Docker (Coming Soon)
```bash
docker build -t scenario-calc .
docker run -p 8501:8501 scenario-calc
```

## Environment Setup

### Required Variables (.env):
```env
DB_HOST=your-supabase-host.supabase.co
DB_PORT=5432
DB_NAME=postgres
DB_USER=postgres
DB_PASSWORD=your-password
```

## Testing

```bash
# Run all tests
cd tests && python -m pytest -v

# Run specific test
python -m pytest test_comprehensive.py -v

# Check coverage
python -m pytest --cov=engine --cov=database
```

## Troubleshooting

### App won't start
```bash
# Check Python version
python --version  # Need 3.9+

# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

### Database connection error
```bash
# Verify .env file exists
cat .env

# Test database connection
python -c "from database.connection import get_db_session; print('OK')"
```

### Performance issues
```bash
# Clear cache
rm -rf .streamlit/cache/

# Check memory usage
# Activity Monitor (Mac) or Task Manager (Windows)
```

## Quick Commands

```bash
# Clean project
./cleanup.sh

# Run linter
flake8 app.py engine/ database/

# Format code
black app.py engine/ database/

# Update dependencies
pip freeze > requirements.txt
```

## Support

- Documentation: See PRODUCTION_READY.md
- Issues: GitHub Issues
- Questions: Open Discussion on GitHub

---

**Ready to Deploy!** 🚀
