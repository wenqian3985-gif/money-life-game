import math
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from game_engine import (  # noqa: E402
    ASSET_KEYS,
    career_probability,
    choose_career,
    create_new_game,
    next_checkpoint_age,
    play_period,
    total_assets,
    validate_state,
    years_to_double,
)


DEFAULT_ALLOCATION = {"cash": 25, "bond": 20, "index": 45, "stock": 10, "challenge": 0}


def _option_for(state):
    from game_engine import current_event

    return current_event(state)["options"][1]["key"]


def _play_until_career(state):
    while state["age"] < state["social_age"]:
        state = play_period(state, DEFAULT_ALLOCATION, True, _option_for(state), 0, 10)
    return state


def _play_to_end(seed=1234):
    state = create_new_game("テスト", start_age=7, social_age=22, seed=seed)
    while not state["ended"]:
        if state["career_pending"]:
            state = choose_career(state, "programmer")
        else:
            state = play_period(state, DEFAULT_ALLOCATION, True, _option_for(state), 0, 10)
    return state


@pytest.mark.parametrize("age", [0, 7, 17])
def test_real_child_start_age_is_preserved(age):
    state = create_new_game("こども", start_age=age, social_age=22, seed=1)
    assert state["age"] == age
    assert state["history"][0]["age"] == age


def test_invalid_ages_are_rejected():
    with pytest.raises(ValueError):
        create_new_game("テスト", start_age=18)
    with pytest.raises(ValueError):
        create_new_game("テスト", social_age=17)


def test_rule_of_72():
    assert years_to_double(7.2) == 10


def test_checkpoint_stops_at_age_18_and_social_entry():
    state = create_new_game("テスト", start_age=16, social_age=22, seed=2)
    assert next_checkpoint_age(state) == 18
    state = play_period(state, DEFAULT_ALLOCATION, True, _option_for(state), 0)
    assert next_checkpoint_age(state) == 22


def test_allocation_must_total_100():
    state = create_new_game("テスト", seed=3)
    bad = dict(DEFAULT_ALLOCATION)
    bad["cash"] = 20
    with pytest.raises(ValueError):
        play_period(state, bad, True, _option_for(state), 0)


def test_minor_nisa_total_never_exceeds_600():
    state = create_new_game("テスト", start_age=0, social_age=22, monthly_contribution_yen=50_000, seed=4)
    while state["age"] < 18:
        state = play_period(state, DEFAULT_ALLOCATION, True, _option_for(state), 0, 0)
    assert 0 <= state["minor_nisa_total"] <= 600


def test_learning_raises_game_career_probability():
    state = create_new_game("テスト", start_age=7, social_age=22, seed=5)
    before = career_probability(state, "doctor")
    state = _play_until_career(state)
    after = career_probability(state, "doctor")
    assert after > before


def test_game_is_deterministic_and_has_yearly_history():
    first = _play_to_end(seed=2027)
    second = _play_to_end(seed=2027)
    assert first["history"] == second["history"]
    assert first["career_result"] == second["career_result"]
    assert len(first["history"]) == 65 - 7 + 1


def test_game_reaches_ending_with_valid_numbers():
    state = _play_to_end()
    assert state["ended"] is True
    assert state["age"] == 65
    assert validate_state(state)
    assert math.isfinite(total_assets(state))
    assert set(ASSET_KEYS).issubset(state["history"][-1])


def test_rebalancing_is_recorded_in_reasons():
    state = create_new_game("テスト", start_age=10, social_age=22, seed=7)
    state["cash"] = 100
    result = play_period(state, DEFAULT_ALLOCATION, True, _option_for(state), 0)
    assert len(result["last_result"]["breakdown"]) == len(ASSET_KEYS)
    assert any(abs(row["配分調整"]) > 0 for row in result["last_result"]["breakdown"])
