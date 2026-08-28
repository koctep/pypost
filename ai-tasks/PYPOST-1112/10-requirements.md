# PYPOST-1112: Key Source Registry Loader Malformed Input Resilience

## Goals

Ensure robust, graceful handling of malformed or non-object JSON key registry files across all key sources.
When a configured encryption key registry file contains non-object JSON data (such as a list, string, or scalar number):
- The system must treat the registry content as invalid and fail gracefully by returning no registry rather than raising unhandled runtime exceptions.
- Key source loading behavior must be uniform across all key providers, preventing crashes when external configuration files contain unexpected formats.

**Implementation language**: Python

## User Stories

- As an application operator or developer, when a configured environment keys file contains malformed or non-object JSON content, I want the system to handle the error gracefully and fall back to alternative resolution paths without crashing.
- As a maintainer, I want key source loaders to exhibit consistent input validation and error handling for all invalid payload structures.

## Definition of Done

- Key source configuration loaders validate that parsed file content conforms to expected mapping structures before attempting property access.
- Non-object JSON inputs cause loaders to log diagnostic information and fail gracefully without unhandled exceptions.
- Automated tests verify graceful failure across key loaders when encountering non-object JSON files.
- All quality gates pass.

## Task Description

- **Problem Description**: When key registry configuration files contain valid JSON that is not a dictionary/object structure, certain key source loaders fail with unhandled runtime errors during attribute access instead of recognizing the payload as invalid and returning cleanly.
- **Scope**: Ensure key configuration file loaders safely handle any valid JSON data type (lists, numbers, strings, booleans, null) without raising unhandled exceptions.
- **Constraints & Assumptions**: Existing valid dictionary-based key registries must continue to load without behavioral modification or performance degradation.

## Non-Functional Requirements

- **Robustness**: No unhandled exceptions on invalid or malformed file contents.
- **Observability**: Clear debug diagnostics when invalid payloads are detected.
- **Compatibility**: 100% backward compatibility with valid registry structures.

## Main Entities

- **Key Source**: Domain component responsible for locating and loading encryption key materials from environment or external files.
- **Key Registry File**: Persistent file containing key mappings and active key identifiers.
- **Key Material**: Cryptographic secrets managed by the application.

## User Scenarios

1. **Non-Mapping File Provided**: An environment points to a JSON file containing a list of strings instead of a key mapping. The loader detects the invalid structure, logs a debug message, and returns `None`, allowing fallback.
2. **Valid Mapping File Provided**: An environment points to a valid JSON key registry object. The loader successfully parses and resolves the active key.

## Q&A

| Question | Answer |
| --- | --- |
| Why is this change necessary? | To avoid unexpected crashes on malformed registry files and provide consistent error handling across all key sources. |
| Does this change alter valid registry loading? | No. Valid key registries continue to be parsed and validated exactly as before. |
