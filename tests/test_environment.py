import unittest

from env.environment import FactoryEnv
from env.models import Job, Robot
from grader.grader import grade


class FactoryEnvironmentTests(unittest.TestCase):
    def setUp(self):
        jobs = [Job(id="job_1", transport_time=2, processing_time=3, required_station_type="assembly", due_step=6)]
        mobile_robots = [Robot(id="m_1", type="mobile")]
        static_robots = [Robot(id="s_1", type="static", capability="assembly")]
        self.env = FactoryEnv(jobs, mobile_robots, static_robots)

    def test_transport_and_processing_take_multiple_steps(self):
        state = self.env.reset().model_dump()
        self.assertEqual(state["jobs"][0]["transport_remaining_time"], 0)

        observation, reward, done, info = self.env.step(("transport", "m_1", "job_1"))
        state = observation.model_dump()
        self.assertTrue(info["valid_action"])
        self.assertFalse(done)
        self.assertTrue(state["jobs"][0]["in_transport"])
        self.assertEqual(state["jobs"][0]["transport_remaining_time"], 1)
        self.assertEqual(state["mobile_robots"][0]["status"], "busy")

        observation, reward, done, info = self.env.step(("wait", None, None))
        state = observation.model_dump()
        self.assertTrue(state["jobs"][0]["transported"])
        self.assertFalse(state["jobs"][0]["completed"])
        self.assertEqual(state["mobile_robots"][0]["status"], "idle")

        observation, reward, done, info = self.env.step(("process", "s_1", "job_1"))
        state = observation.model_dump()
        self.assertTrue(info["valid_action"])
        self.assertTrue(state["jobs"][0]["in_process"])
        self.assertEqual(state["jobs"][0]["processing_remaining_time"], 2)

        self.env.step(("wait", None, None))
        observation, reward, done, info = self.env.step(("wait", None, None))
        state = observation.model_dump()
        self.assertTrue(state["jobs"][0]["completed"])
        self.assertTrue(done)

    def test_malformed_action_is_returned_as_invalid(self):
        observation, reward, done, info = self.env.step(("transport", "m_1"))
        self.assertFalse(info["valid_action"])
        self.assertIn("Action must contain exactly three items", info["error"])
        self.assertEqual(reward, 0.0)

    def test_grade_penalizes_invalid_and_slow_runs(self):
        env = FactoryEnv(
            [Job(id="job_1", transport_time=1, processing_time=1, required_station_type="assembly", due_step=3)],
            [Robot(id="m_1", type="mobile")],
            [Robot(id="s_1", type="static", capability="assembly")],
        )
        fast_state = env.reset().model_dump()
        fast_observation, _, _, _ = env.step(("transport", "m_1", "job_1"))
        fast_state = fast_observation.model_dump()
        fast_observation, _, _, _ = env.step(("process", "s_1", "job_1"))
        fast_state = fast_observation.model_dump()
        fast_score = grade(fast_state)

        slow_env = FactoryEnv(
            [Job(id="job_1", transport_time=1, processing_time=1, required_station_type="assembly", due_step=3)],
            [Robot(id="m_1", type="mobile")],
            [Robot(id="s_1", type="static", capability="assembly")],
        )
        slow_state = slow_env.reset().model_dump()
        slow_observation, _, _, _ = slow_env.step(("wait", None, None))
        slow_state = slow_observation.model_dump()
        slow_observation, _, _, _ = slow_env.step(("transport", "m_1", "job_1"))
        slow_state = slow_observation.model_dump()
        slow_observation, _, _, _ = slow_env.step(("process", "s_1", "job_1"))
        slow_state = slow_observation.model_dump()
        slow_score = grade(slow_state)

        self.assertGreater(fast_score, slow_score)

    def test_processing_requires_matching_station_capability(self):
        env = FactoryEnv(
            [Job(id="job_1", transport_time=1, processing_time=1, required_station_type="welding", due_step=4)],
            [Robot(id="m_1", type="mobile")],
            [Robot(id="s_1", type="static", capability="assembly")],
        )
        env.reset()
        env.step(("transport", "m_1", "job_1"))

        observation, reward, done, info = env.step(("process", "s_1", "job_1"))

        self.assertFalse(info["valid_action"])
        self.assertIn("cannot process station type welding", info["error"])
        self.assertEqual(reward, 0.0)


if __name__ == "__main__":
    unittest.main()
