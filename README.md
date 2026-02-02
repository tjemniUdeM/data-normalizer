## Status
🚧 Work in progress: building a CLI tool to normalize messy CSV/Excel files into clean, backend-ready formats.

## Date parsing rule

This tool supports mixed date formats using a deterministic rule:

**The month must always be the middle component of the date.**

### Accepted formats
Any non-digit delimiter is allowed (`-`, `/`, `.`), as long as the order is one of:

- `YYYY-MM-DD`
- `DD-MM-YYYY`

Examples:
2024-01-05
01/06/2024
2024/01/07

All accepted formats are normalized to:

YYYY-MM-DD

and stored internally as datetime values (`TIMESTAMP` in SQL).

### Unsupported / ambiguous formats
Dates where the month is **not** in the middle are rejected and treated as missing values:
MM-DD-YYYY
YYYY-DD-MM