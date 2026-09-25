# REFERENCE_PROVENANCE — PETCLINIC_EXT_V1

## External independence

- **spring-projects/spring-petclinic** and **spring-petclinic/spring-petclinic-microservices** are public Spring community repositories; they were **not** authored by the EDU-R / SEMS-R paper authors for this study.
- Both repositories **predate** experiment ID `PETCLINIC_EXT_V1` (see `SOURCE_FREEZE.md` commit dates vs freeze date).
- The **target microservice decomposition** (customers / vets / visits business services) is the **existing** Spring PetClinic microservices distribution, not a partition invented for IEEE Access revision scoring.
- The study authors **do not define** the three business-service labels as model output categories; they are used **only** as an evaluation reference after generation.

## Business services used for evaluation reference

| Reference label | Upstream module |
|-----------------|-----------------|
| CUSTOMERS | `spring-petclinic-customers-service` |
| VETS | `spring-petclinic-vets-service` |
| VISITS | `spring-petclinic-visits-service` |

## Explicitly excluded from target business services

Not used as gold partition labels:

- API Gateway (`spring-petclinic-api-gateway`)
- Config Server
- Discovery Server
- Admin Server
- GenAI Service

**Rationale:** infrastructure/support or capabilities without a one-to-one monolith application counterpart in this focused identifier-semantics benchmark.

## Reference use constraint

The microservices repository is used **only** to derive deterministic monolith→service membership rules (`reference_mapping.csv`). It is **never** included in LLM prompts or evidence packages.
