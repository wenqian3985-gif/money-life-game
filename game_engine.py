"""Pure simulation logic for Future Money Quest.

Money values use units of 10,000 Japanese yen (万円). The model is intentionally
simple and educational; it is not an investment or employment forecast.
"""

from __future__ import annotations

import copy
import math
import random
import secrets
from typing import Any

from content import CAREERS, PRODUCTS, QUIZZES, career_by_key, event_for_age


ASSET_KEYS = tuple(PRODUCTS)
END_AGE = 65
MINOR_NISA_ANNUAL_LIMIT = 60.0
MINOR_NISA_TOTAL_LIMIT = 600.0
DEBT_RATE = 0.04
INFLATION_RATE = 0.02
BUDGET_KEYS = (
    "rent",
    "utilities",
    "communications",
    "food",
    "social",
    "transport",
    "investment",
)


def _rng(seed: int, marker: int, label: str) -> random.Random:
    return random.Random(f"{seed}:{marker}:{label}")


def _asset_snapshot(state: dict[str, Any]) -> dict[str, float]:
    return {key: float(state[key]) for key in ASSET_KEYS}


def _history_row(state: dict[str, Any], age: int) -> dict[str, Any]:
    row = {"age": age, "debt": round(state["debt"], 2)}
    row.update({key: round(state[key], 2) for key in ASSET_KEYS})
    row["total_assets"] = round(total_assets(state), 2)
    return row


def create_new_game(
    player_name: str,
    start_age: int = 11,
    social_age: int = 22,
    monthly_contribution_yen: int = 10_000,
    difficulty: str = "小学校高学年",
    seed: int | None = None,
) -> dict[str, Any]:
    """Create a new game using the child's real age."""
    if not 0 <= start_age <= 17:
        raise ValueError("Start age must be between 0 and 17.")
    if not 18 <= social_age <= 30:
        raise ValueError("Social-entry age must be between 18 and 30.")
    if not 0 <= monthly_contribution_yen <= 50_000:
        raise ValueError("Monthly contribution must be 0 to 50,000 yen.")

    actual_seed = seed if seed is not None else secrets.randbelow(10_000_000)
    state: dict[str, Any] = {
        "player_name": player_name.strip() or "プレイヤー",
        "difficulty": difficulty,
        "seed": actual_seed,
        "start_age": start_age,
        "social_age": social_age,
        "monthly_contribution_yen": monthly_contribution_yen,
        "household_budget": None,
        "age": start_age,
        "turn": 0,
        "cash": 10.0,
        "bond": 0.0,
        "index": 0.0,
        "stock": 0.0,
        "challenge": 0.0,
        "debt": 0.0,
        "happiness": 50,
        "knowledge": 0,
        "preparation": 0.0,
        "profession": None,
        "career_pending": False,
        "career_result": None,
        "minor_nisa_total": 0.0,
        "inflation_factor": 1.0,
        "target_allocation": {"cash": 25, "bond": 20, "index": 45, "stock": 10, "challenge": 0},
        "rebalance": True,
        "history": [],
        "reason_history": [],
        "last_result": None,
        "ended": False,
    }
    state["history"].append(_history_row(state, start_age))
    return state


def total_assets(state: dict[str, Any]) -> float:
    return sum(float(state[key]) for key in ASSET_KEYS) - float(state["debt"])


def real_net_worth(state: dict[str, Any]) -> float:
    return total_assets(state) / float(state["inflation_factor"])


def years_to_double(rate_percent: float) -> float:
    if rate_percent <= 0:
        raise ValueError("Rate must be greater than zero.")
    return 72 / rate_percent


def current_quiz(state: dict[str, Any]) -> dict[str, Any]:
    return QUIZZES[state["turn"] % len(QUIZZES)]


def current_event(state: dict[str, Any]) -> dict[str, Any]:
    return event_for_age(state["age"])


def next_checkpoint_age(state: dict[str, Any]) -> int:
    """Advance at most five years, stopping at important milestones."""
    age = int(state["age"])
    target = min(END_AGE, age + 5)
    for milestone in (18, int(state["social_age"]), END_AGE):
        if age < milestone < target:
            target = milestone
    return target


