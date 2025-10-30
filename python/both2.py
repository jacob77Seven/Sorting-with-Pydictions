import random
from sgtree import SGTree, Node

# Game class for handling comparisons and tracking stats
class SortGame:
    
    def __init__(self, data, predictions, ranking):
        self.data = data
        self.predictions = predictions
        self.ranking = ranking
        self.comparison_count = 0
    
    def getSize(self):
        return len(self.data)
    
    def getPredictions(self):
        return self.predictions.copy()
    
    def compare(self, i, j):
        assert i != j, f"Cannot compare element {i} with itself"
        self.comparison_count += 1  # track how many comparisons we make
        return self.ranking[i] < self.ranking[j]
    
    def get_comparison_count(self):
        return self.comparison_count

# Extended scapegoat tree with additional search functions
class ExtendedSGTree(SGTree):
    
    def __init__(self):
        super().__init__()
    
    def getSize(self, node):
        if node is None:
            return 0
        return 1 + self.getSize(node.left) + self.getSize(node.right)
    
    # 1-indexed
    def find_kth_smallest(self, node, k):
        if node is None:
            return None
        
        left_size = self.getSize(node.left)
        if left_size == k - 1:
            return node
        if left_size >= k:
            return self.find_kth_smallest(node.left, k)
        return self.find_kth_smallest(node.right, k - left_size - 1)
    
    # 1-indexed
    def find_kth_largest(self, node, k):
        if node is None:
            return None
        
        right_size = self.getSize(node.right)
        if right_size == k - 1:
            return node
        if right_size >= k:
            return self.find_kth_largest(node.right, k)
        return self.find_kth_largest(node.left, k - right_size - 1)
    
    def find_largest_small(self, node, value, comp):
        if node is None:
            return None
        
        if comp(node.value, value):
            res = self.find_largest_small(node.right, value, comp)
            if res:
                return res
            return node
        
        return self.find_largest_small(node.left, value, comp)
    
    def find_smallest_large(self, node, value, comp):
        if node is None:
            return None
        
        if comp(value, node.value):
            res = self.find_smallest_large(node.left, value, comp)
            if res:
                return res
            return node
        
        return self.find_smallest_large(node.right, value, comp)
    
    def compare_nodes(self, node_a, node_b):
        if node_a is None or node_b is None:
            return False
        return node_a.value < node_b.value
    
    def insert_with_comparators(self, value, dirty, clean, target=-1, game=None):
        if game is not None:
            return self.insert(value, game)
        else:
            new_node = Node(value)
            if self.root is None:
                self.root = new_node
                self.n += 1
                return new_node
            
            current = self.root
            while True:
                if value < current.value:
                    if current.left is None:
                        current.left = new_node
                        new_node.parent = current
                        self.n += 1
                        return new_node
                    current = current.left
                else:
                    if current.right is None:
                        current.right = new_node
                        new_node.parent = current
                        self.n += 1
                        return new_node
                    current = current.right
    
    def LinearOutput(self):
        return self.get_inorder_traversal()


# global vars to keep track of algorithm state
preds = []
uni_preds = []
indexes = []
output_rank = []
inserted = []
p_to_A = []
left_sorted = []
right_sorted = []
combine = []
ai_to_node = []


# make predictions unique by shuffling ties randomly
def new_pred():
    global preds, uni_preds
    
    n = len(preds)
    buckets = [[] for _ in range(n + 1)]  # put elements in buckets by prediction
    uni_preds = [0] * n
    
    for i in range(n):
        bucket_idx = min(preds[i], n)
        buckets[bucket_idx].append(i)
    
    # shuffle within each bucket to break ties
    for bucket in buckets:
        for j in range(len(bucket)):
            swap_idx = random.randint(0, len(bucket) - 1)
            bucket[j], bucket[swap_idx] = bucket[swap_idx], bucket[j]
    
    # assign unique ranks after shuffling
    counter = 0
    for bucket in buckets:
        for element in bucket:
            uni_preds[element] = counter
            counter += 1


