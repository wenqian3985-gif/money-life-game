import math
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from game_engine import (  # noqa: E402
    ASSET_KEYS,
    BUDGET_KEYS,
    annual_salary,
    career_probability,
    career_salary_at_age,
    choose_career,
    create_new_game,
    current_event,
    default_household_budget,
    estimate_take_home,
    max_monthly_investment_yen,
    next_checkpoint_age,
    play_period,
    set_household_budget,
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


def test_initial_investment_sets_starting_net_worth():
    state = create_new_game("こども", initial_investment_yen=300_000, seed=11)
    assert state["initial_investment_yen"] == 300_000
    assert state["cash"] == 30.0
    assert total_assets(state) == 30.0


def test_invalid_ages_are_rejected():
    with pytest.raises(ValueError):
        create_new_game("テスト", start_age=18)
    with pytest.raises(ValueError):
        create_new_game("テスト", social_age=17)
    with pytest.raises(ValueError):
        create_new_game("テスト", initial_investment_yen=1_010_000)


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


def test_take_home_subtracts_tax_and_social_insurance():
    result = estimate_take_home(579, age=22)
    assert result["gross_salary"] == 579
    assert result["social_insurance"] > 0
    assert result["income_tax"] > 0
    assert result["resident_tax"] > 0
    assert 0 < result["annual_take_home"] < result["gross_salary"]
    assert result["monthly_take_home_yen"] > 0


def test_programmer_uses_first_year_salary_then_age_experience_curve():
    from content import career_by_key

    career = career_by_key("programmer")
    first_year = career_salary_at_age(career, age=22, social_age=22)
    age_37 = career_salary_at_age(career, age=37, social_age=22)
    assert first_year == career["starting_salary"] == 360
    assert age_37 == career["salary"]
    assert estimate_take_home(first_year, age=22)["monthly_take_home_yen"] < 300_000


def test_household_budget_must_fit_take_home():
    state = create_new_game("テスト", start_age=17, social_age=18, seed=55)
    state = play_period(state, DEFAULT_ALLOCATION, True, _option_for(state), 0)
    state = choose_career(state, "programmer")
    take_home = estimate_take_home(total_salary := annual_salary(state), age=18)
    assert total_salary > 0
    budget = default_household_budget(int(take_home["monthly_take_home_yen"]))
    saved = set_household_budget(state, budget)
    assert set(saved["household_budget"]) == set(BUDGET_KEYS)
    assert saved["monthly_contribution_yen"] == budget["investment"]
    assert max_monthly_investment_yen(saved) >= budget["investment"]

    too_large = dict(budget)
    too_large["rent"] = int(take_home["monthly_take_home_yen"])
    with pytest.raises(ValueError):
        set_household_budget(state, too_large)


def test_selected_monthly_investment_controls_adult_contribution():
    state = create_new_game("テスト", start_age=17, social_age=18, seed=56)
    state = play_period(state, DEFAULT_ALLOCATION, True, _option_for(state), 0)
    state = choose_career(state, "programmer")
    take_home = estimate_take_home(annual_salary(state), age=18)
    budget = default_household_budget(int(take_home["monthly_take_home_yen"]))
    state = set_household_budget(state, budget)
    result = play_period(
        state,
        DEFAULT_ALLOCATION,
        False,
        _option_for(state),
        0,
        0,
        20_000,
    )
    assert result["last_result"]["monthly_investment_yen"] == 20_000
    assert math.isclose(
        sum(row["積立"] for row in result["last_result"]["breakdown"]),
        120.0,
        abs_tol=0.2,
    )


def test_initial_lump_sum_uses_same_allocation_once():
    state = create_new_game(
        "テスト",
        start_age=10,
        initial_investment_yen=200_000,
        monthly_contribution_yen=0,
        seed=88,
    )
    no_cost_option = current_event(state)["options"][-1]["key"]
    first = play_period(state, DEFAULT_ALLOCATION, False, no_cost_option, 0, 0, 0)
    allocated = first["last_result"]["initial_allocation"]
    assert {row["商品"] for row in allocated}
    assert math.isclose(sum(row["金額"] for row in allocated), 20.0, abs_tol=0.1)
    assert [row["割合"] for row in allocated] == [25, 20, 45, 10]
    assert first["initial_allocation_done"] is True

    second = play_period(first, DEFAULT_ALLOCATION, False, _option_for(first), 0, 0, 0)
    assert second["last_result"]["initial_allocation"] == []


def test_adult_budget_includes_other_and_can_be_updated_each_step():
    state = create_new_game("テスト", start_age=17, social_age=18, seed=90)
    state = play_period(state, DEFAULT_ALLOCATION, True, _option_for(state), 0)
    state = choose_career(state, "programmer")
    take_home = estimate_take_home(annual_salary(state), age=state["age"])
    budget = default_household_budget(int(take_home["monthly_take_home_yen"]))
    assert "other" in budget
    state = set_household_budget(state, budget)
    state = play_period(state, DEFAULT_ALLOCATION, False, _option_for(state), 0, 0, budget["investment"])

    updated = dict(state["household_budget"])
    updated["other"] += 1_000
    state = set_household_budget(state, updated)
    assert state["household_budget"]["other"] == budget["other"] + 1_000


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


def test_debt_reason_records_shortfall_and_interest():
    state = create_new_game("テスト", start_age=10, initial_investment_yen=0, seed=71)
    costly_option = current_event(state)["options"][0]["key"]
    result = play_period(state, DEFAULT_ALLOCATION, True, costly_option, 0)
    debt = result["last_result"]
    assert debt["debt_borrowed"] == 2.0
    assert debt["debt_interest"] > 0
    assert debt["debt_end"] > debt["debt_borrowed"]
    assert "現金が足りず" in debt["debt_reason"]
    assert "年4%の利息" in debt["debt_reason"]
    assert result["debt_history"][-1]["理由"] == debt["debt_reason"]
