# PYPOST-1436: Formalize Structured Errno Mapping and OS Port Preflight Error Classification

## Goals

In PyPost, starting and managing standalone Model Context Protocol (MCP) servers and background web endpoints requires reliable detection and classification of network bind and port availability failures. When a server fails to start because its requested port is already in use, reserved, or unavailable, the system must provide clear, actionable diagnostic feedback to operators and automation agents.

Currently, server error formatting (`format_bind_error`) and preflight port validation (`MCPServerRegistry._validate_os_port`) rely on fragile, locale-dependent English string matching (such as `"address already in use" in str(exc).lower()`, `"permission denied"`, etc.) when inspecting operating system socket exceptions (`OSError` / `socket.error`). This design introduces serious reliability issues across diverse deployment environments:
1. **Locale-Dependent Failure**: On non-English operating systems (e.g. localized Linux distributions, macOS, or Windows configured in German, French, Japanese, Spanish, Russian, Chinese, etc.), system error messages are translated into the host language (e.g. "Die Adresse wird bereits verwendet" instead of "Address already in use"). Substring matching fails entirely, causing port collision errors to be misclassified as generic unhandled exceptions with confusing or unhelpful error messages.
2. **Platform and Winsock Discrepancies**: On Windows, networking socket errors produce distinct Windows Sockets (WSA) error codes (such as `WSAEADDRINUSE` 10048, `WSAEACCES` 10013, `WSAEADDRNOTAVAIL` 10049) rather than standard POSIX errno values. Inconsistent or missing mappings across platforms lead to improper error classification or silent failures during port preflight checks on Windows.
3. **Absence of IPv6 Preflight Probing**: The preflight socket probe is hardcoded to IPv4 (`AF_INET`), completely lacking support for IPv6 addresses (`AF_INET6`). When an operator or AI agent configures an IPv6 loopback (`::1`) or wildcard (`::`) host, the preflight validation either raises address family errors or fails to accurately detect port collisions, creating false negatives and false positives.

The business goal of this task is to formalize cross-platform, locale-independent, structured operating system error classification and multi-family (IPv4/IPv6) socket preflight probing. By replacing fragile string matching with comprehensive structured error code normalization across POSIX and Windows, PyPost will deliver consistent, robust diagnostic messaging and accurate port collision preflight checks across all supported operating systems, languages, and network protocol families.

## Programming Language

- **Implementation language**: Python

## User Stories

- As an **operator using a non-English operating system** (e.g., German, French, Japanese, or Spanish locale), I want port conflict and bind errors to be accurately recognized and explained with clear instructions, so that I can immediately resolve port conflicts without deciphering raw low-level system strings.
- As a **Windows user or developer**, I want Windows Sockets error codes (such as `WSAEADDRINUSE` 10048, `WSAEACCES` 10013, `WSAEADDRNOTAVAIL` 10049) to be normalized and classified equivalently to POSIX errno codes, so that platform differences never lead to misdiagnosed port conflicts or unhandled errors.
- As an **engineer configuring IPv6 or dual-stack services**, I want preflight port probing to accurately probe IPv6 host addresses (such as `::1` and `::`), so that address conflicts on IPv6 endpoints are detected reliably before server launch or reconfiguration.
- As an **AI automation agent / test runner**, I want server bind and preflight errors to be classified deterministically and predictably regardless of the host OS locale or networking configuration, so that programmatic recovery, retry strategies, and diagnostic logging function reliably across heterogeneous CI/CD environments.
- As a **PyPost system maintainer**, I want the codebase to eliminate brittle substring matching on exception text, so that error handling remains resilient to OS-level text translations, future Python runtime changes, and platform socket variations.

## Definition of Done

This task is considered complete when:
1. Substring inspection of exception strings (e.g. `"address already in use" in str(exc).lower()`) is completely eliminated from server bind error handling and port preflight validation.
2. Structured error classification reliably maps POSIX errno values and Windows WSA socket error codes into well-defined error categories (such as Address In Use / Port Busy, Address Not Available, Permission / Access Denied).
3. Cross-platform error normalization covers POSIX errno standards and Windows Winsock codes (`WSAEADDRINUSE` 10048, `WSAEACCES` 10013, `WSAEADDRNOTAVAIL` 10049, as well as BSD/Darwin error constants).
4. Operator-facing bind error messages are informative, actionable, and generated consistently regardless of system locale or language settings.
5. OS port preflight validation supports both IPv4 (`AF_INET`) and IPv6 (`AF_INET6`) host addresses, detecting conflicts and availability on both address families.
6. Unclassified or unexpected operating system errors retain their original error details and exception chain without being masked or lost.
7. Verification passes all project quality gates (`make check` and `make verify-ai-tasks`).

## Task Description

### Problem Statement

During server startup and lifecycle reconfiguration, PyPost must verify whether a chosen TCP port is available on the specified host interface before committing changes or spawning server threads. When a bind failure occurs or preflight checks fail, the system needs to classify the failure:
- Is the port already occupied by another process?
- Is the requested host address invalid or unassignable on this machine?
- Does the process lack administrative/root privileges to bind to the requested port?

