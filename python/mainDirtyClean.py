import sys
import random
import time
import math
import os
from typing import List, Dict, Tuple, Any

# Assuming SortGame and DirtyClean4 are imported from your dirtyClean4.py
# If dirtyClean4.py is in the same directory, use:
from dirtyClean4 import DirtyCleanTree, SortGame, DirtyClean4 

# --- I. Data Generation Functions (from settings.cpp) ---

def default_ranking(size: int) -> List[int]:
    """Creates a simple 0-to-size-1 ranking (index -> rank)."""
    return list(range(size))

def default_relation(n: int, ranking: List[int]) -> List[List[bool]]:
    """
    Creates a "perfect" relation matrix based on the ground truth ranking.
    rel[i][j] is true if ranking[i] < ranking[j].
    """
    rel = [[False for _ in range(n)] for _ in range(n)]
    for i in range(n):
        for j in range(n):
            if i == j: continue
            if ranking[i] < ranking[j]:
                rel[i][j] = True
    return rel

def goodbad_relation(n: int, ranking: List[int], ratio: float) -> List[List[bool]]:
    """
    Mocks the Goodbadrelation setting.
    Starts with a default relation, then corrupts pairs where both items are "bad".
    """
    # Start with the perfect relation
    rel = default_relation(n, ranking)
    
    # Determine which items are "bad"
    ifBad = [random.random() <= ratio for _ in range(n)]
    
    for i in range(n):
        for j in range(i + 1, n):
            # If both items are bad, randomize their relation
            if ifBad[i] and ifBad[j]:
                R = random.random() <= 0.5
                rel[i][j] = R
                rel[j][i] = not R
    return rel

def badgood_relation(n: int, ranking: List[int], ratio: float) -> List[List[bool]]:
    """
    Mocks the Badgoodrelation setting.
    Starts with a default relation, then corrupts pairs where at least one item is "bad".
    """
    # Start with the perfect relation
    rel = default_relation(n, ranking)
    
    # Determine which items are "bad"
    ifBad = [random.random() <= ratio for _ in range(n)]
    
    for i in range(n):
        for j in range(i + 1, n):
            # If at least one item is bad, potentially introduce an error
            if ifBad[i] or ifBad[j]:
                # C++ logic: 50% chance to force (j < i) regardless of truth
                if random.random() <= 0.5:
                    rel[i][j] = False
                    rel[j][i] = True
    return rel

# --- II. Core Game Loop Functions (from main.cpp) ---

def run_test_loop(
    pred_type: str, 
    setting: str, 
    n: int, 
    rep: int, 
    algo: DirtyClean4
) -> List[List[int]]:
    """Runs the main experiment loop based on the C++ main functions."""
    
    # This list will store results per error rate.
    # Format: [ [run1_compares, run2_compares, ...],  (for error_rate 0)
    #           [run1_compares, run2_compares, ...],  (for error_rate 0.05)
    #           ... ]
    results_by_error_rate: List[List[int]] = []
    
    # The C++ code uses a 'gap' of 20 for error_rate from 0 to 1.
    GAP = 20 
    
    if pred_type in ["relational", "r", "dirty"]:
        # Corresponds to main_relational in C++
        print(f"Running relational test: setting={setting}, n={n}, rep={rep}")

        for i in range(GAP + 1):
            start_time = time.time()
            error_rate = i / GAP
            
            # This list holds all results for this single error rate
            rep_results: List[int] = []
            
            # --- C++ Logic Translation ---
            # 1. Create a single ground truth ranking for this error rate.
            ranking = default_ranking(n)
            
            # 2. Generate the noisy relation matrix *once* for this error rate
            #    (This differs from C++'s main_relational, which re-generates
            #     the game *inside* the REP loop, but we'll follow this script's
            #     original structure which implies one game setup per error rate,
            #     and multiple runs on it, though C++ main.cpp is different.
            #     Let's match main.cpp: generate game *inside* rep loop.)

            # C++ main_relational loop structure:
            # for (int i = 0; i < REP / REP_ALGO; i++) {
            #    SortGame *game = new SortGame(); 
            #    ... setup game (Goodbadrelation) ...
            #    for (int rep_algo = 1; rep_algo <= REP_ALGO; rep_algo++) {
            #       game->ReltoRank(); // This shuffles predictions, not relevant for DirtyClean4
            #       controller.runGame();
            #    }
            # }
            # This is complex. A simpler, standard test is REP runs, each with a new game.
            
            print(f"Running error rate: {error_rate:.2f} ({i}/{GAP})")
            
            for r in range(rep):
                # Create a new ground truth ranking for each run
                ranking = default_ranking(n)
                
                # Create a new noisy relation matrix for each run
                noisy_rel = None
                if setting in ["goodbad", "gb", "good-dominating"]:
                    noisy_rel = goodbad_relation(n, ranking, error_rate)
                elif setting in ["badgood", "bg", "bad-dominating"]:
                    noisy_rel = badgood_relation(n, ranking, error_rate)
                else:
                    print(f"Warning: Unknown setting '{setting}'. Using clean relation.")
                    noisy_rel = default_relation(n, ranking)

                # 3. Instantiate the SortGame with the noisy relation
                game = SortGame(n, ranking, noisy_rel) 
                
                # 4. Run the sort algorithm
                #    We create a new sorter instance to reset its internal state
                sorter_instance = DirtyClean4()
                final_ranks = sorter_instance.sort(game)
                
                # 5. Store the number of *clean* comparisons
                rep_results.append(game.get_comparison_count())
            
            # Store all results for this error rate
            results_by_error_rate.append(rep_results)
            
            # Print intermediate progress
            avg_comps = sum(rep_results) / len(rep_results) if rep_results else 0
            print(f"  Finished error = {error_rate:.2f}. Time: {time.time() - start_time:.4f}s. Avg clean compares: {avg_comps:.1f}")
            
    else:
        # Positional tests (main_objects, main2)
        print(f"Error: Positional tests ('{pred_type}') are not implemented in this script.")
        print("Please use 'relational', 'r', or 'dirty'.")
        return []

    return results_by_error_rate

