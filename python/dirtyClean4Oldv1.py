

import random
import math
from typing import Callable, List, Optional, Any, Tuple

# --- Node Class (Augmented for Dirty/Clean Logic) ---
class Node:
    """Represents a node in the Scapegoat Tree. Augmented with st/ed for range tracking."""
    def __init__(self, value: Any, st: Any = None, ed: Any = None):
        self.left: Optional[Node] = None
        self.right: Optional[Node] = None
        self.parent: Optional[Node] = None
        self.value = value
        
        # st (start) and ed (end) are used to track the clean-sorted range (from C++ code)
        self.st: Any = st  # Lower bound (value of nearest clean-smaller ancestor/predecessor)
        self.ed: Any = ed  # Upper bound (value of nearest clean-larger ancestor/successor)

# --- SortGame Class (Minimal Mock-up based on both2.py) ---
# In a real setup, this would be an interface to the game environment.
class SortGame:
    def __init__(self, n: int, ranking: List[int]):
        """Initializes the game with the ground truth ranking."""
        self.n = n
        self.ranking = ranking
        self.comparison_count = 0
    
    def getSize(self) -> int:
        return self.n
    
    def compare(self, i: int, j: int) -> bool:
        """The 'clean' comparison: uses ground truth ranking."""
        self.comparison_count += 1
        return self.ranking[i] < self.ranking[j]

    def dirtyCompare(self, i: int, j: int) -> bool:
        """The 'dirty' comparison: uses the tree's current ordering."""
        # For simplicity in this example, we'll use a slightly corrupted clean comparison
        # In the C++ context, this comparison is handled by the tree structure itself.
        # For a runnable implementation, we assume the tree is using an insertion order
        # that is *close* to the clean order. We'll just proxy the clean compare here,
        # but a real implementation would use the nodes' actual positions or a prediction array.
        return self.compare(i, j) 

    def get_comparison_count(self) -> int:
        return self.comparison_count

