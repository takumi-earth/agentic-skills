# Validator plan contract

The driver accepts JSON:

```json
{
  "schema_version": 1,
  "packages": ["skill-a", "skill-b"],
  "validators": [
    {
      "id": "canonical",
      "kind": "canonical",
      "required": true,
      "command": ["skills-ref", "validate", "{package}"],
      "interpreter": null
    },
    {
      "id": "harness",
      "kind": "harness",
      "required": true,
      "command": ["path/to/quick_validate.py", "{package}"],
      "interpreter": "python3"
    }
  ],
  "max_output_bytes": 20000
}
```

The driver substitutes `{package}` as one argument, never through a shell. Each result records validator ID and kind, package, full argument list, start state, exit code, bounded output, omitted-byte counts, and duration.

Overall exit `0` requires all required validator/package pairs to start and exit `0`. Optional failure remains visible. Missing commands, invalid plans, and nonzero validators are distinct. The driver never installs a command, chooses a fallback, edits a package, or redirects cache and temporary locations.
