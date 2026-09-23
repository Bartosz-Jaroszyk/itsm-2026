# Agent policy

- Bash(rm *): deleting files can destroy work outside the review scope, so cleanup remains an author decision.
- Bash(git push *): publishing changes can affect shared history and releases, so only the repository owner may push.
- Bash(docker *): container commands can consume resources or alter the host environment, so execution requires explicit owner control.
- WebFetch: external content may be untrusted or disclose project context, so reviewers use only repository-provided sources.
