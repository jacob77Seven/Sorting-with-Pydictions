"""
    Implements Algorithm 2 (from LIS.cpp) using a Binary Search Tree.

    This version processes items in their predicted rank order and inserts them
    into a BST. A "finger" (a direct reference to the last inserted node) is
    used to find an efficient starting point for the next insertion by
    traversing up the tree to a suitable ancestor.

    Args:
        game: An object from C++ with methods:
              - getSize()
              - getPredictions()
              - compare(item_a_idx, item_b_idx)

    Returns:
        A list of integers representing the final sorted ranks.
    """

from bst import BinarySearchTree

def displacement_sort_bst(game):
    #trivial case
    n = game.getSize()
    if n == 0:
        return []

    #sorts the indices according to their predicted scores for making subsequent insertions faster
    predictions = game.getPredictions()
    items_to_process = sorted(range(n), key=lambda item_idx: predictions[item_idx])

    #alternative: use a BST with finger search (instead of scapegoat tree)
    tree = BinarySearchTree() 
    finger_node = None

    def is_in_range(item_idx, node, game):
        ancestor = node
        lower_bound = float('-inf')
        upper_bound = float('inf')
        while ancestor.parent:
            if ancestor == ancestor.parent.right:
                lower_bound = max(lower_bound, ancestor.parent.value)
            else:
                upper_bound = min(upper_bound, ancestor.parent.value)
            ancestor = ancestor.parent
        is_above_lower = (lower_bound == float('-inf')) or game.compare(lower_bound, item_idx)
        is_below_upper = (upper_bound == float('inf')) or game.compare(item_idx, upper_bound)
        return is_above_lower and is_below_upper

    #Insertion with finger search
    for item_to_insert in items_to_process:
        if finger_node is None:
            finger_node = tree.insert_from_node(item_to_insert, tree.root, game)
            continue
        #if the element doesn’t fit within bounds, climb up until it does
        start_node = finger_node
        while not is_in_range(item_to_insert, start_node, game):
            if start_node.parent is None:
                start_node = tree.root
                break
            start_node = start_node.parent
        
        finger_node = tree.insert_from_node(item_to_insert, start_node, game)

    #final result generation
    sorted_indices = tree.get_inorder_traversal()
    
    output_rank = [0] * n
    for rank, original_idx in enumerate(sorted_indices):
        output_rank[original_idx] = rank
    
    return output_rank