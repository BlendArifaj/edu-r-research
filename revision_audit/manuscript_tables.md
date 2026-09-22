
## Table extract 1

| Method | k | F1 | ARI | NMI |
| Rule Heuristic | 8 | 0.925 | 0.925 | 0.925 |
| Static graph | 4 | 0.333 | 0.333 | 0.333 |
| Static + Data | 4 | 0.317 | 0.317 | 0.317 |
| Runtime | 5 | 0.368 | 0.368 | 0.368 |
| Combined Graph | 4 | 0.387 | 0.387 | 0.387 |

## Table extract 2

| Model | Cond | F1 | Compliance | Stability |
| Gemini 2.5 Flash | C0 | 0.907 | 1.000 | 0.965 |
|  | C1 | 0.815 | 1.000 | 0.944 |
|  | C2 | 0.784 | 1.000 | 1.000 |
|  | C3 | 0.813 | 1.000 | 0.923 |
| GPT-4o-mini | C0 | 0.825 | 0.833 | 0.996 |
|  | C1 | 0.733 | 0.833 | 0.996 |
|  | C2 | 0.717 | 0.833 | 1.000 |
|  | C3 | 0.733 | 0.833 | 0.995 |
| Llama 3.1 | C0 | 0.907 | 0.667 | 0.981 |
|  | C1 | 0.617 | 0.778 | 0.271 |
|  | C2 | 0.781 | 0.667 | 0.925 |
|  | C3 | 0.500 | 0.667 | 0.684 |

## Table extract 3

| Evidence | F1 | Modularity | Cross-service coupling |
| Static call | 0.333 | 0.287 | 0.429 |
| Static + data | 0.317 | 0.280 | 0.449 |
| Runtime | 0.368 | 0.202 | 0.510 |
| Static + runtime | 0.387 | 0.255 | 0.490 |

## Table extract 4

| Service | Rule rank | LLM Rank | Expert median |
| Student | 1 | 2 | 2 |
| Faculty | 2 | 2 | 3 |
| Finance | 3 | 3 | 4 |
| Grade | 4 | 3 | 3 |
| Library | 5 | 3 | 4 |
| Attendance | 6 | 3 | 3 |

## Table extract 5

| Metric | Monolith | Clustered | Change |
| Requests | 180,144 | 220,512 | +22.4% |
| Throughput | 201.35 RPS | 245.88 RPS | +22.1% |
| Median latency | 140  ms | 120ms | -14.3% |
| p95 latency | 270  ms | 250ms | -7.4% |
| p99 latency | 390  ms | 310ms | -20.5% |
| Failures | 198 | 4 | -98.0% |