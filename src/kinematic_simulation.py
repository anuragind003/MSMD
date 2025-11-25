import numpy as np
from typing import List, Dict, Tuple

class KinematicSimulator:
    """
    Simulates the kinematics of various mechanisms to generate motion data for visualization.
    """

    def __init__(self):
        pass

    def simulate_slider_crank(self, num_frames: int = 50) -> List[Dict]:
        """
        Simulates a slider-crank mechanism.
        Returns a list of frames, where each frame contains coordinates for:
        - Crank (p1, p2)
        - Coupler (p2, p3)
        - Slider (p3)
        """
        frames = []
        
        # Dimensions
        r2 = 1.5  # Crank length
        r3 = 4.0  # Coupler length
        offset = 0.0 # Slider offset
        
        # Input angles (0 to 360 degrees)
        thetas = np.linspace(0, 2*np.pi, num_frames)
        
        for theta in thetas:
            # Crank end point (A)
            Ax = r2 * np.cos(theta)
            Ay = r2 * np.sin(theta)
            
            # Slider position (B)
            # The slider moves along y = offset line.
            # The distance between Crank Tip A and Slider B is length r3.
            # (Bx - Ax)^2 + (By - Ay)^2 = r3^2
            # (Bx - Ax)^2 = r3^2 - (offset - Ay)^2
            # Bx = Ax + sqrt(r3^2 - (offset - Ay)^2)  (Assuming slider is to the right)
            
            term = r3**2 - (offset - Ay)**2
            if term < 0:
                term = 0 # Should not happen with valid dimensions
                
            Bx = Ax + np.sqrt(term)
            By = offset
            
            frames.append({
                'crank': [(0, 0), (Ax, Ay)],
                'coupler': [(Ax, Ay), (Bx, By)],
                'slider': (Bx, By),
                'angle': theta
            })
            
        return frames

    def simulate_rack_pinion(self, num_frames: int = 50) -> List[Dict]:
        """
        Simulates a rack and pinion mechanism.
        """
        frames = []
        
        # Dimensions
        radius = 1.0
        
        # Input angles (oscillating for door latch effect: 0 -> 90 -> 0)
        # Phase 1: 0 to 90
        t1 = np.linspace(0, np.pi/2, num_frames // 2)
        # Phase 2: 90 to 0
        t2 = np.linspace(np.pi/2, 0, num_frames // 2)
        thetas = np.concatenate([t1, t2])
        
        center_x, center_y = 2.0, 1.0
        
        for theta in thetas:
            # Pinion rotation marker
            marker_x = center_x + radius * np.cos(theta)
            marker_y = center_y + radius * np.sin(theta)
            
            # Rack position (x = r * theta)
            # Initial rack pos at theta=0
            # Rack is below pinion. y = center_y - radius = 0.0
            # Let's align rack top with pinion bottom.
            
            rack_start_x = 0.0
            rack_displacement = radius * theta
            
            current_rack_x = rack_start_x + rack_displacement
            
            frames.append({
                'pinion_center': (center_x, center_y),
                'pinion_marker': (marker_x, marker_y),
                'rack_x': current_rack_x,
                'angle': theta
            })
            
        return frames

    def simulate_cam_follower(self, num_frames: int = 50) -> List[Dict]:
        """
        Simulates a simple cam-follower (eccentric cam).
        """
        frames = []
        
        # Dimensions
        cam_radius = 1.0
        eccentricity = 0.5
        
        thetas = np.linspace(0, 2*np.pi, num_frames)
        
        center_x, center_y = 0.0, 0.0
        
        for theta in thetas:
            # Cam geometric center rotates around the shaft (0,0)
            cam_cx = eccentricity * np.cos(theta)
            cam_cy = eccentricity * np.sin(theta)
            
            # Follower sits on top of the cam at x=0
            # Intersection of vertical line x=0 and circle (x-cx)^2 + (y-cy)^2 = R^2
            # (-cx)^2 + (y-cy)^2 = R^2
            # y = cy + sqrt(R^2 - cx^2)
            
            term = cam_radius**2 - cam_cx**2
            if term < 0: term = 0
            
            follower_y = cam_cy + np.sqrt(term)
            
            frames.append({
                'cam_center': (cam_cx, cam_cy),
                'follower_y': follower_y,
                'angle': theta
            })
            
        return frames
