# Validation-driver variant

## Concrete intent

Run declared canonical and harness validators without relying on Python executable bits or collapsing independent command outcomes.

## Approach

Consume an explicit no-shell command plan, invoke declared Python helpers through an interpreter, bound outputs, preserve package scope and exit status, and require every required validator to pass.

## Preserved nuance

The driver never installs tools, invents a fallback, redirects caches, or calls a harness validator a canonical pass.

## Relationships and uncertainty

This complements the resolver and instruction variants. Review should decide whether command evidence should remain stdout JSON or gain a separately owned durable recorder.
