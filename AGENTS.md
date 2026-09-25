- NEVER write unit tests after you write code.
- Highly prefer E2E tests as the sole testing mechanism. Use them to verify complex features work. At the end of E2E tests, produce a verifiable and repeatable artifact.
- If you must test a system in isolation, FIRST write all the ways it could fail, THEN write the code.
- Tautological tests considered harmful.
- Change-detector tests considered harmful.
- Do not create regression tests for bug fixes without a genuine gap in behavior testing.

## Product scope and decisions

- Read `PRODUCT_BRIEF.md` before implementing features. Preserve the distinction between confirmed requirements and proposed defaults; do not present illustrative profiles or scenarios as measured benchmarks.
- Optimize for an AI architect estimating the monthly LLM spending of an entire agent suite. Keep individual costs, assumptions, and scenario differences explainable.
- Build the local web app and Excel workflow first. Do not introduce cloud services, authentication, live agent execution, or a LiteLLM proxy unless the task requires them.
- Keep implementation and setup instructions current. Record material design decisions and limitations in the repository rather than relying on conversation history.

## Architecture and maintainability

- Keep calculation logic independent of the UI, persistence, network access, and spreadsheet libraries. Given the same validated inputs and pricing snapshot, calculations must return the same results.
- Use one canonical calculation model for the UI, scenario comparisons, saved estimates, and exports. Avoid independently maintained pricing logic in different screens or endpoints.
- Isolate LiteLLM behind a small adapter for catalog lookup, token counting, and pricing integration. Provider payloads and library-specific objects must not become the application's persisted domain model.
- Prefer small, typed modules with explicit inputs and outputs. Introduce abstractions for actual requirements; avoid speculative frameworks and premature services.
- Use a dependency manifest and lockfile, pin compatible dependencies, and document repeatable install, run, and verification commands. Check official documentation when implementing unfamiliar or version-sensitive APIs.
- Keep changes scoped to the task and preserve unrelated user changes. Do not add dependencies where existing capabilities are sufficient.

## Cost calculation correctness

- Give every numeric field an explicit unit and meaning: tokens per model call, model calls per invocation, invocations per agent per month, agents per group, and currency per pricing unit. Convert pricing units at the adapter boundary.
- Use decimal arithmetic for money and rates. Preserve precision during aggregation and round only for presentation. Do not derive totals from previously rounded display values.
- Distinguish zero, missing, and invalid values. Missing or unsupported pricing must produce a visible incomplete estimate, never an apparently complete zero-cost result.
- Validate finite, nonnegative inputs and appropriate bounds at the backend boundary as well as in the UI. Agent counts are integers; expected invocation and call counts can be fractional. Apply bounds according to the field's meaning rather than treating every rate as a probability.
- Keep complexity, selected model, and workload volume independent. Changing a model must not silently change execution assumptions.
- Treat additional retry attempts, failure probabilities, retry limits, and normal tool/revision cycles as different concepts. Do not substitute one for another without an explicit conversion.
- Account for cached input, cache writes, reasoning, batch rates, and context-length tiers according to the selected provider's billing rules. Avoid overlapping token categories and double counting reasoning already included in output usage.
- Apply request-level pricing thresholds before scaling to monthly usage. Where aggregate averages cannot adequately represent a threshold, disclose the approximation or require a detailed breakdown.
- Count each agent's execution once. Individual overrides replace their share of a group; detailed workflows replace the corresponding aggregate estimate. An agent's volume must have an explicit manual or derived source.
- Bound loops and retries in detailed workflows. Detect unbounded or ambiguous dependency cycles rather than recursing indefinitely or inventing execution counts.
- Keep LLM spending separate from additional costs. Label currencies and distinguish recurring costs from one-time costs. Annualized totals must state the assumption of unchanged monthly usage.

## Pricing, scenarios, and persistence

