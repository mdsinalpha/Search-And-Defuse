# -*- coding: utf-8 -*-

# python imports
import random

# chillin imports
from chillin_client import RealtimeAI

# project imports
from ks.models import (World, Police, Terrorist, Bomb, Position, Constants,
                       ESoundIntensity, ECell, EAgentStatus)
from ks.commands import DefuseBomb, PlantBomb, Move, ECommandDirection

from math import *

from graph import Graph

class AI(RealtimeAI):

    def __init__(self, world):
        super(AI, self).__init__(world)
        self.done = False

    def initialize(self):

        self.DIRECTIONS = [
            ECommandDirection.Up,
            ECommandDirection.Right,
            ECommandDirection.Down,
            ECommandDirection.Left,
        ]

        self.DIR_TO_POS = {
            ECommandDirection.Up:    (+0, -1),
            ECommandDirection.Right: (+1, +0),
            ECommandDirection.Down:  (+0, +1),
            ECommandDirection.Left:  (-1, +0),
        }

        self.POS_TO_DIR = {
            (+0, -1): ECommandDirection.Up,
            (+1, +0): ECommandDirection.Right,
            (+0, +1): ECommandDirection.Down,
            (-1, +0): ECommandDirection.Left
        }

        self.BOMBSITES_ECELL = [
            ECell.SmallBombSite,
            ECell.MediumBombSite,
            ECell.LargeBombSite,
            ECell.VastBombSite,
        ]

        self.ESOUND_INTENSITIES = [
            ESoundIntensity.Strong,
            ESoundIntensity.Normal,
            ESoundIntensity.Weak
        ]

        self.path = {}
        self.de_bombs = {}

        '''self.pos_to_index = {}
        self.index_to_pos = {}
        self.not_wall_cells = 0
        for i in range(self.world.height):
            for j in range(self.world.width):
                if self.world.board[i][j] != ECell.Wall:
                    print(i, j)
                    print("--")
                    self.pos_to_index[(i, j)] = self.not_wall_cells
                    self.index_to_pos[self.not_wall_cells] = (i, j)
                    self.not_wall_cells += 1
        #print(self.not_wall_cells)
        #print("----------")

        self.g = Graph(self.not_wall_cells)
        for i in range(self.world.height):
            for j in range(self.world.width):
                if self.world.board[i][j] == ECell.Empty:
                    if self.world.board[i-1][j] != ECell.Wall:
                        self.g.add_edge(self.pos_to_index[(i, j)], self.pos_to_index[(i-1, j)], 1)
                    if self.world.board[i+1][j] != ECell.Wall:
                        self.g.add_edge(self.pos_to_index[(i, j)], self.pos_to_index[(i+1, j)], 1)
                    if self.world.board[i][j-1] != ECell.Wall:
                        self.g.add_edge(self.pos_to_index[(i, j)], self.pos_to_index[(i, j-1)], 1)
                    if self.world.board[i][j+1] != ECell.Wall:
                        self.g.add_edge(self.pos_to_index[(i, j)], self.pos_to_index[(i, j+1)], 1)                    
        self.g.floyd_warshall()'''
                    
    def decide(self):
        '''Stupid strategy
        my_agents = self.world.polices if self.my_side == 'Police' else self.world.terrorists
        for agent in my_agents:
            if agent.status == EAgentStatus.Dead:
                continue

            doing_bomb_operation = agent.defusion_remaining_time != -1 if self.my_side == 'Police' else agent.planting_remaining_time != -1

            if doing_bomb_operation:
                self._agent_print(agent.id, 'Continue Bomb Operation')
                continue

            bombsite_direction = self._find_bombsite_direction(agent)
            if bombsite_direction == None:
                self._agent_print(agent.id, 'Random Move')
                self.move(agent.id, random.choice(self._empty_directions(agent.position)))
            else:
                self._agent_print(agent.id, 'Start Bomb Operation')
                if self.my_side == 'Police':
                    self.defuse(agent.id, bombsite_direction)
                else:
                    self.plant(agent.id, bombsite_direction)'''
        
        my_agents = self.world.polices if self.my_side == 'Police' else self.world.terrorists

        if self.my_side == 'Police':
            for agent in my_agents:
                # First Police Strategy 
                # When a police is defusing a bomb, we let him complete his operation:)
                if agent.defusion_remaining_time != -1:
                    continue
                # Second Police Strategy
                if self.path[agent]:
                    if self.de_bombs[agent].agent_id != -1:
                        self.path[agent].clear()
                        self.de_bombs[agent] = None
                    else:
                    # Walk to bomb or defuse it  
                        if len(self.path[agent]) > 1:
                            self.move(agent.id, self.POS_TO_DIR[self._sub_pos(Position(self.path[agent][0][0], self.path[agent][0][1]), agent.position)])
                        else:
                            self.defuse(agent.id, self.POS_TO_DIR[self._sub_pos(bomb.position, agent.position)])
                        self.path[agent].pop(0) 
                # Third Police Strategy
                elif self.world.bomb:
                    for bomb in self.world.bomb:
                        if bomb.agent_id != -1:
                            continue
                        distance = _distance(agent.position, bomb.position)
                        if distance <= self.world.constants.police_vision_distance:
                            # Checking wether bomb is going to explode when police arrives
                            g = Graph(self.world, (agent.position.x, agent.position.y))
                            self.path[agent] = g.bfs((bomb.position.x, bomb.position.y))
                            self.de_bombs[agent] = bomb
                            if (len(self.path[agent]) - 1) * 0.5 + self.world.constants.bomb_defusion_time <= bomb.explosion_remaining_time:
                                # Walk to bomb or defuse it    
                                if len(self.path[agent]) > 1:
                                    self.move(agent.id, self.POS_TO_DIR[self._sub_pos(Position(self.path[agent][0][0], self.path[agent][0][1]), agent.position)])
                                else:
                                    self.defuse(agent.id, self.POS_TO_DIR[self._sub_pos(bomb.position, agent.position)])
                                self.path[agent].pop(0)
                            else:
                                self.path[agent].clear()
                                self.de_bombs[agent] = None
                                # TODO add to blacklist
        else:
            # Terrorist know about a police position when police is near
            pass
        # print(self.world.constants.bomb_defusion_time)self.queue.append(t)
                self.pre[t] = self.queue[0] 
        

    def plant(self, agent_id, bombsite_direction):
        self.send_command(PlantBomb(id=agent_id, direction=bombsite_direction))


    def defuse(self, agent_id, bombsite_direction):
        self.send_command(DefuseBomb(id=agent_id, direction=bombsite_direction))


    def move(self, agent_id, move_direction):
        self.send_command(Move(id=agent_id, direction=move_direction))


    def _empty_directions(self, position):
        empty_directions = []

        for direction in self.DIRECTIONS:
            pos = self._sum_pos_tuples((position.x, position.y), self.DIR_TO_POS[direction])
            if self.world.board[pos[1]][pos[0]] == ECell.Empty:
                empty_directions.append(direction)
        return empty_directions


    def _find_bombsite_direction(self, agent):
        for direction in self.DIRECTIONS:
            pos = self._sum_pos_tuples((agent.position.x, agent.position.y), self.DIR_TO_POS[direction])
            if self.world.board[pos[1]][pos[0]] in self.BOMBSITES_ECELL:
                has_bomb = self._has_bomb(pos)
                if (self.my_side == 'Police' and has_bomb) or (self.my_side == 'Terrorist' and not has_bomb):
                    return direction
        return None


    def _has_bomb(self, position):
        for bomb in self.world.bombs:
            if position[0] == bomb.position.x and position[1] == bomb.position.y:
                return True
        return False


    def _sum_pos_tuples(self, t1, t2):
        return (t1[0] + t2[0], t1[1] + t2[1])


    def _agent_print(self, agent_id, text):
        print('Agent[{}]: {}'.format(agent_id, text))

    def _sub_pos(self, t1:Position, t2:Position):
        return (t1.x - t2.x, t1.y - t2.y)

    def _index(self, x:int, y:int):
        return x * self.world.height + y

    def _pos(self, index:int):
        return Position(index // self.world.height, index % self.world.height)

    def _distance(self, first:Position, second:Position):
        return abs(first.x - second.x) + abs(first.y - second.y)

    def _sounds_a_good_way(self, bomb_sounds_before:list, bomb_sounds_after:list):
        for intensity in self.ESOUND_INTENSITIES:
            before_count = bomb_sounds_before.count(intensity)
            after_count = bomb_sounds_after.count(intensity)
            if before_count != 0 or after_count != 0:
                return before_count <= after_count
        return False
        
        

