# PYPOST-1263: Contention-resistant planner work benchmark

## Research

The existing `test_plan_collection_import_large_dataset_performance` in
`tests/test_collection_import_profile.py` measures `time.perf_counter()` around one
`plan_collection_import` call and rejects elapsed time at or above 100ms. Fixture creation
and conflict discovery already occur outside the timed interval. Production planning in
`pypost/core/collection_import.py` performs synchronous in-memory conflict resolution and
model copying; it does not delegate the measured work to another thread or perform an
asynchronous request.

`time.thread_time()` measures current-thread user and system CPU time and excludes sleep;
`perf_counter()` includes elapsed sleep. `process_time()` is process-wide and could count
other threads' work. These distinctions support current-thread CPU accounting for this
synchronous workload. See [Python time documentation](https://docs.python.org/3/library/time.html).

The Jira failure followed by an isolated approximately 49ms pass motivates removing
scheduling delay from the gate. This is evidence of sensitivity, not proof of every timing
failure's cause.

## Implementation Plan

1. Step 3 adds deterministic meta-tests that call the actual benchmark function before its
   measurement changes. Do not fix the benchmark in the red phase.
2. In Step 4, capture thread CPU and wall observations immediately around its existing real
   planner call. Gate on the thread CPU delta with the existing strict `< 100.0` ms budget.
   Keep wall elapsed milliseconds as contextual failure output.
3. Preserve workload construction, 25-conflict assertion, all three decision types, non-empty
   result collections, and positive request count. No production planner changes.
4. Update the module/test descriptions to say CPU-work budget. Document that this is not a
   guarantee of wall latency under load. The other two profile tests remain unchanged.
5. Run targeted tests through `make test WORKERS=1` with `PYTEST_ARGS` selecting the profile
   module and the new focused regression module; retain the ordinary real-clock benchmark.
   Later quality gates use existing Make targets.

### Failing repro design

Create `tests/test_collection_import_profile_timing_repro.py` with an explicit ten-second
module timeout. Import the profile module and invoke its actual benchmark function directly.
Use a module-local fake time facade via `monkeypatch` replacing the profile module's `time`
binding; do not patch the shared standard-library time module, pytest clocks, or real planner.
Supply controlled `perf_counter` and `thread_time` observations and record their reads.

Wrap the benchmark module's `plan_collection_import` binding with a spy that calls the saved
real planner exactly once and returns its real result. Inspect arguments to establish the
500 incoming collections, 2,500 requests, 25 conflicts and three decision types. Verify
one invocation and record that the clock interval brackets that call, excluding fixture
construction. Fake clock values model scheduling and work cost without busy loops or sleeps.

| Case | Wall delta | Thread CPU delta | Desired outcome |
| --- | --- | --- | --- |
| External descheduling | 500ms | 40ms | Benchmark passes |
| Excess planner CPU work | 500ms | 150ms | Benchmark raises its budget assertion |
| CPU boundary | 500ms | 100ms | Benchmark raises its budget assertion |

The descheduling case is red today because the current wall gate sees 500ms. The slow-work
case must also verify the rejection is explicitly based on CPU work and reports CPU, wall,
and budget context; a wall-only rejection is insufficient. The clock-read record must show
both CPU observations enclosing the real planner call after the fix. A constant passing
value, removed timing assertion, wall-only gate, enlarged budget, or process-wide clock must
not satisfy the meta-tests. The 100ms case protects strict boundary semantics.

The synthetic CPU observations test the benchmark's rejection policy, not an actual planner
optimization. The ordinary real-clock test still exercises actual planner CPU consumption.
This separates reproducible gate verification from incidental host load while retaining
the representative real workload and functional assertions.

## Architecture

```text
Normal test run -> real fixture + real planner -> thread CPU budget assertion
                                          -> wall-time failure context
Meta-test -> actual benchmark + module-local clock observations + real-planner spy
         -> verify pass/fail policy, measurement interval, and workload preservation
```

### Responsibilities and interfaces

- Existing benchmark: owns fixture, real planner invocation, functional checks, timing
  measurement, and CPU-budget assertion. No new public helper API is required.
- `time.thread_time() -> float`: supplies seconds of current-thread CPU work at each bound.
- `time.perf_counter() -> float`: supplies elapsed seconds for diagnostic context.
- Real planner spy: observes existing arguments and returns the actual planner result.
- Focused meta-tests: demonstrate independent scheduling/work observations, genuine budget
  enforcement, and interval placement without dependencies on host load.

### Decisions and limitations

Current-thread CPU excludes unrelated process/thread execution and descheduling while the
planner is synchronous. It still counts actual planner CPU work; the numeric budget stays
100ms. Do not substitute a process CPU clock, add retries, skip platforms, or increase the
budget. Existing supported Python platforms provide the selected thread CPU API.

CPU time is not a user-visible wall-latency guarantee. Blocking waits and I/O would not be
captured by this work-budget gate; the current in-memory planner does not require them.
The existing explicit 60-second profile-module timeout remains the outer hang bound.
If the planner later delegates work or adds blocking operations, this assumption must be
revisited. No wall threshold can deterministically distinguish planner waits from external
scheduler delay within this narrow test.

No application runtime configuration, import behavior, dependencies, or unrelated profile
test changes are needed.

## Q&A

- Why not simply widen the wall budget? That hides planner work regressions and violates AC-6.
- Why not process CPU time? It includes unrelated threads in the test process.
- Why keep wall measurement? It explains observed elapsed latency without making contention
  a false regression signal.
- Why call the benchmark in meta-tests? Testing an isolated clock helper would not prove the
  real performance assertion uses it or retains the real fixture and planner call.
