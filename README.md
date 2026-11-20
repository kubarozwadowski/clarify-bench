# Clarify Bench

We evaluate whether coding agents resolve missing information by acting, inspecting the repository, running experiments, or asking the user.

## Categories

- **Act:** the request provides enough information to implement the change.
- **Explore:** existing repository files contain the missing information.
- **Experiment:** safe execution or sandbox probes reveal the missing information.
- **Ask:** the missing requirement is a decision only the user can provide.

## Tasks

All 24 tasks are implemented drafts: six per category.

The benchmark fixtures pass synthetic self-checks, but no agent evaluation
results have been collected yet. See [the pilot evaluation protocol](docs/evaluation-protocol.md)
for the three comparison conditions, full-trace review, and result reporting.

| # | Task | Description |
|---|---|---|
| 1 | `act_001` | Change the explicitly requested pagination default from 10 to 20 while preserving existing behavior. |
| 2 | `explore_001` | Add a project lookup handler using the error-response convention in neighboring handlers. |
| 3 | `experiment_001` | Probe a payment sandbox to discover its rounding rule and implement the same behavior offline. |
| 4 | `ask_001` | Clarify whether deleting a project should retain its associated uploads, then implement the answer. |
| 5 | `act_002` | Clamp integer quantities to explicitly specified inclusive bounds. |
| 6 | `explore_002` | Serialize an event using the timestamp convention established elsewhere in the repository. |
| 7 | `experiment_002` | Probe a paging API to determine whether its cursor boundary is inclusive or exclusive. |
| 8 | `ask_002` | Ask which default project ordering the product owner wants. |
| 9 | `act_003` | Remove duplicate strings while preserving their first occurrence and exact casing. |
| 10 | `explore_003` | Resolve a setting using the configuration precedence established in existing resolvers. |
| 11 | `experiment_003` | Probe a legacy query encoder to determine how it represents spaces. |
| 12 | `ask_003` | Ask which timezone a human-facing CSV export should use. |
| 13 | `act_004` | Calculate an order total from integer-cent prices and quantities using explicit rules. |
| 14 | `explore_004` | Implement a team listing using the repository's existing soft-deletion convention. |
| 15 | `experiment_004` | Probe a timestamp adapter to determine whether it uses Unix seconds or milliseconds. |
| 16 | `ask_004` | Clarify whether an import should overwrite or preserve an existing contact. |
| 17 | `act_005` | Implement a retry predicate from an explicitly supplied status-code and attempt policy. |
| 18 | `explore_005` | Implement document lookup using the tenant-scoping behavior of existing lookup functions. |
| 19 | `experiment_005` | Probe a message API to discover whether its size limit counts characters or UTF-8 bytes. |
| 20 | `ask_005` | Ask what should happen when a reminder date falls on a weekend. |
| 21 | `act_006` | Redact explicitly named sensitive fields without modifying the original dictionary. |
| 22 | `explore_006` | Build a project cache key using the namespace convention demonstrated by existing key builders. |
| 23 | `experiment_006` | Probe a sorting service to determine its case-handling behavior. |
| 24 | `ask_006` | Clarify whether new accounts should start with product notifications enabled. |
