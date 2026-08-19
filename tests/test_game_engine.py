import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from content import LIFE_STAGES, STRATEGIES  # noqa: E402
from game_engine import (  # noqa: E402
    create_new_game,
    play_turn,
    total_assets,
    validate_state,
    years_to_double,
)


def _play_all(seed=1234, strategy="balanced", insurance_choice="simple_insurance"):
    state = create_new_game("テスト", seed=seed)
    for turn, stage in enumerate(LIFE_STAGES):
        if turn == 2:
            option = insurance_choice
        else:
            option = stage["event"]["options"][1]["key"]
        state = play_turn(state, strategy, option, 0)
    return state


def test_allocations_total_100_percent():
    assert all(sum(item["allocation"].values()) == 100 for item in STRATEGIES.values())


def test_rule_of_72():
    assert years_to_double(7.2) == 10


def test_game_is_deterministic_for_same_seed():
    first = _play_all(seed=2026)
    second = _play_all(seed=2026)
    assert first["profession"] == second["profession"]
    assert first["history"] == second["history"]


def test_game_reaches_ending_with_valid_numbers():
    state = _play_all()
    assert state["ended"] is True
    assert state["turn"] == len(LIFE_STAGES)
    assert validate_state(state)
    assert math.isfinite(total_assets(state))


def test_insurance_reduces_emergency_out_of_pocket_cost():
    insured = _play_all(seed=99, insurance_choice="simple_insurance")
    uninsured = _play_all(seed=99, insurance_choice="no_insurance")
    insured_emergency = insured["history"][3]
    uninsured_emergency = uninsured["history"][3]
    assert insured_emergency["debt"] <= uninsured_emergency["debt"]

