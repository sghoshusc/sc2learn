import numpy

from pysc2.agents import base_agent
from pysc2.lib import actions, features

from enums.sc2_enums import *

import time

# I am not sure if 3 & 5 are correct values to use, but seem to work fine for me
_SUPPLY_DEPOT_RADIUS = 3
_BARRACKS_RADIUS = 5

# Values from pysc2
_PLAYER_SELF = 1
_PLAYER_HOSTILE = 4

_NOT_QUEUED = [0]
_QUEUED = [1]

# for simplicity sake, i set screen size = map size = mini map size = 128 x 128
_MAP_RESOLUTION = 128

# How often to refocus my marines
_STEPS_BEFORE_MARINE_RETARGET = 1000

# When to build additional supply
_MAX_POPULATION_RATIO = 0.8

# Mineral cost for units
_SCV_MINERALS = 50
_MARINE_MINERALS = 50
_SUPPLY_MINERALS = 100
_BARRACKS_MINERALS = 150

# Min# of units to have available
_MAX_SCVS = 20
_MAX_BARRACKS = 10
_MIN_MARINES_BEFORE_ATTACK = 30

class ScriptedBuildAgent(base_agent.BaseAgent):
  def __init__(self):
    super(ScriptedBuildAgent, self).__init__()
    self.last_possible_actions = None
    self.obs = None

    # Scripted decisions are a function of (minerals, food/food_cap, worker#, army#, barrack#)
    self.minerals, self.num_barracks, self.food_used, self.food_cap, self.worker_count, self.army_count = 0, 0, 0, 0, 0, 0

    # flags for state, restructure this
    self.selected_cc = False
    self.selected_scv = False
    self.selected_barracks = False
    self.selected_marine = False

    # Build order is implemented as a stack
    # We push to top when we decide to pursue a strategy
    # The strategy gets removed when all sub steps for the strategy are finished
    # No duplicate entries here
    self.next_build_step = [None]

    self.player_x, self.player_y = None, None
    self.all_locations_to_explore = []
    self.locations_to_explore = []
    self.next_location = 0

    # Setup a bunch of corner case coordinates to send marines to scout later
    min_increment = int(_MAP_RESOLUTION / 8)
    for i in range(min_increment, _MAP_RESOLUTION - min_increment, min_increment):
      self.all_locations_to_explore.append([i, min_increment])
      self.all_locations_to_explore.append([i, _MAP_RESOLUTION - min_increment])
      self.all_locations_to_explore.append([min_increment, i])
      self.all_locations_to_explore.append([_MAP_RESOLUTION - min_increment, i])
    self.locations_to_explore = self.all_locations_to_explore

  def CCSelected(self):
    actions = self.GetAvailableActions()
    if ActionEnum.RallyWorkers.value in actions:
      return True

    return False
  def BarracksSelected(self):
    actions = self.GetAvailableActions()
    if ActionEnum.TrainMarine.value in actions:
      return True

    return False
  def SCVSelected(self):
    actions = self.GetAvailableActions()
    if ActionEnum.Harvest.value in actions and ActionEnum.Cancel.value not in actions:
      return True

    return False
  def MarineSelected(self):
    actions = self.GetAvailableActions()
    if ActionEnum.Attack.value in actions and self.obs.observation['single_select'][0][0] != UnitEnum.TERRAN_SCV.value:
      return True

    return False

  # build order functions
  # build structures
  # These functions are implemented recursively
  # Can't attack with marine if not selected, can't select if none exist, can't build if barracks doesn't exist,
  # can't build barracks if supply depot doesn't exist, can't build Supply Depot if no SCV
  def BOBuildSupplyDepot(self):
    function_id = ActionEnum.NoOp.value
    args = []

    if self.SCVSelected():
      self.selected_scv = True

    if not self.selected_scv:
      scv_indices = self.FindUnitLocationOnScreen(UnitEnum.TERRAN_SCV.value)
      if len(scv_indices) <= 0 or len(scv_indices[0]) <= 0 or len(scv_indices[1]) <= 0:
        return self.BOBuildSCV()

      # Randomly pick an SCV and make him work
      picked_scv_index = numpy.random.randint(len(scv_indices[0]))
      args = [_NOT_QUEUED, [scv_indices[0][picked_scv_index], scv_indices[1][picked_scv_index]]]

      function_id = ActionEnum.SelectPoint.value

      self.selected_scv = True
      return False, function_id, args
    else:
      actions = self.GetAvailableActions()
      if ActionEnum.BuildSupplyDepot.value not in actions:
        self.selected_scv = False
        return False, function_id, args

      free_loc = self.FindFreeBlockOnMap(_SUPPLY_DEPOT_RADIUS)
      if not free_loc:
        return False, function_id, args

      function_id = ActionEnum.BuildSupplyDepot.value
      args = [_NOT_QUEUED, free_loc]

      return True, function_id, args

    return False, function_id, args
  def BOBuildBarracks(self):
    function_id = ActionEnum.NoOp.value
    args = []

    # check if supply depot exist
    y, x = self.FindUnitLocationOnScreen(UnitEnum.TERRAN_SUPPLYDEPOT.value)
    if len(y) <= 0 or len(x) <= 0:
      return self.BOBuildSupplyDepot()

    if self.SCVSelected():
      self.selected_scv = True

    if not self.selected_scv:
      scv_indices = self.FindUnitLocationOnScreen(UnitEnum.TERRAN_SCV.value)
      if len(scv_indices) <= 0 or len(scv_indices[0]) <= 0 or len(scv_indices[1]) <= 0:
        # TODO check if need to move screen
        return False, function_id, args

      picked_scv_index = numpy.random.randint(len(scv_indices[0]))
      args = [_NOT_QUEUED, [scv_indices[0][picked_scv_index], scv_indices[1][picked_scv_index]]]

      function_id = ActionEnum.SelectPoint.value

      self.selected_scv = True
      return False, function_id, args
    else:
      actions = self.GetAvailableActions()
      if ActionEnum.BuildBarracks.value not in actions:
        self.selected_scv = False
        return False, function_id, args

      free_loc = self.FindFreeBlockOnMap(_BARRACKS_RADIUS)
      if not free_loc:
        return False, function_id, args

      function_id = ActionEnum.BuildBarracks.value
      args = [_NOT_QUEUED, free_loc]

      return True, function_id, args

    return False, function_id, args
  def AttackWithMarine(self):
    function_id = ActionEnum.NoOp.value
    args = []

    actions = self.GetAvailableActions()
    if self.MarineSelected():
      self.selected_marine = True

    if not self.selected_marine:
      if ActionEnum.SelectArmy.value in actions:
        function_id = ActionEnum.SelectArmy.value
        args = [_NOT_QUEUED]
        self.selected_marine = True
        return False, function_id, args
      else:
        return self.BOBuildMarine()
    else:
      if not self.MarineSelected():
        self.selected_marine = False
        return False, function_id, args

      function_id = ActionEnum.Attack.value
      args = [_NOT_QUEUED, self.FindEnemyLocationOnMap()]

    return True, function_id, args

  # If we are able to see enemies on explored part of minimap, send marines there,
  # otherwise explore from our list of locations
  def FindEnemyLocationOnMap(self):
    enemy_y, enemy_x = (self.GetFeaturesLayer('minimap', features.SCREEN_FEATURES.player_relative.index) == _PLAYER_HOSTILE).nonzero()
    if enemy_x.any() and enemy_y.any():
      return [enemy_x.mean(), enemy_y.mean()]

    return self.locations_to_explore[self.next_location]

  def FindFreeBlockOnMap(self, radius):
    unit_type_screen_feature = self.GetFeaturesLayer('screen', features.SCREEN_FEATURES.unit_type.index)
    for pivot_y in range(radius, _MAP_RESOLUTION-radius):
      for pivot_x in range(radius, _MAP_RESOLUTION-radius):
        pivot_x, pivot_y = numpy.random.randint(radius, _MAP_RESOLUTION-radius, size=2)
        sub_matrix = unit_type_screen_feature[pivot_y-radius:pivot_y+radius, pivot_x-radius:pivot_x+radius]
        if (sub_matrix == UnitEnum.INVALID.value).all():
          return pivot_x, pivot_y

    self.Log('ERROR, could not find a free block of radius: ' + str(radius))
    return None
  def FindUnitLocationOnScreen(self, unit_enum):
    unit_type_screen_feature = self.GetFeaturesLayer('screen', features.SCREEN_FEATURES.unit_type.index)
    indices = (unit_type_screen_feature == unit_enum).nonzero()
    return [indices[1], indices[0]]
  def FindUnitLocationOnMiniMap(self, unit_enum):
    unit_type_screen_feature = self.GetFeaturesLayer('minimap', features.SCREEN_FEATURES.player_relative.index)
    indices = (unit_type_screen_feature == unit_enum).nonzero()
    return [indices[1], indices[0]]

  # build units
  def BOBuildSCV(self):
    function_id = ActionEnum.NoOp.value
    args = []

    if self.CCSelected():
      self.selected_cc = True

    if not self.selected_cc:
      cc_indices = self.FindUnitLocationOnScreen(UnitEnum.TERRAN_COMMANDCENTER.value)
      if len(cc_indices) <= 0 or len(cc_indices[0]) <= 0 or len(cc_indices[1]) <= 0:
        # check if need to move screen
        return False, function_id, args

      r_i = numpy.random.randint(len(cc_indices[0]))
      args = [_NOT_QUEUED, [cc_indices[0][r_i], cc_indices[1][r_i]]]

      function_id = ActionEnum.SelectPoint.value

      self.selected_cc = True
      return False, function_id, args
    else:
      actions = self.GetAvailableActions()
      if ActionEnum.TrainSCV.value not in actions:
        self.selected_cc = False
        return False, function_id, args

      function_id = ActionEnum.TrainSCV.value
      args = [_QUEUED]
      return True, function_id, args

    return False, function_id, args
  def BOBuildMarine(self):
    # check if barracks exist
    y, x = self.FindUnitLocationOnScreen(UnitEnum.TERRAN_BARRACKS.value)
    if len(y) <= 0 or len(x) <= 0:
      return self.BOBuildBarracks()

    function_id = ActionEnum.NoOp.value
    args = []

    if self.BarracksSelected():
      self.selected_barracks = True

    if not self.selected_barracks:
      cc_indices = self.FindUnitLocationOnScreen(UnitEnum.TERRAN_BARRACKS.value)
      if len(cc_indices) <= 0 or len(cc_indices[0]) <= 0 or len(cc_indices[1]) <= 0:
        # check if need to move screen
        return False, function_id, args

      r_i = numpy.random.randint(len(cc_indices[0]))
      args = [_NOT_QUEUED, [cc_indices[0][r_i], cc_indices[1][r_i]]]

      function_id = ActionEnum.SelectPoint.value

      self.selected_cc = True
      return False, function_id, args
    else:
      actions = self.GetAvailableActions()
      if ActionEnum.TrainMarine.value not in actions:
        self.selected_barracks = False
        return False, function_id, args

      function_id = ActionEnum.TrainMarine.value
      args = [_QUEUED]
      return True, function_id, args

    return False, function_id, args

  def GetAvailableActions(self):
    return self.obs.observation['available_actions']
  def GetFeaturesLayer(self, type, subtype):
    return self.obs.observation[type][subtype]

  def ActionToString(self, id):
    return str(self.action_spec.functions[id].str(True)).strip().split(' ')[0]
  def LogAndUpdateAvailableActions(self, possible_actions):
    if not numpy.array_equal(self.last_possible_actions, possible_actions):
      self.last_possible_actions = possible_actions

      str_possible_actions = [self.ActionToString(id) for id in possible_actions]
      self.Log('Possible: ' + str(str_possible_actions))
  def Log(self, line):
    print(self.LogPrefix() + line)

  def GetNextBuildStep(self):
    if len(self.next_build_step) <= 1:
      # empty, check what we should do next, rules:

      # (1) if population nearing cap, build supply depot
      if self.food_used / self.food_cap > _MAX_POPULATION_RATIO and self.minerals > _SUPPLY_MINERALS and ScriptedBuildAgent.BOBuildSupplyDepot not in self.next_build_step:
        self.next_build_step.insert(0, ScriptedBuildAgent.BOBuildSupplyDepot)

      # (2) macro up to 25 SCVs
      if self.worker_count < _MAX_SCVS and self.food_used + 2 < self.food_cap and self.minerals > _SCV_MINERALS and ScriptedBuildAgent.BOBuildSCV not in self.next_build_step:
        self.next_build_step.insert(0, ScriptedBuildAgent.BOBuildSCV)

      # (3) if floating minerals, build another barrack upto 7
      if self.num_barracks < _MAX_BARRACKS and self.minerals > _BARRACKS_MINERALS and ScriptedBuildAgent.BOBuildBarracks not in self.next_build_step:
        self.next_build_step.insert(0, ScriptedBuildAgent.BOBuildBarracks)
        self.num_barracks += 1

      # (4) keep building marines
      if self.num_barracks > 0 and self.food_used + 2 < self.food_cap and self.minerals > _MARINE_MINERALS and ScriptedBuildAgent.BOBuildMarine not in self.next_build_step:
        self.next_build_step.insert(0, ScriptedBuildAgent.BOBuildMarine)

      # (5) if you have 30+ marines, take them and attack
      if self.army_count > _MIN_MARINES_BEFORE_ATTACK and ScriptedBuildAgent.AttackWithMarine not in self.next_build_step:
        self.next_build_step.insert(0, ScriptedBuildAgent.AttackWithMarine)

    return self.next_build_step[0]
  def RemoveBuildStep(self):
    if len(self.next_build_step) > 1:
      self.next_build_step.pop(0)

  def step(self, obs):
    super(ScriptedBuildAgent, self).step(obs)
    self.obs = obs
    success, function_id, args = False, ActionEnum.NoOp.value, []

    possible_actions = self.GetAvailableActions()
    self.LogAndUpdateAvailableActions(possible_actions)

    self.UpdateCounts()

    next_build_step = self.GetNextBuildStep()
    if not next_build_step:
      return actions.FunctionCall(function_id, args)

    success, function_id, args = next_build_step(self)
    if function_id != ActionEnum.NoOp.value:
      self.Log('Chose ' + self.ActionToString(function_id) + ' ' + str(args) + ' success: ' + str(success))
    if success:
      self.RemoveBuildStep()
      self.Log('Working on ' + str(self.GetNextBuildStep()))

    # (0, 0) is top left of the mini map
    if not self.player_y or not self.player_x:
      player_y, player_x = (self.GetFeaturesLayer('minimap', features.SCREEN_FEATURES.player_relative.index) == _PLAYER_SELF).nonzero()
      self.player_y, self.player_x = player_y.mean(), player_x.mean()
      self.Log('x_mean: ' + str(self.player_x) + ' y_mean: ' + str(self.player_y))

    if self.steps % _STEPS_BEFORE_MARINE_RETARGET == 0:
      self.locations_to_explore.pop(self.next_location)
      if len(self.locations_to_explore) < 1:
        self.locations_to_explore = list(self.all_locations_to_explore)
      self.next_location = numpy.random.randint(0, len(self.locations_to_explore))

    return actions.FunctionCall(function_id, args)

  def UpdateCounts(self):
    # obs.player_common.player_id,
    # obs.player_common.minerals,
    # obs.player_common.vespene,
    # obs.player_common.food_used,
    # obs.player_common.food_cap,
    # obs.player_common.food_army,
    # obs.player_common.food_workers,
    # obs.player_common.idle_worker_count,
    # obs.player_common.army_count,
    # obs.player_common.warp_gate_count,
    # obs.player_common.larva_count,
    player_layer = self.obs.observation['player']

    self.minerals = player_layer[1]
    self.food_used = player_layer[3]
    self.food_cap = player_layer[4]
    self.worker_count = player_layer[6]
    self.army_count = player_layer[8]

    # self.Log('Pop: ' + str(self.food_used) + ' PopLimit: ' + str(self.food_cap) + ' Ratio: ' + str(self.food_used/self.food_cap) + ' SCV: ' + str(self.worker_count) + ' Army: ' + str(self.army_count))

  def LogPrefix(self):
    return '[' + str(self.steps) + ' ' + str(self.reward) + ']'
