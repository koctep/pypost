# PYPOST-1267: Responsive cancellation of large collection imports

## Goals

Let users abandon a large collection import while its file is being read or decoded, without
waiting for the entire file to finish processing. Closing an import should release its background
work promptly and must not publish or apply unwanted collections.

The business reason is the delay identified in
[PYPOST-1229 technical debt](../PYPOST-1229/60-tech-debt.md), follow-up item 2: existing cancellation
opportunities begin only after the whole file has been read and decoded. PYPOST-1266 established
a consistent reader cancellation contract but deliberately left this delay unresolved.

## User Stories

- As a user importing a large collection file, I want cancellation to take effect during file
  loading and decoding, before collection validation begins.
- As a user closing an import, I want the abandoned operation to stop without adding collections
  or showing a parsing error caused by my cancellation.
- As a user who completes an import, I want the same supported file contents, collection results,
  validation feedback, and meaningful progress as before.
- As a maintainer, I want a measured cancellation limit and automated coverage with real large
  files so future changes cannot silently restore the whole-file wait.

## Definition of Done

- Cancellation can stop active file loading and active JSON and YAML decoding without waiting
  for the entire input to be consumed or decoded. Coverage includes YAML accepted through the
  existing fallback behavior for files without a YAML extension.
- The background import stops within one second of a cancellation request in the documented
  large-file regression scenarios on the project's normal test environment. Measurement ends
  when background processing has stopped, rather than when a cancellation notice first appears.
- Regression scenarios use actual local JSON and YAML files of at least 16 MiB, request
  cancellation while the targeted loading or decoding phase is active, and record the measured
  latency and accepted one-second limit. They demonstrate both phases, rather than cancellation
  before processing starts or after decoding finishes.
- Large-file coverage includes many collection records and a large individual text value, so
  responsiveness does not depend solely on frequent collection boundaries.
- A cancelled import produces exactly one cancellation outcome, no completion or failure outcome,
  no published candidates, and no changes to stored or displayed collections.
- Successful imports retain supported JSON/YAML semantics, single-collection and bundle forms,
  collection order, validation results, and file-error behavior. Existing callers that do not
  request cancellation continue to receive their normal results.
- Progress remains meaningful: reading or decoding must not claim that collection validation is
  complete before it is complete.
- Automated regression checks have explicit timeouts and bounded waits; developer documentation
  states the measured latency target, scenarios, and environmental limitations.

## Task Description

The collection import workflow already supports cancellation and discards cancelled results.
However, large input files are fully loaded and decoded before the existing per-record checks.
The user can therefore abandon an operation yet still wait for substantial background work that
will never be used. This task closes that gap for the production collection file import path.

The implementation language is Python. The choice of parsing approach and cancellation
interfaces belongs to Step 2; this document defines the required observable behavior.

### Non-functional Requirements

- Keep the application responsive while importing and cancelling; no forcible termination of
  active processing is permitted.
- Make cancellation responsiveness independent of finishing the whole input, including long text
  values, within the documented regression scenarios.
- Preserve the supported reader cancellation behavior established by PYPOST-1266.
- Avoid exposing imported content through new cancellation diagnostics.

### Constraints and Assumptions

- The one-second bound and 16 MiB minimum are explicit acceptance targets proposed for this issue,
  not measurements or promises established by earlier work. The autonomous requirements review
  accepts these targets before design and implementation proceed.
- Latency coverage assumes readable local files and a normally scheduled test environment. It
  does not promise a hard real-time deadline during operating-system stalls, unresponsive storage,
  or resource exhaustion. Tests must document their input shape and execution conditions.
- Scope covers loading and decoding in collection file import and the focused compatibility and
  latency checks needed to prove the change.
- Redesigning conflict resolution, collection application, library discovery, or environment
  imports is outside scope. Cancellation after collection application begins is also outside scope.
- Teardown wait-policy changes belong to PYPOST-1264. Broader cancellation lifecycle coverage
  belongs to PYPOST-1265; focused outcome checks remain necessary here.
- This task does not introduce new import formats, a maximum supported file size, or a general
  import throughput or memory-use service-level guarantee.

## Main Entities

- **Collection file**: a selected JSON or YAML document containing one collection or a bundle;
  its size and content shape affect the amount of loading and decoding work.
- **Import operation**: the background reading, decoding, and validation of that file, followed
  by either candidates, an ordinary failure, or cancellation.
- **Cancellation request**: the decision to abandon an active import before its results are used.
- **Cancellation latency**: elapsed time from that request until background processing stops.
- **Import outcome**: candidates and validation feedback, a file failure, or one cancellation
  outcome that publishes no candidates.

## Q&A

- **Why is this change needed?** The originating debt item records that large-file reading and
  decoding can outlast the user's decision to abandon the import; users need that work to stop
  promptly instead of waiting for the whole file.
- **Why test both formats and a large text value?** A cancellation guarantee must hold for the
  supported formats and must not depend on reaching the next collection boundary.
- **Does this prescribe a streaming parser?** No. The issue permits alternative approaches; the
  design must meet the observable cancellation and compatibility requirements.
- **Who accepts the requirements?** The autonomous sprint orchestrator after independent review.
  No additional stakeholder answer is needed to establish the documented business reason.
