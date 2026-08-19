"""Pure game logic for Future Money Quest.

All monetary values are expressed in units of 10,000 Japanese yen (万円).
The simulation is educational, deliberately simplified, and not a forecast.
"""

from __future__ import annotations

import copy
import math
import random
import secrets
from typing import Any

from content import LIFE_STAGES, PROFESSIONS, QUIZZES, STRATEGIES


CASH_RATE = 0.002
INFLATION_RATE = 0.02
DEBT_RATE = 0.04


def _rng(seed: int, turn: int, label: str) -> random.Random:
    return random.Random(f"{seed}:{turn}:{label}")


def create_new_game(
    player_name: str,
    difficulty: str = "小学校高学年",
    seed: int | None = None,
) -> dict[str, Any]:
    """Create a deterministic game state from a seed."""
    actual_seed = seed if seed is not None else secrets.randbelow(10_000_000)
    profession = copy.deepcopy(_rng(actual_seed, 0, "career").choice(PROFESSIONS))
    return {
        "player_name": player_name.strip() or "プレイヤー",
        "difficulty": difficulty,
        "seed": actual_seed,
        "profession": profession,
        "turn": 0,
        "age": LIFE_STAGES[0]["age"],
        "cash": 50.0,
        "index": 0.0,
        "stock": 0.0,
        "challenge": 0.0,
        "debt": 0.0,
        "skill": 50,
        "happiness": 50,
        "knowledge": 0,
        "insurance": 0,
        "budget_modifier": 0.0,
        "inflation_factor": 1.0,
        "baseline_cash": 50.0,
        "history": [],
        "last_result": None,
        "ended": False,
    }


def total_assets(state: dict[str, Any]) -> float:
    return state["cash"] + state["index"] + state["stock"] + state["challenge"] - state["debt"]


def real_net_worth(state: dict[str, Any]) -> float:
    return total_assets(state) / state["inflation_factor"]


def current_stage(state: dict[str, Any]) -> dict[str, Any]:
    if state["ended"]:
        raise ValueError("The game has already ended.")
    return LIFE_STAGES[state["turn"]]


def current_quiz(state: dict[str, Any]) -> dict[str, Any]:
    return QUIZZES[state["turn"]]


def annual_salary(state: dict[str, Any]) -> float:
    profession = state["profession"]
    experience_growth = (1 + profession["growth"]) ** state["turn"]
    skill_bonus = max(0, state["skill"] - 50) * 1.8
    return profession["salary"] * experience_growth + skill_bonus


def available_budget(state: dict[str, Any]) -> float:
    """Simplified free cash generated during the current life stage."""
    stage = current_stage(state)
    years = stage["next_age"] - stage["age"]
    free_per_year = max(20.0, annual_salary(state) - stage["living_cost"])
    budget = free_per_year * years * 0.25
    return max(30.0, budget * (1 + state["budget_modifier"]))


def years_to_double(rate_percent: float) -> float:
    if rate_percent <= 0:
        raise ValueError("Rate must be greater than zero.")
    return 72 / rate_percent


def _weighted_choice(rng: random.Random, values: list[float], weights: list[int]) -> float:
    return rng.choices(values, weights=weights, k=1)[0]


def _market_outcomes(state: dict[str, Any], years: int) -> dict[str, float]:
    turn = state["turn"]
    seed = state["seed"]

    index_rate = _weighted_choice(
        _rng(seed, turn, "index"),
        [-0.10, -0.04, 0.02, 0.05, 0.07, 0.09, 0.12],
        [3, 6, 10, 20, 27, 22, 12],
    )
    stock_rate = _weighted_choice(
        _rng(seed, turn, "stock"),
        [-0.30, -0.15, -0.05, 0.08, 0.18, 0.35],
        [10, 15, 15, 25, 22, 13],
    )
    challenge_multiplier = _weighted_choice(
        _rng(seed, turn, "challenge"),
        [0.0, 0.2, 0.5, 1.0, 2.5, 5.0],
        [12, 18, 20, 20, 20, 10],
    )

    return {
        "cash_multiplier": (1 + CASH_RATE) ** years,
        "index_multiplier": min(4.0, max(0.0, (1 + index_rate) ** years)),
        "stock_multiplier": min(12.0, max(0.0, (1 + stock_rate) ** years)),
        "challenge_multiplier": challenge_multiplier,
        "index_rate": index_rate,
        "stock_rate": stock_rate,
    }


