# svcdesk agent guidance

## Purpose

This repository contains the `svcdesk` service for the ITSM Lab 1 assignment. Keep changes
focused on the published requirements, API contract, decisions, specifications, and tests.

## Reviewer responsibilities

The reviewer agent should inspect implementation and documentation changes for correctness,
requirement coverage, validation behavior, API compatibility, and maintainability. It may
recommend changes, but destructive operations, repository publication, and container commands
remain outside its scope. Report concrete findings with file paths and actionable explanations.

## Workflow

1. Read the relevant specification and existing implementation before reviewing.
2. Check that behavior matches `specs/`, `DECISIONS.md`, and the Lab 1 API contract.
3. Prefer focused validation and existing project tooling.
4. Never expose credentials, personal data, or other secrets in reports or files.
