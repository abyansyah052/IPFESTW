#!/bin/bash
# Production Cleanup Script

echo "🧹 Cleaning up project for production deployment..."

# Remove Python cache
echo "Removing __pycache__ directories..."
find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
find . -name "*.pyc" -delete 2>/dev/null || true
find . -name "*.pyo" -delete 2>/dev/null || true
find . -name "*~" -delete 2>/dev/null || true

# Remove IDE files
echo "Removing IDE configuration files..."
rm -rf .vscode/ .idea/ .DS_Store 2>/dev/null || true
find . -name ".DS_Store" -delete 2>/dev/null || true
find . -name "*.swp" -delete 2>/dev/null || true
find . -name "*.swo" -delete 2>/dev/null || true

# Remove test outputs
echo "Removing test artifacts..."
rm -rf .pytest_cache/ .coverage htmlcov/ 2>/dev/null || true

# Remove build artifacts
echo "Removing build artifacts..."
rm -rf build/ dist/ *.egg-info/ 2>/dev/null || true

# Organize test files
echo "Organizing test files..."
mkdir -p tests 2>/dev/null || true

# Remove exports (keep directory)
echo "Cleaning exports directory..."
mkdir -p exports 2>/dev/null || true
rm -rf exports/*.xlsx exports/*.pdf 2>/dev/null || true

# Create necessary directories
echo "Creating necessary directories..."
mkdir -p .streamlit logs exports 2>/dev/null || true

echo "✨ Cleanup complete!"
echo ""
echo "📋 Next steps:"
echo "1. Review .env file for sensitive data"
echo "2. Ensure .env is in .gitignore"
echo "3. Test application: streamlit run app.py"
echo "4. Run tests: cd tests && pytest"
echo "5. Commit and push to GitHub"
echo "6. Deploy to Streamlit Community Cloud"
