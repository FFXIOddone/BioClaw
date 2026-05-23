# BioClaw Autonomous Work Session Design Specification

**Date:** 2026-05-23
**Status:** Approved direction captured for implementation planning
**Scope:** Local-only autonomous project work sessions that can run for up to eight hours through bounded generations, durable checkpoints, and explicit permission policy.

## 1. Purpose

BioClaw currently proves that a product request can move through gene, transcript, protein, validation, assembly, delivery, and archive as a deterministic workflow. That is useful as a simulator, but it is not yet a practical autonomous project worker.

The next layer is an autonomous work session that can operate on a real local project for a bounded window. The session should decompose a project request into small project microtasks, run them through turns and generations, checkpoint progress, verify outputs, and leave local commits when generation evidence reaches terminal state.

The target is not uncontrolled autonomy. The target is a safe local worker that can make real progress for up to eight hours without losing state or drifting outside policy.

## 2. Autonomy Boundary

The default approved boundary is:

- local project reads are allowed;
- local file edits are allowed inside the configured workspace;
- local test, lint, build, and inspection commands are allowed when they match policy;
- local commits are allowed after a generation reaches terminal state and verification passes;
- checkpoint and report files are always allowed inside the configured session directory;
- pushing, deployment, publishing, external network changes, secret reads, package installation, destructive commands, and permission widening are denied unless explicitly allowed in the request file.

The runner must fail closed. If a microtask requests an operation outside policy, the task becomes terminal with a denied or blocked result and evidence. It must not silently skip the task and continue as if it succeeded.

## 3. Session Model

An autonomous session is a durable run record.

Required fields:

- `session_id`;
- `workspace_path`;
- `organism_id`;
- `product_name`;
- `started_at`;
- `max_runtime_seconds`, defaulting to 28800;
- `generation_limit`;
- `turn_limit`;
- `allowed_operations`;
- `denied_operations`;
- `requirements`;
- `status`;
- `checkpoint_dir`;
- generation records;
- task records;
- command records;
- local commit records.

Session statuses:

- `planned`;
- `running`;
- `paused`;
- `blocked`;
- `failed`;
- `completed`;
- `timeout`;
- `policy_denied`;
- `archived`.

Only one active session should exist per workspace by default. A request can opt into a separate `session_id`, but the runner must still record that it is operating on one product organism at a time.

## 4. Request Contract

The CLI should add:

```powershell
python -m bioscaffold run-session .\autonomous-request.json
python -m bioscaffold resume-session .\.bioclaw\sessions\<session_id>\session.json
python -m bioscaffold session-status .\.bioclaw\sessions\<session_id>\session.json
```

Minimal request:

```json
{
  "session_id": "session_auth_module_000001",
  "workspace_path": "C:/Users/jakeb/Projects/SomeProject",
  "organism_id": "organism_000001",
  "product_name": "Authentication Module",
  "max_runtime_seconds": 28800,
  "generation_limit": 24,
  "turn_limit": 96,
  "allow_local_edits": true,
  "allow_local_commits": true,
  "allow_push": false,
  "requirements": [
    {
      "requirement_id": "password-policy",
      "text": "Require password policy.",
      "artifact_type": "code"
    }
  ],
  "verification_commands": [
    "python -m pytest -v"
  ]
}
```

The request is intentionally explicit. The runner should not infer permission to push, deploy, install, or delete because those are irreversible or high-blast-radius operations.

## 5. Runtime Architecture

### 5.1 Session Controller

The session controller owns the long-running loop. It should:

1. load and validate the request;
2. create or resume a session record;
3. compile requirements into product genes;
4. build a queue of tiny project microtasks;
5. execute bounded turns;
6. review each generation;
7. run verification gates;
8. checkpoint after every generation;
9. commit when local edits exist and verification passes;
10. stop when terminal, blocked, failed, or budget exhausted.

The controller should not know how to edit code directly. It delegates actual work to task executors behind a small interface.