Currently, the code relies on checking substrings within `str(exc).lower()`, specifically searching for `"address already in use"`. This approach is fundamentally flawed:
- **Locale Sensitivity**: Exception strings (`exc.strerror` or `str(exc)`) originate from the C standard library's `strerror(errno)` or OS networking layers, which are localized to the active system locale (`LC_MESSAGES`). On non-English systems, the string will never match `"address already in use"`, resulting in degraded diagnostic output.
- **Windows WSA Socket Errors**: Python on Windows can raise `OSError` with specific Winsock WSA error numbers (e.g. 10048 for address in use, 10013 for permission denied, 10049 for address not available). Incomplete or ad-hoc handling of these numbers causes inconsistent behavior across Windows and Unix platforms.
- **Single-Stack IPv4 Probing**: The preflight probe socket is hardcoded to IPv4, which fails or misbehaves when users specify IPv6 loopback (`::1`) or wildcard (`::`) addresses.

### Scope

- **Structured Errno and WSA Error Normalization**:
  - Classifying operating system socket errors using numeric error codes across POSIX and Windows platforms.
  - Handling address in use (`EADDRINUSE`, `WSAEADDRINUSE`), address not available (`EADDRNOTAVAIL`, `WSAEADDRNOTAVAIL`), and permission/access denied (`EACCES`, `WSAEACCES`).
- **Elimination of String Matching**:
  - Replacing all substring checks against exception messages with structured numeric code classification.
- **Multi-Family Socket Preflight Probing**:
  - Supporting both IPv4 and IPv6 address resolution and socket family selection during preflight port availability validation.
  - Ensuring preflight probing does not leave dangling sockets or trigger false collision errors.
- **Actionable Diagnostic Messaging**:
  - Providing clear, operator-oriented guidance depending on the specific error cause (e.g., advising port reassignment for busy ports, permission elevation for privileged ports, or interface verification for unassignable addresses).
- **Graceful Fallback**:
  - Ensuring rare, unmapped OS errors preserve their underlying error details so that troubleshooting remains possible.

### Out of Scope

- Introducing dynamic port auto-assignment or port-hunting heuristics (users and configurations explicitly define the desired port).
- Graphical user interface (GUI) dialog redesign or desktop styling modifications.
- Custom wire protocol or transport implementation changes.
- Modifying underlying network firewall policies or OS security configurations.

### Functional Requirements

- **FR1 (Structured Error Code Normalization)**:
  - The system must inspect the structured numeric error code (`errno` / `winerror`) of `OSError` and socket exceptions rather than parsing textual strings.
  - Normalization must recognize standard POSIX errno values, BSD-specific variants, and Windows Sockets (WSA) error codes.
- **FR2 (Elimination of Textual Substring Matching)**:
  - The system must not rely on English phrases like `"address already in use"` in exception strings.
  - Classification behavior must be identical across English, localized, and non-UTF-8 system locales.
- **FR3 (Discrete Error Cause Categorization)**:
  - The system must categorize network bind and port availability failures into distinct functional causes:
    - **Port In Use / Busy**: The port is already bound by another process or instance.
    - **Address Not Available**: The requested host address cannot be assigned on the current host.
    - **Permission Denied**: The process lacks sufficient OS privileges (e.g., binding to privileged ports below 1024 without root/admin rights, or firewall policy blocking).
    - **Unclassified OS Error**: Any other operating system error, with raw details preserved.
- **FR4 (IPv4 and IPv6 Preflight Probing)**:
  - Preflight socket probing must inspect the host address format and utilize the appropriate socket address family (`AF_INET` for IPv4, `AF_INET6` for IPv6).
  - Probing must correctly validate standard IPv6 loopback (`::1`) and wildcard (`::`) addresses without raising family mismatch exceptions.
- **FR5 (Actionable Diagnostic Messages)**:
  - For port collision failures, the diagnostic message must advise the operator to choose a different port in Settings or stop the conflicting process.
  - For permission denied failures, the diagnostic message must inform the operator about insufficient privileges for the requested port/address.
  - For address unavailable failures, the diagnostic message must inform the operator that the requested host cannot be bound on the local system.
- **FR6 (Preservation of Unclassified Details)**:
  - When an unexpected or unclassified OS error occurs, the resulting diagnostic message must retain the underlying system error description (`exc.strerror` or `str(exc)`) and maintain the original exception context.

### Non-Functional Requirements

- **NFR1 (Cross-Platform Consistency)**:
  - The error classification and preflight probing logic must behave identically on Linux, macOS, and Windows.
- **NFR2 (Locale Independence)**:
  - System behavior and error classification must be 100% deterministic regardless of the host's active locale or UI language configuration.
- **NFR3 (Preflight Probe Hygiene and Latency)**:
  - Preflight socket probing must immediately close and release any probe sockets, avoiding socket leaks, `TIME_WAIT` lockouts, or unnecessary delays during server reconfiguration.
