# This class stores the logic for searching through a chain

import bpy

class UnionFindList: # a combination of unionfind and singlelinkedlist
    def __init__(self, n):
        self.parent = [ i for i in range(n) ]
        self.next = [ -1 for _ in range(n) ]
        self.rank = [ 1 for _ in range(n) ]
    def findRoots(self):
        return [ i for i, v in enumerate(self.parent) if i == v and self.rank[i] != 1 ] # ignore single point
    def findRoot(self, x):
        if self.parent[x] == x:
            return x
        self.parent[x] = self.findRoot(self.parent[x])
        return self.parent[x]
    def getNext(self, x): # return -1 if no next
        return self.next[x]
    def getChainLength(self, x): # x must be the root
        return self.rank[x]
    def getChain(self, x):
        ret = []
        x_next = x
        while x_next != -1:
            ret.append(x_next)
            x_next = self.next[x_next]
        return ret
    def reverseChain(self, x_root, x): # x_root is the head of list, x is the end of list
        if self.rank[x_root] == 1: return
        x_pre = -1
        x_cur = x_root
        while x_cur != -1:
            x_next = self.next[x_cur]
            self.next[x_cur] = x_pre
            self.parent[x_cur] = x # parent of all nodes should be x after reversing
            x_pre = x_cur
            x_cur = x_next
        self.rank[x] = self.rank[x_root]
    def union(self, x, y):
        x_root = self.findRoot(x)
        y_root = self.findRoot(y)
        if x_root == y_root: # already connected
            return
            
        if y_root != y and x_root != x: 
            # Case 1: two root points are independent, should reverse one of chains, choose shorter chain to reverse
            # and transform this situation to Case 2
            if self.rank[x_root] <= self.rank[y_root]:
                self.reverseChain(x_root, x)
                x_root = x
            else:
                self.reverseChain(y_root, y)
                y_root = y
                
        if y_root == y: # Case 2: one of two points is dependent or all two points are dependent
            if self.next[x] != -1:
                self.parent[x] = y
                self.next[y] = x
                self.rank[y] = self.rank[y] + self.rank[x] # y become new root
            else:
                self.parent[y] = x_root
                self.next[x] = y
                self.rank[x_root] = self.rank[x_root] + self.rank[y]
        elif x_root == x:
            if self.next[y] != -1:
                self.parent[y] = x 
                self.next[x] = y 
                self.rank[x] = self.rank[x] + self.rank[y] # x become new root
            else:
                self.parent[x] = y_root
                self.next[y] = x
                self.rank[y_root] = self.rank[y_root] + self.rank[x]
                