# src/main.py
import json
import os
import sys
from mechanism_graph import MechanismGraph
from initial_solution import find_initial_solutions
from synthesis_engine import run_synthesis_for_all_initial_solutions

def load_json_file(filepath: str) -> dict:
    """
    A helper function to load and parse a JSON file.
    
    Args:
        filepath (str): Path to the JSON file
        
    Returns:
        dict: Parsed JSON data or None if file not found
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: Could not find file at {filepath}")
        return None
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in file {filepath}: {e}")
        return None

def create_slider_crank() -> MechanismGraph:
    """
    Creates a slider-crank mechanism for demonstration.
    
    Returns:
        MechanismGraph: Configured slider-crank mechanism
    """
    # E0=Ground, E1=Crank, E2=Coupler, E3=Slider
    slider_crank = MechanismGraph(num_elements=4)
    slider_crank.add_joint(0, 1, 'R')  # Ground to Crank
    slider_crank.add_joint(1, 2, 'R')  # Crank to Coupler
    slider_crank.add_joint(2, 3, 'R')  # Coupler to Slider
    slider_crank.add_joint(0, 3, 'P')  # Ground to Slider (prismatic constraint)
    return slider_crank

def create_four_bar_linkage() -> MechanismGraph:
    """
    Creates a four-bar linkage mechanism for demonstration.
    
    Returns:
        MechanismGraph: Configured four-bar linkage mechanism
    """
    # E0=Ground, E1=Input, E2=Coupler, E3=Output
    four_bar = MechanismGraph(num_elements=4)
    four_bar.add_joint(0, 1, 'R')  # Ground to Input
    four_bar.add_joint(1, 2, 'R')  # Input to Coupler
    four_bar.add_joint(2, 3, 'R')  # Coupler to Output
    four_bar.add_joint(0, 3, 'R')  # Ground to Output
    return four_bar

def run_phase1_demo():
    """Demonstrates the functionality completed in Phase 1."""
    print("=" * 60)
    print("MSMD-Synthesizer: Phase 1 Demo")
    print("=" * 60)

    # 1. Load Knowledge and Task Files
    print("\n[1] Loading knowledge base and design task...")
    
    # Get the directory of the current script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    
    door_latch_task = load_json_file(os.path.join(project_root, 'tasks', 'door_latch_task.json'))
    building_blocks = load_json_file(os.path.join(project_root, 'knowledge_base', 'building_blocks.json'))
    rules = load_json_file(os.path.join(project_root, 'knowledge_base', 'transformation_rules.json'))

    if not all([door_latch_task, building_blocks, rules]):
        print("Failed to load one or more files. Exiting.")
        return

    print(" ✓ Successfully loaded all files.")
    print(f" ✓ Task: {door_latch_task['task_name']}")
    print(f" ✓ Found {len(building_blocks['mechanisms'])} building blocks.")
    print(f" ✓ Found {len(rules['rules'])} transformation rules.")

    # 2. Demonstrate MechanismGraph for a Slider-Crank
    print("\n[2] Demonstrating MechanismGraph with a 4-bar Slider-Crank...")
    
    slider_crank = create_slider_crank()
    print(slider_crank)
    
    # 3. Calculate and Display DOF
    dof = slider_crank.calculate_dof()
    print(f"\n[3] Calculated DOF for Slider-Crank: {dof}")
    assert dof == 1, "DOF calculation for slider-crank should be 1!"
    print(" ✓ DOF calculation is correct.")

    # 4. Test connectivity
    print(f"\n[4] Connectivity Analysis:")
    connectivity = slider_crank.get_connectivity_info()
    print(f" ✓ Connected: {connectivity['is_connected']}")
    print(f" ✓ Number of components: {connectivity['num_components']}")

    # 5. Demonstrate Four-Bar Linkage
    print("\n[5] Demonstrating Four-Bar Linkage...")
    four_bar = create_four_bar_linkage()
    print(four_bar)
    
    four_bar_dof = four_bar.calculate_dof()
    print(f" ✓ Four-bar DOF: {four_bar_dof}")
    assert four_bar_dof == 1, "DOF calculation for four-bar should be 1!"

    # 6. Display task information
    print("\n[6] Design Task Analysis:")
    print(f" ✓ Task: {door_latch_task['task_name']}")
    print(f" ✓ Elements: {list(door_latch_task['elements'].keys())}")
    print(f" ✓ States: {len(door_latch_task['states'])}")
    print(f" ✓ Elemental Functions: {len(door_latch_task['elemental_functions'])}")
    
    print("\nElemental Functions:")
    for ef in door_latch_task['elemental_functions']:
        print(f"  - {ef['ef_id']}: {ef['description']}")

    # 7. Display building blocks
    print(f"\n[7] Available Building Blocks:")
    for mechanism in building_blocks['mechanisms'][:5]:  # Show first 5
        print(f"  - {mechanism['name']}: {mechanism['description']}")
    if len(building_blocks['mechanisms']) > 5:
        print(f"  ... and {len(building_blocks['mechanisms']) - 5} more")

    # 8. Display transformation rules
    print(f"\n[8] Available Transformation Rules:")
    for rule in rules['rules'][:5]:  # Show first 5
        print(f"  - {rule['rule_id']}: {rule['description']}")
    if len(rules['rules']) > 5:
        print(f"  ... and {len(rules['rules']) - 5} more")

    print("\n" + "=" * 60)
    print("Phase 1 Demo Completed Successfully!")
    print("=" * 60)
    print("\nNext Steps for Phase 2:")
    print("1. Implement initial topology generation algorithm")
    print("2. Develop A* search for mechanism modification")
    print("3. Integrate transformation rules with synthesis engine")

def run_phase2_demo():
    """Demonstrates the full synthesis pipeline from Phase 2."""
    print("=" * 60)
    print("MSMD-Synthesizer: Phase 2 Full Synthesis Demo")
    print("=" * 60)

    # 1. Load Task
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    
    task = load_json_file(os.path.join(project_root, 'tasks', 'door_latch_task.json'))
    if not task:
        print("Failed to load task file. Exiting.")
        return

    print(f"\n[1] Loaded Task: {task['task_name']}")
    print(f"    Elements: {list(task['elements'].keys())}")
    print(f"    Elemental Functions: {len(task['elemental_functions'])}")
    for ef in task['elemental_functions']:
        print(f"      - {ef['ef_id']}: {ef['description']} ({ef['type']})")

    # 2. Find Initial Solutions
    print("\n[2] Finding Initial Solutions...")
    initial_solutions = find_initial_solutions(task)
    if not initial_solutions:
        print("Could not find any initial solutions. Process halted.")
        return
        
    print(f"\nFound {len(initial_solutions)} potential starting point(s).")
    
    # 3. Run Synthesis for each Initial Solution
    print("\n[3] Running A* Synthesis...")
    final_solutions = run_synthesis_for_all_initial_solutions(task, initial_solutions)

    # 4. Display Results
    print("\n" + "=" * 60)
    print("SYNTHESIS COMPLETE")
    print("=" * 60)
    
    if not final_solutions:
        print("No valid final mechanisms were synthesized.")
        print("\nPossible reasons:")
        print("- No suitable transformation rules found")
        print("- Search space too constrained")
        print("- Need more sophisticated rule application")
    else:
        print(f"Successfully synthesized {len(final_solutions)} valid mechanism(s):")
        
        for i, solution_node in enumerate(final_solutions):
            print(f"\n--- Solution #{i+1} ---")
            print(f"Modification Path: {' -> '.join(solution_node.path)}")
            print(f"Final DOF: {solution_node.graph.calculate_dof()}")
            print(f"Connected: {solution_node.graph.is_connected()}")
            print("Final Adjacency Matrix:")
            print(solution_node.graph.adj_matrix)
            
            # Visualize the final solution
            try:
                solution_node.graph.visualize(f"Final Solution #{i+1} Topology")
            except Exception as e:
                print(f"Visualization failed: {e}")

    print("\n" + "=" * 60)
    print("Phase 2 Demo Completed!")
    print("=" * 60)
    print("\nKey Achievements:")
    print("✓ Initial solution generation from knowledge base")
    print("✓ A* search algorithm for mechanism modification")
    print("✓ Integration of transformation rules")
    print("✓ Complete synthesis pipeline")
    print("\nNext Steps for Phase 3:")
    print("1. Enhanced visualization and user interface")
    print("2. Improved rule application algorithms")
    print("3. Performance optimization and testing")

if __name__ == '__main__':
    # Run Phase 1 demo first
    print("Running Phase 1 Demo...")
    run_phase1_demo()
    
    print("\n" + "="*80 + "\n")
    
    # Run Phase 2 demo
    print("Running Phase 2 Demo...")
    run_phase2_demo()
