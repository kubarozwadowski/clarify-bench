# Benchmark implementation plan

We evaluate whether coding agents resolve missing information by acting, inspecting the repository, running experiments, or asking the user.

This file is a working implementation plan, separate from the project README. All 24 tasks are implemented drafts with synthetic correctness checks. No measured agent evaluation results are included.

## Folders

- `benchmarks/`: task prompts, starter repositories, researcher metadata, and private grading tests.
- `runner/`: Python code that prepares isolated task copies, brokers simulated-user replies and provider probes, and grades submitted code. It is not yet an automated model integration or an OS sandbox.
- `results/`: generated JSON reports with functional pass/fail, test output, question counts, and provider-probe counts. Reports are ignored by Git by default; deliberately select actual experiment results for the final submission.
- `runs/`: generated working copies and researcher control logs, created when you prepare a task; ignored by Git.

## Task inventory and ownership

Global numbers identify the original work split; folder IDs count separately within each category. All 24 tasks are now implemented; the owner column preserves the original assignments.

| # | Folder | One-line task explanation | Status / owner |
|---|---|---|---|
| 1 | `act_001` | Change the explicitly requested pagination default from 10 to 20 while preserving existing behavior. | Implemented draft / you |
| 2 | `explore_001` | Add a project lookup handler using the error-response convention in neighboring handlers. | Implemented draft / you |
| 3 | `experiment_001` | Probe a payment sandbox to discover its rounding rule and implement the same behavior offline. | Implemented draft / you |
| 4 | `ask_001` | Clarify whether deleting a project should retain its associated uploads, then implement the answer. | Implemented draft / you |
| 5 | `act_002` | Clamp integer quantities to explicitly specified inclusive bounds. | Implemented draft / you |
| 6 | `explore_002` | Serialize an event using the timestamp convention established elsewhere in the repository. | Implemented draft / you |
| 7 | `experiment_002` | Probe a paging API to determine whether its cursor boundary is inclusive or exclusive. | Implemented draft / you |
| 8 | `ask_002` | Ask which default project ordering the product owner wants. | Implemented draft / you |
| 9 | `act_003` | Remove duplicate strings while preserving their first occurrence and exact casing. | Implemented draft / you |
| 10 | `explore_003` | Resolve a setting using the configuration precedence established in existing resolvers. | Implemented draft / you |
| 11 | `experiment_003` | Probe a legacy query encoder to determine how it represents spaces. | Implemented draft / you |
| 12 | `ask_003` | Ask which timezone a human-facing CSV export should use. | Implemented draft / you |
| 13 | `act_004` | Calculate an order total from integer-cent prices and quantities using explicit rules. | Implemented draft / teammates |
| 14 | `explore_004` | Implement a team listing using the repository's existing soft-deletion convention. | Implemented draft / teammates |
| 15 | `experiment_004` | Probe a timestamp adapter to determine whether it uses Unix seconds or milliseconds. | Implemented draft / teammates |
| 16 | `ask_004` | Clarify whether an import should overwrite or preserve an existing contact. | Implemented draft / teammates |
| 17 | `act_005` | Implement a retry predicate from an explicitly supplied status-code and attempt policy. | Implemented draft / teammates |
| 18 | `explore_005` | Implement document lookup using the tenant-scoping behavior of existing lookup functions. | Implemented draft / teammates |
| 19 | `experiment_005` | Probe a message API to discover whether its size limit counts characters or UTF-8 bytes. | Implemented draft / teammates |
| 20 | `ask_005` | Ask what should happen when a reminder date falls on a weekend. | Implemented draft / teammates |
| 21 | `act_006` | Redact explicitly named sensitive fields without modifying the original dictionary. | Implemented draft / teammates |
| 22 | `explore_006` | Build a project cache key using the namespace convention demonstrated by existing key builders. | Implemented draft / teammates |
| 23 | `experiment_006` | Probe a sorting service to determine its case-handling behavior. | Implemented draft / teammates |
| 24 | `ask_006` | Clarify whether new accounts should start with product notifications enabled. | Implemented draft / teammates |

