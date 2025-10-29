import math

class Node:
    def __init__(self, value=0):
        self.left = None
        self.right = None
        self.parent = None
        self.value = value

class SGTree:
    def __init__(self):
        self.root = None
        self.n = 0
        self.alpha = 2/3 #the c++ implementation doesn't use this so we can use a common value

    def size(self, node):
        if node is None:
            return 0
        return 1 + self.size(node.left) + self.size(node.right)

    def insert(self, value, game):
        new_node = Node(value)
        depth = self._bst_insert(new_node)
        
        if depth == -1: #Value already exists
            #we assume no duplicates.A real implementation would need to find and return the existing node.
            return None 

        #logarithmic depth check for scapegoat condition
        h_alpha = math.log(self.n, 1/self.alpha) if self.n > 1 else 1

        if depth > h_alpha:
            #Find the scapegoat by walking up from the new node
            p = new_node.parent
            while self.size(p) <= self.alpha * self.size(p.parent):
                p = p.parent
            self._rebuild_tree(p.parent)
        
        return new_node

    #allows starting the search from an arbitrary node.
    def insert_from_node(self, value, start_node, game):
        #we first find the insertion point starting from `start_node`.
        if not start_node:
            return self.insert(value, game)

        curr = start_node
        while True:
            if game.compare(value, curr.value):
                if curr.left is None:
                    #perform the insertionwhich also handles rebalancing.
                    return self.insert(value, game)
                curr = curr.left
            else:
                if curr.right is None:
                    return self.insert(value, game)
                curr = curr.right

    def _rebuild_tree(self, u):
        n_size = self.size(u)
        p = u.parent
        
        a = [None] * n_size
        self._store_in_array(u, a, 0)

        if p is None:
            self.root = self._build_balanced_from_array(a, 0, n_size)
            if self.root: self.root.parent = None
        elif p.right == u:
            p.right = self._build_balanced_from_array(a, 0, n_size)
            if p.right: p.right.parent = p
        else:
            p.left = self._build_balanced_from_array(a, 0, n_size)
            if p.left: p.left.parent = p

    def _store_in_array(self, u, a, i):
        if u is None:
            return i
        i = self._store_in_array(u.left, a, i)
        a[i] = u
        i += 1
        return self._store_in_array(u.right, a, i)

    def _build_balanced_from_array(self, a, i, n):
        if n == 0:
            return None
        m = n // 2
        
        # The node itself is at a[i+m]
        node = a[i+m]
        node.left = self._build_balanced_from_array(a, i, m)
        if node.left:
            node.left.parent = node
            
        node.right = self._build_balanced_from_array(a, i + m + 1, n - m - 1)
        if node.right:
            node.right.parent = node
            
        return node
    
    #handles the raw BST insertion and returns depth.
    def _bst_insert(self, u):
        w = self.root
        if w is None:
            self.root = u
            self.n += 1
            return 0
            
        d = 0
        while True:
            if u.value < w.value:
                if w.left is None:
                    w.left = u
                    u.parent = w
                    break
                w = w.left
            elif u.value > w.value:
                if w.right is None:
                    w.right = u
                    u.parent = w
                    break
                w = w.right
            else:
                return -1 # Duplicate
            d += 1
            
        self.n += 1
        return d

    def get_inorder_traversal(self):
        result = []
        def _inorder_helper(node):
            if node:
                _inorder_helper(node.left)
                result.append(node.value)
                _inorder_helper(node.right)
        _inorder_helper(self.root)
        return result