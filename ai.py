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

            self.terrorist_strategies = [
                self.first_terrorist_strategy,
                self.second_terrorist_strategy,
                self.third_terrorist_strategy,
                self.fourth_terrorist_strategy,
                self.fifth_terrorist_strategy
            ]

    def update_bombsites(self):

        self.visited_cells = []
        for police in self.world.polices:
            if police.status == EAgentStatus.Alive:
                self._bfs((police.position.y, police.position.x))
                break

        # Path to be followed for defusing a bomb:
        self.path = {}
        self.police_bomb_site = {}

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
            choice_list = [(AI._mdistance(t, allocation_list[0]), t[1], t[2]) for t in tmp_bomb_sites]
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
                a, b, c, site_pos = 0, 0, 0, [None, None, None]
                for sound in l:
                    if sound[0] == ESoundIntensity.Strong:
                        a += 1
                        site_pos[0] = sound[1], sound[2]
                    elif sound[0] == ESoundIntensity.Normal:
                        b += 1
                        site_pos[1] = sound[1], sound[2]
                    else:
                        c += 1
                        site_pos[2] = sound[1], sound[2]
                value, values = a*100+b*10+c, [1, 10, 11, 100, 101, 110, 111]
                self.print("%03d" %(value) if self.world.board[i][j] == ECell.Empty else "---", end=' ')
            self.print("")


        # Let each police circulate around an area that cell inside the area have all sound types
        self.police_circulating_areas = {}
        for police_id, bombsites in self.police_bomb_sites.items():

            bombsite_areas = {}
            for i in range(self.world.height):
                for j in range(self.world.width):
                    l = self.sound_board[i][j]
                    a, b, c, site_pos = 0, 0, 0, [None, None, None]
                    for sound in l:
                        if sound[0] == ESoundIntensity.Strong:
                            a += 1
                            site_pos[0] = sound[1], sound[2]
                        elif sound[0] == ESoundIntensity.Normal:
                            b += 1
                            site_pos[1] = sound[1], sound[2]
                        else:
                            c += 1
                            site_pos[2] = sound[1], sound[2]
                    value, values = a*100+b*10+c, [1, 10, 11, 100, 101, 110, 111]
                    if self.world.board[i][j] == ECell.Empty and value in values:
                        for pos in site_pos:
                            if pos and pos in [(t[1], t[2]) for t in self.police_bomb_sites[police_id]]:
                                if pos not in bombsite_areas:
                                    bombsite_areas[pos] = []
                                if (i, j) in self.visited_cells:
                                    bombsite_areas[pos].append((i+j, i, j))
            self.print("Agent %d bombsite areas:" % police_id)
            self.print(bombsite_areas)
            '''
            # DP
            best_path, pre_path = {}, {}
            for bombsite_index in range(len(bombsite_areas.keys())):
                bombsite, areas = list(bombsite_areas.keys())[bombsite_index], list(bombsite_areas.values())[bombsite_index]
                for area_index, area in enumerate(areas):
                    if bombsite_index == 0:
                        best_path[(bombsite_index, area_index)] = 0
                        pre_path[(bombsite_index, area_index)] = None
                    else:
                        min_path_value, pre_area_index = float("inf"), 0
                        for prev_area_index, prev_area in enumerate(list(bombsite_areas.values())[bombsite_index-1]):
                            current_path_value = best_path[(bombsite_index-1, prev_area_index)] + self._mdistance(area, prev_area)
                            if current_path_value < min_path_value:
                                min_path_value = current_path_value
                                pre_area_index = prev_area_index
                        best_path[(bombsite_index, area_index)] = min_path_value
                        pre_path[(bombsite_index, area_index)] = pre_area_index
    
            
            last_bombsite_index, last_area_index, min_path_value = len(bombsite_areas.keys())-1, 0, float("inf")
            for area_index in range(len(list(bombsite_areas.values())[last_bombsite_index])):
                if best_path[(last_bombsite_index, area_index)] < min_path_value:
                    min_path_value = best_path[(last_bombsite_index, area_index)]
                    last_area_index = area_index
            

            self.print(best_path)
            self.print(pre_path)

            selected_areas = []
            while pre_path[(last_bombsite_index, last_area_index)]:
                area = list(bombsite_areas.values())[last_bombsite_index][last_area_index]
                if area not in selected_areas:
                    selected_areas.append(area)
                last_area_index = pre_path[(last_bombsite_index, last_area_index)]
                last_bombsite_index -= 1
            '''
            selected_areas = []
            for first_site in list(bombsite_areas.values())[0]:
                choice_list = [first_site]
                for other_site in list(bombsite_areas.values())[1:]:
                    choice_list.append(AI._nearest(choice_list[-1], other_site))
                if not selected_areas:
                    selected_areas = choice_list
                if AI._pathdistance(choice_list) < AI._pathdistance(selected_areas):
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
                    try:
                        if strategy(agent):
                            break
                    except Error as e:
                        print(e)
            else:
                self.bomb_defuser_pos = None
                for strategy in self.terrorist_strategies:
                    try:
                        if strategy(agent):
                            break
                    except Error as e:
                        print(e)
        
    
    def plant(self, agent_id, bombsite_direction):
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
                if bomb.defuser_id != -1:
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
            else:
                site_pos[2] = sound[1], sound[2]
        # Listening to server for a sound with priority of strong, normal and week...
        if site_pos[0] and ESoundIntensity.Strong in agent.bomb_sounds:
            self.print("Strong sound bomb found: (%d, %d)" %(site_pos[0][0], site_pos[0][1]))
            dest = site_pos[0]
        elif site_pos[1] and ESoundIntensity.Normal in agent.bomb_sounds:
            self.print("Normal sound bomb found: (%d, %d)" %(site_pos[1][0], site_pos[1][1]))
            dest = site_pos[1]
        elif site_pos[2] and ESoundIntensity.Weak in agent.bomb_sounds:
            self.print("Weak sound bomb found: (%d, %d)" %(site_pos[2][0], site_pos[2][1]))
            dest = site_pos[2]
        # Checking that exact destination of a planted bomb is found and is allocated to this agent!
        if dest is None or dest not in [(t[1], t[2]) for t in self.police_bomb_sites[agent.id]]:
            return False            
        # Let's go and defuseeee :))
        g = Graph(self.world, (agent.position.y, agent.position.x), self._calculate_black_pos(agent))
        path = g.bfs(dest, False)
        if path is None:
                return False
        self.path2[agent.id] = path
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
        police_pos = None
        for police in self.world.polices:
            if AI._distance(police.position, agent.position) <= self.world.constants.terrorist_vision_distance:
                police_pos = police.position
                # A police found around, let's make sure that he/she is defusing a bomb or not:
                for bomb in self.world.bombs:
                    if bomb.defuser_id == police.id and police.defusion_remaining_time > self.world.constants.police_vision_distance:
                        # Police is defusing a bomb, let's escape from a better way!
                        self.bomb_defuser_pos = (police.position.y, police.position.x)
                        police_pos = None
                        if agent.id in self.terrorist_bomb_site:
                            del self.terrorist_bomb_site[agent.id]
                        if agent.id in self.path:
                            del self.path[agent.id]
                        break
        if police_pos:
            # Escaping from misreable police:
            self.print("Near police detected at (%d, %d)" % (police_pos.y, police_pos.x))
            directions, selected_direction, escape_priority_queue = self._empty_directions(agent), None, []
            delta_y, delta_x = AI._sub_pos(police_pos, agent.position)
            self.print("Escaping with (delta_y=%d, delta_x=%d)..." %(delta_y, delta_x))
            if delta_x >= 0 and delta_y >= 0:
                if delta_x == delta_y:
                    escape_priority_queue = [ECommandDirection.Left, ECommandDirection.Up]
                elif delta_x < delta_y:
                    escape_priority_queue = [ECommandDirection.Left, ECommandDirection.Up, ECommandDirection.Down]
                else:
                    escape_priority_queue = [ECommandDirection.Up, ECommandDirection.Left, ECommandDirection.Right]
            elif delta_x >= 0 and delta_y < 0:
                if delta_x == -delta_y:
                    escape_priority_queue = [ECommandDirection.Right, ECommandDirection.Up]
                elif delta_x < -delta_y:
                    escape_priority_queue = [ECommandDirection.Right, ECommandDirection.Up, ECommandDirection.Down]
                else:
                    escape_priority_queue = [ECommandDirection.Up, ECommandDirection.Right, ECommandDirection.Left]
            elif delta_x < 0 and delta_y >= 0:
                if -delta_x == delta_y:
                    escape_priority_queue = [ECommandDirection.Left, ECommandDirection.Down]
                elif -delta_x < delta_y:
                    escape_priority_queue = [ECommandDirection.Left, ECommandDirection.Down, ECommandDirection.Up]
                else:
                    escape_priority_queue = [ECommandDirection.Down, ECommandDirection.Left, ECommandDirection.Right]
            else:
                if -delta_x == -delta_y:
                    escape_priority_queue = [ECommandDirection.Right, ECommandDirection.Down]
                elif -delta_x < -delta_y:
                    escape_priority_queue = [ECommandDirection.Right, ECommandDirection.Down, ECommandDirection.Up]
                else:
                    escape_priority_queue = [ECommandDirection.Down, ECommandDirection.Right, ECommandDirection.Left]
            for escape_direction in escape_priority_queue:
                if escape_direction in directions:
                    selected_direction = escape_direction
                    break
            if selected_direction:
                if agent.id in self.terrorist_bomb_site:
                    del self.terrorist_bomb_site[agent.id]
                if agent.id in self.path:
                    del self.path[agent.id]
                self.waiting_counter[agent.id] = 1
                self.move(agent.id, selected_direction)
            return True
        return False

    def second_terrorist_strategy(self, agent:Terrorist):
        # Waiting...
        if self.waiting_counter[agent.id]:
            self.waiting_counter[agent.id] -= 1
            return True
        return False

    def third_terrorist_strategy(self, agent:Terrorist):
        if agent.footstep_sounds.count(ESoundIntensity.Strong) and (self.world.constants.sound_ranges[ESoundIntensity.Strong] - self.world.constants.police_vision_distance) * 0.5 <= agent.planting_remaining_time:
            self.print("Near police detected while terrorist %d was planting a bomb." %(agent.id))
            # Survive is better than planting this bomb.
            self.move(agent.id, self._bombsite_direction(agent))
            return True
        # When a terrorist is planting a bomb and there is no police around, we let him complete his operation:)
        return agent.planting_remaining_time != -1
    
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
        if agent.id in self.terrorist_bomb_site:
            dest = self.terrorist_bomb_site[agent.id]
        else:
            # Let's find a path to nearest free bomb site for this lucky terrorist:
            bombsite_index, min_distance = -1, float("inf")
            for index, bombsite in enumerate(self.free_bomb_sites):
                path = Graph(self.world, (agent.position.y, agent.position.x), [self.bomb_defuser_pos] if self.bomb_defuser_pos else []).bfs(bombsite)
                distance = float("inf") if path is None else len(path)
                if distance < min_distance:
                    bombsite_index, min_distance = index, distance
            if bombsite_index != -1:
                # There exists a bombsite!
                dest = self.free_bomb_sites[bombsite_index]
                self.print("Terrorist with id %d wants bombsite (%d, %d)." %(agent.id, dest[0], dest[1]))
                self.terrorist_bomb_site[agent.id] = dest
                self.free_bomb_sites.pop(bombsite_index)
            else:
                dest = None
        if dest:
            black_pos = self._calculate_black_pos(agent)
            # Although we are not escaping from a police, we should watch out for defuser police position! 
            if self.bomb_defuser_pos:
                black_pos.append(self.bomb_defuser_pos)
            g = Graph(self.world, (agent.position.y, agent.position.x), black_pos)
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

    @staticmethod
    def _mdistance(t1, t2):
        return abs(t1[1]-t2[1]) + abs(t1[2]-t2[2])
    
    @staticmethod
    def _pathdistance(l:list):
        # Calculating manhataan distance taken when following a path.(list of positions)
        sum = 0
        for index, point in enumerate(l):
            if index < len(l) - 1:
                sum += AI._mdistance(point, l[index+1])
        return sum
    
    @staticmethod
    def _nearest(t, l:list):
        print("-----------------------------------------------------")
        print(l)
        # Finding nearest element(minimum distance) of a list to a value.
        min_point, min_value = l[0], AI._mdistance(t, l[0])
        for point in l[1:]:
            distance = AI._mdistance(t, point)
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
        self.visited_cells.append(source)
        queue = [source]
        while queue:
            x, y = queue[0]
            adjacent = [(x-1, y), (x+1, y), (x, y-1), (x, y+1)]
            for t in adjacent:
                if self.world.board[t[0]][t[1]] == ECell.Empty and t not in self.visited_cells:
                    queue.append(t)
                    self.visited_cells.append(t) 
            queue.pop(0)


