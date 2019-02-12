# -*- coding: utf-8 -*-

# python imports
import random
from math import *

# chillin imports
from chillin_client import RealtimeAI

# project imports
from ks.models import (World, Police, Terrorist, Bomb, Position, Constants,
                       ESoundIntensity, ECell, EAgentStatus)
from ks.commands import DefuseBomb, PlantBomb, Move, ECommandDirection

# my imports
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

        if self.my_side == "Police":
            # Path to be followed for defusing a bomb:
            self.path = {}
            self.de_bombs = {}

            # Sorting all bomb site places:
            self.bomb_sites = []
            for i in range(self.world.height):
                for j in range(self.world.width):
                    if self.world.board[i][j] in self.BOMBSITES_ECELL:
                        self.bomb_sites.append((i ** 2 + j ** 2, i, j))
            self.bomb_sites.sort()

            print("All map bomb sites:")
            print(self.bomb_sites)

            # Allocating bomb sites to polices:
            self.police_bomb_sites = {}
            n, m = len(self.bomb_sites), len(self.world.polices)
            index, len_ = 0, ceil(n / m)
            for police_index in range(len(self.world.polices)-2):
                self.police_bomb_sites[self.world.polices[police_index].id] = self.bomb_sites[index: index+len_]
                index += len_
            remaining = self.bomb_sites[index:]
            self.police_bomb_sites[self.world.polices[len(self.world.polices)-2].id] = remaining[:len(remaining)//2]
            self.police_bomb_sites[self.world.polices[len(self.world.polices)-1].id] = remaining[len(remaining)//2:]        

            print("Map bomb site to polices allocation:")
            print(self.police_bomb_sites)

            # Path to be followed for circulating between bomb sites:
            self.path2 = {}
            self.current_bomb_sound_list = {}

            self.police_strategies = [
                self.first_police_strategy,
                self.second_police_strategy,
                self.third_police_strategy,
                self.fourth_police_strategy,
                self.fifth_police_strategy
            ]

            '''# Test graph bfs:
            print("* ---------- ---------- ---------- *")
            g = Graph(self.world, (10, 17))
            print(g.bfs((2, 21)))
            print("* ---------- ---------- ---------- *")'''

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
        
        for agent in my_agents:
            if agent.status is EAgentStatus.Dead:
                continue
            print("Agent %d position (%d, %d)" %(agent.id, agent.position.y, agent.position.x))
            if self.my_side == 'Police':
                for strategy in self.police_strategies:
                    if strategy(agent):
                        break
            else:
                # Terrorist know about a police position when police is near
                pass

    def plant(self, agent_id, bombsite_direction):
        self.send_command(PlantBomb(id=agent_id, direction=bombsite_direction))


    def defuse(self, agent_id, bombsite_direction):
        self.send_command(DefuseBomb(id=agent_id, direction=bombsite_direction))


    def move(self, agent_id, move_direction):
        self.send_command(Move(id=agent_id, direction=move_direction))

    
    def first_police_strategy(self, agent:Police):
        # When a police is defusing a bomb, we let him complete his operation:)
        return agent.defusion_remaining_time != -1
    
    def second_police_strategy(self, agent:Police):
        if agent.id in self.path and self.path[agent.id]:
            if self.de_bombs[agent.id].agent_id != -1:
                self.path[agent.id].clear()
                self.de_bombs[agent.id] = None
            else:
                # Walk to bomb or defuse it  
                if len(self.path[agent.id]) > 1:
                    try:
                        self.move(agent.id, self.POS_TO_DIR[self._sub_pos(Position(self.path[agent.id][0][1], self.path[agent.id][0][0]), agent.position)])
                    except KeyError as e:
                        self.path[agent.id].clear()
                        self.de_bombs[agent.id] = None
                        return False
                else:
                    self.defuse(agent.id, self.POS_TO_DIR[self._sub_pos(self.de_bombs[agent.id].position, agent.position)])
                self.path[agent.id].pop(0)
                return True 
        return False

    def third_police_strategy(self, agent:Police):
        if self.world.bombs:
            for bomb in self.world.bombs:
                if bomb.agent_id != -1:
                    continue
                distance = self._distance(agent.position, bomb.position)
                if distance <= self.world.constants.police_vision_distance:
                    # Checking wether bomb is going to explode when police arrives
                    g = Graph(self.world, (agent.position.y, agent.position.x), self._calculate_black_pos())
                    self.path[agent.id] = g.bfs((bomb.position.y, bomb.position.x))
                    self.de_bombs[agent.id] = bomb
                    if self.path[agent.id] and ((len(self.path[agent.id]) - 1) * 0.5 + self.world.constants.bomb_defusion_time <= bomb.explosion_remaining_time):
                        # Walk to bomb or defuse it    
                        if len(self.path[agent.id]) > 1:
                            self.move(agent.id, self.POS_TO_DIR[self._sub_pos(Position(self.path[agent.id][0][1], self.path[agent.id][0][0]), agent.position)])
                        else:
                            self.defuse(agent.id, self.POS_TO_DIR[self._sub_pos(bomb.position, agent.position)])
                        self.path[agent.id].pop(0)
                        self.path2[agent.id].clear()
                        return True
                    else:
                        self.path[agent.id].clear()
                        self.de_bombs[agent.id] = None
                        # TODO add to blacklist
        return False

    def fourth_police_strategy(self, agent:Police):
        # Let's continue the path2:
        if agent.id in self.path2 and self.path2[agent.id]:
            if agent.id in self.current_bomb_sound_list:
                print("Agent %d is hearing: " %(agent.id), end='')
                print(self.current_bomb_sound_list[agent.id], " --> ", agent.bomb_sounds)
            if self._sounds_a_good_way(self.current_bomb_sound_list[agent.id], agent.bomb_sounds):
                self.current_bomb_sound_list[agent.id] = agent.bomb_sounds
                print("Agent %d is moving to (%d, %d)" %(agent.id, self.path2[agent.id][0][1], self.path2[agent.id][0][0]))
                try:
                    self.move(agent.id, self.POS_TO_DIR[self._sub_pos(Position(self.path2[agent.id][0][1], self.path2[agent.id][0][0]), agent.position)])
                    self.path2[agent.id].pop(0)
                    return True
                except KeyError as e:
                    self.path2[agent.id].clear()
        return False
        
    def fifth_police_strategy(self, agent:Police):
        # Let's find a path from agent's position to one of its bomb sites:
        print("Changing agent %d bomb site: (%d, %d) --> " %(agent.id ,self.police_bomb_sites[agent.id][0][1], self.police_bomb_sites[agent.id][0][2]), end='')
        self.police_bomb_sites[agent.id].append(self.police_bomb_sites[agent.id].pop(0))
        print("(%d, %d)" %(self.police_bomb_sites[agent.id][0][1], self.police_bomb_sites[agent.id][0][2]))
        self.current_bomb_sound_list[agent.id] = agent.bomb_sounds
        g = Graph(self.world, (agent.position.y, agent.position.x), self._calculate_black_pos())
        dest = self.police_bomb_sites[agent.id][0]
        print("Source : ", agent.position.y, agent.position.x)
        print("Destination : ", dest[1], dest[2])
        self.path2[agent.id] = g.bfs((dest[1], dest[2]))
        print(self.path2[agent.id])
        print("----------")
        if self.path2[agent.id]:
            self.move(agent.id, self.POS_TO_DIR[self._sub_pos(Position(self.path2[agent.id][0][1], self.path2[agent.id][0][0]), agent.position)])
            self.path2[agent.id].pop(0)
            return True
        return False
    
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
        if len(bomb_sounds_before) == 0 and len(bomb_sounds_after) == 0:
            return True
        for intensity in self.ESOUND_INTENSITIES:
            before_count = bomb_sounds_before.count(intensity)
            after_count = bomb_sounds_after.count(intensity)
            if before_count != 0 or after_count != 0:
                return before_count <= after_count
        return False
    
    def _calculate_black_pos(self):
        black_pos = []
        my_agents = self.world.polices if self.my_side == 'Police' else self.world.terrorists
        for agent in my_agents:
            if agent.status is not EAgentStatus.Dead:
                black_pos.append((agent.position.y, agent.position.x))
        return black_pos

        

