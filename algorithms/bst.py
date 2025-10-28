# This file contains the general-purpose Binary Search Tree data structure.

class Node:
    def __init__(self, value):
        self.value = value
        self.left = None
        self.right = None
        self.parent = None #for walking up the tree

class BinarySearchTree:
    def __init__(self):
        self.root = None

    def insert_from_node(self, value, start_node, game):
        if not start_node:
            if not self.root:
                self.root = Node(value)
                return self.root
            else:
                return self.insert_from_node(value, self.root, game)

        curr = start_node
        while curr:
            if game.compare(value, curr.value):
                if curr.left is None:
                    curr.left = Node(value)
                    curr.left.parent = curr
                    return curr.left
                curr = curr.left
            else:
                if curr.right is None:
                    curr.right = Node(value)
                    curr.right.parent = curr
                    return curr.right
                curr = curr.right
        return None

    def get_inorder_traversal(self): #Returns a list of values in sorted order
        result = []
        self._inorder_helper(self.root, result)
        return result

    def _inorder_helper(self, node, result):
        if node:
            self._inorder_helper(node.left, result)
            result.append(node.value)
            self._inorder_helper(node.right, result)