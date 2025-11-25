# src/mechanism_graph.py
import numpy as np
import matplotlib.pyplot as plt
import networkx as nx
from typing import List, Tuple, Optional

class MechanismGraph:
    """
    Represents the topology of a mechanical device using an adjacency matrix.
    Nodes are mechanical elements (links, ground).
    Edges represent kinematic joints.
    """
    # UPDATE: Added 'LSP' (Code 7) -> Limited Spring Prismatic
    JOINT_MAP = {
        'R': 1, 'P': 3, 'X': 2, 'F': -1, 
        'LP': 5,   # Limited Prismatic
        'SP': 6,   # Spring Prismatic
        'LSP': 7   # Limited Spring Prismatic (Stopper + Spring)
    }

    def __init__(self, num_elements: int):
        """
        Initialize a mechanism graph with specified number of elements.
        
        Args:
            num_elements (int): Number of mechanical elements in the mechanism
        """
        if num_elements < 2:
            raise ValueError("A mechanism must have at least 2 elements.")
        self.num_elements = num_elements
        self.adj_matrix = np.zeros((num_elements, num_elements), dtype=int)
        self.element_names = [f"E{i}" for i in range(num_elements)]

    def add_joint(self, elem1_idx: int, elem2_idx: int, joint_type: str) -> None:
        """
        Adds a joint between two elements.
        
        Args:
            elem1_idx (int): Index of first element
            elem2_idx (int): Index of second element
            joint_type (str): Type of joint ('R', 'P', 'X', 'F')
        """
        if joint_type.upper() not in self.JOINT_MAP:
            raise ValueError(f"Unknown joint type: {joint_type}. Use one of {list(self.JOINT_MAP.keys())}")
        
        joint_code = self.JOINT_MAP[joint_type.upper()]
        self.adj_matrix[elem1_idx, elem2_idx] = joint_code
        self.adj_matrix[elem2_idx, elem1_idx] = joint_code

    def calculate_dof(self) -> int:
        """
        Calculates the Degrees of Freedom (DOF) using Grubler's formula variant
        from the thesis (Equation 2.1). F = 3(n₀ - n₋₁ - 1) - 2n₁ - n₂
        
        Returns:
            int: Degrees of freedom of the mechanism
        """
        n0 = self.num_elements  # Total number of elements (links)
        
        # We only need to look at the upper triangle to avoid double counting
        upper_triangle = self.adj_matrix[np.triu_indices(n0, k=1)]
        
        n_minus_1 = np.count_nonzero(upper_triangle == -1)  # Number of fixed joints (F)
        
        # UPDATE: Include Code 7 (LSP) in the 1-DOF count
        n_1 = np.count_nonzero(
            (upper_triangle == 1) | 
            (upper_triangle == 3) | 
            (upper_triangle == 5) | 
            (upper_triangle == 6) |
            (upper_triangle == 7) 
        )
        
        n_2 = np.count_nonzero(upper_triangle == 2)        # Number of higher pairs (X)

        dof = 3 * (n0 - n_minus_1 - 1) - (2 * n_1) - n_2
        return dof

    def get_joint_info(self) -> List[Tuple[int, int, str]]:
        """
        Returns information about all joints in the mechanism.
        
        Returns:
            List[Tuple[int, int, str]]: List of (element1, element2, joint_type) tuples
        """
        joints = []
        for i in range(self.num_elements):
            for j in range(i + 1, self.num_elements):
                if self.adj_matrix[i, j] != 0:
                    joint_code = self.adj_matrix[i, j]
                    joint_type = [key for key, value in self.JOINT_MAP.items() if value == joint_code][0]
                    joints.append((i, j, joint_type))
        return joints

    def visualize(self, title: str = "Mechanism Topology Graph", save_path: Optional[str] = None, highlight_nodes: Optional[List[int]] = None, force_directions: Optional[dict] = None) -> None:
        """
        Creates a simple visualization of the graph using NetworkX and Matplotlib.
        
        Args:
            title (str): Title for the plot
            save_path (str, optional): Path to save the plot as image file
        """
        G = nx.from_numpy_array(self.adj_matrix)
        pos = nx.spring_layout(G)  # positions for all nodes
        
        edge_labels = {}
        for u, v, data in G.edges(data=True):
            joint_code = data['weight']
            # Find the joint type from the code
            joint_type = [key for key, value in self.JOINT_MAP.items() if value == joint_code][0]
            edge_labels[(u, v)] = joint_type

        plt.figure(figsize=(10, 8))
        
        # Create labels dictionary
        labels = {i: name for i, name in enumerate(self.element_names)}
        
        # If highlight_nodes provided, color them differently
        node_colors = []
        for i in range(self.num_elements):
            if highlight_nodes and i in highlight_nodes:
                node_colors.append('orange')
            else:
                node_colors.append('skyblue')

        nx.draw(G, pos, with_labels=True, labels=labels, node_color=node_colors, node_size=2000, 
            edge_color='gray', font_size=10, font_weight='bold')
        nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_color='red', font_size=10)
        
        plt.title(title, fontsize=14, fontweight='bold')
        plt.axis('off')
        
        # Draw force arrows if provided
        try:
            from matplotlib.patches import FancyArrowPatch
            if force_directions:
                ax = plt.gca()
                for node_idx, vec in force_directions.items():
                    if node_idx in pos:
                        start = pos[node_idx]
                        end = (start[0] + vec[0], start[1] + vec[1])
                        arrow = FancyArrowPatch(start, end, arrowstyle='-|>', color='red', mutation_scale=15)
                        ax.add_patch(arrow)
        except Exception:
            pass

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"Graph saved to {save_path}")
            plt.close()
        else:
            plt.show()

    def is_connected(self) -> bool:
        """
        Checks if the mechanism graph is connected.
        
        Returns:
            bool: True if all elements are connected, False otherwise
        """
        G = nx.from_numpy_array(self.adj_matrix)
        return nx.is_connected(G)

    def get_connectivity_info(self) -> dict:
        """
        Returns connectivity information about the mechanism.
        
        Returns:
            dict: Dictionary containing connectivity statistics
        """
        G = nx.from_numpy_array(self.adj_matrix)
        return {
            'is_connected': nx.is_connected(G),
            'num_components': nx.number_connected_components(G),
            'diameter': nx.diameter(G) if nx.is_connected(G) else None,
            'average_clustering': nx.average_clustering(G)
        }

    def __str__(self) -> str:
        """String representation of the mechanism graph."""
        joint_info = self.get_joint_info()
        joint_str = "\n".join([f"  {self.element_names[i]}-{self.element_names[j]}: {joint_type}" 
                              for i, j, joint_type in joint_info])
        
        return f"""Mechanism with {self.num_elements} elements:
Adjacency Matrix:
{self.adj_matrix}

Joints:
{joint_str}

DOF: {self.calculate_dof()}
Connected: {self.is_connected()}"""

    def __repr__(self) -> str:
        """Detailed representation for debugging."""
        return f"MechanismGraph(num_elements={self.num_elements}, dof={self.calculate_dof()})"
