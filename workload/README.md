# SEMS-R workload

This directory generates **synthetic experimental traffic** against SEMS-R.

It is **not** production SEMS user telemetry. Mix percentages are experimental assumptions.

The generator is architecture-neutral. It talks only to `BASE_URL`:

```bash
# monolith
SEMS_BASE_URL=http://localhost:8000 python workload/run_load.py --config smoke

# later: API gateway in front of microservices
SEMS_BASE_URL=http://localhost:8080 python workload/run_load.py --config smoke
```

Journeys (configurable weights, default mix sums to 100):

| Journey | Default weight | Behavior |
| --- | ---: | --- |
| student_dashboard | 35 | profile, courses, grades, account, overview |
| grades | 20 | course, exams, grades, GPA |
| registration | 15 | list courses, current registrations/enrollments; POST only if not already registered/enrolled |
| finance | 10 | invoices, payment attempt, balance, transactions |
| attendance | 10 | session + attendance + summary |
| library | 5 | search books, copies, optional borrow |
| faculty_admin | 5 | faculty, departments, staff, statistics |

Load levels: `smoke`, `low`, `medium`, `high`, `very_high`, `stress` under `workload/config/`.

Seed (safe to re-run; resets tables by default):

```bash
export SEMS_DATABASE_URL=sqlite:///./sems_r.db
python workload/seed.py --scale tiny --seed 42
```
