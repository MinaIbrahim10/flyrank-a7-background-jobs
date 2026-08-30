# FlyRank A7 — Your First Background Job

FlyRank Internship — Backend Track — Week 4 — Assignment A7.

This project demonstrates the professional background-job pattern:

**accept fast → work in the background → report status**

## Stack

- Python
- FastAPI
- Inngest
- Inngest Dev Server

## Current stage

Stage 0 — Hello, server.

## Stage 3 — Retries and validation

A missing topic is a bad request and is rejected immediately with `400`, so no background event is created. A runtime failure such as a temporary service or network problem belongs inside the background job, where retries and backoff can recover from a bad moment without making the client wait.
