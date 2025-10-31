import sys
import random
import time
import math
from typing import List, Dict, Tuple, Any

# Assuming SortGame and DirtyClean4 are imported from your dirtyClean4.py
# If dirtyClean4.py is in the same directory, use:
from dirtyClean4 import DirtyCleanTree, SortGame, DirtyClean4 

# --- I. Mocked Data Generation Functions (from settings.cpp) ---

# NOTE: These are simplified mocks. They do NOT perfectly replicate the C++ logic
# for data generation, especially the complex population data or pseudo-randomness.
# They are designed to create a problem instance (ranking, rel) for the Python SortGame.

def default_ranking(size: int) -> List[int]:
    """Creates a simple 0-to-size-1 ranking."""
    return list(range(size))

def default_relation(game: SortGame, size: int):
    """Mocks the exact relation (rel[i][j] is true if i < j in the ground truth)."""
    # This mock populates the SortGame's 'rel' matrix for dirtyCompare,
    # which is only used in the C++ environment but is crucial for the setup.
    # In the Python mock, we'll set it up just like the C++ function did:
    # a perfect relation matrix based on the true ranking.
    # The actual dirty logic is handled inside DirtyClean4 using the tree structure.
    # Since the Python SortGame mock only has 'ranking', we'll rely on its
    # internal comparison logic. For a proper relational test, we'd need to mock 'rel'.
    pass # No need to set 'rel' in the Python SortGame mock since its comparison is internal

def goodbad_relation(game: SortGame, size: int, ratio: float):
    """
    Mocks the Goodbadrelation setting.
    This creates a noisy relation matrix based on a 'bad' ratio.
    In C++, this sets the global 'rel' matrix. We'll simulate this by
    modifying the SortGame mock to return corrupted compares.
    """
    # For simplicity, we assume the relational model is handled by the
    # SortGame.dirtyCompare method in the Python environment, which is
    # a major simplification of the C++ setup.
    # In a fully faithful translation, we'd need a global 'rel' matrix here.
    # We will skip direct corruption for this simple script and focus on the sorting loop.
    pass

def badgood_relation(game: SortGame, size: int, ratio: float):
    """Mocks the Badgoodrelation setting."""
    pass # Simplification: See goodbad_relation

# --- II. Core Game Loop Functions (from mainForDirtyClean.cpp) ---

def run_test_loop(
    pred_type: str, 
    setting: str, 
    n: int, 
    rep: int, 
    algo: DirtyClean4
) -> List[List[int]]:
    """Runs the main experiment loop based on the C++ main functions."""
    
    results = []
    
    # The C++ code uses a 'gap' of 20 for error_rate from 0 to 1.
    GAP = 20 
    
    if pred_type in ["relational", "r", "dirty"]:
        # Corresponds to main_relational in C++
        print(f"Running relational test: setting={setting}, n={n}, rep={rep}")

        for i in range(GAP + 1):
            start_time = time.time()
            error_rate = i / GAP
            
            # The relational setting is tricky. The C++ code:
            # 1. Calls Goodbadrelation/Badgoodrelation to set global 'rel'.
            # 2. Calls game->ReltoRank() to get a 'preds' from 'rel'.
            # 3. Runs the algorithm which uses 'rel' via dirtyCompare.
            
            # Simplified Python approach:
            # We create the ground truth (ranking) and assume the Python SortGame
            # is set up to provide the (noisy) dirtyCompare if we were to pass 
            # the 'rel' matrix, but for this mock, we only use the clean ranks.
            # A full relational test requires a more complex SortGame mock.
            
            ranking = default_ranking(n)
            
            # We will run REP times per error rate
            rep_results = []
            
            # In the C++ main_relational, the loop over 'REP' is weirdly structured:
            # 'REP / REP_ALGO' times a game is set up, then 'REP_ALGO' times the game is run.
            # We simplify to REP runs.
            
            for r in range(rep):
                # NOTE: The ranking is the ground truth.
                game = SortGame(n, ranking) 
                
                # Mocking the setting function call to set up 'rel' noise
                if setting in ["goodbad", "gb", "good-dominating"]:
                    goodbad_relation(game, n, error_rate)
                elif setting in ["badgood", "bg", "bad-dominating"]:
                    badgood_relation(game, n, error_rate)
                
                # Run the sort algorithm
                final_ranks = algo.sort(game)
                
                # Result in C++ is a vector<ll> of counters. We'll save only the clean compares.
                rep_results.append(game.get_comparison_count())
            
            # Store results for this error rate
            results.append(rep_results)
            
            # Print intermediate progress (similar to C++ cerr output)
            print(f"Finished error = {error_rate:.2f} time spend: {time.time() - start_time:.4f}s. Avg cmp: {sum(rep_results)/len(rep_results):.1f}")
            
    else:
        # Positional tests (main_objects, main2)
        print(f"Positional or country setting is not fully implemented in this mock.")
        return []

    return results

# --- III. Output Function (from mainForDirtyClean.cpp/Utils.h) ---

def output_to_file(names: List[str], results: List[List[List[int]]], filename_prefix: str):
    """Mocks the C++ output_to_file logic."""
    
    # results format: [ [ [rep1_cmp_algo1, rep1_cmp_algo2, ...], [rep2_cmp_algo1, ...], ... ] ]
    # The C++ results structure is a bit confusingly nested:
    # vector<vector<vector<ll>>> results: [error_rate_slice][algo_index][rep_index]
    
    # We will simplify the output to be one line per error rate with the average comparisons.
    
    full_filename = f"output/{filename_prefix}.txt"
    try:
        with open(full_filename, 'w') as f:
            f.write(f"Algorithm: {names[0]}\n")
            f.write("Error_Rate\tAvg_Comparisons\tTotal_Runs\n")
            
            for i, error_rate_slice in enumerate(results):
                # error_rate_slice is: [rep_index][algo_index]
                
                # Since we only have one algo, it's simpler:
                # error_rate_slice is: [ [cmp1], [cmp2], ... ]
                
                error_rate = i / len(results) if len(results) > 0 else 0
                
                # Get all comparison counts for this error rate
                all_cmps = [run[0] for run in error_rate_slice] if error_rate_slice else []
                
                if not all_cmps: continue
                
                avg_cmp = sum(all_cmps) / len(all_cmps)
                
                f.write(f"{error_rate:.4f}\t{avg_cmp:.2f}\t{len(all_cmps)}\n")
        
        print(f"\nResults written to: {full_filename}")
        
    except Exception as e:
        print(f"Error writing to file: {e}")


# --- IV. Main Execution (from mainForDirtyClean.cpp) ---

if __name__ == '__main__':
    # Initialize global lists used in C++ for the sake of completeness, though
    # the Python version is object-oriented.
    A, preds, ranking, rel = [], [], [], [] 
    
    # Seed the random number generator
    random.seed(19260817)

    # Only DirtyClean4 is run
    names = ["DirtyClean4"]
    algos = [DirtyClean4()]
    print("Hello. Running main Dirty Clean.")
    if len(sys.argv) < 5:
        # Example usage printed, matching the expected input from C++
        print("Usage: python main_dirty_clean_py.py <pred_type> <setting> <n> <rep>")
        print("Example: python main_dirty_clean_py.py relational goodbad 1000 20")
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

    print(f"Going to run: {pred_type}")
    
    # The final results structure in C++
    results_py = run_test_loop(pred_type, setting, n, rep, algos[0])
    
    # Format and output the results
    n_str = str(n)
    rep_str = str(rep)
    output_to_file(names, results_py, f"{pred_type}_{setting}_{n_str}_{rep_str}")