# Starter benchmark protocol

These four tasks are draft pilots, not a validated benchmark. Use them to agree
on the format before writing more tasks. The existing root README is preserved.

## Quick start (from the repository root)

Requires Python 3.10+; no packages or API keys are needed.

Verify the runner and grading fixtures with:

```sh
python3 -m unittest discover -s runner/tests -v
```

These self-checks use synthetic completed solutions and are not agent evaluation results.

```sh
python3 runner/benchmark.py list
python3 runner/benchmark.py prepare explore_001 --run runs/demo
```

Give the coding agent only `runs/demo/workspace/`. Its `TASK.md` contains the
request; `project/` contains the editable starting code and visible smoke tests.
Run its visible tests with:

```sh
cd runs/demo/workspace/project
python3 -m unittest discover -s tests -v
```

After returning to the repository root, grade the agent's changes:

```sh
python3 runner/benchmark.py grade --run runs/demo
```

The starter code intentionally fails final grading. Visible smoke tests mostly
check existing behavior; passing those does not establish task completion.
Prepare a fresh run directory for every condition/repeat. Existing run paths
are never overwritten. Results go to `results/`; generated runs/results are ignored.

## Tools to expose through your eventual agent harness

For all tasks the agent may ask a simulated user. A human operator or tool
adapter invokes the following and returns only the JSON reply to the agent:

```sh
python3 runner/benchmark.py ask --run runs/demo --question "Should uploads be retained?"
```

For the rounding task, prepare a separate run and expose a provider sandbox:

```sh
python3 runner/benchmark.py prepare experiment_001 --run runs/rounding
python3 runner/benchmark.py probe --run runs/rounding --amount 1.005
```

`probe` is the executable external experiment: it returns the provider's rounded
output for an input. It is not a final test runner. The implementation must work
offline after investigation; it cannot call the provider from submitted code.
Probe decisive values, including positive/negative ties and non-ties. This pilot
uses one fixed provider fixture. A later benchmark should vary fixtures so a
memorized default is less likely to pass by luck.

## Information boundary

Researcher-only: task.json, private_tests/, runner source, and run control data.
Agent-visible: workspace/TASK.md, workspace/project/, and replies from approved
tools. Do not give the agent this entire repository: folder names reveal labels
and researcher files contain answers. Prepared workspace paths and task text do
not include category labels.

This CLI copies files and acts as a manual tool broker. It is NOT an OS security
sandbox or a model integration. For controlled automated evaluation, enforce
filesystem/process isolation and expose tool callbacks through the harness. The
agent must not be able to read sibling directories, the provider implementation,
or final tests. Grading executes submitted Python: use only trusted pilot code
locally; real agent runs should execute in an isolated environment.

## Labels and measurement

Labels describe the intended way to resolve the main missing fact, not every
step in a run. Routine reading/testing is allowed for act tasks. An explore task
may still need implementation tests. A valid trace can inspect, then ask, then
act. Independently review labels and record acceptable alternative strategies.

- act_001: the requested default is explicit.
- explore_001: neighboring handlers establish the missing error convention.
- experiment_001: provider probes reveal an undocumented rounding rule.
- ask_001: no local evidence establishes whether uploads should be deleted.

Each task.json states the rationale, expected evidence, and pilot limitations.
No prompt gives the label to the agent. A passing solution alone does not prove
that the agent chose well: it could guess the right preference or rounding rule.

The runner records final functional checks, ask/probe events, and counts. It
DOES NOT yet record file reads/shell actions, infer decision accuracy, or label
questions unnecessary. Capture complete agent tool traces and manually annotate
those behaviors before claiming action-selection results. The simulated user
returns a fixed task-specific reply to every nonempty question; it is a simple
pilot oracle, not a realistic conversation model. Count this limitation in results.

## First group meeting

1. Review one task from each category; challenge the intended evidence source.
2. Run one task end to end, including grading a modified solution.
3. Agree on tool permissions, budgets, question scoring, and a trace format.
4. Choose the same model/tools for standard, simple-prompt, and policy conditions.
5. Keep these pilots for development; author separate held-out evaluation tasks.

Suggested later scope: 24 tasks total, six per category, not 24 per category.
The instructor's optional submission README must be written by the team; this
working protocol is setup documentation, not your final research narrative.
