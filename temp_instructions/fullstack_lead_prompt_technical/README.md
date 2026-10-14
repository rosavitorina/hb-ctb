[Package]
Name: Full Stack Lead — Technical Prompt Pack
Purpose: Compact, block-structured instructions for an autonomous coding agent implementing email delivery, registration confirmation, and admin/user RBAC in an existing project.

[Files]
- `prompts/MASTER_PROMPT.md`: main execution prompt.
- `docs/USAGE.md`: usage instructions.

[Usage]
1. Open the CLI/agent in the root of the existing project repository.
2. Provide `prompts/MASTER_PROMPT.md` as the lead agent's main instruction.
3. Configure the transactional email provider and the three administrator identities using the secure mechanism documented by the implementation.
4. Review the final report and run deployment steps separately.

[Limitations]
Model switching, subagent delegation, and auto-allow depend on the installed CLI's real capabilities. The prompt directs the agent to inspect supported commands/settings and never invent unsupported flags.
