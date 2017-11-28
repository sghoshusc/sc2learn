import numpy

from pysc2.agents import base_agent
from pysc2.lib import actions, features

from enums.sc2_enums import *

import time

_SUPPLY_DEPOT_RADIUS = 3
_BARRACKS_RADIUS = 5

_PLAYER_SELF = 1
_PLAYER_HOSTILE = 4

class ScriptedBuildAgent(base_agent.BaseAgent):
  def __init__(self):
    super(ScriptedBuildAgent, self).__init__()
    self.last_possible_actions = None
    self.obs = None

    self.minerals, self.num_barracks, self.food_used, self.food_cap, self.worker_count, self.army_count = 0, 0, 0, 0, 0, 0

    # flags for state, restructure this
    self.selected_cc = False
    self.selected_scv = False
    self.selected_barracks = False
    self.selected_marine = False

    self.next_build_step = [None]

    self.player_x, self.player_y = None, None

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
  def BOBuildSupplyDepot(self):
    function_id = ActionEnum.NoOp.value
    args = []

    if self.SCVSelected():
      self.selected_scv = True

    if not self.selected_scv:
      scv_indices = self.FindUnitLocationOnScreen(UnitEnum.TERRAN_SCV.value)
      if len(scv_indices) <= 0 or len(scv_indices[0]) <= 0 or len(scv_indices[1]) <= 0:
        # TODO check if need to move screen
        return False, function_id, args

      picked_scv_index = numpy.random.randint(len(scv_indices[0]))
      args = [[0], [scv_indices[0][picked_scv_index], scv_indices[1][picked_scv_index]]]

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
      args = [[0], free_loc]

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
      args = [[0], [scv_indices[0][picked_scv_index], scv_indices[1][picked_scv_index]]]

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
      args = [[0], free_loc]

      return True, function_id, args

    return False, function_id, args
  def AttackWithMarine(self):
    function_id = ActionEnum.NoOp.value
    args = []

    if not self.selected_marine:
      function_id = ActionEnum.SelectArmy.value
      args = [[0]]
      self.selected_marine = True
      return False, function_id, args
    else:
      if not self.MarineSelected():
        self.selected_marine = False
        return False, function_id, args

      function_id = ActionEnum.Attack.value
      args = [[0], [128 - self.player_x, 128 - self.player_y]]

    return True, function_id, args

  def FindFreeBlockOnMap(self, radius):
    unit_type_screen_feature = self.GetFeaturesLayer('screen', features.SCREEN_FEATURES.unit_type.index)
    for pivot_y in range(radius, 128-radius):
      for pivot_x in range(radius, 128-radius):
        pivot_x, pivot_y = numpy.random.randint(radius, 128-radius, size=2)
        sub_matrix = unit_type_screen_feature[pivot_y-radius:pivot_y+radius, pivot_x-radius:pivot_x+radius]
        if (sub_matrix == UnitEnum.INVALID.value).all():
          return pivot_x, pivot_y

    self.Log('ERROR, could not find a free block of radius: ' + str(radius))
    return None
  def FindUnitLocationOnScreen(self, unit_enum):
    unit_type_screen_feature = self.GetFeaturesLayer('screen', features.SCREEN_FEATURES.unit_type.index)
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
      args = [[0], [cc_indices[0][r_i], cc_indices[1][r_i]]]

      function_id = ActionEnum.SelectPoint.value

      self.selected_cc = True
      return False, function_id, args
    else:
      actions = self.GetAvailableActions()
      if ActionEnum.TrainSCV.value not in actions:
        self.selected_cc = False
        return False, function_id, args

      function_id = ActionEnum.TrainSCV.value
      args = [[1]]
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
      args = [[0], [cc_indices[0][r_i], cc_indices[1][r_i]]]

      function_id = ActionEnum.SelectPoint.value

      self.selected_cc = True
      return False, function_id, args
    else:
      actions = self.GetAvailableActions()
      if ActionEnum.TrainMarine.value not in actions:
        self.selected_barracks = False
        return False, function_id, args

      function_id = ActionEnum.TrainMarine.value
      args = [[1]]
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
      if self.food_used / self.food_cap > 0.8 and self.minerals > 100 and ScriptedBuildAgent.BOBuildSupplyDepot not in self.next_build_step:
        self.next_build_step.insert(0, ScriptedBuildAgent.BOBuildSupplyDepot)

      # (2) macro up to 25 SCVs
      if self.worker_count < 25 and self.food_used + 2 < self.food_cap and self.minerals > 50 and ScriptedBuildAgent.BOBuildSCV not in self.next_build_step:
        self.next_build_step.insert(0, ScriptedBuildAgent.BOBuildSCV)

      # (3) if floating minerals, build another barrack upto 7
      if self.num_barracks < 7 and self.minerals > 150 and ScriptedBuildAgent.BOBuildBarracks not in self.next_build_step:
        self.next_build_step.insert(0, ScriptedBuildAgent.BOBuildBarracks)
        self.num_barracks += 1

      # (4) keep building marines
      if self.num_barracks > 0 and self.food_used + 2 < self.food_cap and self.minerals > 50 and ScriptedBuildAgent.BOBuildMarine not in self.next_build_step:
        self.next_build_step.insert(0, ScriptedBuildAgent.BOBuildMarine)

      # (5) if you have 30+ marines, take them and attack
      if self.army_count > 30 and ScriptedBuildAgent.AttackWithMarine not in self.next_build_step:
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
      player_y, player_x = (obs.observation['minimap'][features.SCREEN_FEATURES.player_relative.index] == _PLAYER_SELF).nonzero()
      self.player_y, self.player_x = player_y.mean(), player_x.mean()
      self.Log('x_mean: ' + str(self.player_x) + ' y_mean: ' + str(self.player_y))

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