# --- DirtyCleanTree (Augmented Scapegoat Tree) ---
class DirtyCleanTree:
    """A minimal Scapegoat Tree implementation adapted for the DirtyClean4 algorithm."""
    
    # Constants equivalent to C++'s -inf and inf for Node st/ed
    NEG_INF = float('-inf')
    POS_INF = float('inf')
    ALPHA = 2/3 

    def __init__(self):
        self.root: Optional[Node] = None
        self.n = 0
        self.size_limit = 0 # For delete/rebuild tracking (not fully used here)

    def size(self, node: Optional[Node]) -> int:
        if node is None: return 0
        return 1 + self.size(node.left) + self.size(node.right)

    def _store_in_array(self, u: Optional[Node], a: List[Node], i: int) -> int:
        """Stores nodes in an array in in-order sequence."""
        if u is None: return i
        i = self._store_in_array(u.left, a, i)
        a[i] = u
        i += 1
        return self._store_in_array(u.right, a, i)

    def _build_balanced_from_array(self, a: List[Node], i: int, n: int) -> Optional[Node]:
        """Builds a perfectly balanced BST from a sorted array segment."""
        if n == 0: return None
        m = n // 2
        
        node = a[i+m]
        
        node.left = self._build_balanced_from_array(a, i, m)
        if node.left: node.left.parent = node
            
        node.right = self._build_balanced_from_array(a, i + m + 1, n - m - 1)
        if node.right: node.right.parent = node
        
        # Clear st/ed if needed here, or let insertion handle it
        return node

    def _rebuild_tree(self, u: Node):
        """Rebuilds the subtree rooted at u to be perfectly balanced."""
        n_size = self.size(u)
        p = u.parent
        
        a = [None] * n_size # Type hint warning ignored: will be populated with Nodes
        self._store_in_array(u, a, 0)

        new_root = self._build_balanced_from_array(a, 0, n_size)

        if p is None:
            self.root = new_root
            if self.root: self.root.parent = None
        elif p.right == u:
            p.right = new_root
            if p.right: p.right.parent = p
        else:
            p.left = new_root
            if p.left: p.left.parent = p
            
    # --- Specialized Insertion for DirtyClean4 ---

    def _bst_insert_custom(self, new_node: Node, comp: Callable[[int, int], bool]) -> Tuple[Optional[Node], int]:
        """Performs raw BST insertion using a custom comparator. Returns node and depth."""
        w = self.root
        if w is None:
            self.root = new_node
            self.n += 1
            return new_node, 0
            
        d = 0
        path_node = w
        while True:
            # Use the custom dirty comparator
            if comp(new_node.value, w.value):
                if w.left is None:
                    w.left = new_node
                    new_node.parent = w
                    break
                w = w.left
            else: # new_node.value >= w.value
                if w.right is None:
                    w.right = new_node
                    new_node.parent = w
                    break
                w = w.right
            d += 1
            path_node = w # Keep track of the node where the insertion started
            
        self.n += 1
        return new_node, d

    def freeze_insert(self, value: int, dirty: Callable[[int, int], bool], clean: Callable[[int, int], bool]) -> Node:
        """
        Equivalent to the C++ 'freeze_insert'. Inserts using dirtyCompare,
        but sets st/ed bounds using cleanCompare.
        """
        
        # 1. Standard dirty BST insertion
        new_node = Node(value)
        inserted_node, depth = self._bst_insert_custom(new_node, dirty)

        # Handle rebalancing check from C++ logic
        h_alpha = math.log(self.n, 1/self.ALPHA) if self.n > 1 else 1
        if depth > h_alpha:
            p = inserted_node.parent
            while p and self.size(p) <= self.ALPHA * self.size(p.parent):
                p = p.parent
            if p and p.parent:
                self._rebuild_tree(p.parent)

        # 2. Set initial st/ed bounds using cleanCompare
        # This is highly simplified as the true st/ed derivation is complex.
        # We find the nearest clean predecessor (st) and successor (ed).
        
        # Find clean predecessor (largest element clean-smaller than value)
        current = self.root
        pred_val = self.NEG_INF
        while current:
            if current.value == value: break # Should not happen yet
            if clean(current.value, value):
                pred_val = current.value
                current = current.right
            else:
                current = current.left
        new_node.st = pred_val

        # Find clean successor (smallest element clean-larger than value)
        current = self.root
        succ_val = self.POS_INF
        while current:
            if current.value == value: break # Should not happen yet
            if clean(value, current.value):
                succ_val = current.value
                current = current.left
            else:
                current = current.right
        new_node.ed = succ_val
        
        # The true C++ logic determines st/ed from the *path* based on ancestor bounds, 
        # but this simple approach captures the intent of range definition.
        
        return inserted_node

    def insert(self, value: int, dirty: Callable[[int, int], bool], clean: Callable[[int, int], bool], turn_value: int) -> Node:
        """
        The second-phase insert from C++ that happens after del. 
        It re-inserts 'value' using the dirty comparator, but potentially constrained 
        by knowledge of 'turn_value'. Here we just re-run freeze_insert.
        """
        # In the C++ implementation, this insertion likely guides the placement 
        # using 'turn_value' as a hint, but the ultimate structure is still dictated by dirtyCompare.
        # We will re-use freeze_insert, which implicitly re-establishes the bounds.
        return self.freeze_insert(value, dirty, clean)

    def del_node(self, target_node: Node):
        """
        Removes a specific node from the tree. This is simplified BST deletion,
        as full Scapegoat deletion/rebuild is complex.
        """
        # A simple BST delete: relies on not rebalancing, which is usually necessary
        self.n -= 1
        
        # Get parent and figure out if it's a left or right child
        p = target_node.parent
        is_left_child = p and p.left == target_node

        # Case 1: Node has 0 or 1 child
        if not target_node.left:
            replacement = target_node.right
        elif not target_node.right:
            replacement = target_node.left
        else:
            # Case 2: Node has 2 children (find successor)
            successor = target_node.right
            while successor.left:
                successor = successor.left
            
            # Swap values and delete successor (which is now 0 or 1 child case)
            target_node.value = successor.value
            target_node.st = successor.st
            target_node.ed = successor.ed
            return self.del_node(successor) # Recurse on the successor node

        # Link replacement to parent
        if not p:
            self.root = replacement
            if self.root: self.root.parent = None
        elif is_left_child:
            p.left = replacement
            if replacement: replacement.parent = p
        else:
            p.right = replacement
            if replacement: replacement.parent = p
            
    def LinearOutput(self, indexes: List[int]):
        """Performs in-order traversal and appends values to the indexes list."""
        def _inorder_helper(node: Optional[Node]):
            if node:
                _inorder_helper(node.left)
                indexes.append(node.value)
                _inorder_helper(node.right)
        _inorder_helper(self.root)