- Save the effective assumptions and pricing snapshot with each estimate, including provider/model identity, price-relevant region or service tier, units, source, retrieval date, and custom overrides.
- Do not silently reprice saved estimates on load. Make refresh explicit, show its impact, and preserve the ability to reproduce the previous estimate. Report refresh failures while retaining usable saved prices.
- Support custom prices without confusing them with catalog prices. Label tokenizer fallbacks and approximate counts; do not imply provider-exact tokenization without evidence.
- Define and document override precedence for profile, group, individual, and scenario values. Show effective values and their sources, and preserve explicit zero overrides rather than treating them as absent.
- Store scenario changes explicitly. Display the changed parameters alongside resulting costs; do not calculate a hidden percentage adjustment to the final bill or label planning ranges as statistical confidence intervals.
- Version persisted data schemas and bundled defaults. Handle migrations deliberately and preserve existing estimates when defaults change.
- Use transactions or atomic writes for saved data. A failed save or import must not leave a partially updated estimate.
- Make reset scope explicit, preview affected values, and provide undo. Preserve agent definitions and workload volumes unless the user explicitly selects them for reset.

## Spreadsheet and interface quality

- Provide an import template with documented units and accepted fields. Validate complete imports before applying them, with actionable row/column errors and a preview.
- Treat imported spreadsheets as untrusted data: constrain file sizes and row counts, validate structure, and never execute macros, external links, or user-supplied formulas. Write user-provided strings as literal Excel text.
- Export the same effective assumptions and price snapshot used on screen. Include traceable formulas for supported calculations and clearly identify any precomputed results or unsupported recalculation paths.
- Verify exported formula results using a spreadsheet calculation engine when formulas are part of acceptance. Merely checking that cells contain formulas does not verify workbook correctness; disclose when recalculation could not be checked.
- Make the suite total prominent, distinguish partial totals, and provide breakdowns that reconcile to it. Display sufficiently precise values for small per-agent costs without obscuring the overall budget.
- Support keyboard navigation, labeled controls, accessible error messages, and clear loading/empty/error states. Keep bulk editing practical for hundreds of agents.
- Preserve unsaved work across recoverable errors. Avoid network calls on every input edit; calculate from the selected local pricing snapshot.

## Local operation and data handling

- Bind the local service to loopback by default. Do not add telemetry or send customer estimate data to external services without an explicit requirement.
- Routine estimates must not make paid model calls. Keep pricing refresh and optional external token-counting operations explicit; disclose any data leaving the machine.
- Keep secrets out of source control, logs, exports, and browser code. Do not require provider credentials for manual estimates using available price data.
- Return actionable errors without exposing stack traces or sensitive data to the UI. Log enough context to diagnose failures without dumping customer spreadsheets or prompts.

## Verification and handoff

- The testing rules at the top of this file take precedence. Before implementing calculation behavior that needs isolated verification, enumerate its failure modes and independent expected outcomes; write any necessary isolated tests before implementation.
- Prefer E2E journeys through the actual app, persistence, import, and export. Use fixed, versioned pricing fixtures for repeatability; distinguish those checks from live provider/catalog compatibility checks.
- Use independently calculated expected totals for representative scenarios. Do not compute test expectations by calling the implementation under test or merely assert that the UI mirrors the API.
- Cover meaningful risks: incomplete pricing, unit mistakes, duplicate agent counts, override precedence, scenario changes, reset behavior, save/reopen reproducibility, import failure recovery, and workbook reconciliation. Add coverage proportionate to the implemented feature.
- Finish E2E verification with reusable input fixtures, an exported Excel workbook, and a run report recording the command, assumptions/pricing fixture, expected versus actual results, and failures. Screenshots may supplement these artifacts but cannot replace numerical verification.
- Run relevant type, lint, build, and E2E checks provided by the project. Do not introduce tests that only detect text/layout changes or repeat successful checks without a reason.
- In the handoff, state what changed, what was verified, artifact locations, and any unverified behavior or material limitations. Never imply a check passed when it was not run.
