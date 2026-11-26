# ChatGPT follow-up

Run each of the 24 original tasks twice, using a fresh conversation each time.
Use one fixed ChatGPT model and reasoning setting for all 48 runs. This is a
follow-up on cases examined during policy development. Compare conditions
within this follow-up. The Qwen and Claude archives document the original study.

## Run automatically with ChatGPT Plus and Codex CLI

Use these commands from the repository root in your regular Terminal. The runner
looks for the CLI on PATH, then in the ChatGPT app under /Applications. If it
reports that you are signed out, sign in with ChatGPT in the app or run
`codex login` if the standalone CLI is installed.

```sh
python3 runner/openai_followup.py --backend codex --group runs/codex-smoke --tasks experiment_005 ask_002
python3 runner/openai_followup.py --backend codex --group runs/codex-followup
```

The Codex backend defaults to `gpt-6.1-sol` at low reasoning. It launches one
ephemeral CLI call per agent turn and replays only that run's transcript. Both
conditions use the same relay, fixtures, and turn limit. The full run writes
`runs/codex-followup/summary.json`. Rerun the same command to resume. Calls
consume your signed-in Codex allowance.

## Run automatically with the OpenAI API

Create a project key in the OpenAI API dashboard and enable billing or confirm
your API credits. In zsh, enter the key through a hidden prompt so it stays out
of your shell history. Enter the commands from the repository root.

```sh
read -rs 'OPENAI_API_KEY?OpenAI API key: '
export OPENAI_API_KEY
python3 runner/openai_followup.py --group runs/openai-smoke --tasks experiment_005 ask_002
python3 runner/openai_followup.py --group runs/openai-followup
unset OPENAI_API_KEY
```

The smoke command runs both conditions on two tasks. The full command runs all
48 sessions with `gpt-6.2-sol` and low reasoning by default. They are separate
batches. The API is usage billed. The runner uses Python's standard library
and requires no package install. If interrupted, use the same command and
output directory to skip graded sessions and continue from complete logged
turns. A local interruption during a tool action may require inspection of
that run's trace. Keep the API and manual batches separate.

Find the paired counts in `runs/openai-followup/summary.json`. The per-run
traces also record the model ID returned by the API and token usage.

## Prepare manual runs

Run these commands from the repository root. Replace the model label with the
exact model and reasoning setting selected in your app if it differs.

```sh
python3 runner/chatgpt_followup.py prepare \
  --group runs/chatgpt-followup --model "GPT-6.2 Sol (Light)"
```

The script prepares 48 independent workspaces. Follow the order in
`runs/chatgpt-followup/manifest.json`. Each pair has the same task, tool
interface, and 12-turn limit. The assigned order within each pair is seeded.

## Complete a run

1. Open a fresh ChatGPT conversation with the chosen model and reasoning setting.
   Use the same settings for every run, with personalization and unrelated
   tools disabled. Paste only the text of that run's `workspace/CHAT_PROMPT.txt`.
2. Copy the model's whole reply to the clipboard. Type the relay command below
   from the repository root, or recall it with the up arrow. If you copy the
   command itself, it replaces the model reply on the clipboard. Paste only its JSON
   output back into the chat, then repeat. Relay malformed replies verbatim as
   well, so they count toward the same budget. The relay saves the original
   reply and tool outcome and edits the prepared workspace when asked.
3. When the model returns a valid finish action or uses its 12 turns, grade
   the run. Start a fresh conversation for the next run.

```sh
pbpaste | python3 runner/chatgpt_followup.py relay --run runs/chatgpt-followup/run-01
python3 runner/chatgpt_followup.py grade --run runs/chatgpt-followup/run-01
python3 runner/chatgpt_followup.py summarize --group runs/chatgpt-followup
```

The summary compares only task pairs with both conditions graded. It includes
pass counts, automatic source-evidence checks, questions, and probes, with
breakdowns by category. Review transcripts before making claims about whether
specific questions were unnecessary or probes distinguished the alternatives.
The same local test execution assumptions as the existing runner apply.
