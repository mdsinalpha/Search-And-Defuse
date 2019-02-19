from ks.models import (World, ECell, ESoundIntensity)

class Sound:

    def __init__(self, world:World, bomb_sites:list):
        self.world = world
        self.sound_board = [[[] for j in range(world.width)] for i in range(world.height)]
        self.bomb_sites = bomb_sites
        self.X, self.Y, self.Z = tuple(world.constants.sound_ranges.values())
        # print(self.X)
        # print(self.Y)
        # print(self.Z)
        
    
    def fill(self):
        for bombsite in self.bomb_sites:
            self._bfs(bombsite)
        return self.sound_board
    
    def _bfs(self, bombsite:tuple):
        queue, visited, cnt = [bombsite], [bombsite], 1
        while queue and cnt <= self.Z:
            frontier = []
            for node in queue:
                x, y = node
                adjacent = [(x-1, y), (x+1, y), (x, y-1), (x, y+1)]
                for t in adjacent:
                    if t[0]>=0 and t[0]<self.world.height and t[1]>=0 and t[1]<self.world.width and t not in visited:
                        if cnt <= self.X:
                            self.sound_board[t[0]][t[1]].append((ESoundIntensity.Strong, t[0], t[1]))
                        elif cnt <= self.Y:
                            self.sound_board[t[0]][t[1]].append((ESoundIntensity.Normal, t[0], t[1]))
                        elif cnt <= self.Z:
                            self.sound_board[t[0]][t[1]].append((ESoundIntensity.Weak, t[0], t[1]))
                        visited.append(t)
                        frontier.append(t)
            queue = frontier
            cnt += 1
