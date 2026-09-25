"""Deterministic accounting. No IO, provider calls, or floating-point currency."""

from decimal import Decimal

from .models import Estimate, Execution, Price, Scenario

ZERO = Decimal(0)
MILLION = Decimal(1000000)


def selected_rates(price: Price, input_tokens: Decimal):
    rates = {
        "input": price.input,
        "output": price.output,
        "cache_read": price.cache_read,
        "cache_write": price.cache_write,
    }
    for tier in sorted(price.tiers, key=lambda t: t.above):
        if input_tokens > tier.above:
            for key in rates:
                value = getattr(tier, key)
                if value is not None:
                    rates[key] = value
            # A base cached-read price is not evidence for a long-context cached price.
            if tier.cache_read is None:
                rates["cache_read"] = None
            if tier.cache_write is None:
                rates["cache_write"] = None
    return rates


def effective_execution(estimate: Estimate, row) -> Execution:
    return Execution(
        **(estimate.profiles[row.complexity].model_dump() | row.overrides.model_dump(exclude_none=True))
    )


def line_item(estimate: Estimate, row, execution: Execution, scenario: Scenario, step_name: str):
    model_id = scenario.model_id if scenario.model_id is not None else execution.model_id
    volume = row.invocations * scenario.volume_factor
    calls = execution.calls * scenario.calls_factor
    retry = execution.retry_rate * scenario.retry_factor
    input_tokens = execution.input_tokens * scenario.input_factor
    output_tokens = execution.output_tokens * scenario.output_factor
    monthly_calls = Decimal(row.count) * volume * calls * (1 + retry)
    cached_input = input_tokens * execution.cache_fraction
    cache_writes = input_tokens * execution.cache_write_fraction
    uncached_input = input_tokens - cached_input - cache_writes
    price = estimate.prices.get(model_id)
    issues = []
    rates = (
        selected_rates(price, input_tokens)
        if price
        else {"input": None, "output": None, "cache_read": None, "cache_write": None}
    )
    if monthly_calls > 0:
        if price is None:
            issues.append("Select a model with a price snapshot.")
        elif price.unsupported:
            issues.append(
                "Unsupported pricing: " + ", ".join(price.unsupported) + ". Use explicit custom rates."
            )
        else:
            if price.max_input and input_tokens > price.max_input:
                issues.append("Average input exceeds the model input limit.")
            if price.max_output and output_tokens > price.max_output:
                issues.append("Average output exceeds the model output limit.")
        for field, tokens in [
            ("input", uncached_input),
            ("output", output_tokens),
            ("cache_read", cached_input),
            ("cache_write", cache_writes),
        ]:
            if tokens > 0 and rates[field] is None:
                issues.append(f"Missing {field.replace('_', ' ')} price.")
    costs = (
        None
        if issues
        else {
            "input": monthly_calls * uncached_input * (rates["input"] or ZERO) / MILLION,
            "cache": monthly_calls * cached_input * (rates["cache_read"] or ZERO) / MILLION,
            "cache_write": monthly_calls * cache_writes * (rates["cache_write"] or ZERO) / MILLION,
            "output": monthly_calls * output_tokens * (rates["output"] or ZERO) / MILLION,
        }
    )
    return {
        "row_id": row.id,
        "name": row.name,
        "step": step_name,
        "complexity": row.complexity,
        "count": row.count,
        "invocations": volume,
        "calls_per_invocation": calls,
        "retry_rate": retry,
        "input_per_call": input_tokens,
        "output_per_call": output_tokens,
        "cache_fraction": execution.cache_fraction,
        "monthly_calls": monthly_calls,
        "cache_write_fraction": execution.cache_write_fraction,
        "input_tokens": monthly_calls * input_tokens,
        "output_tokens": monthly_calls * output_tokens,
        "model_id": model_id,
        "provider": price.provider if price else "Unselected",
        "rates": rates,
        "costs": costs,
        "cost": sum(costs.values(), ZERO) if costs else None,
        "issues": issues,
    }


def calculate(estimate: Estimate):
    recurring = sum(
        (c.amount * c.quantity for c in estimate.additional_costs if c.frequency == "monthly"), ZERO
    )
    one_time = sum(
        (c.amount * c.quantity for c in estimate.additional_costs if c.frequency == "one-time"), ZERO
    )
    scenarios = []
    for scenario in sorted(estimate.scenarios, key=lambda s: ["Low", "Expected", "High"].index(s.name)):
        lines = []
        for row in estimate.agents:
            if row.steps:
                lines.extend(line_item(estimate, row, step, scenario, step.name) for step in row.steps)
            else:
                lines.append(
                    line_item(estimate, row, effective_execution(estimate, row), scenario, "Aggregate")
                )
        known = sum((line["cost"] for line in lines if line["cost"] is not None), ZERO)
        complete = all(not line["issues"] for line in lines)
        scenarios.append(
            {
                "name": scenario.name,
                "complete": complete,
                "llm_cost": known,
                "monthly_total": known + recurring,
                "annual_total": (known + recurring) * 12 + one_time,
                "first_month": known + recurring + one_time,
                "input_tokens": sum((line["input_tokens"] for line in lines), ZERO),
                "output_tokens": sum((line["output_tokens"] for line in lines), ZERO),
                "monthly_calls": sum((line["monthly_calls"] for line in lines), ZERO),
                "lines": lines,
            }
        )
    warnings = []
    if all(s["complete"] for s in scenarios) and not (
        scenarios[0]["llm_cost"] <= scenarios[1]["llm_cost"] <= scenarios[2]["llm_cost"]
    ):
        warnings.append("Scenario costs are not ordered Low ≤ Expected ≤ High. Review the assumptions.")
    if any(price.tiers for price in estimate.prices.values()):
        warnings.append(
            "Context pricing tiers use average input per call. Split steps when calls cross a threshold."
        )
    return {
        "scenarios": scenarios,
        "agent_count": sum(r.count for r in estimate.agents),
        "recurring": recurring,
        "one_time": one_time,
        "warnings": warnings,
    }
