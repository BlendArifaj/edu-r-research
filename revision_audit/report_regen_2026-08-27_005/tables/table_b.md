# Table B — LLM experimental conditions

| model | condition | n_runs | pairwise_f1 | rule_compliance | stability | uncertain_decisions | unsupported_assumptions |
| --- | --- | --- | --- | --- | --- | --- | --- |
| gemini-2.5-flash | C0 | 3 | 0.9068 | 1.0 | 0.9649 | 2 | 1.3333 |
| gemini-2.5-flash | C1 | 3 | 0.8152 | 1.0 | 0.9438 | 1.6667 | 0.6667 |
| gemini-2.5-flash | C2 | 3 | 0.7835 | 1.0 | 1.0 | 2.6667 | 0.6667 |
| gemini-2.5-flash | C3 | 3 | 0.8128 | 1.0 | 0.9225 | 3 | 2 |
| gpt-4o-mini | C0 | 3 | 0.8247 | 0.8333 | 0.9959 | 0 | 0 |
| gpt-4o-mini | C1 | 3 | 0.7333 | 0.8333 | 1.0 | 0 | 0 |
| gpt-4o-mini | C2 | 3 | 0.7174 | 0.8333 | 0.9953 | 0 | 0 |
| gpt-4o-mini | C3 | 3 | 0.7333 | 0.8333 | 0.9901 | 0 | 0 |
| llama3.1 | C0 | 3 | 0.9068 | 0.6667 | 0.9808 | 0.6667 | 0 |
| llama3.1 | C1 | 3 | 0.6173 | 0.7778 | 0.2712 | 0 | 0 |
| llama3.1 | C2 | 3 | 0.7809 | 0.6667 | 0.9251 | 0 | 0 |
| llama3.1 | C3 | 3 | 0.5 | 0.6667 | 0.6844 | 1 | 1 |

SEMS-R reconstruction. Pairwise scores exclude shared identity (`AuthService`, `UserRepository`).
Expert and historical migration ranks are blank until data exist; they are not fabricated.
