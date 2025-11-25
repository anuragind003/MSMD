# MSMD-Synthesizer

**A Graph-Based Synthesis Tool for Multi-State Mechanical Devices**

## Project Overview

MSMD-Synthesizer is a computational tool designed to automate the type synthesis of multi-state mechanical devices (MSMDs). The tool translates behavioral requirements, specified as Elemental Functions (EFs), into valid mechanism topologies using graph-based representations, constraint satisfaction, and heuristic search algorithms.

## Current Status: Phase 1 Complete ✅

Phase 1 has been successfully completed, establishing the foundational framework for the synthesis tool.

## Project Structure

```
MSMD-Synthesizer/
├── tasks/                          # Design task definitions
│   └── door_latch_task.json       # Example door latch mechanism task
├── knowledge_base/                 # Knowledge representation
│   ├── building_blocks.json       # Known mechanism building blocks
│   └── transformation_rules.json  # Rules for mechanism modification
├── src/                           # Source code
│   ├── __init__.py                # Package initialization
│   ├── mechanism_graph.py         # Core MechanismGraph class
│   └── main.py                    # Demonstration script
├── requirements.txt               # Python dependencies
└── README.md                      # This file
```

## Installation

1. Clone or download the project
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Quick Start

Run the Phase 1 demonstration:

```bash
cd MSMD-Synthesizer/src
python main.py
```

This will:

- Load the knowledge base and design task files
- Demonstrate the MechanismGraph class with slider-crank and four-bar linkage examples
- Show DOF calculations and connectivity analysis
- Display available building blocks and transformation rules

## Key Features (Phase 1)

### MechanismGraph Class

- **Topology Representation**: Uses adjacency matrices to represent mechanism topologies
- **DOF Calculation**: Implements Grubler's formula for degrees of freedom calculation
- **Visualization**: Creates graph visualizations using NetworkX and Matplotlib
- **Connectivity Analysis**: Checks mechanism connectivity and provides statistics

### Knowledge Base

- **Building Blocks**: 10+ fundamental mechanisms (slider-crank, rack-and-pinion, etc.)
- **Transformation Rules**: 10+ rules for mechanism modification
- **Design Tasks**: JSON-based task specification format

### Example Mechanisms

- **Slider-Crank**: 4-element mechanism with 1 DOF
- **Four-Bar Linkage**: 4-element mechanism with 1 DOF
- **Door Latch Task**: Complete design specification with 4 elemental functions

## Phase 1 Deliverables

✅ **Project Structure**: Organized directory structure with clear separation of concerns  
✅ **JSON Schemas**: Machine-readable task definitions and knowledge base  
✅ **MechanismGraph Class**: Core class for mechanism representation and analysis  
✅ **DOF Calculation**: Accurate degrees of freedom computation  
✅ **Visualization**: Graph-based mechanism topology visualization  
✅ **Demonstration Script**: Complete validation of Phase 1 functionality

## Next Steps: Phase 2

Phase 2 will focus on implementing the core synthesis engine:

1. **Initial Topology Generation**: Algorithm to generate valid initial solutions
2. **A\* Search Implementation**: Heuristic search for mechanism modification
3. **Transformation Integration**: Apply transformation rules to resolve mismatches
4. **Synthesis Engine**: Complete synthesis_engine.py module

## Technical Details

### Joint Types

- **R**: Revolute joint (1 DOF constraint)
- **P**: Prismatic joint (1 DOF constraint)
- **X**: Higher pair joint (2 DOF constraint)
- **F**: Fixed joint (-1 DOF constraint)

### DOF Formula

```
F = 3(n₀ - n₋₁ - 1) - 2n₁ - n₂
```

Where:

- n₀ = total number of elements
- n₋₁ = number of fixed joints
- n₁ = number of lower pairs (R, P)
- n₂ = number of higher pairs (X)

## Contributing

This project is currently in active development. Phase 1 provides the foundation for the synthesis algorithms to be implemented in subsequent phases.

## License

This project is part of academic research in mechanical design automation.
