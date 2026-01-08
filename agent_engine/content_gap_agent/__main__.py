"""Entry point for running as a module: python -m content_gap_agent"""

import sys

from .cli import main

if __name__ == "__main__":
    sys.exit(main())
