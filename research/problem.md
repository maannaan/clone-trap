# Problem

A repository that works on the author's machine often fails after a clean clone.

The original developer, CI cache, or coding-agent workspace already has Redis, a global CLI, a generated file, a sibling checkout, or a local `.env`. A fresh machine does not. README may say `npm install && npm run dev` while startup code also reads `REDIS_URL` and expects PostgreSQL.

This is declaration drift, not missing documentation in the abstract:

- source or runtime references a requirement
- setup docs, examples, compose, and manifests do not account for it
- a clean clone cannot reconstruct the author's environment

Clone Trap treats the working tree as evidence. It compares what the repository *claims* you need with what the repository *appears* to require, and reports only the gaps that have independent signals.

It is a reminder, not an enforcer. It must stay read-only, offline, and silent when evidence is thin. It never runs install, generate, Docker, or application commands. It never says a clone will fail.