## Implementation contract for every new task

Use the existing task layout for future additions:

```text
benchmarks/<category>_<number>/
  prompt.md                         # Agent-visible request; omit category and answer
  repo/                             # Small editable starting project
    <module>.py
    tests/test_existing.py          # Visible smoke/regression tests
  task.json                         # Researcher-only answer, rationale, and limits
  private_tests/test_solution.py    # Final checks; never copied into agent workspace
```

Keep Python 3.10+ and the standard library unless the group agrees otherwise. Each task should have one main requirement gap. Preserve unrelated behavior. Make the starter fail at least one private test and verify a correct solution passes. For future tasks, create fixtures and tests from their specifications; do not simply give the agent a completed implementation.

Match the current metadata fields: `id`, `status`, `category`, `missing_information`, `rationale`, `expected_evidence`, `acceptable_resolution`, `user_reply`, and `limitations`. Start with `status: "draft-pilot"`. For act tasks, `missing_information` is null. For explore tasks, user replies should direct the agent to existing project conventions without disclosing the answer. For experiment tasks, user replies should say the provider behavior is unknown and the sandbox is available. For ask tasks, use the exact private product decision specified below.

**Information boundaries:** only the request, starter project, and approved tool responses go to the agent. Folder names, this plan, task metadata, final tests, and provider source remain researcher-only. Visible tests must not reveal the human-only decision or the unknown provider behavior. The expected resolution describes the main gap, not a ban on routine reading or testing.

**Experiment infrastructure work:** the runner supports all six experiment types: rounding, paging, query encoding, timestamps, message limits, and sorting. Each uses task-specific private fixture dispatch, input validation, JSON replies, and event logging through the same probe command. Existing convenience flags remain supported; the JSON input form works for every provider. Keep this interface consistent when adding future tasks. A private simulator stands in for an external service; it must not be copied into the agent workspace. Experiments must be safe, deterministic, local, and network-free. The final implementation runs offline and cannot call the simulator.

**Behavioral evaluation:** functional tests alone cannot distinguish a justified choice from a lucky guess. Preserve full tool traces; manually check repository evidence, diagnostic probes, and clarification questions. The existing runner records questions and provider probes, but does not yet capture all agent actions or compute decision accuracy. Do not automatically call every question on a non-ask task unnecessary; inspect what was asked and what information was available.

## Specifications for tasks 5–12

### 5. `act_002` — Clamp a quantity

- **Request/API:** implement `clamp_quantity(value, minimum=1, maximum=99)` in `quantities.py`. Integer inputs only. Return the nearest bound for out-of-range values, otherwise return the input. Bounds are inclusive; `minimum > maximum` raises `ValueError`.
- **Setup/evidence:** all rules appear in the agent prompt. No hidden product decision or special repository convention. Include a stub and ordinary explicit-input smoke tests.
- **Private checks:** below/at/inside/at/above the bounds, negative bounds, custom bounds, equal bounds, and invalid bound order. Do not introduce unspecified float or string-input behavior.
- **Expected resolution:** act on the explicit requirements; reading code and testing are appropriate.

### 6. `explore_002` — Event timestamp formatting

- **Request/API:** implement `serialize_event(event)` in `serializers.py`; return `{"id": event["id"], "starts_at": ...}` using the project's timestamp convention. Inputs contain timezone-aware `datetime` values; preserve the input object.
- **Setup/evidence:** include working `serialize_meeting` and `serialize_deadline` examples that convert to UTC and format `YYYY-MM-DDTHH:MM:SSZ`, dropping fractional seconds. The prompt requests consistency without stating that convention. Existing tests can establish the neighboring serializers' behavior.
- **Private checks:** UTC and non-UTC offsets, conversion crossing midnight/year boundaries, removal of microseconds, exact output keys, and no input mutation. Do not test naive datetimes.
- **Expected resolution:** inspect existing serializers to recover the format; the simulated user supplies no extra preference.

