# PYPOST-1275: Add Google Drive resumable upload request templates

## Goals

PyPost users need a reusable Google Drive collection example for uploading files that are too
large or otherwise unsuitable for a single request. The current example covers other Drive
operations but does not describe the resumable-upload journey, leaving users to reconstruct the
workflow and increasing the risk of incomplete or incorrect requests.

The business goal is to make the Google Drive v3 collection example a dependable reference for
both starting a resumable upload and sending the file content in chunks through the resulting
upload session. Users should be able to understand the two-stage workflow from the example and
rely on contract coverage and documentation to keep it accurate over time.

## Programming Language

- **Implementation language**: Python for contract coverage and repository validation; JSON for
  the collection example content.

## User Stories

- As a **PyPost user integrating with Google Drive**, I want an example request that starts a
  resumable upload, so that I can obtain the upload session needed for a large-file workflow.
- As a **PyPost user uploading a large file**, I want an example request that sends content chunks
  to the active upload session, so that I can continue the upload using the session returned by
  Google Drive.
- As a **collection author or maintainer**, I want the two resumable-upload stages to be clearly
  represented in the Google Drive example, so that the example is understandable and reusable.
- As a **project maintainer**, I want automated contract checks and accompanying documentation,
  so that future edits do not silently remove or misrepresent the resumable-upload workflow.

## Definition of Done

- The Google Drive example describes a resumable-upload session initiation using the Google Drive
  v3 upload endpoint and the resumable-upload request mode.
- The session-initiation example makes clear that Google Drive returns a session location that is
  used by the subsequent upload stage.
- The Google Drive example describes uploading file content chunks to the returned session
  location using the appropriate update operation.
- The resumable-upload examples contain the request information users need to understand the
  workflow, including the upload intent, file content or chunk context, and relevant response or
  continuation expectations.
- Contract checks verify that both stages exist and preserve their essential Google Drive v3
  semantics, including the session-location handoff between stages.
- `examples/README.md` explains when and how the resumable-upload examples are used, including
  that the second stage depends on the session location from the first stage.
- Existing Google Drive collection examples remain valid and their behavior is not regressed.
- The example and documentation do not require live Google credentials or network access for
  contract validation.

## Task Description

### Problem

The Google Drive collection example lacks a documented resumable upload workflow. Users working
with large files cannot discover from the example how to initiate an upload session or continue
the upload by sending content chunks to the session-specific location.

### Scope

In scope:

- The Google Drive collection example's resumable-upload session-initiation request.
- The Google Drive collection example's chunk-upload request.
- Contract coverage for the presence and essential semantics of both requests.
- User-facing example documentation describing the two-stage workflow and its handoff.

Out of scope:

- Live Google Drive API integration or credential management.
- Implementing a general-purpose upload client, chunk scheduler, retry system, or progress UI.
- Changing unrelated Google Drive operations or other collection examples.
- Guaranteeing a complete upload in the example without the caller supplying file content and
  session-specific values.

### Constraints and assumptions

- The existing Google Drive collection format and project conventions remain the source of truth
  for how examples are represented.
- The workflow is intentionally represented as two request stages: session initiation followed by
  chunk transfer.
- Google Drive supplies the resumable session location after initiation; users or their calling
  workflow provide that location to the chunk-upload stage.
- A chunk may be one part of a larger file upload, so the example must not imply that one request
  necessarily completes every upload.
- Contract validation is local and deterministic and must not depend on cloud credentials,
  network availability, or a live Google Drive account.
- Existing behavior and examples outside this task remain unchanged.

## Main Entities

- **Google Drive collection example**: The maintained reference collection for Google Drive v3
  request workflows.
- **Resumable upload session**: The server-created upload context identified by a session location
  returned after initiation.
- **Upload initiation request**: The first workflow action that asks Google Drive to create a
  resumable session for a file.
- **Upload chunk request**: A subsequent workflow action that sends a portion of file content to
  the active resumable session.
- **File content chunk**: A bounded portion of the file being uploaded, associated with its place
  in the overall upload.
- **Contract check**: A repository validation that confirms the example retains the required
  requests, semantics, and session handoff.

## User Scenarios

1. **Start a resumable upload**: A user selects the Google Drive upload-initiation example,
   supplies the file metadata and upload context, and receives a resumable session location from
   Google Drive.
2. **Send the next chunk**: The user takes the session location from the initiation result,
   supplies a file-content chunk and its position, and sends that chunk to Google Drive.
3. **Continue a multi-chunk upload**: The user repeats the chunk-upload stage for additional
   portions while using the same active session until Google Drive indicates completion or another
   session outcome.
4. **Read the documentation**: A user consults `examples/README.md` to understand that session
   initiation and chunk transfer are separate stages and that the second stage depends on the
   location returned by the first.
5. **Run local validation**: A maintainer runs the repository's contract validation without
   credentials or network access and receives a failure if either required stage or its handoff
   semantics are removed.

## Q&A

| Question | Answer |
| --- | --- |
| Why is this task needed? | To give PyPost users a dependable, discoverable reference for large-file Google Drive uploads that use a resumable session. |
| What are the required workflow stages? | Initiate a resumable upload session, then send file-content chunks to the returned session location. |
| Must the example perform a live upload? | No. The task requires a reusable reference and local contract coverage, not live API integration. |
| Does the chunk stage always upload the entire file? | No. It represents one chunk transfer and may be repeated until the upload is complete. |
| What does the related PYPOST-1268 debt establish? | The earlier Google Drive example intentionally omitted resumable chunking for large files and identified this task as the follow-up. |
| Which files are in scope? | The Google Drive collection example, its contract test, and `examples/README.md`, plus these Step 1 artifacts. |
