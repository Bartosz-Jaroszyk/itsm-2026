# AI review of `lab5-canary/`

Canary parent M: `f348cd7d5de5d651293a514448624f65ec0f3003`  
Canary commit C: `804b61c757e1749d5c140939109b50c9a71d3281`  
Route: local. Reviewer: Copilot security-review agent; underlying model identifier was not reported.

## Original reviewer response

<pre>
{
  "summary": "Reviewed the canary branch tip against its parent: C=804b61c757e1749d5c140939109b50c9a71d3281 and M=f348cd7d5de5d651293a514448624f65ec0f3003. The changed application code contains unsafe shell and SQL interpolation, an unrestricted customer-configured outbound request, and disabled TLS certificate verification. Findings below identify the affected changed lines; no secret values are reproduced.",
  "findings": [
    {
      "path": "lab5-canary/app/attachment_export.py",
      "start_line": 11,
      "end_line": 11,
      "class": "injection",
      "CWE": "CWE-78",
      "rule_id": "shell-command-injection",
      "message": "Untrusted ticket_id is interpolated into a shell command executed with shell=True, allowing command execution through a crafted ticket ID."
    },
    {
      "path": "lab5-canary/app/ticket_search.py",
      "start_line": 8,
      "end_line": 8,
      "class": "injection",
      "CWE": "CWE-89",
      "rule_id": "sql-query-injection",
      "message": "needle is interpolated directly into SQL, allowing crafted search input to alter the query and expose tickets beyond the intended title match."
    },
    {
      "path": "lab5-canary/app/webhook_relay.py",
      "start_line": 6,
      "end_line": 6,
      "class": "ssrf",
      "CWE": "CWE-918",
      "rule_id": "customer-webhook-ssrf",
      "message": "A customer-configured callback URL is used for an outbound POST without destination restrictions, allowing requests to loopback or private-network services."
    },
    {
      "path": "lab5-canary/app/avatar_fetch.py",
      "start_line": 6,
      "end_line": 6,
      "class": "insecure-transport",
      "CWE": "CWE-295",
      "rule_id": "tls-certificate-verification-disabled",
      "message": "TLS certificate verification is disabled, allowing a network attacker to intercept the request and substitute the returned avatar bytes."
    }
  ]
}
</pre>

## Converter input

The following block normalizes the reviewer response to the input schema of
`tools/ai-to-sarif.py`.

```json
{
  "summary": "Reviewed the canary branch tip against its parent: C=804b61c757e1749d5c140939109b50c9a71d3281 and M=f348cd7d5de5d651293a514448624f65ec0f3003. The changed application code contains unsafe shell and SQL interpolation, an unrestricted customer-configured outbound request, and disabled TLS certificate verification. Findings below identify the affected changed lines; no secret values are reproduced.",
  "findings": [
    {
      "file": "lab5-canary/app/attachment_export.py",
      "start_line": 11,
      "end_line": 11,
      "class": "injection",
      "cwe": "CWE-78",
      "rule": "shell-command-injection",
      "message": "Untrusted ticket_id is interpolated into a shell command executed with shell=True, allowing command execution through a crafted ticket ID."
    },
    {
      "file": "lab5-canary/app/ticket_search.py",
      "start_line": 8,
      "end_line": 8,
      "class": "injection",
      "cwe": "CWE-89",
      "rule": "sql-query-injection",
      "message": "needle is interpolated directly into SQL, allowing crafted search input to alter the query and expose tickets beyond the intended title match."
    },
    {
      "file": "lab5-canary/app/webhook_relay.py",
      "start_line": 6,
      "end_line": 6,
      "class": "ssrf",
      "cwe": "CWE-918",
      "rule": "customer-webhook-ssrf",
      "message": "A customer-configured callback URL is used for an outbound POST without destination restrictions, allowing requests to loopback or private-network services."
    },
    {
      "file": "lab5-canary/app/avatar_fetch.py",
      "start_line": 6,
      "end_line": 6,
      "class": "insecure-transport",
      "cwe": "CWE-295",
      "rule": "tls-certificate-verification-disabled",
      "message": "TLS certificate verification is disabled, allowing a network attacker to intercept the request and substitute the returned avatar bytes."
    }
  ]
}
```
