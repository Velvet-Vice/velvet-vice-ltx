import unittest

from services.ollama_client import OllamaClient


class OllamaClientTests(unittest.TestCase):
    def test_matches_exact_model_name(self):
        models = [{"name": "example/model:9b"}]
        self.assertTrue(
            OllamaClient.model_is_loaded(models, "example/model:9b")
        )

    def test_matches_model_when_tag_differs(self):
        models = [{"model": "example/model:latest"}]
        self.assertTrue(
            OllamaClient.model_is_loaded(models, "example/model:9b")
        )

    def test_does_not_match_different_model(self):
        models = [{"name": "example/other:9b"}]
        self.assertFalse(
            OllamaClient.model_is_loaded(models, "example/model:9b")
        )

    def test_release_does_not_reload_an_already_unloaded_model(self):
        client = OllamaClient("http://127.0.0.1:11434")
        requests = []

        def request(endpoint, payload=None, timeout=None):
            requests.append((endpoint, payload, timeout))
            return {"models": []}

        client._request_json = request
        client.release_models(["example/model:9b"], 20)
        self.assertEqual(
            [entry[0] for entry in requests],
            ["/api/ps"],
        )

    def test_release_requests_unload_only_for_loaded_model(self):
        client = OllamaClient("http://127.0.0.1:11434")
        responses = iter(
            [
                {"models": [{"name": "example/model:9b"}]},
                {},
                {"models": []},
            ]
        )
        requests = []

        def request(endpoint, payload=None, timeout=None):
            requests.append((endpoint, payload, timeout))
            return next(responses)

        client._request_json = request
        client.release_models(["example/model:9b"], 20)
        self.assertEqual(
            [entry[0] for entry in requests],
            ["/api/ps", "/api/generate", "/api/ps"],
        )
        self.assertEqual(requests[1][1]["keep_alive"], 0)


if __name__ == "__main__":
    unittest.main()
