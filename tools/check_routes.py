#!/usr/bin/env python3
"""
Check API server routes
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from api_server import app
    
    print("🔍 Checking API Server Routes")
    print("=" * 40)
    
    for route in app.routes:
        methods = getattr(route, 'methods', None)
        path = getattr(route, 'path', 'N/A')
        print(f"  {methods} {path}")
    
    print("\n✅ Route check complete")
    
except Exception as e:
    print(f"❌ Error checking routes: {e}")
    import traceback
    traceback.print_exc()
