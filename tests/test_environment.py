import unittest

from env.environment import FactoryEnv
from env.models import Job, Robot
from grader.grader import grade


class FactoryEnvironmentTests(unittest.TestCase):
    def setUp(self):
        jobs = [Job(id="job_1", transport_time=2, processing_time=3)]
        mobile_robots = [Robot(id="m_1", type="mobile")]
        static_robots = [Robot(id="s_1", type="static")]
        self.env = FactoryEnv(jobs, mobile_robots, static_robots)

    def test_transport_and_processing_take_multiple_steps(self):
        state = self.env.reset()
        self.assertEqual(state["jobs"][0]["transport_remaining_time"], 0)

        state, reward, done, info = self.env.step(("transport", "m_1", "job_1"))
        self.assertTrue(info["valid_action"])
        self.assertFalse(done)
        self.assertTrue(state["jobs"][0]["in_transport"])
        self.assertEqual(state["jobs"][0]["transport_remaining_time"], 1)
        self.assertEqual(state["mobile_robots"][0]["status"], "busy")

        state, reward, done, info = self.env.step(("wait", None, None))
        self.assertTrue(state["jobs"][0]["transported"])
        self.assertFalse(state["jobs"][0]["completed"])
        self.assertEqual(state["mobile_robots"][0]["status"], "idle")

        state, reward, done, info = self.env.step(("process", "s_1", "job_1"))
        self.assertTrue(info["valid_action"])
        self.assertTrue(state["jobs"][0]["in_process"])
        self.assertEqual(state["jobs"][0]["processing_remaining_time"], 2)

        self.env.step(("wait", None, None))
        state, reward, done, info = self.env.step(("wait", None, None))
        self.assertTrue(state["jobs"][0]["completed"])
        self.assertTrue(done)

    def test_malformed_action_is_returned_as_invalid(self):
        state, reward, done, info = self.env.step(("transport", "m_1"))
        self.assertFalse(info["valid_action"])
        self.assertIn("Action must contain exactly three items", info["error"])
        self.assertLess(reward, 0)

    def test_grade_penalizes_invalid_and_slow_runs(self):
        env = FactoryEnv(
            [Job(id="job_1", transport_time=1, processing_time=1)],
            [Robot(id="m_1", type="mobile")],
            [Robot(id="s_1", type="static")],
        )
        fast_state = env.reset()
        fast_state, _, _, _ = env.step(("transport", "m_1", "job_1"))
        fast_state, _, _, _ = env.step(("process", "s_1", "job_1"))
        fast_score = grade(fast_state)

        slow_env = FactoryEnv(
            [Job(id="job_1", transport_time=1, processing_time=1)],
            [Robot(id="m_1", type="mobile")],
            [Robot(id="s_1", type="static")],
        )
        slow_state = slow_env.reset()
        slow_state, _, _, _ = slow_env.step(("wait", None, None))
        slow_state, _, _, _ = slow_env.step(("transport", "m_1", "job_1"))
        slow_state, _, _, _ = slow_env.step(("process", "s_1", "job_1"))
        slow_score = grade(slow_state)

        self.assertGreater(fast_score, slow_score)


if __name__ == "__main__":
    unittest.main()
