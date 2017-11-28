import importlib
import threading

from pysc2 import maps
from pysc2.env import available_actions_printer, run_loop, sc2_env
from pysc2.lib import stopwatch

from absl import app, flags

FLAGS = flags.FLAGS
flags.DEFINE_integer("screen_resolution", 128,
                     "Resolution for screen feature layers.")
flags.DEFINE_integer("minimap_resolution", 128,
                     "Resolution for minimap feature layers.")

flags.DEFINE_integer("max_agent_steps", 1000000, "Total agent steps.")
flags.DEFINE_integer("game_steps_per_episode", 1000000, "Game steps per episode.")
flags.DEFINE_integer("step_mul", 1, "Game steps per agent step.")

flags.DEFINE_string("agent", "agents.scripted_build_agent.ScriptedBuildAgent",
                    "Which agent to run")
flags.DEFINE_enum("agent_race", "T", sc2_env.races.keys(), "Agent's race.")
flags.DEFINE_enum("bot_race", "R", sc2_env.races.keys(), "Bot's race.")
flags.DEFINE_enum("difficulty", None, sc2_env.difficulties.keys(),
                  "Bot's strength.")

flags.DEFINE_bool("profile", False, "Whether to turn on code profiling.")
flags.DEFINE_bool("trace", False, "Whether to trace the code execution.")
flags.DEFINE_integer("parallel", 1, "How many instances to run in parallel.")

flags.DEFINE_bool("save_replay", False, "Whether to save a replay at the end.")

flags.DEFINE_string("map", "Flat128", "Name of a map to use.")
flags.mark_flag_as_required("map")

def run_thread(agent_cls, map_name, visualize):
  with sc2_env.SC2Env(
      map_name=map_name,
      agent_race=FLAGS.agent_race,
      bot_race=FLAGS.bot_race,
      difficulty=FLAGS.difficulty,
      step_mul=FLAGS.step_mul,
      game_steps_per_episode=FLAGS.game_steps_per_episode,
      screen_size_px=(FLAGS.screen_resolution, FLAGS.screen_resolution),
      minimap_size_px=(FLAGS.minimap_resolution, FLAGS.minimap_resolution),
      visualize=visualize) as env:
    env = available_actions_printer.AvailableActionsPrinter(env)
    agent = agent_cls()
    run_loop.run_loop([agent], env, FLAGS.max_agent_steps)
    if FLAGS.save_replay:
      env.save_replay(agent_cls.__name__)

def main(unused_argv):
  stopwatch.sw.trace = FLAGS.trace

  maps.get(FLAGS.map)  # Assert the map exists.

  agent_module, agent_name = FLAGS.agent.rsplit(".", 1)
  agent_cls = getattr(importlib.import_module(agent_module), agent_name)

  threads = []
  for _ in range(FLAGS.parallel - 1):
    t = threading.Thread(target=run_thread, args=(agent_cls, FLAGS.map, True))
    threads.append(t)
    t.start()

  run_thread(agent_cls, FLAGS.map, True)

  for t in threads:
    t.join()

if __name__ == "__main__":
  app.run(main)
