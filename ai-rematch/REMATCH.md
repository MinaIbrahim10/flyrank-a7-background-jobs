# AI Prompt Rematch

## What changed in the second prompt

The first prompt described the required behavior, but it left room for the AI to rename events, choose different error messages, omit documentation details, and make its own structural decisions.

The improved prompt made observable contracts explicit.

It specified:

- exact route behavior
- exact HTTP status codes
- exact event names
- exact retry count
- exact failure message
- exact cron expression
- exact durable sleep type and duration
- exact README cron examples
- tests and documentation expectations
- a strict rule not to modify files outside `ai-rematch/`

## Result

The second AI generation followed the specification more closely.

Compared with AI V1:

1. The requested event names were preserved instead of silently renamed.
2. The exact runtime error message was preserved.
3. The README included the requested cron examples.
4. API behavior received broader automated test coverage.
5. Failed report state was handled explicitly.
6. The generated version still remained isolated inside its own directory.

Verification:

```text
Compilation: passed
Tests: 7 passed
No files outside ai-rematch/ modified
```

## One-sentence prompt lesson

Making names, messages, status codes, and schedules explicit contracts reduced the AI's freedom to make reasonable but specification-breaking substitutions.
