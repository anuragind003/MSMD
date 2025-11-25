# MSMD-Synthesizer Package
"""
MSMD-Synthesizer: A Graph-Based Synthesis Tool for Multi-State Mechanical Devices

This package provides tools for automated synthesis of multi-state mechanical devices
using graph-based representations and constraint satisfaction techniques.

Phase 1: Foundational Framework and Knowledge Representation
- MechanismGraph class for representing mechanism topologies
- JSON-based knowledge base for building blocks and transformation rules
- DOF calculation and visualization capabilities
"""

__version__ = "1.0.0"
__author__ = "MSMD-Synthesizer Team"

from .mechanism_graph import MechanismGraph
from .initial_solution import find_initial_solutions
from .synthesis_engine import run_synthesis_for_all_initial_solutions

__all__ = ['MechanismGraph', 'find_initial_solutions', 'run_synthesis_for_all_initial_solutions']
