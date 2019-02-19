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
from ai import AI
from graph import Graph
from sound import Sound

class Strategy(AI):

    def __init__(self, world):
        super(self).__init__(world)
    
    
