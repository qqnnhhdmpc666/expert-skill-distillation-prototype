from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class TokenBudgetResult:
    token_count: int
    token_budget: int
    over_budget: bool
    remaining_tokens: int


def estimate_tokens(text: str) -> int:
    """Small deterministic token proxy used for local budget comparisons."""

    return len(re.findall(r"\w+|[^\w\s]", text, flags=re.UNICODE))


def check_token_budget(text: str, token_budget: int) -> TokenBudgetResult:
    token_count = estimate_tokens(text)
    return TokenBudgetResult(
        token_count=token_count,
        token_budget=token_budget,
        over_budget=token_count > token_budget,
        remaining_tokens=token_budget - token_count,
    )