def annual_salary(state: dict[str, Any]) -> float:
    profession = state.get("profession")
    if not profession or state["age"] < state["social_age"]:
        return 0.0
    years = max(0, state["age"] - state["social_age"])
    return float(profession["salary"]) * (1.018**years)


def _salary_income_deduction(gross_salary: float) -> float:
    """2026 learning-model salary deduction, in 万円."""
    if gross_salary <= 190:
        return 65.0
    if gross_salary <= 360:
        return gross_salary * 0.30 + 8
    if gross_salary <= 660:
        return gross_salary * 0.20 + 44
    if gross_salary <= 850:
        return gross_salary * 0.10 + 110
    return 195.0


def _basic_income_deduction(total_income: float) -> float:
    """Simplified 2026 basic deduction bands, in 万円."""
    if total_income <= 132:
        return 95.0
    if total_income <= 336:
        return 88.0
    if total_income <= 489:
        return 68.0
    if total_income <= 655:
        return 63.0
    if total_income <= 2350:
        return 58.0
    if total_income <= 2400:
        return 48.0
    if total_income <= 2450:
        return 32.0
    if total_income <= 2500:
        return 16.0
    return 0.0


def _progressive_income_tax(taxable_income: float) -> float:
    """Japanese national income-tax quick table, in 万円."""
    if taxable_income <= 0:
        return 0.0
    brackets = (
        (195, 0.05, 0.0),
        (330, 0.10, 9.75),
        (695, 0.20, 42.75),
        (900, 0.23, 63.60),
        (1800, 0.33, 153.60),
        (4000, 0.40, 279.60),
        (math.inf, 0.45, 479.60),
    )
    for ceiling, rate, deduction in brackets:
        if taxable_income <= ceiling:
            return max(0.0, taxable_income * rate - deduction)
    raise AssertionError("Income-tax bracket was not found.")


def estimate_take_home(gross_salary: float, age: int = 22) -> dict[str, float | int]:
    """Estimate annual deductions and monthly take-home for learning purposes.

    Values are simplified and assume a single salaried employee in Tokyo with no
    dependants. Annual money fields use 万円; the monthly take-home uses 円.
    """
    gross = max(0.0, float(gross_salary))
    employee_social_rate = 0.04925 + 0.0915 + 0.00115 + 0.005
    if 40 <= age <= 64:
        employee_social_rate += 0.0081
    social_insurance = gross * employee_social_rate

    employment_income = max(0.0, gross - _salary_income_deduction(gross))
    taxable_income = max(
        0.0,
        employment_income
        - social_insurance
        - _basic_income_deduction(employment_income),
    )
    income_tax = _progressive_income_tax(taxable_income) * 1.021
    resident_taxable = max(0.0, employment_income - social_insurance - 43.0)
    resident_tax = resident_taxable * 0.10 + (0.5 if resident_taxable > 0 else 0.0)
    take_home = max(0.0, gross - social_insurance - income_tax - resident_tax)
    return {
        "gross_salary": round(gross, 1),
        "social_insurance": round(social_insurance, 1),
        "income_tax": round(income_tax, 1),
        "resident_tax": round(resident_tax, 1),
        "annual_take_home": round(take_home, 1),
        "monthly_take_home_yen": int(round(take_home * 10_000 / 12 / 1000) * 1000),
    }


def default_household_budget(monthly_take_home_yen: int) -> dict[str, int]:
    """Return a balanced editable monthly budget rounded to 1,000 yen."""
    ratios = {
        "rent": 0.28,
        "utilities": 0.05,
        "communications": 0.03,
        "food": 0.14,
        "social": 0.08,
        "transport": 0.05,
        "investment": 0.10,
    }
    return {
        key: int(round(monthly_take_home_yen * ratio / 1000) * 1000)
        for key, ratio in ratios.items()
    }


def max_monthly_investment_yen(state: dict[str, Any]) -> int:
    """Return take-home remaining after the six non-investment budget items."""
    if not state.get("profession"):
        return 50_000
    take_home = int(
        estimate_take_home(annual_salary(state), int(state["age"]))[
            "monthly_take_home_yen"
        ]
    )
    budget = state.get("household_budget") or {}
    fixed_costs = sum(int(budget.get(key, 0)) for key in BUDGET_KEYS if key != "investment")
    return max(0, take_home - fixed_costs)