class BothAlgo2:
    
    def __init__(self):
        pass
    
    # main sorting algorithm
    def sort(self, game):
        global preds, uni_preds, indexes, output_rank, inserted, p_to_A
        global left_sorted, right_sorted, combine, ai_to_node
        
        n = game.getSize()
        
        # get predictions and setup
        preds = game.getPredictions()
        indexes = list(range(n))
        
        new_pred()  # make predictions unique
        
        # init tracking arrays
        inserted = [0] * n
        p_to_A = [0] * n
        ai_to_node = [None] * n
        
        # map predictions to actual indices
        for i in range(n):
            p_to_A[uni_preds[i]] = i
            inserted[i] = 0
        
        # create the two main trees
        left_sorted_tree = ExtendedSGTree()
        right_sorted_tree = ExtendedSGTree()
        
        inserted_count = 0
        delta = 1  # start with delta = 1, doubles each round
        
        # main algorithm loop - process in rounds with increasing delta
        while delta // 2 <= n and inserted_count < n:
            # temporary trees for this round
            left_bef = ExtendedSGTree()
            right_aft = ExtendedSGTree()
            
            # comparator functions for the trees
            def left_sorted_cmp(a, b):
                return left_sorted_tree.compare_nodes(ai_to_node[a], ai_to_node[b])
            
            def right_sorted_cmp(a, b):
                return right_sorted_tree.compare_nodes(ai_to_node[a], ai_to_node[b])
            
            # forward pass - try to insert into left tree
            for i in range(n):
                A_i = p_to_A[i]
                
                # skip if already inserted
                if inserted[A_i] != 0:
                    if inserted[A_i] > 0:
                        left_bef.insert_with_comparators(A_i, left_sorted_cmp, left_sorted_cmp, -1, game)
                    continue
                
                # find delta-th largest in left_bef
                lowerbound = left_bef.find_kth_largest(left_bef.root, delta)
                
                # insert into left tree if larger than delta-th largest
                if lowerbound is None or game.compare(lowerbound.value, A_i):
                    target = None
                    
                    if lowerbound is None:
                        def left_bef_comp(a, b):
                            return game.compare(a, b)
                        target = left_bef.find_largest_small(left_bef.root, A_i, left_bef_comp)
                    elif delta == 1:
                        target = lowerbound
                    else:
                        def left_bef_comp(a, b):
                            assert b == A_i
                            if ai_to_node[a] and ai_to_node[lowerbound.value]:
                                if left_sorted_tree.compare_nodes(ai_to_node[a], ai_to_node[lowerbound.value]):
                                    return True
                            return game.compare(a, A_i)
                        target = left_bef.find_largest_small(left_bef.root, A_i, left_bef_comp)
                    
                    def left_dirty(a, b):
                        assert a == A_i
                        if target is None or b == target.value:
                            return True
                        if ai_to_node[target.value] and ai_to_node[b]:
                            return left_sorted_tree.compare_nodes(ai_to_node[target.value], ai_to_node[b])
                        return False
                    
                    def left_clean(a, b):
                        return True
                    
                    target_value = -1 if target is None else target.value
                    ai_to_node[A_i] = left_sorted_tree.insert_with_comparators(A_i, left_dirty, left_clean, target_value, game)
                    inserted[A_i] = delta
                    left_bef.insert_with_comparators(A_i, left_sorted_cmp, left_sorted_cmp, -1, game)
                    inserted_count += 1
            
            # backward pass - try to insert into right tree
            for i in range(n - 1, -1, -1):
                A_i = p_to_A[i]
                
                # skip if already inserted  
                if inserted[A_i] != 0:
                    if inserted[A_i] < 0:
                        right_aft.insert_with_comparators(A_i, right_sorted_cmp, right_sorted_cmp, -1, game)
                    continue
                
                # find delta-th smallest in right_aft
                upperbound = right_aft.find_kth_smallest(right_aft.root, delta)
                
                # insert into right tree if smaller than delta-th smallest
                if upperbound is None or game.compare(A_i, upperbound.value):
                    target = None
                    
                    if upperbound is None:
                        def right_aft_comp(a, b):
                            return game.compare(a, b)
                        target = right_aft.find_smallest_large(right_aft.root, A_i, right_aft_comp)
                    else:
                        def right_aft_comp(a, b):
                            assert a == A_i
                            if ai_to_node[upperbound.value] and ai_to_node[b]:
                                if right_sorted_tree.compare_nodes(ai_to_node[upperbound.value], ai_to_node[b]):
                                    return True
                            return game.compare(A_i, b)
                        target = right_aft.find_smallest_large(right_aft.root, A_i, right_aft_comp)
                    
                    def right_dirty(a, b):
                        assert a == A_i
                        if target is None:
                            return False
                        if b == target.value:
                            return False
                        if ai_to_node[target.value] and ai_to_node[b]:
                            return right_sorted_tree.compare_nodes(ai_to_node[target.value], ai_to_node[b])
                        return False
                    
                    def right_clean(a, b):
                        return False
                    
                    target_value = -1 if target is None else target.value
                    ai_to_node[A_i] = right_sorted_tree.insert_with_comparators(A_i, right_dirty, right_clean, target_value, game)
                    inserted[A_i] = -delta
                    right_aft.insert_with_comparators(A_i, right_sorted_cmp, right_sorted_cmp, -1, game)
                    inserted_count += 1
            
            delta <<= 1  # double delta for next round
        
        # extract sorted sequences from both trees
        left_sorted = left_sorted_tree.LinearOutput()
        right_sorted = right_sorted_tree.LinearOutput()
        
        # merge the two sorted sequences
        combine = []
        lpt = 0
        rpt = 0
        
        # standard merge of two sorted arrays
        while lpt < len(left_sorted) or rpt < len(right_sorted):
            if lpt == len(left_sorted):
                combine.append(right_sorted[rpt])
                rpt += 1
            elif rpt == len(right_sorted):
                combine.append(left_sorted[lpt])
                lpt += 1
            elif game.compare(left_sorted[lpt], right_sorted[rpt]):
                combine.append(left_sorted[lpt])
                lpt += 1
            else:
                combine.append(right_sorted[rpt])
                rpt += 1
        
        # convert back to ranking format
        output_rank = [0] * len(indexes)
        for i in range(len(indexes)):
            output_rank[combine[i]] = i
        
        return output_rank