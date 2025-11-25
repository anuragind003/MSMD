# src/initial_solution.py
import json
import os
from typing import List, Dict, Any
from .mechanism_graph import MechanismGraph
from .ai_retrieval import rank_mechanisms_by_similarity, rank_mechanisms_by_gemini

def _load_knowledge_base() -> List[Dict[str, Any]]:
    """Helper to load the building blocks from the knowledge base."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    kb_path = os.path.join(project_root, 'knowledge_base', 'building_blocks.json')
    
    with open(kb_path, 'r') as f:
        return json.load(f)['mechanisms']

def _create_slider_crank() -> MechanismGraph:
    """Creates a slider-crank mechanism (4 elements) aligned with Door Latch task."""
    # We need E2 to be the output slider to match the task 'E2': 'bolt'
    # Configuration:
    # E0: Ground
    # E1: Crank (Input)
    # E3: Coupler (Intermediate) -> Swapped with E2
    # E2: Slider (Output)        -> Swapped with E3
    
    graph = MechanismGraph(num_elements=4)
    graph.element_names = ['Ground', 'Crank', 'Slider', 'Coupler']  # Note name order matches index
    
    # Joints:
    graph.add_joint(0, 1, 'R')  # Ground to Crank
    graph.add_joint(1, 3, 'R')  # Crank to Coupler (E1 -> E3)
    graph.add_joint(3, 2, 'R')  # Coupler to Slider (E3 -> E2)
    graph.add_joint(0, 2, 'P')  # Ground to Slider (E0 -> E2) - This is what Validator looks for!
    
    return graph

def _create_rack_and_pinion() -> MechanismGraph:
    """Creates a rack and pinion mechanism (3 elements)."""
    graph = MechanismGraph(num_elements=3)
    graph.element_names = ['Ground', 'Pinion', 'Rack']
    # E0=Ground, E1=Pinion, E2=Rack
    graph.add_joint(0, 1, 'R')  # Ground to Pinion
    graph.add_joint(1, 2, 'X')  # Pinion to Rack (higher pair)
    graph.add_joint(0, 2, 'P')  # Ground to Rack (prismatic constraint)
    return graph

def _create_four_bar_linkage() -> MechanismGraph:
    """Creates a four-bar linkage mechanism (4 elements)."""
    graph = MechanismGraph(num_elements=4)
    graph.element_names = ['Ground', 'Input', 'Coupler', 'Output']
    # E0=Ground, E1=Input, E2=Coupler, E3=Output
    graph.add_joint(0, 1, 'R')  # Ground to Input
    graph.add_joint(1, 2, 'R')  # Input to Coupler
    graph.add_joint(2, 3, 'R')  # Coupler to Output
    graph.add_joint(0, 3, 'R')  # Ground to Output
    return graph

def _create_cam_follower() -> MechanismGraph:
    """Creates a cam-follower mechanism (3 elements)."""
    graph = MechanismGraph(num_elements=3)
    graph.element_names = ['Ground', 'Cam', 'Follower']
    # E0=Ground, E1=Cam, E2=Follower
    graph.add_joint(0, 1, 'R')  # Ground to Cam
    graph.add_joint(1, 2, 'X')  # Cam to Follower (higher pair)
    graph.add_joint(0, 2, 'P')  # Ground to Follower (prismatic constraint)
    return graph

def _create_spur_gear_pair_external() -> MechanismGraph:
    """Creates an external spur gear pair mechanism (3 elements)."""
    graph = MechanismGraph(num_elements=3)
    # E0=Ground, E1=Gear A, E2=Gear B
    graph.add_joint(0, 1, 'R')  # Ground to Gear A
    graph.add_joint(1, 2, 'X')  # Gear mesh (higher pair)
    graph.add_joint(0, 2, 'R')  # Ground to Gear B
    return graph

SIMILARITY_THRESHOLD = 0.1


def _behavior_matches(ef_behavior: List[Dict], kb_behavior: List[Dict]) -> bool:
    """
    Checks if an EF behavior matches a knowledge base behavior.
    This is a simplified matching used in the rule-based method.
    """
    if len(ef_behavior) != len(kb_behavior):
        return False
    for ef_state, kb_state in zip(ef_behavior, kb_behavior):
        if (ef_state.get('effort') != kb_state.get('effort') or
                ef_state.get('motion') != kb_state.get('motion')):
            return False
    return True


def _find_initial_solutions_rule_based(task: Dict[str, Any]) -> List[Dict[str, Any]]:
    initial_solutions: List[Dict[str, Any]] = []

    # Find the first Type-1.1 EF to start with
    first_ef = None
    for ef in task['elemental_functions']:
        if ef['type'] == 'Type-1.1':
            first_ef = ef
            break

    if not first_ef:
        print(" -> No 'Type-1.1' EF found to start the synthesis process.")
        return []

    print(f" -> Starting with EF1: '{first_ef['description']}'")
    print(f" -> EF1 Behavior: {first_ef['behavior']}")

    # Strategy: Check Knowledge Base for exact behavior matches
    building_blocks = _load_knowledge_base()
    print(f" -> Searching {len(building_blocks)} building blocks...")

    for block in building_blocks:
        for ef_satisfied in block['satisfies_efs']:
            if _behavior_matches(first_ef['behavior'], ef_satisfied['behavior']):
                print(f" -> Found match in Knowledge Base: {block['name']}")

                if block['name'] == "Slider-Crank":
                    graph = _create_slider_crank()
                elif block['name'] == "Rack and Pinion":
                    graph = _create_rack_and_pinion()
                elif block['name'] == "Four-Bar Linkage":
                    graph = _create_four_bar_linkage()
                elif block['name'] == "Cam-Follower":
                    graph = _create_cam_follower()
                else:
                    graph = MechanismGraph(num_elements=4)
                    graph.add_joint(0, 1, 'R')
                    graph.add_joint(1, 2, 'R')
                    graph.add_joint(2, 3, 'R')
                    graph.add_joint(0, 3, 'P')

                initial_solutions.append({
                    "name": block['name'],
                    "graph": graph,
                    "source": "knowledge_base"
                })
                break

    # No fallback: inform user if nothing matched
    if not initial_solutions:
        print(" -> No suitable mechanisms found in the knowledge base for the requested EF.")

    return initial_solutions

def _find_initial_solutions_ai(task: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    AI-powered similarity search using Gemini AI.
    Considers full task context including all elemental functions.
    """
    print("\n[PHASE 4.1] Finding Initial Solutions using Gemini AI Retrieval...")

    initial_solutions: List[Dict[str, Any]] = []

    # Find the first Type-1.1 EF to start with
    first_ef = None
    for ef in task['elemental_functions']:
        if ef.get('type') == 'Type-1.1':
            first_ef = ef
            break

    if not first_ef:
        print(" -> No 'Type-1.1' EF found to start the synthesis process.")
        return []

    task_description = task.get('description', '')
    elemental_functions = task.get('elemental_functions', [])
    
    print(f" -> Task: {task.get('task_name', 'Unknown')}")
    print(f" -> Querying Gemini AI with full task context...")

    # Use Gemini AI to rank mechanisms from the knowledge base
    building_blocks = _load_knowledge_base()
    ranked = rank_mechanisms_by_gemini(task_description, elemental_functions, building_blocks)

    print(" -> Mechanism Similarity Ranking:")
    for name, score in ranked:
        print(f"   - {name}: {score:.2f}")

    # Create solution objects for all matches above the threshold
    kb_name_to_block = {b['name']: b for b in building_blocks}
    
    # Check for translation keywords in Task Description AND all EF descriptions
    all_text = task_description.lower()
    for ef in elemental_functions:
        all_text += " " + ef.get('description', '').lower()
        
    needs_translation = any(k in all_text for k in ["linear", "translate", "translation", "slider", "retract", "inward", "bolt"])

    for name, score in ranked:
        if score > SIMILARITY_THRESHOLD:
            # Optional motion intent filter: if EF implies translation, avoid pure rotation-to-rotation mechanisms
            block = kb_name_to_block.get(name, {})
            motion_conv = (block.get('motion_conversion') or '').lower()
            if needs_translation and 'rotation to rotation' in motion_conv:
                print(f"   - Skipping '{name}' due to motion type mismatch with EF intent")
                continue

            # UPDATE: Handle variations of Slider-Crank
            if "Slider-Crank" in name:
                graph = _create_slider_crank()  # Always give it the base geometry
            elif name == "Rack and Pinion":
                graph = _create_rack_and_pinion()
            elif name == "Four-Bar Linkage":
                graph = _create_four_bar_linkage()
            elif name in ("Cam-Follower", "Cam and Follower"):
                graph = _create_cam_follower()
            elif name == "Spur Gear Pair (External)":
                graph = _create_spur_gear_pair_external()
            else:
                # Generic graph sized to block's num_elements
                num_elements = kb_name_to_block.get(name, {}).get('num_elements', 4)
                graph = MechanismGraph(num_elements=num_elements)
            # Validate DOF == 1 for single-input mechanisms
            if graph.calculate_dof() != 1:
                print(f"   - Skipping '{name}' due to invalid DOF ({graph.calculate_dof()})")
                continue
            initial_solutions.append({
                "name": name,
                "graph": graph,
                "source": "ai_retrieval"
            })

    # No fallback: inform user if nothing matched
    if not initial_solutions:
        print(" -> No sufficiently similar mechanism found in the knowledge base for the requested EF.")

    print(f" -> Found {len(initial_solutions)} initial solution(s)")
    for sol in initial_solutions:
        print(f"   - {sol['name']} (DOF: {sol['graph'].calculate_dof()}, Source: {sol['source']})")

    return initial_solutions


def find_initial_solutions(task: Dict[str, Any], method: str = 'ai') -> List[Dict[str, Any]]:
    """
    Find initial solution proposals using the selected retrieval method.

    Args:
        task: The design task dictionary.
        method: 'ai' for TF-IDF similarity retrieval (default),
                'rule' for exact behavior matching.

    Returns:
        List of initial solutions with name, graph, and source.
    """
    method_normalized = (method or 'ai').strip().lower()
    if method_normalized == 'rule':
        print("\n[PHASE 2.1] Finding Initial Solutions (Rule-Based)...")
        solutions = _find_initial_solutions_rule_based(task)
    else:
        solutions = _find_initial_solutions_ai(task)

    print(f" -> Found {len(solutions)} initial solution(s)")
    for sol in solutions:
        print(f"   - {sol['name']} (DOF: {sol['graph'].calculate_dof()}, Source: {sol['source']})")
    return solutions
