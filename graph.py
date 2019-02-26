from ks.models import (World, ECell)

class Graph:

    def __init__(self, world:World, source:tuple, black_pos:list=[]):
        self.world = world
        self.source = source
        self.black_pos = black_pos
        self.queue = [source]
        self.pre = {source:None}
    
    def bfs(self, destination:tuple, pop_destination=True):
        while self.queue and self.queue[0] != destination:
            x, y = self.queue[0]
            adjacent = [(x-1, y), (x+1, y), (x, y-1), (x, y+1)]
            for t in adjacent:
                if self.promising(t, destination):
                    self.queue.append(t)
                    self.pre[t] = self.queue[0]   
            self.queue.pop(0)
        if self.queue:
            # Empty path means source and destination are adjacent!
            path = []
            it = self.queue[0]
            while it != self.source:
                path.append(it)
                it = self.pre[it]
            if pop_destination:
                path.pop(0)
            path.reverse()
            return path
        else:
            # None means there is no path to destination.
            return None
    
    def promising(self, t:tuple, destination:tuple):
        return (self.world.board[t[0]][t[1]] == ECell.Empty or t == destination) and t not in self.black_pos and t not in self.pre
        
