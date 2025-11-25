import os
import json
from typing import Optional, List, Tuple

from .initial_solution import find_initial_solutions
from .synthesis_engine import run_synthesis, SearchNode
from .visualizer import Visualizer


def _list_task_files(tasks_dir: str) -> List[str]:
    return [f for f in os.listdir(tasks_dir) if f.endswith('.json')]


def select_task(tasks_dir: str = 'tasks') -> Optional[str]:
    """Lets the user select a design task from the tasks directory."""
    print("\n--- Task Selection ---")

    if not os.path.isdir(tasks_dir):
        print(f"Tasks directory not found: {tasks_dir}")
        return None

    task_files = _list_task_files(tasks_dir)
    if not task_files:
        print("No task files found in the 'tasks/' directory.")
        return None

    for i, filename in enumerate(task_files):
        print(f"[{i+1}] {filename}")

    while True:
        try:
            choice = int(input("Select a task to run: ")) - 1
            if 0 <= choice < len(task_files):
                return os.path.join(tasks_dir, task_files[choice])
            else:
                print("Invalid selection. Please try again.")
        except ValueError:
            print("Please enter a number.")


def _load_task(task_filepath: str) -> Optional[dict]:
    try:
        with open(task_filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Failed to load task file '{task_filepath}': {e}")
        return None


def _ensure_output_dir(path: str = 'output') -> None:
    if not os.path.exists(path):
        os.makedirs(path)


def _select_retrieval_method() -> str:
    print("\n--- Retrieval Method ---")
    print("[1] AI (Gemini AI) - default - Intelligent semantic matching")
    print("[2] Rule-based (exact behavior match)")
    choice = input("Choose retrieval method [1/2]: ").strip()
    if choice == '2':
        return 'rule'
    return 'ai'


def main_cli() -> None:
    """Main function to run the interactive command-line interface."""
    print("======================================================")
    print(" Welcome to CoDe-SyMM 2.0 Synthesis Tool")
    print("======================================================")

    task_filepath = select_task()
    if not task_filepath:
        return

    task = _load_task(task_filepath)
    if task is None:
        return

    print(f"\n--- Starting Synthesis for: {task.get('task_name', os.path.basename(task_filepath))} ---")

    # 1. Choose retrieval method and find Initial Solutions
    method = _select_retrieval_method()
    initial_solutions = find_initial_solutions(task, method=method)
    if not initial_solutions:
        print("\nCould not find any initial solutions. Process halted.")
        return

    print(f"\nFound {len(initial_solutions)} potential starting point(s).")

    # 2. Run Synthesis for each
    final_solutions: List[Tuple[str, SearchNode]] = []
    _ensure_output_dir('output')
    visualizer = Visualizer()

    for i, initial_sol in enumerate(initial_solutions):
        print(f"\n--- Exploring Initial Solution #{i+1}: {initial_sol['name']} ---")
        final_node = run_synthesis(task, initial_sol, enable_visualization=True)
        if final_node:
            final_solutions.append((initial_sol['name'], final_node))
            
            # Print step-by-step visualization location
            if hasattr(final_node, 'path') and final_node.path:
                task_name = task.get('task_name', 'Unknown_Task').replace(" ", "_")
                mechanism_name = initial_sol['name'].replace(" ", "_")
                steps_dir = f"output/synthesis_steps/{task_name}/{mechanism_name}"
                print(f"  -> Step-by-step visualizations saved to: {steps_dir}/")

    # 3. Display Results
    print("\n======================================================")
    print("               SYNTHESIS COMPLETE")
    print("======================================================")
    if not final_solutions:
        print("No valid final mechanisms were synthesized.")
    else:
        print(f"Successfully synthesized {len(final_solutions)} valid mechanism(s).")
        for i, (name, solution_node) in enumerate(final_solutions):
            print(f"\n--- Final Solution #{i+1} (from '{name}') ---")
            if hasattr(solution_node, 'path') and solution_node.path:
                print(f"  Modification Path: {' -> '.join(solution_node.path)}")
            else:
                print("  Modification Path: (none)")

            output_filename = f"solution_{i+1}_{name.replace(' ', '_')}.png"
            visualizer.draw_schematic(name, solution_node, output_filename)
            print(f"  -> Schematic saved to 'output/{output_filename}'")

            # Generate Animation
            gif_filename = f"solution_{i+1}_{name.replace(' ', '_')}.gif"
            print(f"  -> Generating animation for '{name}'...")
            visualizer.generate_animation(name, gif_filename, solution_node=solution_node)

    print("\nExiting CoDe-SyMM 2.0.")


if __name__ == '__main__':
    main_cli()


