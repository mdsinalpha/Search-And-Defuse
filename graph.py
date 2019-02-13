'''class Graph:

    def __init__(self, v:int):
        self.v = v
        self.floyd = [[float("inf") for j in range(v)] for i in range(v)]
        self.pre = [[-1 for j in range(self.v)] for i in range(self.v)]

    def add_edge(self, findex:int, sindex:int, value):
        self.floyd[findex][sindex] = value
    
    def floyd_warshall(self):
        for k in range(self.v):
            for i in range(self.v):
                for j in range(self.v):
                    if(self.floyd[i][k]+self.floyd[k][j]<self.floyd[i][j]):
                        self.floyd[i][j] = self.floyd[i][k] + self.floyd[k][j]
                        self.pre[i][j] = k
        #print(self.v)
        #print(self.floyd)
        #print("----------")
        #print(self.pre)
        #print("----------")
    
    def sp(self, findex:int, sindex:int):
        return self.floyd[findex][sindex]
    
    def path(self, findex:int, sindex:int):
        self.path_list = []
        self._path(findex, sindex)
        return self.path_list

    def _path(self, findex:int, sindex:int):
        k = self.pre[findex][sindex]
        if k != -1:
            self._path(findex, k)
            self.path_list.append(k)
            self._path(k, sindex)
'''

from ks.models import (World, ECell)

class Graph:

    def __init__(self, world:World, source:tuple, black_pos:list=[]):
        self.world = world
        self.source = source
        self.black_pos = black_pos
        self.queue = [source]
        self.pre = {source:None}
    
    def bfs(self, destination:tuple):
        while self.queue and self.queue[0] != destination:
            x, y = self.queue[0]
            adjacent = [(x-1, y), (x+1, y), (x, y-1), (x, y+1)]
            for t in adjacent:
                if self.promising(t, destination):
                    self.queue.append(t)
                    self.pre[t] = self.queue[0]   
            self.queue.pop(0)
        # Empty path means there is no way to destination or source and destination are adjacent!
        path = []
        if self.queue:
            it = self.queue[0]
            while it != self.source:
                path.append(it)
                it = self.pre[it]
            path.pop(0)
        path.reverse()
        return path
    
    def promising(self, t:tuple, destination:tuple):
        return (self.world.board[t[0]][t[1]] == ECell.Empty or t == destination) and t not in self.black_pos and t not in self.pre
        
