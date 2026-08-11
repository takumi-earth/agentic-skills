---
name: bootstrap-skills-ref-validation
description: "Resolve and verify a repository-pinned `skills-ref` validator when skill validation reports a missing CLI or `skills_ref` module. Use in canonical skill checkouts that may vendor or pin the validator and when Python helpers may lack executable mode. Do not install dependencies, mutate environments, or substitute validators without explicit authority."
---

# Bootstrap Skills-Ref Validation

Distinguish source discovery, environment mutation, and validation.

## Resolve identities before acting

Read [the bootstrap contract](references/bootstrap-contract.md). Track these identities separately:

- distribution name, commonly `skills-ref`;
- import module, commonly `skills_ref`;
- CLI executable, commonly `skills-ref`;
- repository-pinned source path;
- package-declared version and dependencies.

Check the repository's own guidance and pinned reference layout before declaring the validator unavailable. Treat user shorthand as an input to bounded resolution, not permission to search the whole home directory.

## Keep installation separately authorized

If the CLI or module is absent but an expected pinned source exists, report the exact source, metadata, intended install command, dependency effects, and verification commands. Run the install only when the user explicitly authorizes environment mutation. Do not redirect caches or temporary directories to evade a failed intended command.

## Verify provenance and validation

After an authorized install, verify the imported module path, CLI version or help surface, declared source version, and cleanliness of pinned reference input. Invoke `.py` helpers through their declared Python interpreter when they are not executable; a missing executable bit is not by itself a sandbox failure.

Report canonical validator status and any harness-specific validator status separately. Never treat a fallback validator as proof that the canonical gate passed.
