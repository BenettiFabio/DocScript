import sys
from pathlib import Path

from src.cli import main

###############
# Description #
###############
"""
Entry Point of DocScript subModule! Enjoy
"""

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))

if __name__ == "__main__":
    main()
