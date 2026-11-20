# Exploratory local-model pilot — 20 November 2026

## Setup

One trial of each of the 24 draft tasks was run under three conditions:
`standard`, `ask_when_unsure`, and `decision_policy` (72 runs). All runs used
the same locally installed `qwen3:14b` model through `runner/local_agent.py`,
temperature 0, seed 598, 8,192-token context, and a 12-step cap. Condition
order was shuffled within each task. The adapter exposed only task-workspace
file operations, visible tests, a simulated-user question, and the task's
provider probe. Full model messages and tool requests/replies were logged.

The 72-run manifest is complete. The runner's 23 self-checks passed after the
pilot. This is an exploratory local-model result, not a general estimate of
coding-agent performance.

## Results

`Functional pass` means the final code artifact passed both original visible
tests and private tests, even if the agent reached its step cap before a final
message. `Finished and passed` requires a final message as well.

| Condition | Functional pass | Finished and passed | Source evidence | Questions | Unnecessary questions* | Provider probes | Step cap |
|---|---:|---:|---:|---:|---:|---:|---:|
| Standard | 18/24 | 17/24 | 20/24 | 5 | 1 | 33 | 4 |
| Ask when unsure | 18/24 | 17/24 | 20/24 | 12 | 8 | 36 | 5 |
| Decision policy | 18/24 | 17/24 | 20/24 | 4 | 0 | 35 | 5 |

| Category | Standard | Ask when unsure | Decision policy |
|---|---:|---:|---:|
| Act | 6/6 | 6/6 | 6/6 |
| Explore | 6/6 | 6/6 | 6/6 |
| Experiment | 2/6 | 3/6 | 2/6 |
| Ask | 4/6 | 3/6 | 4/6 |

Source evidence is a **narrow automated trace check**, not manual decision
accuracy. It requires a direct edit without an ask/probe on act tasks, reading
the relevant existing module before editing on explore tasks, a provider probe
that distinguishes fixture alternatives on experiment tasks, or a targeted
product question before editing on ask tasks. Each condition met this check
on 6/6 act, 6/6 explore, 4/6 experiment, and 4/6 ask tasks. The counts are
separate from final code correctness.

\*One reviewer inspected every one of the 21 successful simulated-user
questions and judged whether it was needed to resolve the main gap. Standard:
4 necessary, 1 unnecessary. Ask when unsure: 4 necessary, 8 unnecessary.
Decision policy: 4 necessary, 0 unnecessary. The two unnecessary questions on
experiment tasks asked the user for an undocumented provider rule the prompt
said the user did not know. Seven more were repeated data-structure questions
in one `ask_004` run after the product answer had been supplied. A second
independent reviewer has not checked these labels.

## Trace examples

- **Human-only choice (`ask_002`):** all three conditions implemented an
  ordering without asking. Visible tests passed, but private tests failed
  because the chosen order disagreed with the hidden product preference.
- **Over-asking (`ask_004`):** the `ask_when_unsure` run asked eight questions,
  including seven repeated data-structure questions, and reached the step cap
  with failing code. The standard and decision-policy runs each asked once and
  passed.
- **Probe quality (`experiment_001` and `experiment_005`):** all six runs
  probed their providers but failed. Rounding probes did not distinguish
  half-even from half-up; message-size probes used only ASCII, which cannot
  distinguish code points from UTF-8 bytes.
- **Unnecessary clarification (`experiment_002`):** standard and
  `ask_when_unsure` asked the user about the provider cursor boundary before
  probing it. The decision-policy run probed without asking. All three
  produced functionally passing code but reached the step cap.

## Interpretation and limits

The decision policy did **not** improve functional pass rate or the automated
source-evidence rate in this one local-model trial. It used fewer unnecessary
questions than the other prompts, particularly the generic ask instruction.
This is a descriptive comparison over 24 small synthetic tasks, with one
model and one run per task/condition. A single task changes a category rate by
16.7 percentage points, so the table does not support a broad or precise
effect claim. The simulated user returns a fixed answer to every nonempty
question, which can reward poorly targeted questions. Final grading executes
model-written Python without a hardened OS sandbox. Counterbalanced provider
and preference variants and an independent question review remain future
work before presenting a stronger research conclusion.

Raw traces, grades, the manifest, automated summaries, and the per-question
review are in the [pilot log archive](../results/local-qwen3-14b-neutral-20261120-logs.zip).
The exact condition prompts are
in `runner/study.py`; the local adapter and metrics are in `runner/local_agent.py`,
`runner/report.py`, and `runner/trace_metrics.py`.