# --- DirtyClean4 Algorithm ---
class DirtyClean4:
    def __init__(self):
        self.path: List[Node] = []
        self.indexes: List[int] = []

    def _find_path(self, x: Node):
        """Traces the path from node x up to the root."""
        self.path.clear()
        helper = x
        while helper is not None:
            self.path.append(helper)
            helper = helper.parent

    def _index_to_rank(self, n: int):
        """Converts the final sorted index list to a rank list (0-based ranking)."""
        output_rank = [0] * n
        for i in range(len(self.indexes)):
            output_rank[self.indexes[i]] = i
        return output_rank

    def sort(self, game: SortGame) -> List[int]:
        """Main sorting logic, converted from DirtyClean4.cpp."""
        n = game.getSize()
        tree = DirtyCleanTree()
        
        INF = tree.POS_INF
        NEG_INF = tree.NEG_INF

        # Comparators (using lambdas and capturing 'game' and 'tree' constants)
        dirty_comp: Callable[[int, int], bool] = lambda a, b: game.dirtyCompare(a, b)
        clean_comp: Callable[[int, int], bool] = lambda a, b: game.compare(a, b)

        # 1. Shuffle elements
        shuffledA = list(range(n))
        random.shuffle(shuffledA)

        # 2. Main insertion loop
        for ai in shuffledA:
            # --- insertElement logic start ---

            # Phase 1: Dirty Insert (Initial placement with range tracking)
            p1 = tree.freeze_insert(ai, dirty_comp, clean_comp)
            p1_copy = p1
            
            self._find_path(p1)
            path_size = len(self.path)
            max_path_index = path_size - 1

            # Check initial bounds at the inserted node (p1 is the first element on path)
            leftInclude = (p1.st == NEG_INF) or game.compare(p1.st, ai)
            rightInclude = (p1.ed == INF) or game.compare(ai, p1.ed)
            lastLeftBound = p1.st
            lastRightBound = p1.ed
            
            minLeftInclude = max_path_index
            minRightInclude = max_path_index

            st, ed = 0, 0
            
            # --- Expansion Phase (Exponential Search for range violation) ---
            # Search up the path until both clean bounds (st, ed) are respected by ancestors
            while not leftInclude or not rightInclude:
                st = ed
                # C++ logic: ed = min((int)path.size() - 1, max(ed + 1, ed * 2));
                ed = min(max_path_index, max(st + 1, st * 2) if st > 0 else 1)
                
                if ed >= max_path_index:
                    leftInclude = True
                    rightInclude = True
                    minLeftInclude = min(minLeftInclude, max_path_index)
                    minRightInclude = min(minRightInclude, max_path_index)
                    break
                
                tg = self.path[ed]
                
                # Check for Left boundary violation
                if not leftInclude and tg.st != lastLeftBound:
                    # Is the new bound (tg.st) cleanly smaller than ai?
                    leftInclude = (tg.st == NEG_INF) or game.compare(tg.st, ai)
                    lastLeftBound = tg.st
                
                # Check for Right boundary violation
                if not rightInclude and tg.ed != lastRightBound:
                    # Is ai cleanly smaller than the new bound (tg.ed)?
                    rightInclude = (tg.ed == INF) or game.compare(ai, tg.ed)
                    lastRightBound = tg.ed
                
                if leftInclude: minLeftInclude = min(minLeftInclude, ed)
                if rightInclude: minRightInclude = min(minRightInclude, ed)

            # --- Search Phase (Binary Search for 'turn' index) ---
            # Find the lowest node on the path (highest index) that fixes the boundary.
            
            # The C++ implementation of the binary search phase here is highly confusing 
            # and seems to re-mix st/ed checks and path segment logic.
            # We will use the resulting 'ed' index from the expansion as the highest point 
            # where the bounds are satisfied, and then perform a simple linear search 
            # for the minimal violating point (the 'turn' node) within the range [st, ed].
            
            # Reverting to the C++ logic structure for fidelity, though its intent is arcane
            lastLeftBound = self.path[st].st
            lastRightBound = self.path[st].ed
            stLeftInclude = (minLeftInclude <= st)
            stRightInclude = (minRightInclude <= st)
            
            temp_st = st
            temp_ed = ed
            
            while temp_ed - temp_st > 1:
                mid = (temp_st + temp_ed) // 2
                tg = self.path[mid]

                if not stLeftInclude:
                    # Check if tg's left boundary is the issue
                    is_clean_smaller = (tg.st == NEG_INF) or game.compare(tg.st, ai)
                    if tg.st != lastLeftBound and is_clean_smaller:
                        # Left boundary is fixed at 'mid' or above
                        pass
                    else:
                        # Left boundary is NOT fixed by mid (or is the same as the start bound)
                        lastLeftBound = tg.st
                        stLeftInclude = False
                        temp_st = mid
                        continue
                
                if not stRightInclude:
                    # Check if tg's right boundary is the issue
                    is_clean_larger = (tg.ed == INF) or game.compare(ai, tg.ed)
                    if tg.ed != lastRightBound and is_clean_larger:
                        # Right boundary is fixed at 'mid' or above
                        pass
                    else:
                        # Right boundary is NOT fixed by mid (or is the same as the start bound)
                        lastRightBound = tg.ed
                        stRightInclude = False
                        lastLeftBound = tg.st
                        stLeftInclude = True
                        temp_st = mid
                        continue
                
                temp_ed = mid
                
            turn_index = min(temp_st + 1, temp_ed)
            turn = self.path[turn_index]

            # Phase 2: Del and Re-insert (if needed)
            if turn.value == ai:
                # Value found at 'turn' node, implies minimal clean compares were needed.
                pass
            else:
                # Clean-order violation found: delete the dirty-inserted node and re-insert
                tree.del_node(p1_copy)
                tree.insert(ai, dirty_comp, clean_comp, turn.value)

        # 3. Final Output
        self.indexes.clear()
        tree.LinearOutput(self.indexes)

        # Convert final sorted values (indexes) to ranks (output_rank)
        return self._index_to_rank(n)