### 5.2 Policy Engine

The policy engine decides whether a task or command is allowed.

Default denied classes:

- push;
- deploy;
- publish;
- install;
- secret read;
- destructive filesystem operations;
- shell commands outside workspace;
- commands that modify global machine state;
- network mutation;
- credential or token printing.

Default allowed classes:

- read files inside workspace;
- search files inside workspace;
- write files inside workspace;
- create checkpoint/report files;
- run configured verification commands;
- run git status/diff/add/commit inside workspace.

### 5.3 Task Executors

The first implementation should support a small useful set:

- `inspect_file`: read or search local files;
- `write_file`: write a bounded local file change;
- `run_command`: run an allowlisted local command;
- `verify`: run configured verification commands;
- `git_commit`: commit terminal generation changes;
- `record`: write evidence, checkpoint, or report.

This is enough to prove real project progress without pretending the system can already do every software-engineering task.

### 5.4 Checkpoint Store

Every generation checkpoint should write:

- `session.json`;
- `generation_<n>.json`;
- `task_log.jsonl`;
- `command_log.jsonl`;
- `diff.patch`;
- `verification.json`;
- `delivery_report.json` when terminal.

The checkpoint must be sufficient to resume without relying on chat history.

### 5.5 Commit Gate

Local commits are allowed only when all are true:

- the generation is closed;
- all tasks are terminal;
- policy has no unresolved denial;
- verification commands pass;
- git diff is non-empty;
- commit message is generated from generation evidence.

If verification fails, the session should checkpoint the failure and either create follow-up tasks or stop as `blocked`, depending on remaining budget and configured limits.

## 6. Data Flow

```text
request JSON
-> session validation
-> genome compilation
-> project microtask queue
-> turn execution
-> generation review
-> verification gate
-> checkpoint
-> optional local commit
-> next generation or terminal delivery report
```

The important shift from the current runner is that a task is not just a simulated biological transition. It can become a real local project action, but it still must remain small, auditable, terminal, and policy-checked.

## 7. Error Handling

Errors must become evidence:

- invalid request: exit code `2`, no session created unless a session path was already established;
- policy denial: terminal task with `policy_denied` evidence;
- command failure: terminal task with exit code, stdout path, stderr path, and command class;
- verification failure: generation blocked with verification evidence;
- timeout: session status `timeout`, checkpoint written before exit;
- resume mismatch: exit code `2` when request/workspace/session IDs do not match;
- dirty workspace before start: blocked unless request explicitly allows starting dirty.

The runner must never report `completed` unless verification evidence exists for the final generation.

## 8. Testing Requirements

Tests must cover:

- request validation for default eight-hour runtime;
- denied push/deploy/install/destructive operations;
- session creation writes durable checkpoint files;
- a session can resume from `session.json`;
- a generation with terminal tasks and passing verification can create a local commit;
- failed verification blocks commit and writes evidence;
- timeout produces checkpointed `timeout` state;
- CLI commands return deterministic JSON.

The first implementation can use temporary git repositories in tests to prove edits, verification, commits, and checkpoints without touching external projects.

## 9. Non-Goals

The first autonomous mode will not:

- push to remotes;
- deploy products;
- install dependencies;
- read secrets;
- call model providers directly;
- manage multiple active products in one workspace;
- promise high-quality code generation without a bounded executor;
- run unbounded shell commands.

Those may become later generations after the local-only loop proves durable.

## 10. Acceptance Criteria

The slice is accepted when:

- a JSON request starts a session with `max_runtime_seconds` defaulting to 28800;
- the session creates checkpoints under `.bioclaw/sessions/<session_id>/`;
- the runner can execute at least one local edit through a terminal project microtask;
- verification commands gate commits;
- a passing generation creates a local commit when `allow_local_commits` is true;
- a failing generation leaves checkpointed evidence and does not commit;
- `resume-session` continues from a saved checkpoint;
- `session-status` prints deterministic JSON;
- full tests pass.
