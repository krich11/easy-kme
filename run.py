#!/usr/bin/env python3
"""
Launcher script for Easy-KME server.
"""

import sys
import os
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.main import run_server

if __name__ == "__main__":
    run_server() 