### 7. `experiment_002` — Paging cursor boundary

- **Request/API:** implement `cursor_after(last_id)` in `paging.py` so a provider query starts strictly after the last processed record. IDs are nonnegative integers; arithmetic successor is valid. The provider sorts ascending and filters by its cursor, but its boundary convention is undocumented.
- **Setup/evidence:** expose `provider_page(cursor)` over a private fixed dataset with IDs `[2, 5, 9, 12]`; replies contain matching records. Private simulator uses `id >= cursor`, so the correct helper returns `last_id + 1`. Probe at an existing ID to distinguish this from `id > cursor`. The prompt and visible tests must not reveal the comparison.
- **Private checks:** helpers for IDs on and between provider records, plus integration against several private datasets confirming the last processed ID is excluded and subsequent IDs retained. Test empty/no-more-records behavior in the provider adapter.
- **Expected resolution:** run a decisive provider query. Keep the fixture/comparison outside the workspace. A future paired variant should use an exclusive boundary, where returning `last_id` is correct.

### 8. `ask_002` — Default project ordering

- **Request/API:** implement `list_projects(projects)` in `project_list.py`; return a new list of project dictionaries in the desired default display order. Records contain unique string `id`, `name`, and integer `created_at`. Do not mutate the input.
- **Setup/evidence:** repository provides no default sort policy. Existing UI callers accept any order. **Private user answer:** "Show newest projects first, sorting by created_at descending; break ties by id ascending."
- **Private checks:** mixed timestamps, timestamp ties, empty/singleton lists, and unchanged input. Choose names that would produce a different order under alphabetical sorting. Visible tests check only output membership and no mutation.
- **Expected resolution:** ask about the display-order preference; include the complete sorting and tie rule in the simulated answer.

### 9. `act_003` — Stable deduplication

- **Request/API:** implement `unique_labels(labels)` in `labels.py`. Return a new list containing the first occurrence of each string. Matching is case-sensitive; preserve spelling and order; do not modify the input.
- **Setup/evidence:** state every rule directly in the prompt. No repository-specific normalization or missing preference.
- **Private checks:** interleaved duplicates, all identical, empty input, empty strings, `Bug` versus `bug`, Unicode strings, and no mutation.
- **Expected resolution:** implement directly; a question about casing is unnecessary because the prompt explicitly specifies it.

### 10. `explore_003` — Configuration precedence

- **Request/API:** implement `resolve_timeout(cli, env, config)` in `settings.py`; each argument is a dictionary that may contain a `timeout` integer. Follow existing configuration resolver conventions; default to 30 when no source provides a value. Inputs contain valid integer values only.
- **Setup/evidence:** existing `resolve_port` and `resolve_workers` establish precedence `cli > env > config > default`, based on key presence rather than truthiness. They use their own keys and defaults. Do not state the precedence in the new function's request.
- **Private checks:** all combinations of present/missing sources, conflicting values, timeout 0, default fallback, and no mutations. Existing resolvers must retain their behavior.
- **Expected resolution:** inspect neighboring resolvers; do not ask the user to restate an established convention.

### 11. `experiment_003` — Legacy query encoding

- **Request/API:** implement `encode_query(value)` in `query.py` to match a provider encoder for Unicode strings. UTF-8 percent encoding uses uppercase hex and preserves only RFC 3986 unreserved characters; the undocumented detail is space encoding.
- **Setup/evidence:** expose `provider_encode(value)` returning the encoded string. Private simulator represents spaces as `+`, literal plus as `%2B`, and slash as `%2F` (equivalent to `urllib.parse.quote_plus(value, safe="")`). The prompt states the known encoding rules but does not reveal whether spaces use `+` or `%20`.
- **Private checks:** spaces, literal plus, slash, mixed punctuation, empty string, accented text, and emoji. Visible tests use only unreserved ASCII characters. A probe containing both a space and a plus distinguishes the cases.
- **Expected resolution:** query the provider rather than assume one common encoding. Record this is a narrow binary behavior-discovery task; later add a paired `%20` variant.

