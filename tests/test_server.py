import unittest

from fastapi.testclient import TestClient

from server.app import app


class ServerTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_reset_creates_isolated_sessions(self):
        first = self.client.post("/reset", json={"task": "easy"})
        second = self.client.post("/reset", json={"task": "easy"})

        first_payload = first.json()
        second_payload = second.json()

        self.assertNotEqual(first_payload["session_id"], second_payload["session_id"])

        first_step = self.client.post(
            "/step",
            json={
                "session_id": first_payload["session_id"],
                "action": {"action_type": "transport", "robot_id": "m_1", "job_id": "job_1"},
            },
        )
        second_step = self.client.post(
            "/step",
            json={
                "session_id": second_payload["session_id"],
                "action": {"action_type": "wait", "robot_id": None, "job_id": None},
            },
        )

        self.assertTrue(first_step.json()["state"]["jobs"][0]["transported"])
        self.assertFalse(second_step.json()["state"]["jobs"][0]["transported"])

    def test_step_rejects_malformed_actions(self):
        reset_response = self.client.post("/reset", json={"task": "easy"})
        session_id = reset_response.json()["session_id"]

        response = self.client.post(
            "/step",
            json={"session_id": session_id, "action": {"action_type": "transport", "robot_id": "m_1"}},
        )

        self.assertEqual(response.status_code, 422)

    def test_state_endpoint_returns_current_session_state(self):
        reset_response = self.client.post("/reset", json={"task": "easy"})
        session_id = reset_response.json()["session_id"]

        state_response = self.client.get("/state", params={"session_id": session_id})

        self.assertEqual(state_response.status_code, 200)
        payload = state_response.json()
        self.assertEqual(payload["session_id"], session_id)
        self.assertEqual(payload["task"], "easy")


if __name__ == "__main__":
    unittest.main()