def set_household_budget(
    state: dict[str, Any], budget: dict[str, int]
) -> dict[str, Any]:
    """Save the adult monthly budget after validating it against take-home pay."""
    if not state.get("profession"):
        raise ValueError("Choose a career before setting an adult budget.")
    if set(budget) != set(BUDGET_KEYS):
        raise ValueError("Budget must contain every expense category.")
    clean_budget = {key: int(value) for key, value in budget.items()}
    if any(value < 0 for value in clean_budget.values()):
        raise ValueError("Budget values cannot be negative.")
    take_home = int(
        estimate_take_home(annual_salary(state), int(state["age"]))[
            "monthly_take_home_yen"
        ]
    )
    if sum(clean_budget.values()) > take_home:
        raise ValueError("Monthly spending cannot exceed monthly take-home pay.")

    new_state = copy.deepcopy(state)
    new_state["household_budget"] = clean_budget
    new_state["monthly_contribution_yen"] = clean_budget["investment"]
    return new_state


def career_probability(state: dict[str, Any], career_key: str) -> int:
    """Return a learning-game probability, not a real employment statistic."""
    career = career_by_key(career_key)
    bonus = state["preparation"] * 0.7 + state["knowledge"] * 0.12
    return int(min(90, round(career["probability"] + bonus)))


def choose_career(state: dict[str, Any], career_key: str) -> dict[str, Any]:
    """Resolve the chosen dream career deterministically from the game seed."""
    if state["age"] < state["social_age"]:
        raise ValueError("Career selection is not available yet.")
    if state.get("profession"):
        raise ValueError("Career has already been selected.")

    new_state = copy.deepcopy(state)
    career = copy.deepcopy(career_by_key(career_key))
    probability = career_probability(new_state, career_key)
    roll = _rng(new_state["seed"], new_state["social_age"], career_key).randint(1, 100)
    achieved = roll <= probability
    if achieved:
        profession = career
        message = f"夢への準備が実った！ {career['name']}としてスタート。"
    else:
        profession = copy.deepcopy(career)
        profession["name"] = f"{career['name']}につながる見習い"
        profession["salary"] = round(career["salary"] * 0.75)
        message = "今回は直行ルートではなかったけれど、関連する仕事から夢に近づく道を選んだよ。"

    new_state["profession"] = profession
    new_state["career_pending"] = False
    new_state["career_result"] = {
        "dream": career["name"],
        "achieved": achieved,
        "probability": probability,
        "roll": roll,
        "message": message,
    }
    return new_state


def _year_rates(seed: int, age: int) -> dict[str, float]:
    """Generate a plausible but fictional market year."""
    choices = {
        "cash": ([0.001, 0.002, 0.004], [30, 50, 20]),
        "bond": ([-0.06, -0.02, 0.01, 0.03, 0.05, 0.07], [8, 12, 25, 30, 18, 7]),
        "index": ([-0.25, -0.12, -0.04, 0.05, 0.09, 0.14, 0.22], [5, 10, 12, 20, 25, 20, 8]),
        "stock": ([-0.40, -0.22, -0.08, 0.08, 0.18, 0.30, 0.45], [8, 12, 13, 20, 22, 17, 8]),
        "challenge": ([-0.65, -0.35, -0.12, 0.10, 0.35, 0.70], [12, 18, 18, 20, 20, 12]),
    }
    rates = {}
    for key, (values, weights) in choices.items():
        rates[key] = _rng(seed, age, key).choices(values, weights=weights, k=1)[0]
    return rates


def _pay_event(state: dict[str, Any], cost: float) -> tuple[float, float]:
    paid = min(float(state["cash"]), max(0.0, cost))
    state["cash"] -= paid
    borrowed = max(0.0, cost - paid)
    state["debt"] += borrowed
    return paid, borrowed