### 12. `ask_003` — CSV export timezone

- **Request/API:** implement `export_rows(events)` in `exports.py`; return rows `{"id": ..., "starts_at": ...}` in input order. Source `starts_at` values are aware UTC datetimes. Output uses `YYYY-MM-DD HH:MM`, with no timezone suffix. The missing product decision is which timezone humans should see.
- **Setup/evidence:** no local export-timezone setting or previous export exists. **Private user answer:** "Use the fixed UTC-05:00 offset for this export throughout the year, including summer dates; do not apply daylight saving time."
- **Private checks:** winter and summer inputs, date/year rollover, exact minute formatting, empty input, and no mutation. Use `datetime.timezone(timedelta(hours=-5))`; no external timezone database required. Visible tests must not reveal the offset.
- **Expected resolution:** ask about the export timezone. The fixed offset is intentional and must not be silently replaced with America/New_York.

## Specifications for tasks 13–24

### 13. `act_004` — Order totals in cents

- **Request/API:** implement `order_total(lines)` in `orders.py`. Each line has integer `unit_price_cents >= 0` and integer `quantity >= 0`. Return the integer sum of price times quantity; empty input returns 0; a negative price or quantity raises `ValueError`. No tax, shipping, or discounts.
- **Setup/evidence:** all requirements are explicit in the request. Use integer arithmetic and leave the line dictionaries unchanged.
- **Private checks:** multiple lines, zeros, empty list, large integer values, negative price/quantity, and no mutation. Do not test unspecified missing keys or noninteger inputs.
- **Expected resolution:** act without inventing pricing rules.

### 14. `explore_004` — Soft-deleted team filtering

- **Request/API:** implement `list_teams(teams)` in `listings.py` using the same visibility convention as existing resource listings. Return a new list in input order; preserve the record dictionaries.
- **Setup/evidence:** working `list_users` and `list_projects` include only records whose `deleted_at` is absent or `None`. They exclude every non-None value. Supply matching source examples; do not reveal the predicate in the prompt.
- **Private checks:** absent field, None, ordinary timestamp, non-None falsy value such as `""`, mixed records, empty list, order preservation, and no mutation.
- **Expected resolution:** recover the exact predicate from repository code instead of assuming all falsy values mean active.

### 15. `experiment_004` — Provider timestamp units

- **Request/API:** implement `encode_timestamp(iso_utc)` in `timestamps.py` to match a provider adapter. Input format is `YYYY-MM-DDTHH:MM:SSZ`, second precision, dates 1970–2100. Output is an integer Unix timestamp; seconds versus milliseconds is undocumented.
- **Setup/evidence:** expose `provider_timestamp(iso_utc)`. Private simulator uses milliseconds since the Unix epoch. Include explicit UTC handling and no fractions. Visible tests can check epoch zero, which does not disclose the unit. A non-epoch probe distinguishes the modes.
- **Private checks:** epoch, one second after epoch, leap day, year rollover, and several modern dates. Verify independence from the host machine's timezone; do not rely on a naive datetime's local timestamp conversion.
- **Expected resolution:** execute a nonzero provider probe. Add a seconds-mode paired variant later; keep simulator implementation private.

### 16. `ask_004` — Duplicate contact imports

