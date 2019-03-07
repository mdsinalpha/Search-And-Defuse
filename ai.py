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
from sound import Sound

class AI(RealtimeAI):

    def __init__(self, world):
        super(AI, self).__init__(world)
        self.done = False

    DEBUG = True

    @staticmethod
    def print(values, end='\n'):
        if AI.DEBUG:
            print(values, end=end)

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

            self.police_status = {}
            for police in self.world.polices:
                self.police_status[police.id] = police.status

            # Path to be followed for defusing a bomb:
            self.path = {}
            self.police_bomb_site = {}
            self.police_defusing_site = {}

            self.update_bombsites()

            # Path to be followed by hearing an specific bomb sound:
            self.path2 = {}

            # Path to be followed for circulating between bomb sites:
            self.path3 = {}
            self.current_bomb_sound_list = {}

            self.police_strategies = [
                self.first_police_strategy,
                self.second_police_strategy,
                self.third_police_strategy,
                self.fourth_police_strategy,
                self.fifth_police_strategy,
                self.sixth_police_strategy,
                self.seventh_police_strategy
            ]
        
        else:

            # Path to be followed for planting a bomb:
            self.path = {}
            self.terrorist_bomb_site = {}

            # Making free bombsites list:
            self.free_bomb_sites = []
            for i in range(self.world.height):
                for j in range(self.world.width):
                    if self.world.board[i][j] in self.BOMBSITES_ECELL:
                        self.free_bomb_sites.append((i, j))
            
            self.print("All map bomb sites:")
            self.print(self.free_bomb_sites)

            # Waiting counter to confuse polices after escape:
            self.waiting_counter = [0 for i in range(len(self.world.terrorists))]

            # Strong sounds counter:
            self.strong_sounds = [0 for i in range(len(self.world.terrorists))]

            self.terrorist_strategies = [
                self.first_terrorist_strategy,
                self.second_terrorist_strategy,
                self.third_terrorist_strategy,
                self.fourth_terrorist_strategy,
                self.fifth_terrorist_strategy
            ]

    def update_bombsites(self):

        self.visited_cells = {}
        for police in self.world.polices:
            if police.status == EAgentStatus.Alive:
                self._bfs((police.position.y, police.position.x))
                break

        # Sorting all bomb site places:
        self.bomb_sites = []
        tmp_bomb_sites = []
        for i in range(self.world.height):
            for j in range(self.world.width):
                if self.world.board[i][j] in self.BOMBSITES_ECELL and self._valid_bombsite((i, j)):
                    self.bomb_sites.append((i+j, i, j))
                    tmp_bomb_sites.append((i+j, i, j))
        self.bomb_sites.sort()
        tmp_bomb_sites.sort()
        
        self.print("All map bomb sites:")
        self.print(self.bomb_sites)

        # Allocating bomb sites to polices:
        self.police_bomb_sites = {}
        P, B = 0, len(tmp_bomb_sites)
        for police in self.world.polices:
            if police.status == EAgentStatus.Alive:
                P += 1
        for police in self.world.polices:
            if police.status == EAgentStatus.Dead:
                continue
            allocation_len = B//P if B%P==0 else B//P +1 if police.id < B%P else B//P
            allocation_list = [tmp_bomb_sites[-1]]
            choice_list = [(self._bdistance(t, allocation_list[0]), t[1], t[2]) for t in tmp_bomb_sites]
            choice_list.sort()
            allocation_list = choice_list[:allocation_len]
            for bombsite in allocation_list:
                tmp_bomb_sites.remove((bombsite[1]+bombsite[2], bombsite[1], bombsite[2]))
            self.police_bomb_sites[police.id] = allocation_list

        self.print("Map bomb site to polices allocation:")
        self.print(self.police_bomb_sites)

        # Sound board to determine what sounds could be heared from an specified cell
        self.sound_board = Sound(self.world, [(site[1], site[2]) for site in self.bomb_sites]).fill()
        self.print("Sound board: ")
        for i in range(self.world.height):
            for j in range(self.world.width):
                l = self.sound_board[i][j]
                a, b, c, v, site_pos = 0, 0, 0, 0, [None, None, None, None]
                for sound in l:
                    if sound[0] == ESoundIntensity.Strong:
                        a += 1
                        site_pos[0] = sound[1], sound[2]
                    elif sound[0] == ESoundIntensity.Normal:
                        b += 1
                        site_pos[1] = sound[1], sound[2]
                    elif sound[0] == ESoundIntensity.Weak:
                        c += 1
                        site_pos[2] = sound[1], sound[2]
                    else:
                        v += 1 
                        site_pos[3] = sound[1], sound[2]
                value, values = a*100+b*10+c, [1, 10, 11, 100, 101, 110, 111]
                self.print(("%03d" %(value) if v == 0 else "VVV") if self.world.board[i][j] == ECell.Empty else "---", end=' ')
            self.print("")


        # Let each police circulate around an area that cell inside the area have all sound types
        self.police_circulating_areas = {}
        for police_id, bombsites in self.police_bomb_sites.items():

            bombsite_areas = {}
            for i in range(self.world.height):
                for j in range(self.world.width):
                    l = self.sound_board[i][j]
                    a, b, c, v, site_pos, v_pos = 0, 0, 0, 0, [None, None, None], []
                    for sound in l:
                        if sound[0] == ESoundIntensity.Strong:
                            a += 1
                            site_pos[0] = sound[1], sound[2]
                        elif sound[0] == ESoundIntensity.Normal:
                            b += 1
                            site_pos[1] = sound[1], sound[2]
                        elif sound[0] == ESoundIntensity.Weak:
                            c += 1
                            site_pos[2] = sound[1], sound[2]
                        else:
                            v += 1
                            v_pos.append((sound[1], sound[2]))
                    # TODO Change!
                    value, values = a*100+b*10+c, [10, 100, 110]
                    site_pos.extend(v_pos)
                    if self.world.board[i][j] == ECell.Empty and (v >= 1 or value in values):
                        for pos in site_pos:
                            if pos and pos in [(t[1], t[2]) for t in self.police_bomb_sites[police_id]]:
                                if pos not in bombsite_areas:
                                    bombsite_areas[pos] = []
                                if (i, j) in self.visited_cells.keys():
                                    bombsite_areas[pos].append((i+j, i, j))
            self.print("Agent %d bombsite areas:" % police_id)
            self.print(bombsite_areas)
           
            selected_areas = []
            for first_site in list(bombsite_areas.values())[0]:
                choice_list = [first_site]
                for other_site in list(bombsite_areas.values())[1:]:
                    choice_list.append(self._nearest(choice_list[-1], other_site))
                if not selected_areas:
                    selected_areas = choice_list
                if self._pathdistance(choice_list) < self._pathdistance(selected_areas):
                    selected_areas = choice_list
            selected_areas = list(set(selected_areas))
            selected_areas.sort()

            self.print("Agent %d selected areas:" % police_id)
            for area in selected_areas:
                self.print("(%d, %d) : %s" %(area[1], area[2], self.sound_board[area[1]][area[2]]))
            self.print("---------- ---------- ----------")
            self.police_circulating_areas[police_id] = selected_areas
            
        self.print("Polices circulating areas:")
        self.print(self.police_circulating_areas)

        self.police_circulate_index = {}
        self.police_circulate_iter = {}
        for police_id, areas in self.police_circulating_areas.items():
            self.police_circulate_index[police_id] = len(areas)-1
            self.police_circulate_iter[police_id] = 1

  
    def decide(self):

        if self.my_side == "Police":
            flag = True
            # Updating bombsites when a bomb explodes!
            for i in range(self.world.height):
                for j in range(self.world.width):
                    if self.world.board[i][j] not in self.BOMBSITES_ECELL and (i+j, i, j) in self.bomb_sites:
                        flag = False
                        self.print("Unfortunately a bomb explosion has detected, restarting polices bombsites and circulating areas allocation.")
                        for index, bomb in self.police_defusing_site.items():
                            if bomb == (i, j):
                                del self.police_defusing_site[index]
                                break
                        for index, bomb in self.police_bomb_site.items():
                            if bomb == (i, j):
                                del self.police_bomb_site[index]
                                if index in self.path:
                                    del self.path[index]
                                break
                        self.update_bombsites()
            # Updating allocation when a police dies :(
            if flag:
                for police in self.world.polices:
                    if police.status != self.police_status[police.id]:
                        self.police_status[police.id] = police.status
                        self.print("Unfortunately we have lost one of our agents :( restarting allocation.")
                        self.update_bombsites()
            

        else:
            # Updating free bomb sites:
            for i in range(self.world.height):
                for j in range(self.world.width):
                    if self.world.board[i][j] in self.BOMBSITES_ECELL and (i, j) not in self.free_bomb_sites and (i, j) not in self.terrorist_bomb_site.values() and not self._has_bomb((i, j)):
                        self.print("Bombsite (%d, %d) freed." %(i, j))
                        self.free_bomb_sites.append((i, j))

        
        my_agents = self.world.polices if self.my_side == 'Police' else self.world.terrorists

        for agent in my_agents:
            if agent.status == EAgentStatus.Dead:
                continue
            self.print("Agent %d position (%d, %d)" %(agent.id, agent.position.y, agent.position.x))
            if self.my_side == 'Police':
                self.print("Agent %d hearing: %s" %(agent.id, agent.bomb_sounds))
                for strategy in self.police_strategies:
                    if strategy(agent):
                        break

            else:
                self.bomb_defuser_pos = None
                if ESoundIntensity.Strong in agent.footstep_sounds:
                    self.strong_sounds[agent.id] += 1
                else:
                    self.strong_sounds[agent.id] = 0
                for strategy in self.terrorist_strategies:
                    if strategy(agent):
                        break
        
    
    def plant(self, agent_id, bombsite_direction):
        strong_sound_const, police_vision = self.world.constants.sound_ranges[ESoundIntensity.Strong], self.world.constants.police_vision_distance
        if self.strong_sounds[agent_id] < strong_sound_const - (police_vision+2):
            self.send_command(PlantBomb(id=agent_id, direction=bombsite_direction))

    def _plant(self, agent_id:int, end_pos:Position, start_pos:Position):
        sub = AI._sub_pos(end_pos, start_pos)
        if sub in self.POS_TO_DIR:
            self.plant(agent_id, self.POS_TO_DIR[sub])
            return True
        return False

    def defuse(self, agent_id, bombsite_direction):
        self.send_command(DefuseBomb(id=agent_id, direction=bombsite_direction))
    
    def _defuse(self, agent_id:int, end_pos:Position, start_pos:Position):
        sub = AI._sub_pos(end_pos, start_pos)
        if sub in self.POS_TO_DIR:
            self.defuse(agent_id, self.POS_TO_DIR[sub])
            return True
        return False

    def move(self, agent_id, move_direction):
        
        self.send_command(Move(id=agent_id, direction=move_direction))
    
    def _move(self, agent_id:int, end_pos:Position, start_pos:Position):
        sub = AI._sub_pos(end_pos, start_pos)
        if sub in self.POS_TO_DIR:
            self.move(agent_id, self.POS_TO_DIR[sub])
            return True
        return False
    
    
    def first_police_strategy(self, agent:Police):
        # When a police is defusing a bomb, we let him complete his operation:)
        return agent.defusion_remaining_time != -1
    
    def second_police_strategy(self, agent:Police):
         # Let's continue the path:
        if agent.id in self.path:
        # Walk to bomb or defuse it    
            if self.path[agent.id]:
                if self._move(agent.id, Position(self.path[agent.id][0][1], self.path[agent.id][0][0]), agent.position):
                    self.path[agent.id].pop(0)
                else:
                    del self.path[agent.id]
                    return False
            else:
                bomb = self.police_bomb_site[agent.id]
                del self.path[agent.id]
                if not self._defuse(agent.id, Position(bomb[1], bomb[0]), agent.position):
                    return False
            return True
        return False

    def third_police_strategy(self, agent:Police):
        # Check each police vision to detect a bomb defusion:
        if self.world.bombs:
            for bomb in self.world.bombs:
                if bomb.defuser_id != -1 or ((bomb.position.y, bomb.position.x) in self.police_defusing_site.values() and (agent.id not in self.police_defusing_site or self.police_defusing_site[agent.id] != (bomb.position.y, bomb.position.x))):
                    continue
                distance = AI._distance(agent.position, bomb.position)
                if distance <= self.world.constants.police_vision_distance:
                    # Checking wether bomb is going to explode when police arrives
                    g = Graph(self.world, (agent.position.y, agent.position.x), self._calculate_black_pos(agent))
                    path = g.bfs((bomb.position.y, bomb.position.x))
                    if path is None:
                        return True
                    if agent.id in self.path2:
                        del self.path2[agent.id] 
                    if agent.id in self.path3:
                        del self.path3[agent.id]
                    self.police_bomb_site[agent.id] = (bomb.position.y, bomb.position.x)
                    self.path[agent.id] = path
                    self.police_defusing_site[agent.id] = (bomb.position.y, bomb.position.x)
                    if len(self.path[agent.id]) * 0.5 + self.world.constants.bomb_defusion_time <= bomb.explosion_remaining_time:
                        # Walk to bomb or defuse it    
                        if self.path[agent.id]:
                            if self._move(agent.id, Position(self.path[agent.id][0][1], self.path[agent.id][0][0]), agent.position):
                                self.path[agent.id].pop(0)
                            else:
                                del self.path[agent.id]
                        else:
                            if self._defuse(agent.id, bomb.position, agent.position):
                                del self.path[agent.id]
                    else:
                        del self.path[agent.id]
                    # Wether police can defuse the bomb or not True can keep the police safe(hold for some cycles) from a path2 leading to the bomb!
                    return True
        return False
    
    def fourth_police_strategy(self, agent:Police):
        # Let's continue the path2:
        if agent.id in self.path2: 
            if self.path2[agent.id]:
                if self._move(agent.id, Position(self.path2[agent.id][0][1], self.path2[agent.id][0][0]), agent.position):
                    self.path2[agent.id].pop(0)
                    return True
                else:
                    del self.path2[agent.id]
            else:
                del self.path2[agent.id]
        return False
    
    def fifth_police_strategy(self, agent:Police):
        # Using an extreme police power, sound board!
        sounds = self.sound_board[agent.position.y][agent.position.x]
        # Collecting exact location of a bombsite for a possible hearing sound from agent's position:
        site_pos, dest = [None, None, None], None
        for sound in sounds:
            if sound[0] == ESoundIntensity.Strong:
                site_pos[0] = sound[1], sound[2]
            elif sound[0] == ESoundIntensity.Normal:
                site_pos[1] = sound[1], sound[2]
            elif sound[0] == ESoundIntensity.Weak:
                site_pos[2] = sound[1], sound[2]
        # Listening to server for a sound with priority of strong, normal and week...
        if site_pos[0] and ESoundIntensity.Strong in agent.bomb_sounds:
            self.print("Strong sound bomb found: (%d, %d)" %(site_pos[0][0], site_pos[0][1]))
            dest = site_pos[0]
        elif site_pos[1] and ESoundIntensity.Normal in agent.bomb_sounds:
            self.print("Normal sound bomb found: (%d, %d)" %(site_pos[1][0], site_pos[1][1]))
            dest = site_pos[1]
        '''
        elif site_pos[2] and ESoundIntensity.Weak in agent.bomb_sounds:
            self.print("Weak sound bomb found: (%d, %d)" %(site_pos[2][0], site_pos[2][1]))
            dest = site_pos[2]
        '''
        # Checking that exact destination of a planted bomb is found!
        if dest is None or dest in self.police_defusing_site.values():
            return False            
        # Let's go and defuseeee :))
        g = Graph(self.world, (agent.position.y, agent.position.x), self._calculate_black_pos(agent))
        path = g.bfs(dest, False)
        if path is None:
                return False
        self.path2[agent.id] = path
        self.police_defusing_site[agent.id] = dest
        if self.path2[agent.id]:
            if self._move(agent.id, Position(self.path2[agent.id][0][1], self.path2[agent.id][0][0]), agent.position):
                self.path2[agent.id].pop(0)
            else:
                del self.path2[agent.id]
                return False
        else:
                del self.path2[agent.id]
                return False
        if agent.id in self.path3:
            del self.path3[agent.id]
        return True
        
    def sixth_police_strategy(self, agent:Police):
        if agent.id in self.police_defusing_site:
            del self.police_defusing_site[agent.id]
        # Let's continue the path3:
        if agent.id in self.path3:
            if not self.path3[agent.id]:
                del self.path3[agent.id]
                return False
            if self._move(agent.id, Position(self.path3[agent.id][0][1], self.path3[agent.id][0][0]), agent.position):
                self.path3[agent.id].pop(0)
                return True
            else:
                del self.path3[agent.id]
        return False
        
    def seventh_police_strategy(self, agent:Police):
        # Let's find a path from agent's position to one of its circulating areas:
        g = Graph(self.world, (agent.position.y, agent.position.x), self._calculate_black_pos(agent))
        _index = self.police_circulate_index[agent.id]
        dest = self.police_circulating_areas[agent.id][_index]
        # Iterating from start to end, then from end to start.
        if _index in [0, len(self.police_circulating_areas[agent.id])-1]:
            self.police_circulate_iter[agent.id] *= -1
        if len(self.police_circulating_areas[agent.id]) > 1:
            self.police_circulate_index[agent.id] += self.police_circulate_iter[agent.id]
        self.print("Source : (%d, %d)" %(agent.position.y, agent.position.x))
        self.print("Destination : (%d, %d)" %(dest[1], dest[2]))
        path = g.bfs((dest[1], dest[2]), False)
        if path is None:
            return False
        self.path3[agent.id] = path
        self.print(self.path3[agent.id])
        if self.path3[agent.id]:
            if self._move(agent.id, Position(self.path3[agent.id][0][1], self.path3[agent.id][0][0]), agent.position):
                self.path3[agent.id].pop(0)
                return True
            else:
                del self.path3[agent.id]
        else:
            del self.path3[agent.id]
        return False

    #  ---------------------------------------------------------------------------------------------------------------------
    
    def first_terrorist_strategy(self, agent:Terrorist):
        # If there's a police near, change direction and run!
        police_positions, police_pos, police = [], None, None
        for polices in self.world.polices:
            if AI._distance(polices.position, agent.position) <= self.world.constants.terrorist_vision_distance:
                police_positions.append(polices.position)
                police = polices
        # Escaping from two or more polices:
        if len(police_positions) > 1:
            escape_directions = self._escape_direction(agent, police_positions[0])[1]
            for police_pos in police_positions[1:]:
                escape_directions = list(set(escape_directions)&set(self._escape_direction(agent, police_pos)[1]))
            selected_direction, directions = None, self._empty_directions(agent)
            for direction in escape_directions:
                if direction in directions:
                    selected_direction = direction
                    break
            if selected_direction:
                if agent.id in self.terrorist_bomb_site:
                    del self.terrorist_bomb_site[agent.id]
                if agent.id in self.path:
                    del self.path[agent.id]
                self.waiting_counter[agent.id] = 1
                self.move(agent.id, selected_direction)
                self.print("Escaping from two or more polices to: ", end='')
                self.print(selected_direction)
                return True
        elif len(police_positions) == 1:
            police_pos = police_positions[0]
            # A police found around, let's make sure that he/she is defusing a bomb or not:
            for bomb in self.world.bombs:
                if bomb.defuser_id == police.id:
                    # Police is defusing a bomb, let's escape from a better way!
                    self.bomb_defuser_pos = (police.position.y, police.position.x)
                    black_pos = self._calculate_black_pos(agent)
                    # Although we are not escaping from a police, we should watch out for defuser police position! 
                    black_pos.append(self.bomb_defuser_pos)
                    g = Graph(self.world, (agent.position.y, agent.position.x), black_pos)
                    dest = self._terrorist_destination(agent, (police_pos.y, police_pos.x))
                    path = g.bfs(dest)
                    if police.defusion_remaining_time and police.defusion_remaining_time < len(path):
                        aim_point = path[police.defusion_remaining_time-1]
                        if self._distance(police.position, Position(aim_point[1], aim_point[0])) > self.world.constants.police_vision_distance:
                            # Escapeeeeeeee.
                            police_pos = None
                            self.terrorist_bomb_site[agent.id] = dest
                            self.path[agent.id] = path
                            break
        '''
        police_pos = None
        for police in self.world.polices:
            if AI._distance(police.position, agent.position) <= self.world.constants.terrorist_vision_distance:
                police_pos = police.position
                '''
        if police_pos:
            selected_direction = self._escape_direction(agent, police_pos)[0]
            if selected_direction:
                if agent.id in self.terrorist_bomb_site:
                    del self.terrorist_bomb_site[agent.id]
                if agent.id in self.path:
                    del self.path[agent.id]
                self.waiting_counter[agent.id] = 1
                self.move(agent.id, selected_direction)
            else:
                # Let's try our chance and speculate where police wants to go after this cycle, then escape!
                stay = False
                for bomb in self.world.bombs:
                    if self._distance(bomb.position, agent.position) <= self.world.constants.terrorist_vision_distance:
                       stay = True
                       break
                if not stay:
                    g = Graph(self.world, (police_pos.y, police_pos.x))
                    police_path = g.bfs((agent.position.y, agent.position.x))
                    self.print("Police speculated path while escaping:")
                    self.print(police_path)
                    if police_path:
                        selected_direction = self._escape_direction(agent, Position(police_path[0][1], police_path[0][0]))[0]
                        if agent.id in self.terrorist_bomb_site:
                            del self.terrorist_bomb_site[agent.id]
                        if agent.id in self.path:
                            del self.path[agent.id]
                        self.waiting_counter[agent.id] = 1
                        self.move(agent.id, selected_direction)
            return True
        return False

    def _escape_direction(self, agent:Terrorist, police_pos:tuple):
        # Escaping from misreable police:
        self.print("Near police detected at (%d, %d)" % (police_pos.y, police_pos.x))
        directions, selected_direction, escape_priority_queue = self._empty_directions(agent), None, []
        delta_x, delta_y = AI._sub_pos(police_pos, agent.position)
        self.print("Escaping with (delta_y=%d, delta_x=%d)..." %(delta_y, delta_x))
        if delta_x == 0:
            if delta_y > 0:
                escape_priority_queue = [ECommandDirection.Up, ECommandDirection.Left, ECommandDirection.Right]
            else:
                escape_priority_queue = [ECommandDirection.Down, ECommandDirection.Right, ECommandDirection.Left]
        elif delta_y == 0:
            if delta_x > 0:
                escape_priority_queue = [ECommandDirection.Left, ECommandDirection.Up, ECommandDirection.Down]
            else:
                escape_priority_queue = [ECommandDirection.Right, ECommandDirection.Down, ECommandDirection.Up]
        else:
            if delta_x > 0 and delta_y > 0:
                if delta_x > delta_y:
                    escape_priority_queue = [ECommandDirection.Left, ECommandDirection.Up]
                else:
                    escape_priority_queue = [ECommandDirection.Up, ECommandDirection.Left]
            elif delta_x > 0 and delta_y < 0:
                if delta_x > -delta_y:
                    escape_priority_queue = [ECommandDirection.Left, ECommandDirection.Down]
                else:
                    escape_priority_queue = [ECommandDirection.Down, ECommandDirection.Left]
            elif delta_x < 0 and delta_y > 0:
                if -delta_x > delta_y:
                    escape_priority_queue = [ECommandDirection.Right, ECommandDirection.Up]
                else:
                    escape_priority_queue = [ECommandDirection.Up, ECommandDirection.Right]
            else:
                if -delta_x > -delta_y:
                    escape_priority_queue = [ECommandDirection.Right, ECommandDirection.Down]
                else:
                    escape_priority_queue = [ECommandDirection.Down, ECommandDirection.Right] 
        for escape_direction in escape_priority_queue:
            if escape_direction in directions:
                selected_direction = escape_direction
                break
        return selected_direction, escape_priority_queue


    def second_terrorist_strategy(self, agent:Terrorist):
        '''
        # Waiting...
        if self.waiting_counter[agent.id]:
            self.waiting_counter[agent.id] -= 1
            return True
        '''
        # When a bomb is exploding around you, avoid it!
        for bomb in self.world.bombs:
            if bomb.explosion_remaining_time == 1:
                dis = self._distance(agent.position, bomb.position)
                if dis == 1:
                    self.move(agent.id, self._empty_directions(agent)[0])
                    return True
                elif dis == 2:
                    return True
        return False

    def third_terrorist_strategy(self, agent:Terrorist):
        if agent.planting_remaining_time != -1:  
            strong_sound_const, police_vision = self.world.constants.sound_ranges[ESoundIntensity.Strong], self.world.constants.police_vision_distance
            if self.strong_sounds[agent.id] >= strong_sound_const - (police_vision+2):
                self.print("Near police detected while terrorist %d was planting a bomb." %(agent.id))
                # Survive is better than planting this bomb.
                self.move(agent.id, self._bombsite_direction(agent))
                # When a terrorist is planting a bomb and there is no police around, we let him complete his operation:)
            return True
        return False
    
    def fourth_terrorist_strategy(self, agent:Terrorist):
        # Continue to your path or plant a bomb
        if agent.id in self.path:
            if self.path[agent.id]:
                path = self.path[agent.id]
                if self._move(agent.id, Position(path[0][1], path[0][0]), agent.position):
                    self.print("Agent %d is moving: (%d, %d) --> (%d, %d)" %(agent.id, agent.position.y, agent.position.x, path[0][0], path[0][1]))
                    path.pop(0)
                    return True
                else:
                    del self.path[agent.id]
            else:
                # Hey terrorist, you are adjacent to a bombsite... Hurry up and plant!
                dest = self.terrorist_bomb_site[agent.id]
                del self.terrorist_bomb_site[agent.id]
                del self.path[agent.id]
                if self._plant(agent.id, Position(dest[1], dest[0]), agent.position):
                     self.print("Agent %d is planting a bomb!" %agent.id)
                     return True
        return False
    
    def fifth_terrorist_strategy(self, agent:Terrorist):
        dest = self._terrorist_destination(agent)
        if dest:
            g = Graph(self.world, (agent.position.y, agent.position.x), self._calculate_black_pos(agent))
            path = g.bfs(dest)
            if path:
                # Move!
                if self._move(agent.id, Position(path[0][1], path[0][0]), agent.position):
                    path.pop(0)    
                    self.path[agent.id] = path
                    return True
            else:
                # Hey terrorist, you are adjacent to a bombsite... Hurry up and plant!
                del self.terrorist_bomb_site[agent.id]
                if self._plant(agent.id, Position(dest[1], dest[0]), agent.position):
                    return True
                # Your way is closed:) please wait.
        return False
    
    def _terrorist_destination(self, agent:Terrorist, police_danger_pos:tuple=None):
        dest = None
        if agent.id in self.terrorist_bomb_site:
            dest = self.terrorist_bomb_site[agent.id]
        else:
            # Let's find a path to nearest free bomb site for this lucky terrorist:
            bombsite_index, min_distance = -1, float("inf")
            for index, bombsite in enumerate(self.free_bomb_sites):
                if police_danger_pos and abs(bombsite[0]-police_danger_pos[0]) + abs(bombsite[1]-police_danger_pos[1]) <= self.world.constants.police_vision_distance:
                    continue
                path = Graph(self.world, (agent.position.y, agent.position.x), [self.bomb_defuser_pos] if self.bomb_defuser_pos else []).bfs(bombsite)
                distance = float("inf") if path is None else len(path) // self._ecell_score(self.world.board[bombsite[0]][bombsite[1]]) 
                if distance < min_distance:
                    bombsite_index, min_distance = index, distance
            if bombsite_index != -1:
                # There exists a bombsite!
                dest = self.free_bomb_sites[bombsite_index]
                self.print("Terrorist with id %d wants bombsite (%d, %d)." %(agent.id, dest[0], dest[1]))
                self.terrorist_bomb_site[agent.id] = dest
                self.free_bomb_sites.pop(bombsite_index)
        return dest
    
    def _empty_directions(self, agent):
        # Adjacent empty cells of a position make some directions...
        position, empty_directions = agent.position, []
        for direction in self.DIRECTIONS:
            pos = AI._sum_pos_tuples((position.x, position.y), self.DIR_TO_POS[direction])
            agents_pos = self._calculate_black_pos(agent)
            if self.world.board[pos[1]][pos[0]] == ECell.Empty and (pos[1], pos[0]) not in agents_pos:
                empty_directions.append(direction)
        return empty_directions
    
    def _bombsite_direction(self, agent):
        position = agent.position
        for direction in self.DIRECTIONS:
            pos = pos = AI._sum_pos_tuples((position.x, position.y), self.DIR_TO_POS[direction])
            if self.world.board[pos[1]][pos[0]] in self.BOMBSITES_ECELL:
                return direction

    def _has_bomb(self, position):
        for bomb in self.world.bombs:
            if position[1] == bomb.position.x and position[0] == bomb.position.y:
                return True
        return False

    @staticmethod
    def _sum_pos_tuples(t1, t2):
        return (t1[0] + t2[0], t1[1] + t2[1])

    @staticmethod
    def _sub_pos(t1:Position, t2:Position):
        return (t1.x - t2.x, t1.y - t2.y)

    @staticmethod
    def _distance(first:Position, second:Position):
        return abs(first.x - second.x) + abs(first.y - second.y)
    
    def _calculate_black_pos(self, agent):
        # Alive agent positions around an specified agent: 
        black_pos = []
        my_agents = self.world.polices if self.my_side == 'Police' else self.world.terrorists
        for my_agent in my_agents:
            if my_agent.status is not EAgentStatus.Dead and my_agent != agent and AI._distance(my_agent.position, agent.position) == 1:
                black_pos.append((my_agent.position.y, my_agent.position.x))
        return black_pos


    def _mdistance(self, t1, t2):
        # return abs(self.visited_cells[(t1[1], t1[2])] - self.visited_cells[(t2[1], t2[2])])
        return abs(t1[1]-t2[1]) + abs(t1[2]-t2[2])
    
    def _bdistance(self, t1, t2):
        g = Graph(self.world, (t1[1], t1[2]))
        path = g.bfs((t2[1], t2[2]))
        return float("inf") if path is None else len(path)
    
    def _pathdistance(self, l:list):
        # Calculating manhataan distance taken when following a path.(list of positions)
        sum = 0
        for index, point in enumerate(l):
            if index < len(l) - 1:
                sum +=  self._mdistance(point, l[index+1])
        return sum
    
    def _nearest(self, t, l:list):
        # Finding nearest element(minimum distance) of a list to a value.
        min_point, min_value = l[0], self._mdistance(t, l[0])
        for point in l[1:]:
            distance = self._mdistance(t, point)
            if  distance < min_value:
                min_point = point
                min_value = distance
        return min_point

    def _valid_bombsite(self, pos:tuple):
        # Checking wether there exists at least one path from polices to a bombsite or not.
        res = False
        for police in self.world.polices:
            path = Graph(self.world, (police.position.y, police.position.x)).bfs(pos, pop_destination=False)
            if path is not None:
                res = True
                break
        return res
    
    def _bfs(self, source:tuple):
        self.visited_cells[source] = 0
        queue, depth = [source], 1
        while queue:
            frontier = []
            for item in queue:
                x, y = item
                adjacent = [(x-1, y), (x+1, y), (x, y-1), (x, y+1)]
                for t in adjacent:
                    if self.world.board[t[0]][t[1]] != ECell.Wall and t not in self.visited_cells.keys():
                        self.visited_cells[t] = depth 
                        if self.world.board[t[0]][t[1]] == ECell.Empty:
                            frontier.append(t)
            depth += 1
            queue = frontier
    
    def _ecell_score(self, cell:ECell):
        if cell ==  ECell.SmallBombSite:
            return self.world.constants.score_coefficient_small_bomb_site
        elif cell == ECell.MediumBombSite:
            return self.world.constants.score_coefficient_medium_bomb_site
        elif cell == ECell.LargeBombSite:
            return self.world.constants.score_coefficient_large_bomb_site
        elif cell == ECell.VastBombSite:
            return self.world.constants.score_coefficient_vast_bomb_site


