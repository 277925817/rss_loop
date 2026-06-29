# AGENTS.md

## Role

This file is the lightweight router for Codex and other agents.

It does not contain product requirements, loop state, budget policy, task
details, API fields, test cases, or acceptance gates. It only tells agents where
to start and how to resolve document responsibility.

## Command Rule

Always start by applying `loop-constraints.md`, then read `LOOP.md`.

Every agent must read:

1. `loop-constraints.md` for hard safety rules.
2. `LOOP.md` for loop ownership, cadence, roles, and handoff.
3. `STATE.md` for current mission, active lanes, blockers, and kill switches.
4. `loop-budget.md` before any autonomous loop run.
5. `docs/10_loop_usage.md` for runbook steps.
6. `docs/11_evidence_and_reports.md` for report and evidence contracts.
7. `docs/12_command_matrix.md` for verification command interfaces.
8. `docs/13_codex_automations.md` for Codex App / CLI automation prompts.
9. `skills/<role>/SKILL.md` or `.codex/skills/<role>/SKILL.md` for
   role-specific behavior.

Product implementation tasks then continue through:

1. `workflows.md` for product workflow state transitions.
2. `tasks.md` for the product task DAG and acceptance mapping.
3. `docs/01_prd.md` through `docs/08_acceptance.md` for product truth.

Loop readiness checks use `docs/09_loop_readiness.md`.

## Completion Rule

Product completion requires `docs/08_acceptance.md` to evaluate all required
gates as `PASS` and `STOP_ALLOWED = true`.

L3 loop readiness requires `docs/09_loop_readiness.md` to evaluate all required
gates as `PASS` and `LOOP_READY = true`.

Loop readiness never substitutes for product completion, and product completion
never substitutes for loop readiness.

## Priority Rule

For agent operation and safety, apply this order:

1. `loop-constraints.md`
2. `LOOP.md`
3. `STATE.md`
4. `loop-budget.md`
5. `docs/09_loop_readiness.md`
6. `docs/13_codex_automations.md`
7. `workflows.md`
8. `tasks.md`

For product behavior conflicts, apply this order:

1. `docs/05_api_contract.md`
2. `docs/04_data_model.md`
3. `docs/06_dev_rules.md`
4. `docs/03_ui_spec.md`
5. `docs/01_prd.md`
6. `docs/02_arch.md`

`docs/07_test_spec.md` defines how to test. `docs/08_acceptance.md` defines
when product work may stop.

## Scope Rule

Keep this file small. Put loop state in `STATE.md`, run history in
`loop-run-log.md`, budget in `loop-budget.md`, and safety constraints in
`loop-constraints.md`.
