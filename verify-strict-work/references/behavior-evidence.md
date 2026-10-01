# Behavior evidence and acceptance

For operation or lifecycle changes, use authorized behavior evidence to check the declared operation boundary: ordinary success, applicable partial completion, required finalization, specified recovery succeeding or exhausting its contract, and the complete typed outcome returned afterward. Exercise supported paths rather than forcing every operation into a generic success/failure matrix or adding speculative recovery scenarios.

Check completed effects, original and recovery failures, resource identities, and remaining state together. Resource custody alone proves neither disposal completion nor a transfer of workflow responsibility. A test can correctly pass by observing the promised typed failure after required handling; preserve the distinction between that contractual correctness and the operation's failure. Consumer evidence should exercise the consumer's response without reimplementing shared handling or requiring all workflows to respond identically.

Treat planned, written, compiled, and executed as separate observations. Test source does not prove compilation or execution; a successful build establishes compilation only for the tests and configuration it actually included, not that a test body ran. Report a newly written, unexecuted test as unexecuted rather than failed or behaviorally covered.

Attribute execution evidence to the actual command, scope, source and configuration, timestamp, and underlying result or evidence locator available. Missing attribution limits the claim; it does not authorize another read, command, or artifact. After a source, configuration, or scope change, reconcile only the affected current claims. Preserve the earlier result as an observation of its original inputs, even when it no longer supports current acceptance.

A focused nonzero command is diagnostic evidence even when its test assertions say `N pass, 0 fail`.

Report independently:

- assertions or test cases;
- process exit status;
- policy thresholds;
- artifact generation;
- canonical gate status.

Do not call exit code `1` passing, successful, clear, or green. Exit `0` alone establishes neither passing behavior nor an accepted focused or canonical gate: the observed scope and results must satisfy that gate's declared criteria, including its required assertions and policy thresholds. Close a behavioral claim only when executed evidence observes its named semantic owner and contract. Do not call focused checks equivalent to an unrun top-level gate. Worker or verifier summaries are not proof without the underlying authorized artifact or command result.