# --- Example Usage (Matching the C++ environment structure) ---
if __name__ == '__main__':
    # Define a set of items (indices) and their true ranking (0 is smallest)
    
    # 5 items: True order is 0, 1, 2, 3, 4
    # The list below indicates the rank of the index: 
    # Item 0 has rank 3
    # Item 1 has rank 1
    # Item 2 has rank 4
    # Item 3 has rank 0
    # Item 4 has rank 2
    # True sorted order: 3, 1, 4, 0, 2
    
    N = 5
    ground_ranking = [3, 1, 4, 0, 2] # index -> rank
    
    # Check if the ranking array is valid (length N and ranks 0 to N-1)
    if len(ground_ranking) != N or sorted(ground_ranking) != list(range(N)):
        print("Error: Invalid ground ranking array.")
    else:
        game = SortGame(N, ground_ranking)
        
        # Instantiate and run the sorting algorithm
        dirty_sorter = DirtyClean4()
        final_ranks = dirty_sorter.sort(game)
        
        # Verify result
        # final_ranks[i] should be the final rank of element i
        # The element with rank 0 should be index 3 (as ground_ranking[3] == 0)
        # The element with rank 1 should be index 1 (as ground_ranking[1] == 1)
        
        # Expected output: the input ground_ranking array itself, since the algorithm
        # is supposed to produce the final, correct rank for each element index.
        
        print(f"Total comparisons made: {game.get_comparison_count()}")
        print(f"Input Ranking (index -> rank): {ground_ranking}")
        print(f"Algorithm Output Ranks: {final_ranks}")
        
        # The result of the algorithm is a final rank array. If sorted, it means the
        # algorithm succeeded in ordering the elements by rank.
        
        success = final_ranks == ground_ranking
        print(f"Sorting Success: {'Yes' if success else 'No'}")
        
        if not success:
            print("\nNote: The success check depends on the SortGame.dirtyCompare implementation.")
            print("Since the true dirty compare is unavailable, this uses a placeholder.")
