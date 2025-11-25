import os
from typing import List
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyArrowPatch
from matplotlib.animation import FuncAnimation, PillowWriter
from .kinematic_simulation import KinematicSimulator

# Animation defaults
DEFAULT_NUM_FRAMES = 120
DEFAULT_FPS = 12
PAUSE_FRAMES_PER_RULE = 40
FINAL_CYCLES = 2


class Visualizer:
    """
    Translates a MechanismGraph and modification path into a 2D schematic.
    """

    def __init__(self) -> None:
        if not os.path.exists('output'):
            os.makedirs('output')
        self.simulator = KinematicSimulator()

    def generate_animation(self, base_mechanism_name: str, filename: str, solution_node=None, num_frames: int = DEFAULT_NUM_FRAMES, fps: int = DEFAULT_FPS, pause_frames_per_rule: int = PAUSE_FRAMES_PER_RULE, final_cycles: int = FINAL_CYCLES) -> None:
        """
        Generates a GIF animation for the synthesized mechanism.
        Shows progressive application of rules if solution_node is provided.
        """
        name = (base_mechanism_name or "").lower()
        
        fig, ax = plt.subplots(figsize=(8, 6))
        ax.set_aspect('equal')
        ax.grid(True, linestyle='--', alpha=0.6)
        
        # Get base simulation frames
        sim_frames = []
        if "slider-crank" in name:
            sim_frames = self.simulator.simulate_slider_crank(num_frames=num_frames)
        elif "rack" in name and "pinion" in name:
            sim_frames = self.simulator.simulate_rack_pinion(num_frames=num_frames)
        elif "cam" in name and "follower" in name:
            sim_frames = self.simulator.simulate_cam_follower(num_frames=num_frames)
        else:
            print(f"Animation not supported for {base_mechanism_name}")
            plt.close(fig)
            return

        # Construct Progressive Frames
        # Structure: {'data': frame_data, 'title': str, 'visible_rules': list, 'annotation': str}
        animation_frames = []
        
        # 1. Base Mechanism Phase
        iteration_idx = 0
        for f in sim_frames[:len(sim_frames)//2]: # Show half cycle
            animation_frames.append({
                'data': f, 
                'title': f"Base: {base_mechanism_name}", 
                'visible_rules': [],
                'annotation': "Base Mechanism (Satisfies EF1: Motion)",
                'iteration': iteration_idx
            })
            
        # 2. Rule Application Phase
        applied_rules = []
        if solution_node and hasattr(solution_node, 'path'):
            for ri, rule in enumerate(solution_node.path, start=1):
                # Determine annotation based on rule
                note = ""
                if "R3.1" in rule: note = "Adding Stopper (Satisfies EF2: Limit)"
                elif "R4.1" in rule: note = "Adding Spring (Satisfies EF3: Return)"
                elif "R2.1" in rule: note = "Adding Var. Joint (Satisfies EF4: Slamming)"
                
                # Transition frames (pause to show rule application)
                last_data = sim_frames[0] # Use a neutral pose
                for _ in range(pause_frames_per_rule):
                    animation_frames.append({
                        'data': last_data,
                        'title': f"Applying {rule}...",
                        'visible_rules': applied_rules + [rule],
                        'annotation': note
                        ,'iteration': ri
                    })
                applied_rules.append(rule)
                
        # 3. Final Mechanism Phase
        for f in sim_frames * final_cycles: # Show full cycle for configured cycles
            animation_frames.append({
                'data': f,
                'title': f"Final Mechanism (Satisfies Task)",
                'visible_rules': applied_rules,
                'annotation': "Full Functionality Verified",
                'iteration': len(solution_node.path) if solution_node and hasattr(solution_node, 'path') else iteration_idx
            })

        update_func = None
        
        if "slider-crank" in name:
            ax.set_xlim(-2, 8)
            ax.set_ylim(-3, 3)
            
            # Static elements
            ax.plot([-1, 7], [-0.2, -0.2], 'k-', lw=5) # Ground
            
            # Dynamic elements
            line_crank, = ax.plot([], [], 'r-o', lw=3, label='Crank')
            line_coupler, = ax.plot([], [], 'b-o', lw=3, label='Coupler')
            rect_slider = patches.Rectangle((0, 0), 1, 0.5, fc='gray', ec='black')
            ax.add_patch(rect_slider)
            
            # Forces
            arrow_input = FancyArrowPatch((0,0), (0,0), connectionstyle="arc3,rad=.5", arrowstyle="Simple,tail_width=0.5,head_width=4,head_length=8", color="orange", alpha=0.0)
            ax.add_patch(arrow_input)
            arrow_output = FancyArrowPatch((0,0), (0,0), arrowstyle="simple", color="blue", alpha=0.0)
            ax.add_patch(arrow_output)
            
            # Rule elements (Hidden initially)
            stopper = patches.Rectangle((6.0, -0.2), 0.2, 1.0, fc='red', alpha=0.0) # R3.1
            ax.add_patch(stopper)
            spring, = ax.plot([], [], 'g-', lw=2, alpha=0.0) # R4.1
            
            # Text Annotations
            txt_annotation = ax.text(3, 2.5, "", ha='center', fontsize=10, bbox=dict(facecolor='white', alpha=0.8))
            iteration_text = ax.text(-1.5, 2.5, "", ha='left', fontsize=10, bbox=dict(facecolor='white', alpha=0.8))
            
            def update_slider_crank(frame_wrapper):
                frame = frame_wrapper['data']
                rules = frame_wrapper['visible_rules']
                ax.set_title(frame_wrapper['title'])
                txt_annotation.set_text(frame_wrapper['annotation'])
                iteration_text.set_text(f"Iteration: {frame_wrapper.get('iteration', 0)}")
                
                # Update Motion
                c_pts = frame['crank']
                line_crank.set_data([p[0] for p in c_pts], [p[1] for p in c_pts])
                cp_pts = frame['coupler']
                line_coupler.set_data([p[0] for p in cp_pts], [p[1] for p in cp_pts])
                s_pos = frame['slider']
                rect_slider.set_xy((s_pos[0] - 0.5, s_pos[1] - 0.25))
                
                # Update Forces
                # Input Torque on Crank
                arrow_input.set_positions((0.5, -0.5), (0.5, 0.5)) # Simplified
                arrow_input.set_alpha(0.6)
                
                # Output Force on Slider
                arrow_output.set_positions((s_pos[0], s_pos[1]), (s_pos[0]-1.0, s_pos[1]))
                arrow_output.set_alpha(0.6)
                
                # Update Rules Visibility
                if any('R3.1' in r for r in rules): # Stopper
                    stopper.set_alpha(1.0)
                else:
                    stopper.set_alpha(0.0)
                    
                if any('R4.1' in r for r in rules): # Spring
                    spring.set_alpha(1.0)
                    # Draw spring from slider to wall
                    sx = s_pos[0] + 0.5
                    spring_x = np.linspace(sx, 7.0, 20)
                    spring_y = -0.2 + 0.1 * np.sin(10 * spring_x) # Wiggle
                    spring.set_data(spring_x, spring_y)
                else:
                    spring.set_alpha(0.0)
                
                return line_crank, line_coupler, rect_slider, stopper, spring, arrow_input, arrow_output, txt_annotation, iteration_text
                
            update_func = update_slider_crank

        elif "rack" in name and "pinion" in name:
            ax.set_xlim(-1, 7)
            ax.set_ylim(-1, 4)
            
            # Dynamic elements
            pinion_circle = patches.Circle((0,0), 1.0, fc='lightgray', ec='black')
            ax.add_patch(pinion_circle)
            pinion_marker, = ax.plot([], [], 'ro')
            rack_rect = patches.Rectangle((0, 0), 6, 0.4, fc='gray', ec='black')
            ax.add_patch(rack_rect)
            
            # Forces
            arrow_input = FancyArrowPatch((0,0), (0,0), connectionstyle="arc3,rad=.5", arrowstyle="Simple,tail_width=0.5,head_width=4,head_length=8", color="orange", alpha=0.0)
            ax.add_patch(arrow_input)
            arrow_output = FancyArrowPatch((0,0), (0,0), arrowstyle="simple", color="blue", alpha=0.0)
            ax.add_patch(arrow_output)
            
            # Rule elements
            stopper = patches.Rectangle((5.5, -0.2), 0.2, 1.0, fc='red', alpha=0.0) # R3.1
            ax.add_patch(stopper)
            spring, = ax.plot([], [], 'g-', lw=2, alpha=0.0) # R4.1
            
            # Text Annotation
            txt_annotation = ax.text(3, 3.5, "", ha='center', fontsize=10, bbox=dict(facecolor='white', alpha=0.8))
            iteration_text = ax.text(-1.5, 3.5, "", ha='left', fontsize=10, bbox=dict(facecolor='white', alpha=0.8))
            
            def update_rack_pinion(frame_wrapper):
                frame = frame_wrapper['data']
                rules = frame_wrapper['visible_rules']
                ax.set_title(frame_wrapper['title'])
                txt_annotation.set_text(frame_wrapper['annotation'])
                iteration_text.set_text(f"Iteration: {frame_wrapper.get('iteration', 0)}")
                
                # Update Motion
                pc = frame['pinion_center']
                pinion_circle.center = pc
                pm = frame['pinion_marker']
                pinion_marker.set_data([pm[0]], [pm[1]])
                rx = frame['rack_x']
                rack_rect.set_xy((rx, -0.4)) # Adjusted to be tangent
                
                # Update Forces
                arrow_input.set_positions((pc[0]-0.5, pc[1]-0.5), (pc[0]+0.5, pc[1]+0.5))
                arrow_input.set_alpha(0.6)
                
                arrow_output.set_positions((rx+3, -0.2), (rx+2, -0.2))
                arrow_output.set_alpha(0.6)
                
                # Update Rules
                if any('R3.1' in r for r in rules): # Stopper
                    stopper.set_alpha(1.0)
                else:
                    stopper.set_alpha(0.0)
                    
                if any('R4.1' in r for r in rules): # Spring
                    spring.set_alpha(1.0)
                    # Draw spring from rack end to wall
                    rack_end = rx + 6
                    spring_x = np.linspace(rack_end, 7.0, 20)
                    spring_y = -0.2 + 0.1 * np.sin(10 * spring_x)
                    spring.set_data(spring_x, spring_y)
                else:
                    spring.set_alpha(0.0)
                
                return pinion_circle, pinion_marker, rack_rect, stopper, spring, arrow_input, arrow_output, txt_annotation, iteration_text
            
            update_func = update_rack_pinion

        elif "cam" in name and "follower" in name:
            ax.set_xlim(-3, 3)
            ax.set_ylim(-3, 3)
            
            # Dynamic elements
            cam_circle = patches.Circle((0,0), 1.0, fc='lightgray', ec='black')
            ax.add_patch(cam_circle)
            follower_stem, = ax.plot([], [], 'k-', lw=4)
            follower_head = patches.Rectangle((-0.2, 0), 0.4, 0.2, fc='blue')
            ax.add_patch(follower_head)
            
            # Forces
            arrow_input = FancyArrowPatch((0,0), (0,0), connectionstyle="arc3,rad=.5", arrowstyle="Simple,tail_width=0.5,head_width=4,head_length=8", color="orange", alpha=0.0)
            ax.add_patch(arrow_input)
            
            # Rule elements
            stopper = patches.Rectangle((-0.5, 2.5), 1.0, 0.1, fc='red', alpha=0.0) # R3.1
            ax.add_patch(stopper)
            spring, = ax.plot([], [], 'g-', lw=2, alpha=0.0) # R4.1
            
            # Text Annotation
            txt_annotation = ax.text(0, 2.8, "", ha='center', fontsize=10, bbox=dict(facecolor='white', alpha=0.8))
            iteration_text = ax.text(-2.5, 2.8, "", ha='left', fontsize=10, bbox=dict(facecolor='white', alpha=0.8))
            
            def update_cam_follower(frame_wrapper):
                frame = frame_wrapper['data']
                rules = frame_wrapper['visible_rules']
                ax.set_title(frame_wrapper['title'])
                txt_annotation.set_text(frame_wrapper['annotation'])
                iteration_text.set_text(f"Iteration: {frame_wrapper.get('iteration', 0)}")
                
                # Update Motion
                cc = frame['cam_center']
                cam_circle.center = cc
                fy = frame['follower_y']
                follower_stem.set_data([0, 0], [fy, fy + 2])
                follower_head.set_xy((-0.2, fy))
                
                # Update Forces
                arrow_input.set_positions((cc[0]-0.5, cc[1]-0.5), (cc[0]+0.5, cc[1]+0.5))
                arrow_input.set_alpha(0.6)
                
                # Update Rules
                if any('R3.1' in r for r in rules): # Stopper
                    stopper.set_alpha(1.0)
                else:
                    stopper.set_alpha(0.0)
                    
                if any('R4.1' in r for r in rules): # Spring
                    spring.set_alpha(1.0)
                    # Draw spring around stem
                    sy = np.linspace(fy, fy+2, 20)
                    sx = 0.2 * np.sin(20 * sy)
                    spring.set_data(sx, sy)
                else:
                    spring.set_alpha(0.0)
                
                return cam_circle, follower_stem, follower_head, stopper, spring, arrow_input, txt_annotation, iteration_text
                
            update_func = update_cam_follower

        # Create Animation
        ani = FuncAnimation(fig, update_func, frames=animation_frames, blit=False, interval=int(1000/fps))
        
        # Save
        filepath = os.path.join('output', filename)
        try:
            # Try to save both GIF and MP4 (if ffmpeg present)
            try:
                ani.save(filepath, writer=PillowWriter(fps=fps))
                print(f" -> GIF saved to '{filepath}'")
            except Exception as e:
                print(f" -> Failed to save GIF: {e}")
            # Try MP4
            try:
                from matplotlib.animation import FFMpegWriter
                mp4_path = os.path.splitext(filepath)[0] + '.mp4'
                writer = FFMpegWriter(fps=fps)
                ani.save(mp4_path, writer=writer)
                print(f" -> MP4 saved to '{mp4_path}'")
            except Exception:
                pass
            
            # Save a static preview frame as PNG for pause/toggle actions
            try:
                preview_path = os.path.splitext(filepath)[0] + '_preview.png'
                # Draw first frame to export
                first_frame = animation_frames[0]
                update_func(first_frame)
                plt.savefig(preview_path, dpi=200, bbox_inches='tight')
                print(f" -> Preview saved to '{preview_path}'")
            except Exception as e:
                print(f" -> Failed to save preview image: {e}")
            
            # Generate HTML playback file to provide play/pause via JS
            try:
                html_path = os.path.splitext(filepath)[0] + '.html'
                self._generate_html_player(filepath, preview_path, html_path)
                print(f" -> HTML player saved to '{html_path}'")
            except Exception as e:
                print(f" -> Failed to save HTML player: {e}")
            print(f" -> Animation saved to '{filepath}'")
        except Exception as e:
            print(f" -> Failed to save animation: {e}")
        
        plt.close(fig)

    def _generate_html_player(self, gif_path: str, preview_path: str, html_path: str) -> None:
        """Generates a simple HTML wrapper for the GIF with play/pause and step text controls.
        If HTML can detect an MP4 version (same base name), it prefers video element for better controls.
        """
        gif_name = os.path.basename(gif_path)
        preview_name = os.path.basename(preview_path) if preview_path and os.path.exists(preview_path) else ''
        mp4_path = os.path.splitext(gif_path)[0] + '.mp4'
        mp4_name = os.path.basename(mp4_path) if os.path.exists(mp4_path) else ''

        html = [
            '<!doctype html>',
            '<html>',
            '<head>',
            '  <meta charset="utf-8" />',
            f'  <title>Animation: {gif_name}</title>',
            '  <style>body{font-family: Arial, sans-serif; display:flex; flex-direction:column; align-items:center; padding:10px;} #player{max-width:90%; height:auto; border:1px solid #ddd;} .controls{margin-top:10px;}</style>',
            '</head>',
            '<body>',
        ]

        if mp4_name:
            # Use HTML5 video (if mp4 exists)
            html += [f'  <video id="video_player" width="640" controls>', f'    <source src="{mp4_name}" type="video/mp4">', '    Your browser does not support the video tag.', '  </video>']
        else:
            # Use GIF and preview toggle
            html += [f'  <img id="player" src="{preview_name}" alt="Preview" />']

        html += [
            '  <div class="controls">',
        ]

        if mp4_name:
            html += [f'    <button onclick="document.getElementById(\'video_player\').play()">Play</button>', f'    <button onclick="document.getElementById(\'video_player\').pause()">Pause</button>']
        else:
            html += [f'    <button id="play_btn">Play</button>', f'    <button id="pause_btn">Pause</button>']

        # Add step description placeholder
        html += [
            '    <span id="step_text" style="margin-left:20px; font-weight:bold;"></span>',
            '  </div>',
            '  <script>',
        ]

        if mp4_name:
            html += [
                '    const video = document.getElementById("video_player");',
                '    const stepText = document.getElementById("step_text");',
                '    video.onplay = () => stepText.textContent = "Playing";',
                '    video.onpause = () => stepText.textContent = "Paused";',
            ]
        else:
            html += [
                '    const player = document.getElementById("player");',
                '    const preview = "' + preview_name + '";',
                '    const gif = "' + gif_name + '";',
                '    const playBtn = document.getElementById("play_btn");',
                '    const pauseBtn = document.getElementById("pause_btn");',
                '    const stepText = document.getElementById("step_text");',
                '    playBtn.onclick = () => { player.src = gif; stepText.textContent = "Playing"; };',
                '    pauseBtn.onclick = () => { player.src = preview; stepText.textContent = "Paused"; };',
            ]

        html += [
            '  </script>',
            '</body>',
            '</html>'
        ]

        with open(html_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(html))

    def draw_schematic(self, base_mechanism_name: str, solution_node, filename: str) -> None:
        """
        Main dispatch method. Calls the correct drawing function based on the mechanism name.
        Also generates a NetworkX graph visualization of the mechanism topology.
        """
        fig, ax = plt.subplots(figsize=(8, 6))
        ax.set_aspect('equal')
        ax.set_xlim(-2, 8)
        ax.set_ylim(-2, 4)
        ax.set_title(f"Solution Schematic: {base_mechanism_name}")
        ax.grid(True, linestyle='--', alpha=0.6)

        name = (base_mechanism_name or "").lower()
        if "slider-crank" in name and "spring" not in name:
            self._draw_slider_crank(ax)
        elif "slider-crank" in name and "spring" in name:
            self._draw_slider_crank(ax)
            # Add spring annotation for the variant
            ax.plot([0, 1.5], [1.5, 1.5], 'k--', alpha=0.6)
            ax.text(0.75, 1.7, "Return Spring", ha='center', color='green')
        elif "rack" in name and "pinion" in name:
            self._draw_rack_and_pinion(ax)
        elif "four" in name and "bar" in name:
            self._draw_four_bar(ax)
        elif "cam" in name and "follower" in name:
            self._draw_cam_follower(ax)
        elif "spur" in name and "gear" in name:
            self._draw_spur_gear_pair(ax)
        elif "scotch" in name and "yoke" in name:
            self._draw_scotch_yoke(ax)
        elif "worm" in name and "wheel" in name:
            self._draw_worm_and_wheel(ax)
        elif "bevel" in name and "gear" in name:
            self._draw_bevel_gear_pair(ax)
        else:
            self._draw_generic_graph(ax, getattr(solution_node, 'graph', None))

        self._annotate_modifications(ax, getattr(solution_node, 'path', []))

        filepath = os.path.join('output', filename)
        plt.savefig(filepath, dpi=200, bbox_inches='tight')
        plt.close(fig)
        
        # Also generate NetworkX graph visualization
        if hasattr(solution_node, 'graph') and solution_node.graph is not None:
            graph_filename = filename.replace('.png', '_graph.png')
            self.draw_networkx_graph(solution_node.graph, base_mechanism_name, graph_filename, getattr(solution_node, 'path', []))

    def _draw_slider_crank(self, ax) -> None:
        # Ground
        ax.plot([-1, 7], [-0.2, -0.2], color='black', linewidth=5)
        ax.text(3, -0.5, "Ground", ha='center')

        # Crank
        ground_p1 = (0, 0)
        crank_p = (1.5, 1.5)
        ax.plot([ground_p1[0], crank_p[0]], [ground_p1[1], crank_p[1]], 'r-o', linewidth=3)
        ax.text(0.75, 0.9, "Crank (Input)")

        # Coupler
        coupler_p = (5, 0)
        ax.plot([crank_p[0], coupler_p[0]], [crank_p[1], coupler_p[1]], 'b-o', linewidth=3)

        # Slider body
        slider = patches.Rectangle((4.5, -0.15), 1.0, 0.3, facecolor='gray', edgecolor='black')
        ax.add_patch(slider)
        ax.text(5.0, 0.3, "Slider (Bolt)", ha='center')

    def _draw_rack_and_pinion(self, ax) -> None:
        # Pinion
        pinion_center = (2, 1)
        pinion = patches.Circle(pinion_center, radius=1.0, facecolor='lightgray', edgecolor='black')
        ax.add_patch(pinion)
        ax.plot(pinion_center[0], pinion_center[1], 'ro')
        ax.text(pinion_center[0], pinion_center[1] + 1.2, "Pinion (Handle)")

        # Rack
        rack = patches.Rectangle((0, -0.2), 6, 0.4, facecolor='gray', edgecolor='black')
        ax.add_patch(rack)
        ax.text(3, -0.5, "Rack (Bolt)", ha='center')
        for i in range(1, 6):
            ax.plot([i, i + 0.2, i + 0.4], [0.2, 0.5, 0.2], color='black')

    def _draw_four_bar(self, ax) -> None:
        # Ground pivots
        g1 = (0, 0)
        g2 = (5, 0)
        ax.plot([g1[0]-0.2, g1[0]+0.2], [g1[1], g1[1]], 'k-', lw=4)
        ax.plot([g2[0]-0.2, g2[0]+0.2], [g2[1], g2[1]], 'k-', lw=4)
        # Links
        input_p = (1.5, 1.5)
        coupler_p = (3.3, 1.0)
        ax.plot([g1[0], input_p[0]], [g1[1], input_p[1]], 'r-o', lw=3)
        ax.plot([input_p[0], coupler_p[0]], [input_p[1], coupler_p[1]], 'b-o', lw=3)
        ax.plot([coupler_p[0], g2[0]], [coupler_p[1], g2[1]], 'g-o', lw=3)
        ax.text(2.5, 1.7, "Coupler", ha='center')

    def _draw_cam_follower(self, ax) -> None:
        # Cam disk
        cam_center = (2, 1)
        cam = patches.Circle(cam_center, radius=0.8, facecolor='lightgray', edgecolor='black')
        ax.add_patch(cam)
        ax.text(2, 2.1, "Cam", ha='center')
        # Follower slider
        track = patches.Rectangle((1.8, -0.3), 0.4, 2.2, facecolor='none', edgecolor='black', linestyle='--')
        ax.add_patch(track)
        follower = patches.Rectangle((1.7, 0.6), 0.6, 0.6, facecolor='gray', edgecolor='black')
        ax.add_patch(follower)
        ax.text(3.2, 0.9, "Follower", ha='left')

    def _draw_spur_gear_pair(self, ax) -> None:
        c1 = (2.0, 1.0)
        c2 = (4.5, 1.0)
        g1 = patches.Circle(c1, radius=1.0, facecolor='lightgray', edgecolor='black')
        g2 = patches.Circle(c2, radius=1.2, facecolor='lightgray', edgecolor='black')
        ax.add_patch(g1)
        ax.add_patch(g2)
        ax.plot([c1[0], c2[0]], [c1[1], c2[1]], 'k--', alpha=0.5)
        ax.text(2.0, 2.3, "Spur Gear 1", ha='center')
        ax.text(4.5, 2.5, "Spur Gear 2", ha='center')

    def _draw_scotch_yoke(self, ax) -> None:
        # Slider slot
        slot = patches.Rectangle((3.8, -0.4), 0.6, 2.8, facecolor='none', edgecolor='black')
        ax.add_patch(slot)
        slider = patches.Rectangle((3.7, 0.6), 0.8, 0.6, facecolor='gray', edgecolor='black')
        ax.add_patch(slider)
        # Crank and pin
        ground = (0, 0)
        crank_tip = (2.0, 1.0)
        ax.plot([ground[0], crank_tip[0]], [ground[1], crank_tip[1]], 'r-o', lw=3)
        pin = patches.Circle(crank_tip, radius=0.1, facecolor='red', edgecolor='black')
        ax.add_patch(pin)
        ax.plot([crank_tip[0], 4.1], [crank_tip[1], 0.9], 'k--', alpha=0.5)
        ax.text(0.9, 0.8, "Crank", ha='center')

    def _draw_worm_and_wheel(self, ax) -> None:
        # Worm (cylinder depiction)
        worm = patches.Rectangle((0.5, 0.8), 2.5, 0.4, facecolor='lightgray', edgecolor='black')
        ax.add_patch(worm)
        for i in range(6):
            ax.plot([0.6 + i*0.4, 0.8 + i*0.4], [0.8, 1.2], 'k-', alpha=0.6)
        # Wheel (gear)
        wheel_center = (4.5, 1.0)
        wheel = patches.Circle(wheel_center, radius=1.0, facecolor='lightgray', edgecolor='black')
        ax.add_patch(wheel)
        ax.text(1.8, 1.5, "Worm", ha='center')
        ax.text(4.5, 2.3, "Wheel", ha='center')

    def _draw_bevel_gear_pair(self, ax) -> None:
        c1 = (3.0, 1.5)
        c2 = (4.5, 0.0)
        g1 = patches.Circle(c1, radius=1.0, facecolor='lightgray', edgecolor='black')
        g2 = patches.Circle(c2, radius=1.0, facecolor='lightgray', edgecolor='black')
        ax.add_patch(g1)
        ax.add_patch(g2)
        ax.plot([c1[0], c2[0]], [c1[1], c2[1]], 'k--', alpha=0.5)
        ax.text(2.9, 2.8, "Bevel Gear", ha='center')

    def draw_networkx_graph(self, graph, mechanism_name: str, filename: str, path: List[str] = None) -> None:
        """
        Creates a NetworkX visualization of the mechanism graph topology.
        Shows nodes (elements) and edges (joints) with joint type labels.
        """
        import networkx as nx
        
        G = nx.from_numpy_array(graph.adj_matrix)
        pos = nx.spring_layout(G, seed=42)  # Consistent layout
        
        # Create edge labels from joint types
        edge_labels = {}
        for u, v, data in G.edges(data=True):
            joint_code = data['weight']
            # Find the joint type from the code
            joint_type = None
            for key, value in graph.JOINT_MAP.items():
                if value == joint_code:
                    joint_type = key
                    break
            if joint_type:
                edge_labels[(u, v)] = joint_type
        
        fig, ax = plt.subplots(figsize=(10, 8))
        
        # Node colors: highlight Ground (node 0) in different color
        node_colors = ['lightcoral' if i == 0 else 'skyblue' for i in range(graph.num_elements)]
        
        # Draw the graph
        nx.draw(G, pos, ax=ax, with_labels=True, labels={i: name for i, name in enumerate(graph.element_names)},
                node_color=node_colors, node_size=2000, edge_color='gray', 
                font_size=10, font_weight='bold')
        nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_color='red', font_size=10, ax=ax)
        
        # Title with DOF information
        dof = graph.calculate_dof()
        title = f"Mechanism Graph: {mechanism_name}\nDOF = {dof}"
        ax.set_title(title, fontsize=14, fontweight='bold')
        ax.axis('off')
        
        # Add modification annotations
        if path:
            y_pos = 0.95
            ax.text(0.02, y_pos, "Applied Rules:", transform=ax.transAxes, 
                   fontsize=10, weight='bold', verticalalignment='top')
            for rule_id in path:
                y_pos -= 0.05
                rule_desc = self._get_rule_description(rule_id)
                ax.text(0.02, y_pos, f"  • {rule_id}: {rule_desc}", 
                       transform=ax.transAxes, fontsize=9, verticalalignment='top')
        
        # Add legend for joint types
        legend_text = "Joint Types:\n"
        for joint_type, code in graph.JOINT_MAP.items():
            legend_text += f"  {joint_type} = {self._get_joint_description(joint_type)}\n"
        ax.text(0.98, 0.02, legend_text, transform=ax.transAxes, 
               fontsize=8, verticalalignment='bottom', horizontalalignment='right',
               bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
        
        filepath = os.path.join('output', filename)
        plt.savefig(filepath, dpi=200, bbox_inches='tight')
        print(f"  -> NetworkX graph saved to 'output/{filename}'")
        plt.close(fig)
    
    def _get_rule_description(self, rule_id: str) -> str:
        """Returns a human-readable description for a rule ID."""
        rule_map = {
            'R3.1': 'Add Stopper',
            'R4.1': 'Add Return Spring',
            'R2.1': 'Add Variable Joint',
            'R1.1': 'Add Revolute Joint',
            'R1.2': 'Add Prismatic Joint'
        }
        return rule_map.get(rule_id, 'Unknown')
    
    def _get_joint_description(self, joint_type: str) -> str:
        """Returns a description for each joint type."""
        joint_desc = {
            'R': 'Revolute',
            'P': 'Prismatic',
            'X': 'Higher Pair',
            'F': 'Fixed',
            'LP': 'Limited Prismatic',
            'SP': 'Spring-Loaded Prismatic',
            'LSP': 'Limited Spring Prismatic'
        }
        return joint_desc.get(joint_type, 'Unknown')
    
    def _draw_generic_graph(self, ax, graph) -> None:
        ax.text(0.5, 0.5, "Generic Graph Visualization\n(saved silently)",
                ha='center', va='center', fontsize=12, color='red')
        # Avoid calling graph.visualize() here to prevent blocking pop-ups

    def _annotate_modifications(self, ax, path: List[str]) -> None:
        y_pos = 3.5
        ax.text(0, y_pos, "Modifications:", fontsize=10, weight='bold')
        if not path:
            ax.text(0, y_pos - 0.4, " - None", fontsize=9)
            return

        for rule_id in path:
            y_pos -= 0.4
            if rule_id == "R3.1":
                ax.text(0, y_pos, " - R3.1: Added Stopper", fontsize=9)
                stopper = patches.Rectangle((6, -0.15), 0.2, 0.5, facecolor='darkred')
                ax.add_patch(stopper)
                ax.text(6.1, 0.5, "Stopper", ha='center', color='darkred')
            elif rule_id == "R4.1":
                ax.text(0, y_pos, " - R4.1: Added Return Spring", fontsize=9)
                ax.plot([0, 1.5], [1.5, 1.5], 'k--', alpha=0.5)
                ax.text(0.75, 1.6, "Spring", ha='center', color='green')


