import pytest

from scoreboard import ScoreStore


def make_store(tmp_path) -> ScoreStore:
    return ScoreStore(tmp_path / "scores.db")


def test_record_round_and_summary(tmp_path):
    store = make_store(tmp_path)
    store.record_round("alice", 4, 3)
    store.record_round("alice", 4, 4)

    summary = store.get_player_summary("alice")

    assert summary is not None
    assert summary.rounds_played == 2
    assert summary.total_questions == 8
    assert summary.total_correct == 7
    assert summary.accuracy == pytest.approx(7 / 8)


def test_leaderboard_orders_by_accuracy_then_correct(tmp_path):
    store = make_store(tmp_path)
    store.record_round("alice", 4, 4)  # 100%
    store.record_round("bob", 10, 8)   # 80%
    store.record_round("carol", 5, 5)  # 100%

    leaders = store.leaderboard(limit=2)

    assert [entry.player for entry in leaders] == ["carol", "alice"]
    assert leaders[0].accuracy == pytest.approx(1.0)
    assert leaders[1].accuracy == pytest.approx(1.0)


def test_invalid_scores_raise(tmp_path):
    store = make_store(tmp_path)

    with pytest.raises(ValueError):
        store.record_round("", 1, 1)
    with pytest.raises(ValueError):
        store.record_round("alice", 0, 0)
    with pytest.raises(ValueError):
        store.record_round("alice", 3, 4)
