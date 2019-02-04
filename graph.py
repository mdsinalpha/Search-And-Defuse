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

    def __init__(self, world:World, source:tuple):
        self.world = world
        self.source = source
        self.queue = [source]
        self.pre = {}
    
    def bfs(destination:tuple):
        while self.queue[0] != destination:
            x, y = self.queue[0]
            if(self.world.board[x-1][y] != ECell.Wall)
                t = (x-1, y)
                if t not in self.pre:
                    self.queue.append(t)
                    self.pre[t] = self.queue[0]
            if(self.world.board[x+1][y] != ECell.Wall)
                t = (x+1, y)
                if t not in self.pre:
                    self.queue.append(t)
                    self.pre[t] = self.queue[0]
            if(self.world.board[x][y-1] != ECell.Wall)
                t = (x, y-1)
                if t not in self.pre:
                    self.queue.append(t)
                    self.pre[t] = self.queue[0]
            if(self.world.board[x][y+1] != ECell.Wall)
                t = (x, y+1)
                if t not in self.pre:
                    self.queue.append(t)
                    self.pre[t] = self.queue[0]   
            self.queue.pop(0)
        path = []
        it = self.queue[0]
        while it != source:
            path.append(it)
            it = self.pre[it]
        path.reverse()
        return path
