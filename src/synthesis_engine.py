# src/synthesis_engine.py
import heapq
import json
import copy
import os
from typing import List, Dict, Any, Optional, Set, Tuple
from .mechanism_graph import MechanismGraph
from .ef_validator import validate_ef_satisfaction, check_all_efs_satisfied
from .synthesis_visualizer import SynthesisVisualizer

class SearchNode:
    """Represents a state in the A* search space."""
    
    def __init__(
        self, 
        graph: MechanismGraph, 
        satisfied_efs: Set[str], 
        path: Optional[List[str]] = None,
        satisfied_ef_types: Optional[Set[str]] = None
    ):
        """
        Initialize a search node.
        
        Args:
            graph: The current mechanism graph
            satisfied_efs: Set of satisfied EF IDs
            path: List of rule IDs applied to reach this state
            satisfied_ef_types: Set of satisfied EF types (e.g., {'Type-1.1', 'Type-2'})
        """
        self.graph = graph
        self.satisfied_efs = set(satisfied_efs)
        self.path = path if path else []
        # Track which EF types are satisfied (for dynamic rule matching)
        self.satisfied_ef_types = set(satisfied_ef_types) if satisfied_ef_types else set()

    def __lt__(self, other):
        """For heapq comparison - this is a placeholder since priority is handled externally."""
        return len(self.path) < len(other.path)

    def get_state_tuple(self) -> Tuple:
        """Creates a hashable representation of the state for the visited set."""
        # Convert adj matrix to a tuple of tuples to make it hashable
        matrix_tuple = tuple(map(tuple, self.graph.adj_matrix))
        # frozenset is a hashable, immutable set
        efs_tuple = frozenset(self.satisfied_efs)
        return (matrix_tuple, efs_tuple)

    def __str__(self) -> str:
        """String representation for debugging."""
        return f"SearchNode(satisfied_efs={self.satisfied_efs}, types={self.satisfied_ef_types}, path={self.path})"

