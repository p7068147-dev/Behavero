# Security Policy

Behavero is an early-stage local investigation utility, not a sandbox or malware
containment product.

- Run only commands you understand and are authorized to execute.
- Do not use `behavero run` to execute unknown or suspected malware.
- Use a disposable VM or isolated test machine for risky experiments.
- The monitored directory is not a security boundary. Programs can modify files
  elsewhere, access networks, or launch other processes.
- Reports may expose usernames, paths, filenames, and command arguments. Review
  them before sharing publicly.
