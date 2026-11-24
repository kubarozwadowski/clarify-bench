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

For a fully logged **exploratory local-model pilot**, `runner/local_agent.py`
can run all 24 tasks across the three conditions through Ollama:

```sh
ollama serve
python3 runner/local_agent.py --model qwen3:14b --group runs/local-pilot-001
```

The adapter gives the model only `list_files`, `read_file`, `write_file`,
`run_tests`, `ask_user`, and `probe_provider`. It records messages, tool
requests, and tool results in each run's `control/agent_trace.jsonl`, plus
functional grades and a group manifest. It uses temperature 0 and a fixed
seed, and randomizes condition order within each task. Its file tool restricts
reads to the prepared workspace and writes to existing top-level project
Python modules. Visible and private grading still execute model-written
Python without OS process isolation, and one local model with one repeat does
not establish general effects. Do not mix its results with a hosted model's
results in one comparison.

For an **isolated Claude Code run**, `runner/claude_agent.py` runs each task
in a Docker container that mounts only that run's `workspace/`:

```sh
claude setup-token                       # once; then export CLAUDE_CODE_OAUTH_TOKEN=<token>
python3 runner/claude_agent.py --build   # once; builds the clarify-bench-agent image
python3 runner/claude_agent.py --model claude-sonnet-5-5 --group runs/claude-pilot-001
```

The agent gets Claude Code's `Bash`, `Read`, `Edit`, `Write`, `Glob`, and
`Grep` inside the container, plus `ask_user` and `probe_provider`. Those two
are answered by a tool server in the driver process on the host, so
`task.json`, private tests, and provider fixtures never enter the container.
The driver saves the raw Claude Code stream as `control/claude_stream.jsonl`
and a normalized `control/agent_trace.jsonl` in the local adapter's event
format (`Read` becomes `read_file`, `Edit`/`Write` become `write_file`), so the
two summary commands below work on either kind of group. `--tasks`, `--trials`,
and `--timeout` work as in the local adapter. Remaining limits:

- The container has internet access, which Claude Code needs. Each run's
  `agent_result.json` lists shell commands that look like network use in
  `network_commands`; review any that appear.
- The auth token is an environment variable inside the container, so the
  agent's shell can read it.
- Claude Code offers no temperature or seed setting; the seed only fixes
  condition order.
- Claude Code does most file work through `Bash` (`cat file`,
  `cat > file <<EOF`, `sed -i`). The driver adds a `read_file` or `write_file`
  event after each such command, marked `"derived_from": "bash"`. This is a
  text match on workspace file names, so an unusual command can be missed or
  miscounted; confirm against the `bash` event when a run matters. To rebuild
  a finished group's traces from the saved stream after changing these rules:
  `python3 runner/claude_agent.py --rebuild runs/claude-pilot-001`.
- Grading still runs the agent's Python on the host after the container exits.

After the run, generate two distinct summaries:

```sh
python3 runner/report.py runs/local-pilot-001
python3 runner/trace_metrics.py runs/local-pilot-001
```

The first reports functional pass and tool-use counts. The second checks
task-specific observable evidence: direct action, reading established code,
a discriminating provider probe, or a targeted question before editing. Its
`source_evidence` field is an automated trace metric, **not** a manual judgment
of decision accuracy or question necessity. Review traces before making those
stronger claims.

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
