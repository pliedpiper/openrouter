import os
from unittest import mock

import main


def test_load_env_value_reads_from_file(tmp_path, monkeypatch):
    env_path = tmp_path / ".env"
    env_path.write_text(
        """
        # comment
        TEST_KEY = "secret"
        """
    )
    monkeypatch.delenv("TEST_KEY", raising=False)

    value = main.load_env_value("TEST_KEY", env_path=str(env_path))

    assert value == "secret"
    assert os.environ["TEST_KEY"] == "secret"


def test_gather_responses_calls_each_model(monkeypatch):
    sentinel_prompt = "hello world"
    fake_client = mock.Mock()
    expected = {model_id: f"{model_id}:{sentinel_prompt}" for _, model_id in main.MODELS}

    def fake_fetch(client, model_id, prompt):
        assert client is fake_client
        assert prompt == sentinel_prompt
        return expected[model_id]

    with mock.patch("main.fetch_model_response", side_effect=fake_fetch) as patched:
        responses = main.gather_responses(fake_client, sentinel_prompt)

    assert len(responses) == len(main.MODELS)
    for (label, model_id), (resp_label, answer) in zip(main.MODELS, responses):
        assert resp_label == label
        assert answer == expected[model_id]
    assert patched.call_count == len(main.MODELS)


def test_prompt_for_guess_retries_until_valid(monkeypatch):
    selectable = {"1": "alpha", "2": "beta"}
    inputs = iter(["5", "2"])
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))

    choice = main.prompt_for_guess(selectable, 1)

    assert choice == "beta"
