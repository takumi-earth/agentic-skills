# Resolver-script variant

## Concrete intent

Report validator installation and provenance state through deterministic, read-only discovery.

## Approach

Inspect only the supplied repository and pinned source path, then emit typed CLI, import, source, metadata, version, dependency, and helper-mode states plus an inert install plan.

## Preserved nuance

The script never installs, searches broadly, rewrites source, or treats source presence as authority to mutate the environment.

## Relationships and uncertainty

This executable alternative complements the instruction variant. Review should decide which packaging metadata formats and helper paths belong in the generic resolver.
