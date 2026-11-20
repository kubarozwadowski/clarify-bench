# Pilot evaluation protocol

The 24 tasks are draft fixtures. The runner's self-checks establish that their
tests can distinguish the included reference and wrong solutions; they are not
agent results. This protocol produces trace-reviewed pilot results without
silently treating functional success as a good uncertainty decision.

## Conditions

Use the same model version, tool access, time limit, and task order for all
conditions. `runner/study.py` stores the exact condition prompt and its hash in
each run. The three conditions are:

1. `standard`: complete the task with available inspection, tests, user, and
   provider tools.
2. `ask_when_unsure`: the same access, with a generic instruction to ask when
   unsure.
3. `decision_policy`: the same access, with a short source-of-uncertainty rule
   covering request, repository, executable probe, and human preference.

The prompts are the intervention. Do not change task text, provider fixtures,
or tool access between conditions. Randomize condition order within each task
and repeat, and record model identity and settings with the full trace. A pilot
can start with one run per task/condition; repeats and paired variants improve
the strength of later claims.

## Prepare and conduct one run

From the repository root:

```sh
python3 runner/study.py prepare act_001 --condition standard --trial 1 --run runs/act001-standard-1
```

Give the agent **only** `runs/act001-standard-1/workspace/` and the approved
user/provider tool interface. Have it read `AGENT_INSTRUCTIONS.md` and `TASK.md`,
then edit only `project/`. An operator may broker the following tool calls and
return only their JSON replies:

```sh
python3 runner/benchmark.py ask --run runs/act001-standard-1 --question "<agent's exact question>"
python3 runner/benchmark.py probe --run runs/experiment-run --input '{"amount":"1.005"}'
```

Record the full agent transcript, including file reads, tests, tool calls,
questions, provider probes, final message, and timestamps, as a trace file.
Do not put that trace in the agent workspace. Keep the agent away from the
researcher repository, `control/`, `task.json`, private tests, and reference
solutions. The current CLI does **not** enforce this isolation: for final
comparisons, use a process/container setup that blocks reads outside the
prepared workspace and brokers tool calls separately. Runs without that
boundary should be labeled exploratory pilots.

## Review a trace

Write an annotation JSON file such as:

```json
{
  "reviewer": "reviewer-id",
  "observed_resolution": "explore",
  "evidence_sufficient": true,
  "evidence": ["trace event 7: read existing resolver before implementing"],
  "unnecessary_question_count": 0,
  "notes": "The agent used the repository's established precedence."
}
```

`observed_resolution` is the source that actually settled the main gap:
`act`, `explore`, `experiment`, `ask`, or `unclear`. Routine file reading and
testing do not turn an act task into an explore task. A diagnostic probe must
distinguish the provider alternatives; a generic probe is insufficient.
For ask tasks, check that the agent asked about the missing product decision
before committing to a choice. For every task, note questions the agent could
have answered from the prompt, repository, or provider. Set
`evidence_sufficient` false when the trace does not justify the chosen label,
even if the code passes. Cite trace events in `evidence`. Have a second reviewer
resolve disagreements before presenting decision accuracy.

```sh
python3 runner/study.py review --run runs/act001-standard-1 --trace /path/to/full-trace.jsonl --annotation /path/to/annotation.json
python3 runner/study.py summarize --runs-dir runs --output results/pilot-summary.json
```

`review` runs functional grading, validates the annotation, and saves a copy
of the trace and a review report under the run's researcher-only `control/`.
`summarize` reports descriptive counts and flags incomplete task/trial blocks.
Compare conditions only on complete blocks. Keep raw traces and individual
reviews available for auditing; do not present synthetic self-check outcomes as
agent runs.

## Presentation-ready evidence

Report the model, run count, task count, repeats, condition prompts, tool
access, review procedure, and any isolation limits. Show functional pass rate
and decision accuracy separately, both overall and by category. Show questions,
unnecessary questions, and provider probes per condition. Include a few short,
trace-backed cases that explain why an agent succeeded or failed. With six
tasks per category, describe rates as pilot estimates rather than precise
population effects. Add paired provider/preference variants before claiming
that success reflects investigation rather than a memorized or lucky default.
