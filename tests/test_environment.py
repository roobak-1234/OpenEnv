import unittest

from env.environment import FactoryEnv
from env.models import Job, Robot
from grader.grader import MAX_SCORE, MIN_SCORE, grade


class FactoryEnvironmentTests(unittest.TestCase):
    def setUp(self):
        jobs = [
            Job(
                id="job_1",
                transport_time=2,
                processing_time=3,
                required_station_type="assembly",
                source_zone="receiving",
                release_step=0,
                due_step=6,
            )
        ]
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
            [
                Job(
                    id="job_1",
                    transport_time=1,
                    processing_time=1,
                    required_station_type="assembly",
                    source_zone="receiving",
                    release_step=0,
                    due_step=3,
                )
            ],
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
            [
                Job(
                    id="job_1",
                    transport_time=1,
                    processing_time=1,
                    required_station_type="assembly",
                    source_zone="receiving",
                    release_step=0,
                    due_step=3,
                )
            ],
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
            [
                Job(
                    id="job_1",
                    transport_time=1,
                    processing_time=1,
                    required_station_type="welding",
                    source_zone="receiving",
                    release_step=0,
                    due_step=4,
                )
            ],
            [Robot(id="m_1", type="mobile")],
            [Robot(id="s_1", type="static", capability="assembly")],
        )
        env.reset()
        env.step(("transport", "m_1", "job_1"))

        observation, reward, done, info = env.step(("process", "s_1", "job_1"))

        self.assertFalse(info["valid_action"])
        self.assertIn("cannot process station type welding", info["error"])
        self.assertEqual(reward, 0.0)

    def test_job_must_be_released_before_transport(self):
        env = FactoryEnv(
            [
                Job(
                    id="job_1",
                    transport_time=1,
                    processing_time=1,
                    required_station_type="assembly",
                    source_zone="kitting",
                    release_step=2,
                    due_step=5,
                )
            ],
            [Robot(id="m_1", type="mobile")],
            [Robot(id="s_1", type="static", capability="assembly")],
        )
        env.reset()

        observation, reward, done, info = env.step(("transport", "m_1", "job_1"))

        self.assertFalse(info["valid_action"])
        self.assertIn("has not been released yet", info["error"])
        self.assertEqual(reward, 0.0)

    def test_grade_is_strictly_inside_zero_and_one(self):
        perfect_like_state = {
            "jobs": [
                {"completed": True, "transport_time": 1, "processing_time": 1, "priority": 5},
            ],
            "mobile_robots": [{"id": "m_1"}],
            "static_robots": [{"id": "s_1"}],
            "time_step": 1,
            "metrics": {
                "valid_actions": 2,
                "invalid_actions": 0,
                "on_time_completions": 1,
                "late_completions": 0,
                "priority_weighted_completed": 5,
                "priority_weighted_on_time": 5,
                "overdue_job_ticks": 0,
            },
        }
        empty_like_state = {
            "jobs": [
                {"completed": False, "transport_time": 1, "processing_time": 1, "priority": 1},
            ],
            "mobile_robots": [{"id": "m_1"}],
            "static_robots": [{"id": "s_1"}],
            "time_step": 100,
            "metrics": {
                "valid_actions": 0,
                "invalid_actions": 100,
                "on_time_completions": 0,
                "late_completions": 1,
                "priority_weighted_completed": 0,
                "priority_weighted_on_time": 0,
                "overdue_job_ticks": 100,
            },
        }

        high_score = grade(perfect_like_state)
        low_score = grade(empty_like_state)

        self.assertEqual(high_score, MAX_SCORE)
        self.assertEqual(low_score, MIN_SCORE)
        self.assertGreater(high_score, 0.0)
        self.assertLess(high_score, 1.0)
        self.assertGreater(low_score, 0.0)
        self.assertLess(low_score, 1.0)

    def test_overdue_jobs_are_tracked_in_metrics(self):
        env = FactoryEnv(
            [
                Job(
                    id="job_1",
                    transport_time=2,
                    processing_time=2,
                    required_station_type="assembly",
                    source_zone="receiving",
                    release_step=0,
                    due_step=1,
                )
            ],
            [Robot(id="m_1", type="mobile")],
            [Robot(id="s_1", type="static", capability="assembly")],
        )
        env.reset()

        observation, _, _, _ = env.step(("wait", None, None))
        observation, _, _, _ = env.step(("wait", None, None))
        state = observation.model_dump()

        self.assertGreater(state["jobs"][0]["overdue_steps"], 0)
        self.assertGreater(state["metrics"]["overdue_job_ticks"], 0)

    def test_released_jobs_metric_only_counts_available_work(self):
        env = FactoryEnv(
            [
                Job(
                    id="job_1",
                    transport_time=1,
                    processing_time=1,
                    required_station_type="assembly",
                    source_zone="receiving",
                    release_step=0,
                    due_step=4,
                ),
                Job(
                    id="job_2",
                    transport_time=1,
                    processing_time=1,
                    required_station_type="assembly",
                    source_zone="kitting",
                    release_step=3,
                    due_step=6,
                ),
            ],
            [Robot(id="m_1", type="mobile")],
            [Robot(id="s_1", type="static", capability="assembly")],
        )
        state = env.reset().model_dump()
        self.assertEqual(state["metrics"]["released_jobs"], 0)

        observation, _, _, _ = env.step(("wait", None, None))
        state = observation.model_dump()
        self.assertEqual(state["metrics"]["released_jobs"], 1)

        observation, _, _, _ = env.step(("wait", None, None))
        observation, _, _, _ = env.step(("wait", None, None))
        observation, _, _, _ = env.step(("wait", None, None))
        state = observation.model_dump()
        self.assertEqual(state["metrics"]["released_jobs"], 2)


if __name__ == "__main__":
    unittest.main()
