from ks.models import (World, ECell, ESoundIntensity)

class Sound:

    def __init__(self, world:World, bomb_sites:list):
        self.world = world
        self.sound_board = [[[] for j in range(world.width)] for i in range(world.height)]
        self.bomb_sites = bomb_sites
        self.X, self.Y, self.Z = tuple(world.constants.sound_ranges.values())     
    
    def fill(self):
        for bombsite in self.bomb_sites:
            # Extracting each bombsite's sounds:
            self._bfs(bombsite)
        for i in range(self.world.height):
            for j in range(self.world.width):
                l, new = self.sound_board[i][j], []
                for sound in [ESoundIntensity.Weak, ESoundIntensity.Normal, ESoundIntensity.Strong]:
                    # Duplicate sounds are useless...
                    if  [t[0] for t in l].count(sound) == 1:
                        for item in l:
                            if item[0] == sound:
                                new.append(item)
                self.sound_board[i][j] = new
        return self.sound_board
    
    def _bfs(self, bombsite:tuple):
        queue, visited, cnt = [bombsite], [bombsite], 1
        while queue and cnt <= self.Z:
            frontier = []
            for node in queue:
                x, y = node
                adjacent = [(x-1, y), (x+1, y), (x, y-1), (x, y+1)]
                for t in adjacent:
                    if self.world.board[t[0]][t[1]] != ECell.Wall and t not in visited:
                        if cnt <= self.X:
                            self.sound_board[t[0]][t[1]].append((ESoundIntensity.Strong, bombsite[0], bombsite[1]))
                        elif cnt <= self.Y:
                            self.sound_board[t[0]][t[1]].append((ESoundIntensity.Normal, bombsite[0], bombsite[1]))
                        elif cnt <= self.Z:
                            self.sound_board[t[0]][t[1]].append((ESoundIntensity.Weak, bombsite[0], bombsite[1]))
                        visited.append(t)
                        frontier.append(t)
            queue = frontier
            cnt += 1