def _load_transformation_rules() -> List[Dict[str, Any]]:
    """Load transformation rules from the knowledge base."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    rules_path = os.path.join(project_root, 'knowledge_base', 'transformation_rules.json')
    
    with open(rules_path, 'r') as f:
        return json.load(f)['rules']

def _apply_rule_to_graph(graph: MechanismGraph, rule: Dict[str, Any]) -> MechanismGraph:
    """
    Apply a transformation rule to a mechanism graph.
    This is a simplified implementation - in a real system, this would be more sophisticated.
    
    Args:
        graph: The mechanism graph to modify
        rule: The transformation rule to apply
        
    Returns:
        Modified mechanism graph
    """
    new_graph = copy.deepcopy(graph)
    num_elements = new_graph.num_elements
    
    # Get the operation type
    operation = rule.get('suggested_operation', '')
    
    if operation == 'ADD_REVOLUTE_JOINT':
        # Add a revolute joint between two elements
        # For simplicity, add between elements 0 and 1 if not already connected
        if num_elements > 1 and new_graph.adj_matrix[0, 1] == 0:
            new_graph.add_joint(0, 1, 'R')
    
    elif operation == 'ADD_PRISMATIC_JOINT':
        # Add a prismatic joint between two elements
        if num_elements > 2 and new_graph.adj_matrix[0, 2] == 0:
            new_graph.add_joint(0, 2, 'P')
        elif num_elements > 1 and new_graph.adj_matrix[0, 1] == 0:
            new_graph.add_joint(0, 1, 'P')
    
    elif operation == 'ADD_VARIABLE_JOINT':
        # Add a variable constraint joint (simplified as a revolute for now)
        if num_elements > 2 and new_graph.adj_matrix[1, 2] == 0:
            new_graph.add_joint(1, 2, 'R')
        elif num_elements > 1 and new_graph.adj_matrix[0, 1] == 0:
            new_graph.add_joint(0, 1, 'R')
    
    elif operation == 'ADD_STOPPER':
        modified = False
        for i in range(num_elements):
            for j in range(i + 1, num_elements):
                curr = new_graph.adj_matrix[i, j]
                if curr == 3:  # Prismatic -> Limited
                    new_graph.adj_matrix[i, j] = 5  # LP
                    new_graph.adj_matrix[j, i] = 5
                    modified = True
                    break
                elif curr == 6:  # Spring -> Limited Spring
                    new_graph.adj_matrix[i, j] = 7  # LSP
                    new_graph.adj_matrix[j, i] = 7
                    modified = True
                    break
            if modified:
                break
        
        if not modified and num_elements > 1 and new_graph.adj_matrix[0, 1] == 0:
            new_graph.add_joint(0, 1, 'F')
    
    elif operation == 'ADD_RETURN_SPRING':
        modified = False
        for i in range(num_elements):
            for j in range(i + 1, num_elements):
                curr = new_graph.adj_matrix[i, j]
                if curr == 3:  # Prismatic -> Spring
                    new_graph.adj_matrix[i, j] = 6  # SP
                    new_graph.adj_matrix[j, i] = 6
                    modified = True
                    break
                elif curr == 5:  # Limited -> Limited Spring
                    new_graph.adj_matrix[i, j] = 7  # LSP
                    new_graph.adj_matrix[j, i] = 7
                    modified = True
                    break
            if modified:
                break
    
    elif operation == 'ADD_DAMPER':
        # Add a damping element - simplified as adding a prismatic joint
        if num_elements > 3 and new_graph.adj_matrix[2, 3] == 0:
            new_graph.add_joint(2, 3, 'P')
        elif num_elements > 2 and new_graph.adj_matrix[1, 2] == 0:
            new_graph.add_joint(1, 2, 'P')
        elif num_elements > 1 and new_graph.adj_matrix[0, 1] == 0:
            new_graph.add_joint(0, 1, 'P')
    
    elif operation == 'ADD_OVER_CENTER':
        # Add over-center mechanism - simplified as adding a revolute joint
        if num_elements > 1 and new_graph.adj_matrix[0, 1] == 0:
            new_graph.add_joint(0, 1, 'R')
    
    elif operation == 'ADD_CAM_MECHANISM':
        # Add cam mechanism - simplified as adding a higher pair joint
        if num_elements > 2 and new_graph.adj_matrix[1, 2] == 0:
            new_graph.add_joint(1, 2, 'X')
        elif num_elements > 1 and new_graph.adj_matrix[0, 1] == 0:
            new_graph.add_joint(0, 1, 'X')
    
    elif operation == 'ADD_GEAR_TRAIN':
        # Add gear train - simplified as adding a higher pair joint
        if num_elements > 2 and new_graph.adj_matrix[0, 2] == 0:
            new_graph.add_joint(0, 2, 'X')
        elif num_elements > 1 and new_graph.adj_matrix[0, 1] == 0:
            new_graph.add_joint(0, 1, 'X')
    
    elif operation == 'ADD_LINK':
        # Add a link - this would require increasing the number of elements
        # For simplicity, we'll just add a joint between existing elements
        if num_elements > 1 and new_graph.adj_matrix[0, 1] == 0:
            new_graph.add_joint(0, 1, 'R')
    
    return new_graph

def run_synthesis(
    task: Dict[str, Any], 
    initial_solution: Dict[str, Any],
    enable_visualization: bool = True
) -> Optional[SearchNode]:
    """
    Uses A* search to find a sequence of modifications to satisfy all EFs.
    Now with dynamic EF type tracking, validation, and step-by-step visualization.
    
    Args:
        task: The design task dictionary
        initial_solution: The initial solution to start from
        enable_visualization: Whether to save step-by-step visualizations
        
    Returns:
        SearchNode representing the final solution, or None if no solution found
    """
    print(f"\n[PHASE 2.2] Starting A* Synthesis for '{initial_solution['name']}'...")
    
    rules = _load_transformation_rules()
    all_ef_ids = {ef['ef_id'] for ef in task['elemental_functions']}
    # Initialize visualizer
    visualizer = None
    if enable_visualization:
        task_name = task.get('task_name', 'Unknown_Task')
        visualizer = SynthesisVisualizer(task_name, initial_solution['name'])
        # Save initial state
        first_ef = next((ef for ef in task['elemental_functions'] if ef['ef_id'] == 'EF1'), None)
        first_ef_type = first_ef.get('type', 'Unknown') if first_ef else 'Unknown'
        visualizer.save_step(
            initial_solution['graph'],
            iteration=0,
            satisfied_efs=['EF1'],
            description=f"Initial: {first_ef_type}",
            task=task
        )
    
    # Find first EF and its type
    first_ef = next((ef for ef in task['elemental_functions'] if ef['ef_id'] == 'EF1'), None)
    if not first_ef:
        print("Error: No EF1 found in task")
        return None
    
    first_ef_type = first_ef.get('type', 'Type-1.1')
    
    # Validate initial solution satisfies EF1
    is_valid, reason = validate_ef_satisfaction(initial_solution['graph'], first_ef, task)
    if not is_valid:
        print(f"Warning: Initial solution may not satisfy EF1: {reason}")
    
    # Start with the first EF satisfied (EF1)
    start_node = SearchNode(
        initial_solution['graph'], 
        satisfied_efs={'EF1'},
        satisfied_ef_types={first_ef_type}
    )
    
    # Priority Queue (Open List): (priority, cost, node)
    # Priority = cost + heuristic
    initial_heuristic = len(all_ef_ids) - 1  # Number of unsatisfied EFs
    open_list = [(initial_heuristic, 0, start_node)]
    
    # Closed List: Stores hashable state tuples of visited nodes
    visited = {start_node.get_state_tuple()}
    
    iteration = 0
    max_iterations = 100  # Prevent infinite loops
    
    while open_list and iteration < max_iterations:
        iteration += 1
        priority, cost, current_node = heapq.heappop(open_list)
        
        print(f" -> Iteration {iteration}: {current_node}")
        
        # GOAL CHECK with validation
        all_satisfied, unsatisfied_list = check_all_efs_satisfied(
            current_node.graph,
            current_node.satisfied_efs,
            task
        )
        if all_satisfied:
            print(" -> GOAL REACHED! Found a valid modification path.")
            print(f" -> Final path: {' -> '.join(current_node.path)}")
            if visualizer:
                visualizer.save_step(
                    current_node.graph,
                    iteration=iteration,
                    satisfied_efs=list(current_node.satisfied_efs),
                    description="FINAL SOLUTION",
                    task=task
                )
            return current_node
        
        # --- GENERATE SUCCESSORS ---
        unsatisfied_efs = all_ef_ids - current_node.satisfied_efs
        if not unsatisfied_efs:
            continue
        
        # Pick the next EF to solve (simple sequential order for now)
        next_ef_id = sorted(list(unsatisfied_efs))[0]
        next_ef = next(ef for ef in task['elemental_functions'] if ef['ef_id'] == next_ef_id)
        required_ef_type = next_ef['type']
        
        print(f" -> Next EF to satisfy: {next_ef_id} ({next_ef['description']}, Type: {required_ef_type})")
        
        # DYNAMIC RULE MATCHING: Try rules from any satisfied EF type
        applicable_rules = []
        for existing_ef_type in current_node.satisfied_ef_types:
            matching_rules = [
                r for r in rules 
                if (r['applies_to']['existing_ef'] == existing_ef_type and 
                    r['applies_to']['required_ef'] == required_ef_type)
            ]
            applicable_rules.extend(matching_rules)
        
        # Remove duplicates (same rule_id)
        seen_rule_ids = set()
        unique_rules = []
        for rule in applicable_rules:
            if rule['rule_id'] not in seen_rule_ids:
                seen_rule_ids.add(rule['rule_id'])
                unique_rules.append(rule)
        applicable_rules = unique_rules
        
        print(f" -> Found {len(applicable_rules)} applicable rules (from types: {current_node.satisfied_ef_types})")
        
        if not applicable_rules:
            print(f" -> Dead end: No rule found for transition to {required_ef_type}")
            continue
        
        for rule in applicable_rules:
            print(f"   -> Applying rule '{rule['rule_id']}': {rule['description']}")
            
            # Create a new state by applying the rule
            new_graph = _apply_rule_to_graph(current_node.graph, rule)
            
            # Check if the new graph is valid (connected and reasonable DOF)
            if not new_graph.is_connected():
                print(f"     -> Skipping: Graph not connected after applying {rule['rule_id']}")
                continue
            
            new_dof = new_graph.calculate_dof()
            if new_dof < 0 or new_dof > 3:  # Reasonable DOF range
                print(f"     -> Skipping: Invalid DOF ({new_dof}) after applying {rule['rule_id']}")
                continue
            
            # VALIDATE EF SATISFACTION
            is_valid, validation_reason = validate_ef_satisfaction(new_graph, next_ef, task)
            if not is_valid:
                print(f"     -> Skipping: EF validation failed - {validation_reason}")
                continue
            
            # Update satisfied EFs and types
            new_satisfied_efs = current_node.satisfied_efs.union({next_ef_id})
            new_satisfied_ef_types = current_node.satisfied_ef_types.union({required_ef_type})
            new_path = current_node.path + [rule['rule_id']]
            
            new_node = SearchNode(
                new_graph, 
                new_satisfied_efs, 
                new_path,
                new_satisfied_ef_types
            )
            if new_node.get_state_tuple() in visited:
                print(f"     -> Skipping: State already visited")
                continue
            
            visited.add(new_node.get_state_tuple())
            # Save visualization step
            if visualizer:
                visualizer.save_step(
                    new_graph,
                    iteration=iteration,
                    rule_applied=rule['rule_id'],
                    satisfied_efs=list(new_satisfied_efs),
                    description=f"Applied {rule['rule_id']} to satisfy {next_ef_id}"
                )
            
            new_cost = cost + rule.get('cost', 1)
            heuristic = len(all_ef_ids) - len(new_satisfied_efs)
            new_priority = new_cost + heuristic
            
            heapq.heappush(open_list, (new_priority, new_cost, new_node))
            print(f"     -> Added to queue: Priority={new_priority}, Cost={new_cost}, Heuristic={heuristic}, Validated: ✓")
    
    if iteration >= max_iterations:
        print(f" -> A* Search stopped after {max_iterations} iterations (max limit reached)")
    else:
        print(" -> A* Search failed to find a solution.")
    
    return None

def run_synthesis_for_all_initial_solutions(task: Dict[str, Any], initial_solutions: List[Dict[str, Any]]) -> List[SearchNode]:
    """
    Run synthesis for all initial solutions and return all valid final solutions.
    
    Args:
        task: The design task dictionary
        initial_solutions: List of initial solutions to try
        
    Returns:
        List of valid final solutions
    """
    print(f"\n[PHASE 2.3] Running synthesis for {len(initial_solutions)} initial solutions...")
    
    final_solutions = []
    
    for i, initial_sol in enumerate(initial_solutions):
        print(f"\n--- Processing Initial Solution {i+1}/{len(initial_solutions)}: {initial_sol['name']} ---")
        
        final_node = run_synthesis(task, initial_sol)
        if final_node:
            final_solutions.append(final_node)
            print(f" -> SUCCESS: Found solution for {initial_sol['name']}")
        else:
            print(f" -> FAILED: No solution found for {initial_sol['name']}")
    
    print(f"\n[PHASE 2.3] Synthesis complete: {len(final_solutions)}/{len(initial_solutions)} solutions found")
    
    return final_solutions
