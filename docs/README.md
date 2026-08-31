# Proof screenshots

## Core assignment proof

`inngest-core-proof.png`

Shows the core Inngest runs, including successful and failed report work and automatic heartbeat cron activity.

## Concurrency proof

`concurrency-limit-proof.png`

Shows the five `make-report` runs used to demonstrate the concurrency limit of two.

## Durable restart — before restart

`durable-before-restart.png`

Shows the durable run after earlier steps had completed while FastAPI was interrupted.

## Durable restart — after restart

`durable-after-restart.png`

Shows the same durable workflow after FastAPI restarted and the run completed.
