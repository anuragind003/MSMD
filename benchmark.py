import os
import json
import time
from typing import Dict, Any, List

from tabulate import tabulate

# Local imports
from src.initial_solution import find_initial_solutions
from src.synthesis_engine import run_synthesis


def run_single_benchmark(task_filepath: str, method: str) -> Dict[str, Any]:
    """Run one synthesis task and return performance metrics for a method."""
    with open(task_filepath, 'r', encoding='utf-8') as f:
        task = json.load(f)

    start_time = time.time()

    # Step 1: Find initial solutions via selected method
    initial_solutions = find_initial_solutions(task, method=method)
    num_initial = len(initial_solutions)

    # Step 2: Run synthesis if starting points were found (use first candidate)
    final_node = None
    if initial_solutions:
        final_node = run_synthesis(task, initial_solutions[0])

    duration = time.time() - start_time

    # Build path string with a clear placeholder when no modifications were needed
    if final_node:
        path_list = getattr(final_node, 'path', []) or []
        path_str = " -> ".join(path_list) if len(path_list) > 0 else "(none)"
    else:
        path_str = "N/A"

    return {
        "Task": task.get('task_name', os.path.basename(task_filepath)),
        "Method": "AI-Enhanced" if method == 'ai' else "Baseline",
        "Success": "Yes" if final_node else "No",
        "Time (sec)": f"{duration:.2f}",
        "# Initial Solutions": num_initial,
        "Final Path": path_str,
    }


def main() -> None:
    print("==============================================")
    print("      Running CoDe-SyMM 2.0 Benchmark")
    print("==============================================")

    task_dir = os.path.join(os.path.dirname(__file__), 'evaluation_tasks')
    task_files = sorted([
        os.path.join(task_dir, f)
        for f in os.listdir(task_dir)
        if f.endswith('.json')
    ])

    results: List[Dict[str, Any]] = []
    for task_file in task_files:
        print(f"\n--- BENCHMARKING TASK: {os.path.basename(task_file)} ---")
        results.append(run_single_benchmark(task_file, method='rule'))
        results.append(run_single_benchmark(task_file, method='ai'))

    print("\n\n==============================================")
    print("              Benchmark Results")
    print("==============================================")

    headers = ["Task", "Method", "Success", "Time (sec)", "# Initial Solutions", "Final Path"]
    table_data = [[r[h] for h in headers] for r in results]
    print(tabulate(table_data, headers=headers, tablefmt="grid"))


if __name__ == '__main__':
    main()


