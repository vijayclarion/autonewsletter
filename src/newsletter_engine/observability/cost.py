"""Token accounting and cost computation from config/models.yaml pricing (FR-024)."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ModelUsage:
    input_tokens: int = 0
    output_tokens: int = 0
    calls: int = 0


@dataclass
class CostTracker:
    """Accumulates per-model token usage; pricing is per 1M tokens."""

    pricing: dict[str, dict[str, float]]
    usage: dict[str, ModelUsage] = field(default_factory=dict)

    def record(self, model: str, input_tokens: int, output_tokens: int) -> None:
        entry = self.usage.setdefault(model, ModelUsage())
        entry.input_tokens += input_tokens
        entry.output_tokens += output_tokens
        entry.calls += 1

    def cost_for(self, model: str) -> float:
        price = self.pricing.get(model)
        if price is None:
            return 0.0
        entry = self.usage.get(model, ModelUsage())
        return (
            entry.input_tokens * price.get("input", 0.0)
            + entry.output_tokens * price.get("output", 0.0)
        ) / 1_000_000

    def summary(self) -> dict:
        models = {
            model: {
                "calls": entry.calls,
                "input_tokens": entry.input_tokens,
                "output_tokens": entry.output_tokens,
                "cost_usd": round(self.cost_for(model), 6),
            }
            for model, entry in self.usage.items()
        }
        return {
            "models": models,
            "total_cost_usd": round(sum(m["cost_usd"] for m in models.values()), 6),
        }
