[Preconditions]
- Existing project repository is available.
- Agent/CLI is started at the repository root.
- Version control/backup is recommended before major changes.

[Steps]
1. Provide `prompts/MASTER_PROMPT.md` to the primary agent using the CLI's documented file-input mechanism.
2. Allow the agent to inspect the project and actual CLI capabilities.
3. Configure provider credentials through environment variables/secret management; never paste secrets into committed files.
4. Supply the three administrator emails or stable IDs through the documented secure configuration.
5. Review tests, migration/setup instructions, and final report before production deployment.

[Safety]
- Tests must use mock/sandbox email transport.
- Production deployment, real customer emails, destructive operations, and irreversible changes require explicit authorization.
- Unsupported model switching or auto-allow settings must be reported, not fabricated.