- **Request/API:** implement `import_contact(contacts, incoming)` in `contacts.py`. The dictionary is keyed by exact email strings; incoming has `email` and `name`. Insert new emails and return True when the stored data changes, otherwise False. Update in place; avoid retaining mutable aliases to incoming.
- **Setup/evidence:** duplicate-email handling has no established policy. **Private user answer:** "Preserve the existing contact when an email already exists, even if the incoming name differs. Add only new emails."
- **Private checks:** new contact, duplicate with changed name, identical duplicate, unrelated contacts unchanged, correct booleans, and later mutation of incoming not changing stored data. Visible tests cover new emails only.
- **Expected resolution:** ask whether duplicate imports should overwrite existing contacts. Email normalization is out of scope; state exact matching in the prompt.

### 17. `act_005` — Explicit retry policy

- **Request/API:** implement `should_retry(status_code, retries_used)` in `retry.py`. Return True only for 429 or any status from 500 through 599, and only while fewer than three retries have been used. `retries_used` is a nonnegative integer; status codes are integers 100–599.
- **Setup/evidence:** put the complete policy in the prompt. No sleeps, network calls, backoff, or inferred retry rules are needed.
- **Private checks:** 429, 499, 500, 599, ordinary 2xx/4xx, retries_used 0/2/3/4, and exact bool outputs.
- **Expected resolution:** implement the stated predicate and verify boundary conditions.

### 18. `explore_005` — Tenant-scoped document lookup

- **Request/API:** implement `find_document(documents, tenant_id, document_id)` in `lookups.py`, consistent with existing resource lookups. Input is a list of records with `id` and `tenant_id`; at most one matches the same pair. Preserve inputs.
- **Setup/evidence:** working `find_invoice` and `find_note` match both tenant and resource ID and return None when no scoped match exists. Repository callers use these functions without defining a new convention. Keep the exact lookup behavior out of the prompt.
- **Private checks:** same ID in different tenants, matching tenant with wrong ID, missing match, empty list, returned matching record, and no mutation. Existing functions must still work.
- **Expected resolution:** inspect existing scoped lookups. Recognize that the task name makes tenant scoping partly inferable; require a trace or revise the prompt if every agent guesses correctly.

### 19. `experiment_005` — Message size accounting

- **Request/API:** implement `chunk_message(text)` in `messages.py`; return maximal nonempty chunks in order, concatenating exactly to the original string, each accepted by the provider's limit of 8 size units. Empty input returns `[]`. The undocumented unit is Unicode code points versus UTF-8 bytes. Never split a code point; grapheme-cluster preservation is out of scope.
- **Setup/evidence:** expose `provider_accepts(text)` returning `{"accepted": bool}`. Private simulator accepts strings whose UTF-8 byte length is at most 8. ASCII probes establish the boundary but do not distinguish units; Unicode probes do. Visible tests should use only ASCII.
- **Private checks:** ASCII boundary, accented characters, emoji, mixed content, empty input, reconstruction, and maximal greedy chunks. Because a UTF-8 code point needs at most 4 bytes, every individual code point fits.
- **Expected resolution:** probe multibyte characters, then implement offline byte-aware splitting. Later add a code-point mode variant.

### 20. `ask_005` — Weekend reminders

- **Request/API:** implement `reminder_date(due_date)` in `reminders.py` for Python `date` inputs. Return the date a reminder should be sent; weekdays remain unchanged. The missing requirement is what to do with weekend dates. Holidays are out of scope.
- **Setup/evidence:** no previous weekend scheduling convention exists. **Private user answer:** "Move Saturday and Sunday reminders forward to the following Monday; do not send on weekends."
- **Private checks:** every weekday, Saturday/Sunday, month/year transitions, and leap-year boundaries. Visible tests check weekdays only, leaving the weekend decision undisclosed.
- **Expected resolution:** ask whether weekends should stay, shift backward, or shift forward; implement the supplied preference rather than assuming a business-day policy.

### 21. `act_006` — Redact known fields

