# src/ef_validator.py
"""
EF (Elemental Function) Validation Module
Validates whether a mechanism graph can satisfy a given elemental function.
"""

from typing import Dict, Tuple, List, Set
from .mechanism_graph import MechanismGraph


def validate_ef_satisfaction(
    graph: MechanismGraph,
    ef: Dict,
    task: Dict
) -> Tuple[bool, str]:
    """
    Validate if a mechanism graph can satisfy a given elemental function.
    
    Args:
        graph: The mechanism graph to validate
        ef: Elemental function dictionary with behavior specification
        task: Full task dictionary (for element mapping)
        
    Returns:
        Tuple of (is_valid, reason_string)
    """
    # Basic checks
    if not graph.is_connected():
        return False, "Graph is not connected"
    
    dof = graph.calculate_dof()
    if dof < 0:
        return False, f"Invalid DOF: {dof} (over-constrained)"
    if dof > 3:
        return False, f"DOF too high: {dof} (under-constrained for single-input mechanism)"
    
    # Check if graph has required elements
    ef_behavior = ef.get('behavior', [])
    task_elements = task.get('elements', {})
    
    # Map element IDs to indices (E1 -> 1, E2 -> 2, etc.)
    element_to_idx = {}
    for elem_id, elem_name in task_elements.items():
        # Extract number from E1, E2, etc.
        try:
            idx = int(elem_id[1:])  # Remove 'E' prefix
            element_to_idx[elem_id] = idx
        except:
            continue
    
    # Check if all elements in EF behavior are present in graph
    required_elements = {beh.get('element') for beh in ef_behavior if 'element' in beh}
    available_elements = set(element_to_idx.keys())
    
    if not required_elements.issubset(available_elements):
        missing = required_elements - available_elements
        return False, f"Missing elements in graph: {missing}"

    # Check Kinematic Type Compatibility (e.g. Linear Motion requirements)
    # Strategy: Identify elements that imply linear motion based on their name in the task definition
    # and ensure they have a Prismatic Joint to Ground if they are moving.
    task_elements = task.get('elements', {})
    linear_keywords = ['bolt', 'rack', 'slider', 'piston', 'ram', 'plunger']
    
    linear_element_ids = []
    for elem_id, elem_name in task_elements.items():
        if any(k in elem_name.lower() for k in linear_keywords):
            linear_element_ids.append(elem_id)
            
    ef_behavior = ef.get('behavior', [])
    for beh in ef_behavior:
        elem_id = beh.get('element')
        motion = beh.get('motion', '0')
        
        # If a known linear element is moving, verify its kinematic constraint
        if elem_id in linear_element_ids and motion != '0':
            try:
                # Convert E2 -> index 2
                elem_idx = int(elem_id[1:])
                # Check connection to Ground (Index 0)
                joint_to_ground = graph.adj_matrix[0, elem_idx]
                
                # UPDATE: Allow 3, 5, 6, and 7 (LSP)
                if joint_to_ground not in [3, 5, 6, 7]:
                     return False, f"Kinematic Mismatch: Element '{elem_id}' ({task_elements.get(elem_id)}) requires Linear Motion (Prismatic Joint to Ground), but found code {joint_to_ground}."
            except (ValueError, IndexError):
                pass

    # Validate behavior patterns based on EF type
    ef_type = ef.get('type', '')
    
    if ef_type == 'Type-1.1':
        # Type-1.1: Input effort on one element, output motion on another
        # Check: At least one element with effort, one with motion
        has_effort = any(beh.get('effort') != '0' for beh in ef_behavior)
        has_motion = any(beh.get('motion') != '0' for beh in ef_behavior)
        if not (has_effort and has_motion):
            return False, "Type-1.1 requires both effort input and motion output"
        # Check connectivity: elements with effort and motion should be connected
        return True, "Type-1.1 pattern validated"
    
    elif ef_type == 'Type-1.2':
        # Type-1.2: Variable constraint (input can be on different element)
        # Similar to Type-1.1 but with variable constraint capability
        has_effort = any(beh.get('effort') != '0' for beh in ef_behavior)
        has_motion = any(beh.get('motion') != '0' for beh in ef_behavior)
        if not (has_effort and has_motion):
            return False, "Type-1.2 requires both effort input and motion output"
        # Check for variable joint (would need more sophisticated check)
        return True, "Type-1.2 pattern validated (variable constraint assumed)"
    
    elif ef_type == 'Type-2':
        # Type-2: Constraint/stopper
        # UPDATE: Allow 5 (LP), 7 (LSP), or -1 (F)
        import numpy as np
        upper_tri = graph.adj_matrix[np.triu_indices(graph.num_elements, k=1)]
        if any(x in upper_tri for x in [5, 7, -1]):
            return True, "Type-2 constraint satisfied"
        return False, "Type-2 requires Stopper"
    
    elif ef_type == 'Type-3':
        # Type-3: Return spring
        # UPDATE: Allow 6 (SP) or 7 (LSP)
        import numpy as np
        upper_tri = graph.adj_matrix[np.triu_indices(graph.num_elements, k=1)]
        if any(x in upper_tri for x in [6, 7]):
            return True, "Type-3 constraint satisfied"
        return False, "Type-3 requires Spring"
    
    else:
        # Unknown type - basic validation only
        return True, f"Unknown EF type '{ef_type}' - basic validation passed"


def check_all_efs_satisfied(
    graph: MechanismGraph,
    satisfied_ef_ids: Set[str],
    task: Dict
) -> Tuple[bool, List[str]]:
    """
    Check if all required EFs are satisfied and return list of unsatisfied EFs.
    
    Args:
        graph: Current mechanism graph
        satisfied_ef_ids: Set of EF IDs that are marked as satisfied
        task: Full task dictionary
        
    Returns:
        Tuple of (all_satisfied, list_of_unsatisfied_ef_ids)
    """
    all_ef_ids = {ef['ef_id'] for ef in task.get('elemental_functions', [])}
    unsatisfied = all_ef_ids - satisfied_ef_ids
    
    # Additionally validate that satisfied EFs are actually valid
    validated_satisfied = set()
    for ef_id in satisfied_ef_ids:
        ef = next((e for e in task['elemental_functions'] if e['ef_id'] == ef_id), None)
        if ef:
            is_valid, _ = validate_ef_satisfaction(graph, ef, task)
            if is_valid:
                validated_satisfied.add(ef_id)
            else:
                unsatisfied.add(ef_id)  # Mark as unsatisfied if validation fails
    
    all_satisfied = len(unsatisfied) == 0
    return all_satisfied, list(unsatisfied)

