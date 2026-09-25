# Verification — current implementation

Verified on September 25, 2026.

## Results

- `npm run build`: passed (TypeScript and production frontend build).
- `npm run check`: passed (strict TypeScript, formatting, Python lint).
- `npm run test:e2e`: all 6 browser journeys passed against the real local FastAPI/SQLite app.
- The dependency installation audit on September 23 reported zero npm vulnerabilities after overriding the test-only ExcelJS UUID dependency to a patched compatible version; this audit was not rerun for this change.
- LiteLLM 1.102.1 bundled catalog normalization: 3,278 text-model/service entries, zero skipped invalid entries. This checks catalog parsing, not correctness against every provider's bill.
- Desktop and mobile artifacts were visually inspected. The mobile check verifies that the page itself does not overflow horizontally; wide agent tables scroll within their container.

## Repeatable evidence

Run from the repository root:

```sh
npm run build
npm run check
npm run test:e2e
```

The tests start a separate local server at port 8011 with a separate SQLite database. They do not mutate the main application's saved estimates.

- [Verification results](../artifacts/verification.json): expected and observed arithmetic outcomes.
- [Browser test results](../artifacts/e2e-results.json): full run status, durations, and diagnostics.
- [Example customer workbook](../artifacts/mortgage-budget.xlsx): fixed synthetic model pricing, low/expected/high totals, recurring and one-time costs.
- [Tier and cache workbook](../artifacts/tier-cache-budget.xlsx) and [input fixture](../artifacts/tier-cache-fixture.json): input/output/context-tier and cache partition accounting.
- [Import fixture](../artifacts/agent-import.xlsx), [300-agent fixture](../artifacts/300-agents-import.xlsx), and [invalid fixture](../artifacts/invalid-import.xlsx).
- [Invalid cache import fixture](../artifacts/invalid-cache-import.xlsx): a row whose override conflicts with its active profile is rejected during preview.
- [Cache-hit workbook](../artifacts/cache-hit-budget.xlsx): checks the bundled LiteLLM 1.102.1 cache-hit field fallback through the browser and spreadsheet engine.
- [Desktop screenshot](../artifacts/suite-desktop.png) and [mobile screenshot](../artifacts/suite-mobile.png).

The synthetic model's rates are $2/M input and $8/M output. Two simple agents at 1,000 invocations/month each produce $12.24 / $16.32 / $24.48 in the starter scenarios. With $25 monthly and $100 one-time costs, expected first-year spending is $595.84. The 300-agent group fixture produces $244.80/month at 100 invocations per agent.

A delayed-save and delayed-refresh browser journey verifies that edits made during either operation remain in the draft and that only the earlier save is marked persisted. The cache-hit journey uses the pinned bundled catalog entry for `deepseek/deepseek-coder` and independently expects $0.59976/month in the exported workbook. These checks do not validate the provider's live price.

Workbook formulas were independently evaluated with HyperFormula, including changing a calculation input and checking propagation to the summary. Microsoft Excel's desktop UI was not automated. The workbook's Read me sheet identifies which inputs are recalculable and where selected pricing tiers require a fresh export or explicit rate update.

## Current limits

- Manual volume entry and bounded model-call steps are implemented. Automatic business-volume mapping and agent call-graph propagation are not.
- Pricing refresh is implemented with snapshot preservation and a before/after preview; live network refresh and every provider's billing rules were not covered by the deterministic E2E run.
- Catalog pricing is community-maintained. Models with missing or recognized unsupported prices remain visibly incomplete. Multimodal, hosted tool, storage, priority/flex, and contract-specific charges may require explicit additional items or custom rates.
- The 300-agent test verifies aggregate budgeting; it is not a performance benchmark for 1,000 individually expanded rows.
- No live agent execution/monitoring, accounts, or cloud deployment is included.