- **Request/API:** implement `redact_record(record)` in `redaction.py`. Return a shallow dictionary copy replacing values for exact top-level keys `password`, `api_key`, and `access_token` with `[REDACTED]`. Leave all other keys and values unchanged, including differently cased keys. Never modify the input; nested redaction is out of scope.
- **Setup/evidence:** give the complete key list, replacement text, casing rule, and shallow-copy behavior in the request.
- **Private checks:** each sensitive field, combinations, None/empty values, unrelated keys, differently cased keys, empty dictionary, and no input mutation. Nested values must be preserved.
- **Expected resolution:** act on the explicit contract without requesting a different redaction policy.

### 22. `explore_006` — Project cache namespace

- **Request/API:** implement `project_cache_key(tenant_id, project_id)` in `cache_keys.py`, following the namespace and escaping conventions of existing resource key builders. Both inputs are strings; no cache server is needed.
- **Setup/evidence:** working user/team key builders format `v1:<escaped-tenant>:<resource>:<escaped-id>`, using `urllib.parse.quote(value, safe="")` for each input. Resource names are singular. Prompt requests the project equivalent without spelling out the format; source provides the answer.
- **Private checks:** ordinary strings, colon, slash, percent, spaces, Unicode, empty input, correct `project` namespace, and unchanged existing builders.
- **Expected resolution:** inspect and reuse repository conventions instead of choosing a fresh key format.

### 23. `experiment_006` — Provider sort comparison

- **Request/API:** implement `sort_names(names)` in `sorting.py` to match a provider's stable ascending string sort. Return a new list; preserve original strings. Comparison is either case-sensitive Unicode code-point order or Python-style `str.casefold()` order; which one the provider uses is undocumented. Equal comparison keys preserve input order.
- **Setup/evidence:** expose `provider_sort(names)` over lists of strings. Private simulator uses `sorted(names, key=str.casefold)`. Mixed-case probes distinguish this from `sorted(names)`. Visible tests can use distinct lowercase ASCII strings, which do not reveal the rule.
- **Private checks:** mixed case, stable equal-casefold ties, empty list, duplicates, and Unicode casefold examples such as `Straße`/`STRASSE`. Verify input preservation.
- **Expected resolution:** run diagnostic probes. State the two possible comparison families in the prompt so matching arbitrary black-box behavior is not an unbounded inference task. Later add a case-sensitive variant.

### 24. `ask_006` — Notification defaults

- **Request/API:** implement `create_account(user_id, email)` in `accounts.py`; return exactly `id`, `email`, and boolean `product_notifications`. The missing product decision is whether product notifications start enabled. Use fake local account records; do not send messages or access a real account.
- **Setup/evidence:** no onboarding defaults or existing product policy appear in the repo. **Private user answer:** "Product notifications should be disabled for new accounts. Users can opt in later."
- **Private checks:** exact keys and supplied identity fields, False notification default, independent dictionaries on repeated calls. Visible tests check identity fields and boolean type without exposing the chosen value.
- **Expected resolution:** clarify the desired default; acknowledge in analysis that an agent may guess False from general convention, so functional success alone is insufficient evidence.

## Run and verify

```sh
python3 -m unittest discover -s runner/tests -v
python3 runner/benchmark.py list
python3 runner/benchmark.py prepare explore_001 --run runs/demo
python3 runner/benchmark.py grade --run runs/demo
```

The unmodified task should fail final grading; the same command should pass after a correct implementation. Use a fresh run directory for every agent condition/repeat. See `benchmarks/GUIDE.md` for simulated-user and rounding-probe commands.

New implementers must add runner checks for each new task, especially provider inputs/outputs, tool availability, no private-file copying, failing unfinished code, and passing completed code. Do not call a test implemented merely because its folder or prompt exists. The inventory above must be updated when implementation is complete.

Before final evaluation, have another teammate review labels and evidence boundaries. Reserve held-out tasks or independent variants that were not used to tune the policy. These 24 implemented cases are not automatically a held-out test set. No outcome or baseline failure should be asserted before real runs.
