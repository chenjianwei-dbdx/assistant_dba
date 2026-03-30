"""Test configuration for backend tests"""
import sys
from pathlib import Path

# Add backend/src to path for imports
backend_src = Path(__file__).parent.parent / "src"
if str(backend_src) not in sys.path:
    sys.path.insert(0, str(backend_src))