# --- III. Output Function (from Utils.cpp) ---

def output_to_file(names: List[str], results_by_error_rate: List[List[int]], filename_prefix: str):
    """
    Writes results to a file in a format similar to the C++ version.
    'results_by_error_rate' format: [ [rep1_cmp, rep2_cmp, ...], (error 0)
                                      [rep1_cmp, rep2_cmp, ...], (error 0.05)
                                      ... ]
    """
    
    # Ensure the output directory exists
    output_dir = "output_data"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    full_filename = f"{output_dir}/{filename_prefix}.txt"
    
    num_error_steps = len(results_by_error_rate)
    if num_error_steps == 0:
        print("No results to write.")
        return
        
    num_algos = len(names) # We only have 1
    num_reps = len(results_by_error_rate[0]) if num_error_steps > 0 else 0
    
    try:
        with open(full_filename, 'w') as f:
            # Header line: Algorithm names
            f.write(" ".join(names) + "\n")
            
            # Second line: dimensions (algos, error_steps, reps)
            f.write(f"{num_algos} {num_error_steps} {num_reps}\n")
            
            # Data blocks
            # C++ format: one block per algorithm
            for algo_index in range(num_algos):
                # For each algorithm, write one line per error rate
                for error_step_index in range(num_error_steps):
                    # Get the list of repetition results for this algo and error rate
                    # Since we only have one algo, results_by_error_rate[error_step_index] is the list.
                    rep_data = results_by_error_rate[error_step_index]
                    
                    # Convert all rep results to strings
                    rep_strings = [str(cmp_count) for cmp_count in rep_data]
                    
                    f.write(" ".join(rep_strings) + " \n") # Add trailing space like C++
    
        print(f"\nResults successfully written to: {full_filename}")
        
    except Exception as e:
        print(f"Error writing to file '{full_filename}': {e}")


# --- IV. Main Execution (from main.cpp) ---

if __name__ == '__main__':
    # Seed the random number generator (matches C++)
    random.seed(19260817)

    # We are only testing DirtyClean4
    names = ["DirtyClean4"]
    algos = [DirtyClean4()] # We pass the class/instance to the loop
    
    print("--- Python DirtyClean4 Test Harness ---")
    
    if len(sys.argv) < 5:
        # Example usage printed, matching the expected input from C++
        print("\nUsage: python mainDirtyClean.py <pred_type> <setting> <n> <rep>")
        print("  <pred_type>: 'relational', 'r', or 'dirty'")
        print("  <setting>: 'goodbad' or 'badgood'")
        print("  <n>: Number of items (e.g., 1000)")
        print("  <rep>: Repetitions per error rate (e.g., 20)")
        print("\nExample: python mainDirtyClean.py relational goodbad 1000 20")
        sys.exit(1)

    # Read command-line arguments
    pred_type = sys.argv[1].lower()
    setting = sys.argv[2].lower()
    
    n, rep = 0, 0
    try:
        n = int(sys.argv[3])
        rep = int(sys.argv[4])
    except (ValueError, IndexError):
        print("Error: N and REP must be integers.")
        sys.exit(1)

    # --- Run the Test Loop ---
    # We pass the first (and only) algorithm *instance*
    # Note: The loop creates new instances internally, so this is just a placeholder
    final_results = run_test_loop(pred_type, setting, n, rep, algos[0])
    
    # --- Format and Output the Results ---
    if final_results:
        n_str = str(n)
        rep_str = str(rep)
        filename = f"{pred_type}_{setting}_{n_str}_{rep_str}"
        output_to_file(names, final_results, filename)
    else:
        print("No results were generated.")