def _pay(state: dict[str, Any], amount: float) -> float:
    """Pay from cash first and borrow any shortage. Return new borrowing."""
    if amount <= 0:
        return 0.0
    paid_from_cash = min(state["cash"], amount)
    state["cash"] -= paid_from_cash
    borrowed = amount - paid_from_cash
    state["debt"] += borrowed
    return borrowed


def _apply_effect(state: dict[str, Any], effect: dict[str, Any]) -> dict[str, float]:
    cost = float(effect.get("cost", 0))
    original_cost = cost
    if effect.get("insurable"):
        coverage = {0: 0.0, 1: 0.60, 2: 0.85}.get(state["insurance"], 0.0)
        cost *= 1 - coverage

    borrowed = _pay(state, cost)
    state["happiness"] += int(effect.get("happiness", 0))
    state["knowledge"] += int(effect.get("knowledge", 0))
    state["skill"] += int(effect.get("skill", 0))
    if "insurance" in effect:
        state["insurance"] = int(effect["insurance"])
    state["budget_modifier"] += float(effect.get("budget_modifier", 0))
    return {"original_cost": original_cost, "actual_cost": cost, "borrowed": borrowed}


def play_turn(
    state: dict[str, Any],
    strategy_key: str,
    event_option_key: str,
    quiz_answer_index: int,
) -> dict[str, Any]:
    """Resolve one life stage and return a new immutable-style state."""
    if state["ended"]:
        raise ValueError("The game has already ended.")
    if strategy_key not in STRATEGIES:
        raise ValueError("Unknown strategy.")

    new_state = copy.deepcopy(state)
    stage = current_stage(new_state)
    quiz = current_quiz(new_state)
    event = stage["event"]
    option = next((o for o in event["options"] if o["key"] == event_option_key), None)
    if option is None:
        raise ValueError("Unknown event option.")

    budget = available_budget(new_state)
    event_cost = {"original_cost": 0.0, "actual_cost": 0.0, "borrowed": 0.0}
    if event.get("intro_effect"):
        event_cost = _apply_effect(new_state, event["intro_effect"])
    option_cost = _apply_effect(new_state, option["effect"])

    strategy = STRATEGIES[strategy_key]
    allocation = strategy["allocation"]
    if sum(allocation.values()) != 100:
        raise ValueError("Strategy allocation must total 100%.")

    amounts = {key: budget * percent / 100 for key, percent in allocation.items()}
    new_state["cash"] += amounts["cash"]
    new_state["index"] += amounts["index"]
    new_state["stock"] += amounts["stock"]
    new_state["challenge"] += amounts["challenge"]
    new_state["happiness"] += max(1, round(amounts["enjoy"] / 25))
    if amounts["skill"] > 0:
        new_state["skill"] += min(15, 2 + round(amounts["skill"] / 18))
        new_state["knowledge"] += 2

    quiz_correct = quiz_answer_index == quiz["correct"]
    new_state["knowledge"] += 6 if quiz_correct else 2

    years = stage["next_age"] - stage["age"]
    market = _market_outcomes(new_state, years)
    new_state["cash"] *= market["cash_multiplier"]
    new_state["index"] *= market["index_multiplier"]
    new_state["stock"] *= market["stock_multiplier"]
    new_state["challenge"] *= market["challenge_multiplier"]
    new_state["debt"] *= (1 + DEBT_RATE) ** years
    new_state["inflation_factor"] *= (1 + INFLATION_RATE) ** years

    # Reference path: the same investable money is kept as low-interest cash.
    reference_contribution = amounts["cash"] + amounts["index"] + amounts["stock"] + amounts["challenge"]
    reference_cost = event_cost["actual_cost"] + option_cost["actual_cost"]
    new_state["baseline_cash"] = max(0.0, new_state["baseline_cash"] - reference_cost)
    new_state["baseline_cash"] = (new_state["baseline_cash"] + reference_contribution) * market["cash_multiplier"]

    new_state["happiness"] = max(0, min(100, new_state["happiness"]))
    new_state["knowledge"] = max(0, min(100, new_state["knowledge"]))
    new_state["skill"] = max(0, min(100, new_state["skill"]))
    new_state["age"] = stage["next_age"]

    history_item = {
        "age": stage["next_age"],
        "stage": stage["label"],
        "strategy": strategy["name"],
        "event_choice": option["label"],
        "total_assets": round(total_assets(new_state), 2),
        "real_assets": round(real_net_worth(new_state), 2),
        "cash": round(new_state["cash"], 2),
        "index": round(new_state["index"], 2),
        "stock": round(new_state["stock"], 2),
        "challenge": round(new_state["challenge"], 2),
        "debt": round(new_state["debt"], 2),
        "happiness": new_state["happiness"],
        "knowledge": new_state["knowledge"],
    }
    new_state["history"].append(history_item)

    result = {
        "stage": stage["label"],
        "choice_lesson": option["lesson"],
        "quiz_correct": quiz_correct,
        "quiz_explanation": quiz["explanation"],
        "budget": budget,
        "amounts": amounts,
        "event_cost": event_cost,
        "option_cost": option_cost,
        "market": market,
        "years": years,
        "history": history_item,
    }
    new_state["last_result"] = result
    new_state["turn"] += 1
    new_state["ended"] = new_state["turn"] >= len(LIFE_STAGES)
    return new_state


