# Review effect matrix

| Effect class | Typical action | Usually implied by `review` alone? | Separate authority example |
| --- | --- | --- | --- |
| Read | Inspect named source or logs | Yes, when relevant | User places repository or artifact in scope |
| Inline analysis | Return findings in the response | Yes | User asks to review, diagnose, or explain |
| Persist artifact | Write report, ledger, or scratch packet | No | User asks to create a report file |
| Collector | Run a helper that produces evidence files | No | Workflow explicitly requires collector output |
| Probe or verification | Execute tests, builds, network probes, or behavioral checks | No | User authorizes validation or verification |
| Source mutation | Apply a remediation | No | User asks to fix or implement |
| Git persistence | Stage, commit, amend, or push | No | User explicitly requests that exact Git effect |
| Activation | Install, link, synchronize, register, or enable | No | User explicitly authorizes activation |
| Publication | Send, publish, deploy, or open external changes | No | User explicitly requests external publication |

For each proposed action, cite the literal instruction or controlling workflow contract. Artifact creation does not imply activation; validation does not imply remediation; implementation does not imply commit; commit does not imply push.

Continue an independently authorized lane even when a neighboring class is blocked. Do not create optional evidence merely to keep working.
