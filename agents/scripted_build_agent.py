import numpy

from pysc2.agents import base_agent
from pysc2.lib import actions, features

from enums.sc2_enums import *

import time

_SUPPLY_DEPOT_RADIUS = 5
_BARRACKS_RADIUS = 7
_EBAY_RADIUS = 7

class ScriptedBuildAgent(base_agent.BaseAgent):
  def __init__(self):
    super(ScriptedBuildAgent, self).__init__()
    self.last_possible_actions = None
    self.obs = None

    self.build_order = [ScriptedBuildAgent.BOBuildSCV,
                        ScriptedBuildAgent.BOBuildSupplyDepot,
                        ScriptedBuildAgent.BOBuildSCV,
                        ScriptedBuildAgent.BOBuildSCV,
                        ScriptedBuildAgent.BOBuildSCV,
                        ScriptedBuildAgent.BOBuildSCV,
                        ScriptedBuildAgent.BOBuildBarracks,
                        ScriptedBuildAgent.BOBuildSCV,
                        ScriptedBuildAgent.BOBuildSCV,
                        ScriptedBuildAgent.BOBuildSCV,
                        ScriptedBuildAgent.BOBuildSCV,
                        ScriptedBuildAgent.BOBuildSCV,
                        ScriptedBuildAgent.BOBuildSCV,
                        ScriptedBuildAgent.BOBuildSCV,
                        ScriptedBuildAgent.BOBuildSCV,
                        ScriptedBuildAgent.BOBuildSupplyDepot,
                        ScriptedBuildAgent.BOBuildSCV,
                        ScriptedBuildAgent.BOBuildSCV,
                        ScriptedBuildAgent.BOBuildMarine,
                        ScriptedBuildAgent.BOBuildMarine,
                        ScriptedBuildAgent.BOBuildSCV,
                        ScriptedBuildAgent.BOBuildSCV,
                        ScriptedBuildAgent.BOBuildMarine,
                        ScriptedBuildAgent.BOBuildSupplyDepot,
                        ScriptedBuildAgent.BOBuildBarracks,
                        ScriptedBuildAgent.BOBuildMarine,
                        ScriptedBuildAgent.BOBuildMarine,
                        ScriptedBuildAgent.BOBuildEBay,
                        ScriptedBuildAgent.BOBuildSupplyDepot,
                        ScriptedBuildAgent.BOBuildMarine,
                        ScriptedBuildAgent.BOBuildMarine,
                        ScriptedBuildAgent.BOBuildMarine,
                        ScriptedBuildAgent.BOBuildMarine,
                        ScriptedBuildAgent.BOBuildMarine,
                        ScriptedBuildAgent.BOBuildMarine,
                        ScriptedBuildAgent.BOBuildMarine,
                        ScriptedBuildAgent.BOBuildMarine,
                        ScriptedBuildAgent.BOBuildMarine,
                        ScriptedBuildAgent.BOBuildMarine,
                        ScriptedBuildAgent.BOBuildMarine,
                        ScriptedBuildAgent.BOBuildBarracks,
                        ScriptedBuildAgent.BOBuildSupplyDepot,
                        ScriptedBuildAgent.BOBuildMarine,
                        ScriptedBuildAgent.BOBuildMarine,
                        ScriptedBuildAgent.BOBuildMarine,
                        ScriptedBuildAgent.BOBuildMarine,
                        ScriptedBuildAgent.BOBuildMarine,
                        ScriptedBuildAgent.BOBuildMarine,
                        ScriptedBuildAgent.BOBuildMarine,
                        ScriptedBuildAgent.BOBuildMarine,
                        ScriptedBuildAgent.BOBuildMarine,
                        ScriptedBuildAgent.BOBuildMarine,
                        ScriptedBuildAgent.BOBuildMarine,
                        ScriptedBuildAgent.BOBuildMarine,
                        ScriptedBuildAgent.BOBuildMarine,
                        ScriptedBuildAgent.BOBuildMarine,
                        ScriptedBuildAgent.BOBuildMarine,
                        ScriptedBuildAgent.BOBuildMarine,
                        ScriptedBuildAgent.BOBuildMarine,
                        ScriptedBuildAgent.BOBuildMarine,
                        ScriptedBuildAgent.BOBuildMarine,
                        ScriptedBuildAgent.BOBuildMarine,
                        ScriptedBuildAgent.BOBuildSupplyDepot,
                        ScriptedBuildAgent.BOBuildMarine,
                        ScriptedBuildAgent.BOBuildMarine,
                        ScriptedBuildAgent.BOBuildMarine,
                        ScriptedBuildAgent.BOBuildMarine,
                        ScriptedBuildAgent.BOBuildMarine,
                        ScriptedBuildAgent.BOBuildMarine,
                        ScriptedBuildAgent.BOBuildMarine,
                        ScriptedBuildAgent.BOBuildMarine,
                        ScriptedBuildAgent.BOBuildMarine,
                        ScriptedBuildAgent.BOBuildMarine,
                        ScriptedBuildAgent.BOBuildMarine,
                        ScriptedBuildAgent.BOBuildMarine,
                        ScriptedBuildAgent.BOBuildMarine,
                        ScriptedBuildAgent.BOBuildMarine,
                        ScriptedBuildAgent.BOBuildMarine,
                        ScriptedBuildAgent.BOBuildMarine,
                        ScriptedBuildAgent.BOBuildMarine,
                        ScriptedBuildAgent.BOBuildMarine,
                        ScriptedBuildAgent.BOBuildMarine,
                        ScriptedBuildAgent.BOBuildMarine,
                        ScriptedBuildAgent.BOBuildSupplyDepot,
                        ScriptedBuildAgent.BOBuildMarine,
                        ScriptedBuildAgent.BOBuildMarine,
                        ScriptedBuildAgent.BOBuildMarine,
                        ScriptedBuildAgent.BOBuildMarine,
                        ScriptedBuildAgent.BOBuildMarine,
                        ScriptedBuildAgent.BOBuildMarine,
                        ScriptedBuildAgent.BOBuildMarine,
                        ScriptedBuildAgent.BOBuildMarine,
                        ScriptedBuildAgent.BOBuildMarine,
                        ScriptedBuildAgent.BOBuildMarine,
                        ScriptedBuildAgent.BOBuildMarine,
                        ScriptedBuildAgent.BOBuildMarine,
                        ScriptedBuildAgent.BOBuildMarine,
                        ScriptedBuildAgent.BOBuildMarine,
                        ScriptedBuildAgent.BOBuildMarine,
                        ScriptedBuildAgent.BOBuildMarine,
                        ScriptedBuildAgent.BOBuildMarine,
                        ScriptedBuildAgent.BOBuildMarine,
                        ScriptedBuildAgent.BOBuildMarine,
                        ScriptedBuildAgent.BOBuildMarine,
                        None
                        ]
    self.rem_build_steps = 0

    # flags for state, restructure this
    self.selected_cc = False
    self.selected_scv = False
    self.selected_barracks = False

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
  def BOBuildEBay(self):
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
      if ActionEnum.BuildEngineeringBay.value not in actions:
        self.selected_scv = False
        return False, function_id, args

      free_loc = self.FindFreeBlockOnMap(_EBAY_RADIUS)
      if not free_loc:
        return False, function_id, args

      function_id = ActionEnum.BuildEngineeringBay.value
      args = [[0], free_loc]

      return True, function_id, args

    return False, function_id, args

  def FindFreeBlockOnMap(self, radius):
    unit_type_screen_feature = self.GetFeaturesLayer('screen', features.SCREEN_FEATURES.unit_type.index)
    for pivot_y in range(radius, 64-radius):
      for pivot_x in range(radius, 64-radius):
        pivot_x, pivot_y = numpy.random.randint(radius, 64-radius, size=2)
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
    if len(self.build_order) <= 0:
      return None

    return self.build_order[0]
  def RemoveBuildStep(self):
    self.build_order.pop(0)

  def step(self, obs):
    super(ScriptedBuildAgent, self).step(obs)
    self.obs = obs
    time.sleep(0.02)
    success, function_id, args = False, ActionEnum.NoOp.value, []

    possible_actions = self.GetAvailableActions()
    self.LogAndUpdateAvailableActions(possible_actions)

    # if self.steps % 100 != 0:
    #   return actions.FunctionCall(function_id, args)

    next_build_step = self.GetNextBuildStep()
    if not next_build_step:
      return actions.FunctionCall(function_id, args)

    if self.rem_build_steps != len(self.build_order):
      self.rem_build_steps = len(self.build_order)

    success, function_id, args = next_build_step(self)
    if function_id != ActionEnum.NoOp.value:
      self.Log('Chose ' + self.ActionToString(function_id) + ' ' + str(args))
    if success:
      self.RemoveBuildStep()
      self.Log('Working on ' + str(self.GetNextBuildStep()))

    return actions.FunctionCall(function_id, args)

  def LogPrefix(self):
    return '[' + str(self.steps) + ' ' + str(self.reward) + ']'