def play_period(
    state: dict[str, Any],
    allocation: dict[str, int],
    rebalance: bool,
    event_option_key: str,
    quiz_answer_index: int,
    learning_percent: int = 10,
    monthly_investment_yen: int | None = None,
) -> dict[str, Any]:
    """Simulate every year until the next five-year or milestone checkpoint."""
    if state["ended"]:
        raise ValueError("The game has already ended.")
    if state.get("career_pending"):
        raise ValueError("Choose a career before continuing.")
    if set(allocation) != set(ASSET_KEYS) or sum(allocation.values()) != 100:
        raise ValueError("Allocation must contain all products and total 100%.")
    if any(not 0 <= value <= 100 for value in allocation.values()):
        raise ValueError("Allocation percentages must be between 0 and 100.")
    if not 0 <= learning_percent <= 30:
        raise ValueError("Learning percent must be between 0 and 30.")

    monthly_investment = (
        int(state["monthly_contribution_yen"])
        if monthly_investment_yen is None
        else int(monthly_investment_yen)
    )
    if monthly_investment < 0:
        raise ValueError("Monthly investment cannot be negative.")
    if state.get("profession") and state.get("household_budget"):
        if monthly_investment > max_monthly_investment_yen(state):
            raise ValueError("Monthly investment exceeds take-home pay after living costs.")
    elif monthly_investment > 50_000:
        raise ValueError("Pre-career monthly investment must be 0 to 50,000 yen.")

    new_state = copy.deepcopy(state)
    new_state["monthly_contribution_yen"] = monthly_investment
    start_age = int(new_state["age"])
    target_age = next_checkpoint_age(new_state)
    event = current_event(new_state)
    option = next((item for item in event["options"] if item["key"] == event_option_key), None)
    if option is None:
        raise ValueError("Unknown event option.")

    before = _asset_snapshot(new_state)
    contributions = {key: 0.0 for key in ASSET_KEYS}
    rebalance_deltas = {key: 0.0 for key in ASSET_KEYS}
    market_changes = {key: 0.0 for key in ASSET_KEYS}
    event_changes = {key: 0.0 for key in ASSET_KEYS}

    paid, borrowed = _pay_event(new_state, float(option.get("cost", 0)))
    event_changes["cash"] -= paid
    new_state["debt"] += float(option.get("debt", 0))
    new_state["happiness"] += int(option.get("happiness", 0))
    new_state["knowledge"] += int(option.get("knowledge", 0))

    quiz = current_quiz(new_state)
    quiz_correct = quiz_answer_index == quiz["correct"]
    new_state["knowledge"] += 6 if quiz_correct else 2
    total_learning_spend = 0.0
    nisa_added = 0.0
    yearly_rates: list[dict[str, float]] = []

    for age in range(start_age, target_age):
        planned = monthly_investment * 12 / 10_000

        school_year = age < new_state["social_age"]
        learning_spend = planned * learning_percent / 100 if school_year else 0.0
        financial_contribution = max(0.0, planned - learning_spend)
        total_learning_spend += learning_spend
        if school_year:
            new_state["preparation"] = min(
                50.0,
                new_state["preparation"] + learning_percent / 10 + learning_spend / 20,
            )

        allocated = {
            key: financial_contribution * allocation[key] / 100 for key in ASSET_KEYS
        }
        for key in ASSET_KEYS:
            new_state[key] += allocated[key]
            contributions[key] += allocated[key]

        if rebalance:
            pool = sum(new_state[key] for key in ASSET_KEYS)
            for key in ASSET_KEYS:
                target_value = pool * allocation[key] / 100
                delta = target_value - new_state[key]
                new_state[key] = target_value
                rebalance_deltas[key] += delta

        if age < 18:
            eligible_ratio = (allocation["bond"] + allocation["index"]) / 100
            eligible_amount = min(financial_contribution * eligible_ratio, MINOR_NISA_ANNUAL_LIMIT)
            remaining = max(0.0, MINOR_NISA_TOTAL_LIMIT - new_state["minor_nisa_total"])
            used = min(eligible_amount, remaining)
            new_state["minor_nisa_total"] += used
            nisa_added += used

        rates = _year_rates(new_state["seed"], age)
        yearly_rates.append(rates)
        for key in ASSET_KEYS:
            old_value = new_state[key]
            new_state[key] = max(0.0, old_value * (1 + rates[key]))
            market_changes[key] += new_state[key] - old_value

        new_state["debt"] *= 1 + DEBT_RATE
        new_state["inflation_factor"] *= 1 + INFLATION_RATE
        new_state["age"] = age + 1
        new_state["history"].append(_history_row(new_state, age + 1))

    new_state["target_allocation"] = dict(allocation)
    new_state["rebalance"] = bool(rebalance)
    if new_state.get("household_budget"):
        new_state["household_budget"]["investment"] = monthly_investment
    new_state["happiness"] = max(0, min(100, new_state["happiness"]))
    new_state["knowledge"] = max(0, min(100, new_state["knowledge"]))
    new_state["turn"] += 1
    new_state["career_pending"] = (
        new_state["age"] >= new_state["social_age"] and new_state.get("profession") is None
    )
    new_state["ended"] = new_state["age"] >= END_AGE

    breakdown = []
    for key in ASSET_KEYS:
        average_rate = sum(item[key] for item in yearly_rates) / max(1, len(yearly_rates))
        parts = [f"積立 {contributions[key]:+.1f}万円"]
        if abs(rebalance_deltas[key]) >= 0.05:
            parts.append(f"配分調整 {rebalance_deltas[key]:+.1f}万円")
        if key == "cash" and event_changes[key]:
            parts.append(f"イベント {event_changes[key]:+.1f}万円")
        parts.append(f"値動き {market_changes[key]:+.1f}万円（年平均 {average_rate * 100:+.1f}%）")
        breakdown.append(
            {
                "商品": f"{PRODUCTS[key]['emoji']} {PRODUCTS[key]['name']}",
                "開始": round(before[key], 1),
                "積立": round(contributions[key], 1),
                "配分調整": round(rebalance_deltas[key], 1),
                "値動き": round(market_changes[key], 1),
                "終了": round(new_state[key], 1),
                "増減の理由": " / ".join(parts),
            }
        )

    result = {
        "age_range": f"{start_age}歳→{target_age}歳",
        "event_title": event["title"],
        "event_choice": option["label"],
        "lesson": option["lesson"],
        "event_cost": float(option.get("cost", 0)),
        "event_borrowed": borrowed + float(option.get("debt", 0)),
        "quiz_correct": quiz_correct,
        "quiz_explanation": quiz["explanation"],
        "learning_spend": round(total_learning_spend, 1),
        "monthly_investment_yen": monthly_investment,
        "nisa_added": round(nisa_added, 1),
        "breakdown": breakdown,
    }
    new_state["last_result"] = result
    new_state["reason_history"].extend(
        [{"期間": result["age_range"], **item} for item in breakdown]
    )
    return new_state


