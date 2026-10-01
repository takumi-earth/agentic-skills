# Upstream reconciliation and reviewed bases

Use this procedure for an authorized source update. Comparison alone does not grant these effects.

## Preserve three distinct inputs

- The archived upstream base owns the previous external bytes and committed provenance.
- The requested committed upstream revision owns current external input, including original notices and executable status.
- The canonical repository owns our customized behavior, metadata, compact instructions, references, and distribution policy.

For each changed package, read complete relevant files and classify every material upstream delta: adopted, represented in our layout, incompatible with a settled local choice, or deferred. Exact-text equality is sufficient for an unchanged external file, not for concluding that a refactored skill preserves behavior. Do not use package versions, whole bodies, hashes, or first-match replacement to patch semantic instruction ownership blindly.

An unchanged local file can take an authorized upstream correction directly when it introduces no unresolved contract or ownership choice. A customized entrypoint needs semantic reconciliation; a new upstream section may belong in an existing conditional reference rather than the core. Preserve meaningful negative cases and exception boundaries. Do not retire a local capability because upstream removed its filename.

New upstream packages are review leads. Adopt them into the canonical root only after the user selects that effect. Upstream-only removal can be recorded while keeping the local package; local deletion or capability retirement needs its own user decision. Contributor-only definitions stay distinct from user-facing enablement.

## Validate before advancing a base

1. Close the complete authorized source correction set for the selected packages.
2. Run `skills-ref validate ./<package>` and the available harness validator on each changed package. Preserve interface policy; do not regenerate unrelated fields.
3. Run the package's direct script tests and relevant routing/workflow controls. Exit status, assertions, source alignment, runtime compatibility, and installation remain separate observations.
4. Generate the final comparison after the last source edit and validation. A changed upstream revision, local file, or baseline invalidates the affected report, not the user's settled design decision.

For the required current report, use the helper's artifact option rather than redirecting verification output:

```bash
python3 scripts/manage_ripwire_skills.py check \
  --output ~/agentic-skills/.scratchpad/manage-ripwire-skills/comparison.json \
  --replace-report
```

Use the exact report path under the declared canonical repository's `.scratchpad/manage-ripwire-skills/`; adjust it when another root is explicitly selected. `--replace-report` refreshes only this manager's existing comparison for the same roots. The helper refuses unrelated report replacement and all output outside canonical scratch.

## Record every review unit

Use one decision per changed package. For an accepted unit, name existing canonical files that express the reconciled behavior and state what was adopted or deliberately represented locally. An existing filename does not prove semantic coverage; the agent must establish it from the reviewed source and authorized tests.

```json
{
  "packages": [
    {
      "name": "ripwire-navigate",
      "disposition": "accepted",
      "reason": "Adopt the new selector while preserving compact navigation and the staged-only boundary.",
      "evidence": ["ripwire-navigate/SKILL.md", "ripwire-navigate/navigation-reference.md"]
    },
    {
      "name": "ripwire-opt-remarks",
      "disposition": "deferred",
      "reason": "A new contributor command needs an explicit ownership decision."
    }
  ]
}
```

The example is a shape, not a claim that those packages changed. Decisions and any required comparison report are workflow input under canonical scratch; they never create permission for the chosen source effects.

```bash
python3 scripts/manage_ripwire_skills.py acknowledge \
  --report ~/agentic-skills/.scratchpad/manage-ripwire-skills/comparison.json \
  --decisions ~/agentic-skills/.scratchpad/manage-ripwire-skills/decisions.json
```

Pass the same explicit roots used by `check` when defaults do not apply. The helper takes an exclusive writer lock, verifies fresh baseline/upstream/local inputs, requires complete unique dispositions, and advances only accepted package bases. All-deferred input is a no-write result. Stale inputs or a retained writer lock cause a diagnostic; do not steal the lock, overwrite the archive, or reset Git to make acknowledgement pass.

The archive is an upstream history record, not proof of user acceptance, runtime compatibility, or successful synchronization. Re-read the post-check state and report outstanding units without creating another audit of unchanged facts.

## Keep ownership durable

`$link-agentic-skills` owns separately authorized canonical distribution. Never run the tool repository's skill installer after an upstream pull. If an update changed actual harness link targets, report the exact drift and obtain the required link-migration authority instead of silently installing another copy.
