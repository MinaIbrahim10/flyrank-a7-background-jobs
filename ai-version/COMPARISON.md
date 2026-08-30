# AI V1 Comparison

## What the AI did well

The AI version passed compilation and four automated endpoint tests.

It also added several implementation details that were stronger than my first hand-built version:

1. It protected the shared in-memory report dictionary with a `threading.Lock`.
2. It added an Inngest `on_failure` handler so a permanently failed report is updated to `status="failed"`.
3. It added automated tests immediately, including a check that invalid topic input does not enqueue an event.
4. It removes a newly created pending report if sending the Inngest event itself fails.

These are useful production-minded improvements.

## What the AI changed or silently decided

The generated implementation did not follow every requested contract exactly.

### 1. Event names changed

Requested hello event:

```text
test/hello
```

AI V1 used:

```text
demo/hello.requested
```

Requested report event:

```text
report/requested
```

AI V1 used:

```text
reports/requested
```

The system still works internally because both sender and receiver use the same AI-chosen event name, but this silently changes the requested external contract.

### 2. Failure message changed

Requested:

```text
The report oven is broken!
```

AI V1 used:

```text
report build requested to fail
```

The behavior is similar, but the requested observable failure contract was not preserved exactly.

### 3. Project structure was silently chosen

My hand-built version separates:

```text
app/main.py
app/inngest_jobs.py
app/store.py
```

AI V1 puts nearly the entire implementation into:

```text
ai-version/app.py
```

The AI version is shorter and easy to inspect for a small demo. My version has clearer separation of API, job definitions, and state.

### 4. README coverage was incomplete

The generated README explains the core background-job flow but does not include the requested cron examples:

```text
0 8 * * *
0 22 * * 0
```

### 5. The AI added concurrency protection without being asked

AI V1 introduced a `threading.Lock` around shared report state.

That was a sensible decision, but my original prompt did not specify a concurrency model, so the AI decided one itself.

## Hand-built version vs AI V1

### Hand-built version advantages

- Exact requested event names.
- Exact requested failure behavior/message.
- Clear separation between API, Inngest functions, and store.
- README follows the assignment stages closely.
- Built stage-by-stage with visible checkpoints.

### AI V1 advantages

- Automated tests from the first generated version.
- Locking around shared in-memory state.
- Failure callback updates reports to `failed`.
- Cleanup when event enqueueing fails.
- More compact implementation.

## What my original prompt forgot to specify clearly

The prompt described the major behavior well, but it did not strongly say that names and messages were immutable API contracts.

It also did not explicitly require:

- exact event names with no renaming
- exact failure message
- exact README cron examples
- a preferred project structure
- failure-state persistence
- thread-safety expectations

Those omissions gave the AI room to make reasonable but different decisions.

## V1 verification

```text
python -m compileall .       PASS
python -m unittest -v        4 passed
required routes              PASS
git diff --check             PASS
```

The AI version is functional, but not specification-identical.
