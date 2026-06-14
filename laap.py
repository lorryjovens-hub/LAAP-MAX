#!/usr/bin/env python
"""LAAP - Lifeform Autonomous Adaptive Protocol"""
import sys, os
_this_dir = os.path.dirname(os.path.abspath(__file__))
if _this_dir not in sys.path:
    sys.path.insert(0, _this_dir)
from laap.__main__ import main
sys.exit(main())
