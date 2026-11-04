from noodles.models.recommendations import recommendation_payload


def test_recommendations_are_ranked_and_start_with_small_model() -> None:
    models = recommendation_payload()

    assert [item["rank"] for item in models] == [1, 2, 3, 4, 5, 6]
    assert models[0]["parameters"] == "1.7B"
    assert all(item["suggested_quantization"] == "Q4_K_M" for item in models)


def test_recommendation_payload_returns_independent_values() -> None:
    first = recommendation_payload()
    first[0]["label"] = "changed"

    assert recommendation_payload()[0]["label"] == "Qwen3 1.7B"