def ending_profile(state: dict[str, Any]) -> dict[str, str]:
    """Return a qualitative ending that does not rank wealth alone."""
    if not state["ended"]:
        raise ValueError("The ending is only available after the game ends.")

    net = total_assets(state)
    liquidity_ratio = state["cash"] / max(1, state["cash"] + state["index"] + state["stock"] + state["challenge"])
    if state["debt"] > net * 0.25:
        return {
            "title": "立て直しチャレンジャー",
            "emoji": "🧭",
            "message": "挑戦の経験は十分。次は借金と緊急予備費のバランスを見直すと、冒険を続けやすくなります。",
        }
    if state["knowledge"] >= 45 and state["happiness"] >= 60:
        return {
            "title": "しなやか冒険家",
            "emoji": "🌈",
            "message": "お金を守りながら、学びと楽しみにも使えました。資産は人生の目的ではなく、選択肢を増やす道具です。",
        }
    if liquidity_ratio >= 0.55:
        return {
            "title": "堅実な守り人",
            "emoji": "🛡️",
            "message": "予想外への強さが光ります。長い時間を味方につける投資も組み合わせると、未来の幅が広がります。",
        }
    if state["challenge"] + state["stock"] > state["cash"] + state["index"]:
        return {
            "title": "大胆な航海士",
            "emoji": "⛵",
            "message": "大きな波に乗る力があります。現金と分散を少し足すと、嵐の中でも航海を続けやすくなります。",
        }
    return {
        "title": "未来を育てる設計士",
        "emoji": "🌳",
        "message": "使う・守る・育てるを組み合わせました。早く始めた小さなお金が、時間とともに大きな木になりました。",
    }


def validate_state(state: dict[str, Any]) -> bool:
    numeric_keys = ["cash", "index", "stock", "challenge", "debt", "inflation_factor"]
    return all(math.isfinite(float(state[key])) and float(state[key]) >= 0 for key in numeric_keys)

