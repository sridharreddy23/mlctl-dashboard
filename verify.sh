#!/bin/bash

echo "🔍 MLCtl Dashboard Verification"
echo "================================"
echo ""

# Check backend
echo "📦 Backend:"
if [ -f backend/main.py ] && [ -f backend/mlctl_core.py ] && [ -f backend/requirements.txt ]; then
    echo "  ✓ Core files present"
else
    echo "  ✗ Missing core files"
    exit 1
fi

# Check frontend
echo "🎨 Frontend:"
if [ -f frontend/package.json ] && [ -f frontend/src/App.vue ] && [ -d frontend/src/components ]; then
    echo "  ✓ Core files present"
else
    echo "  ✗ Missing core files"
    exit 1
fi

# Check frontend build
if [ -d frontend/dist ] && [ -f frontend/dist/index.html ]; then
    echo "  ✓ Built and ready"
else
    echo "  ⚠ Not built yet (run: cd frontend && npm run build)"
fi

# Check dependencies
echo "📚 Dependencies:"
if [ -d backend/venv ]; then
    echo "  ✓ Backend venv ready"
else
    echo "  ⚠ Backend venv not created"
fi

if [ -d frontend/node_modules ]; then
    echo "  ✓ Frontend node_modules ready"
else
    echo "  ⚠ Frontend node_modules not installed"
fi

echo ""
echo "✨ All checks passed!"
echo ""
echo "Next steps:"
echo "1. Set environment variables in .env file"
echo "2. Run: ./start.sh"
echo "3. Visit: http://localhost:5173"
