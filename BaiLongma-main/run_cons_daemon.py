#!/usr/bin/env python3
"""Wrapper to run aris_body_bridge daemon with logging to file."""
import sys
import os

log_path = os.path.expanduser("~/.hermes/shared/cons-daemon.log")
os.makedirs(os.path.dirname(log_path), exist_ok=True)

with open(log_path, "a", buffering=1) as log:
    sys.stdout = log
    sys.stderr = log

    from aris_body_bridge import daemon_loop
    daemon_loop()
