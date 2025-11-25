# src/synthesis_visualizer.py
"""
Step-by-step visualization system for the synthesis process.
Saves mechanism graphs at each A* iteration for analysis.
"""

import os
from typing import Optional, List
from .mechanism_graph import MechanismGraph


class SynthesisVisualizer:
    """Manages step-by-step visualization during synthesis."""
    
    def __init__(self, task_name: str, base_mechanism_name: str, output_dir: str = "output"):
        """
        Initialize the visualizer for a synthesis run.
        
        Args:
            task_name: Name of the design task
            base_mechanism_name: Name of the initial mechanism
            output_dir: Base output directory
        """
        self.task_name = task_name
        self.base_mechanism_name = base_mechanism_name
        self.output_dir = output_dir
        self.steps_dir = os.path.join(
            output_dir, 
            "synthesis_steps", 
            task_name.replace(" ", "_").replace("/", "_"),
            base_mechanism_name.replace(" ", "_").replace("/", "_")
        )
        self.step_count = 0
        
        # Create directory structure
        os.makedirs(self.steps_dir, exist_ok=True)
        # Steps metadata
        self.steps_info_path = os.path.join(self.steps_dir, 'steps_info.json')
        self.steps_info = []
        # Load existing if present
        if os.path.exists(self.steps_info_path):
            try:
                with open(self.steps_info_path, 'r', encoding='utf-8') as f:
                    self.steps_info = json.load(f)
            except Exception:
                self.steps_info = []
    
    def save_step(
        self, 
        graph: MechanismGraph, 
        iteration: int,
        rule_applied: Optional[str] = None,
        satisfied_efs: Optional[List[str]] = None,
        description: Optional[str] = None
        , task: Optional[dict] = None
    ) -> str:
        """
        Save a visualization of the current synthesis step.
        
        Args:
            graph: Current mechanism graph
            iteration: A* iteration number
            rule_applied: Rule ID that was applied (if any)
            satisfied_efs: List of satisfied EF IDs
            description: Optional description text
            
        Returns:
            Path to saved image file
        """
        self.step_count += 1
        
        # Build filename
        if rule_applied:
            filename = f"step_{iteration:03d}_{rule_applied}.png"
        else:
            filename = f"step_{iteration:03d}_initial.png"
        
        filepath = os.path.join(self.steps_dir, filename)
        
        # Build title with context
        title_parts = [f"Step {iteration}: {self.base_mechanism_name}"]
        if rule_applied:
            title_parts.append(f"Rule: {rule_applied}")
        if satisfied_efs:
            title_parts.append(f"EFs: {', '.join(sorted(satisfied_efs))}")
        if description:
            title_parts.append(description)
        
        title = " | ".join(title_parts)
        
        # Determine highlights (force nodes) using EF info if task provided
        highlight_nodes = []
        force_directions = {}
        if task and satisfied_efs:
            ef_map = {ef['ef_id']: ef for ef in task.get('elemental_functions', [])}
            task_elements = task.get('elements', {})
            for ef_id in satisfied_efs:
                ef = ef_map.get(ef_id)
                if not ef:
                    continue
                for beh in ef.get('behavior', []):
                    elem_id = beh.get('element')
                    effort = beh.get('effort', '0')
                    motion = beh.get('motion', '0')
                    if elem_id:
                        # try numeric mapping first
                        try:
                            idx = int(elem_id[1:])
                        except Exception:
                            idx = None

                        # fallback: find by name (e.g. bolt/rack/slider in graph elem names)
                        if idx is None or idx >= graph.num_elements:
                            name = (task_elements.get(elem_id) or '').lower()
                            idx = next((i for i, n in enumerate(graph.element_names) if name and name in n.lower()), None)

                        if idx is not None and idx < graph.num_elements:
                            if effort != '0':
                                if idx not in highlight_nodes:
                                    highlight_nodes.append(idx)
                                # direction for effort arrow: toward positive x
                                force_directions[idx] = (0.6, 0)
                            if motion != '0':
                                if idx not in highlight_nodes:
                                    highlight_nodes.append(idx)
                                # direction for motion arrow: positive x
                                force_directions[idx] = (0.6, 0)

        # Save visualization with highlights and force directions
        graph.visualize(title=title, save_path=filepath, highlight_nodes=highlight_nodes, force_directions=force_directions)
        
        # Record metadata
        step_meta = {
            'iteration': iteration,
            'filename': filename,
            'rule_applied': rule_applied,
            'satisfied_efs': satisfied_efs or [],
            'description': description or ''
        }
        self.steps_info.append(step_meta)
        try:
            with open(self.steps_info_path, 'w', encoding='utf-8') as f:
                json.dump(self.steps_info, f, indent=2)
        except Exception:
            pass
        
        return filepath
    
    def get_steps_directory(self) -> str:
        """Get the directory where step images are saved."""
        return self.steps_dir
    
    def get_summary_path(self) -> str:
        """Get path for summary file."""
        return os.path.join(self.steps_dir, "synthesis_summary.txt")