def ending_profile(state: dict[str, Any]) -> dict[str, str]:
    if not state["ended"]:
        raise ValueError("The ending is only available after the game ends.")
    if state["debt"] > max(30, total_assets(state) * 0.25):
        return {"title": "立て直しチャレンジャー", "emoji": "🧭", "message": "挑戦の経験は十分。次は借金と予備の現金のバランスを見直そう。"}
    if state["knowledge"] >= 55 and state["happiness"] >= 60:
        return {"title": "しなやか冒険家", "emoji": "🌈", "message": "守る・育てる・楽しむ・学ぶを、自分で考えて組み合わせられたね。"}
    risky = state["stock"] + state["challenge"]
    steady = state["cash"] + state["bond"] + state["index"]
    if risky > steady:
        return {"title": "大胆な航海士", "emoji": "⛵", "message": "大きな波を体験したね。現金と分散も足すと、航海を続けやすくなるよ。"}
    return {"title": "未来を育てる設計士", "emoji": "🌳", "message": "小さなお金と学びを、時間を味方につけて育てたね。"}


def validate_state(state: dict[str, Any]) -> bool:
    numeric_keys = [*ASSET_KEYS, "debt", "inflation_factor", "minor_nisa_total"]
    return all(math.isfinite(float(state[key])) and float(state[key]) >= 0 for key in numeric_keys)


def career_names() -> list[str]:
    return [item["name"] for item in CAREERS]
