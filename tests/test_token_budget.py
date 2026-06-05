from skill_deployment.token_budget import check_token_budget, estimate_tokens


def test_estimate_tokens_counts_words_and_punctuation() -> None:
    assert estimate_tokens("R005: response envelope, request_id.") >= 5


def test_check_token_budget_flags_over_budget() -> None:
    result = check_token_budget("one two three four", token_budget=3)

    assert result.over_budget is True
    assert result.remaining_tokens < 0