- **NFR4 (Robust Error Chaining)**:
  - When wrapping or re-raising exceptions, the system must maintain explicit exception chaining (`from exc`) for traceability and debugging.

### Constraints and Assumptions

- The solution must rely on standard Python libraries (`socket`, `errno`, `ipaddress`, etc.) without introducing heavy external dependencies.
- Loopback probing must not interfere with or disrupt active services already running on non-conflicting ports.
- Host systems may have IPv6 enabled or disabled; probing must handle systems where IPv6 is not available without crashing.

### Main Business Entities

| Business Entity | Description | Attributes (Business Perspective) |
| --- | --- | --- |
| **Server Bind Error Event** | An operational failure occurring when an MCP server or web server fails to bind to its configured host and port. | Host address, port number, server identifier, raw operating system error code, root cause classification. |
| **Preflight Port Probe** | A preliminary network validation check to verify port availability on the host before committing a server launch or reconfiguration. | Target host, target port, address family (IPv4/IPv6), availability verdict, detected conflict cause. |
| **Error Cause Category** | A standardized functional category representing the nature of a socket bind or preflight failure. | Category type (Port Busy, Address Unavailable, Permission Denied, Unclassified), category description. |
| **Operator Diagnostic Message** | A user-facing explanation of why the server failed to start, along with concrete corrective action steps. | Server name, address string, root cause explanation, operator remediation advice. |
| **Endpoint Network Address** | The network identity on which a service endpoint is configured to listen. | Host representation (IPv4/IPv6 literal, hostname, loopback), TCP port number. |

### User Scenarios

#### Scenario 1: Port Collision on Localized Non-English Linux Environment
An operator runs PyPost on a Debian Linux workstation configured with a German locale (`LANG=de_DE.UTF-8`). A standalone MCP server is configured on port 8080, which is already occupied by a local web proxy. When PyPost attempts to bind the port, the OS raises an `OSError` with `errno.EADDRINUSE` and a localized message `"Die Adresse wird bereits verwendet"`. Because the system inspects structured error codes, it recognizes `EADDRINUSE` immediately and outputs: `"Cannot start MCP Server on 127.0.0.1:8080: port is busy or unavailable. Choose another port in Settings or stop the process using this port."`

#### Scenario 2: Windows Winsock Port Conflict
A developer runs PyPost on Windows 11. An MCP server tries to bind to port 5000, which is occupied by another application. The Windows networking stack returns error code 10048 (`WSAEADDRINUSE`). The structured error normalizer recognizes 10048 and maps it to the Port Busy category, presenting the operator with clear guidance rather than failing with an unhandled exception.

#### Scenario 3: Preflight Probing on an IPv6 Loopback Address
An automated AI agent configures an MCP server to listen on IPv6 loopback (`::1`, port 9090). Prior to launching the server, the registry executes a preflight check. The preflight prober detects that `::1` is an IPv6 address, creates an `AF_INET6` socket probe, and tests port availability. The check succeeds cleanly without raising address family mismatch errors, and the server proceeds to start.

#### Scenario 4: Permission Denied on Privileged Low Port
A user mistakenly configures a server to bind to port 80 without administrative privileges on Linux. The OS raises `errno.EACCES` (or `WSAEACCES` 10013 on Windows). The system classifies the error under Permission Denied and informs the operator that the process lacks permission to bind to the requested port.

#### Scenario 5: Address Not Available on Unbound Network Interface
A user specifies a static IP address that is not configured on any local network adapter (e.g. `192.168.1.99`). The OS raises `errno.EADDRNOTAVAIL` (or `WSAEADDRNOTAVAIL` 10049 on Windows). The system identifies that the address is unavailable on the host machine and advises the operator to check the host IP configuration.

## Q&A

**Q: Why is structured errno classification preferred over substring matching on exception text?**  
A: Operating system exception strings are localized to the system language and subject to wording changes across OS versions, platforms, and Python runtime releases. In non-English environments, `"address already in use"` is never present in the error string. Structured numeric error codes (`exc.errno` and Windows WSA codes) are immutable, deterministic, and universal across all languages.

**Q: Why must IPv6 support be included in preflight validation?**  
A: Modern containerized, development, and enterprise environments increasingly use IPv6 addresses (such as `::1` for loopback or `::` for all interfaces). Probing only `AF_INET` either crashes with `OSError` (family mismatch) or fails to detect real conflicts on IPv6 addresses, creating blind spots for IPv6 deployments.

**Q: Does eliminating string matching risk missing unknown platform-specific errors?**  
A: No. Standardized POSIX and Windows Sockets codes are exhaustive for network bind operations (`EADDRINUSE`, `EADDRNOTAVAIL`, `EACCES`, and their WSA counterparts). Furthermore, any error code outside this known set falls back to preserving the underlying OS error message, ensuring that unexpected errors remain completely visible and traceable.

**Q: How does this improve the developer and operator experience?**  
A: Operators get clear, consistent, actionable error guidance regardless of their operating system or language settings. Automation agents and test runners receive deterministic status and error feedback, eliminating mysterious test flakes or unhandled exceptions in diverse CI environments.
