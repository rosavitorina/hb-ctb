[Role/Context]
Principal Full Stack Developer, Technical Lead, Security Engineer, Project Coordinator.
Existing application with functional registration and login. Extend the current codebase; do not start a new project.

[Task]
Implement:
1. Invitation/access-code email delivery.
2. Successful-registration confirmation email.
3. Role-based access control (RBAC): `admin` and `user`.
4. Safe bootstrap for three explicitly configured administrators.
5. Automated tests, configuration docs, and final report.
6. Autonomous execution and cost-aware multi-agent orchestration, subject to actual CLI capabilities.

[Execution Policy]
- Work autonomously from repository inspection through implementation and verification.
- Do not request approval for routine decisions or implementation steps.
- Ask only if a genuinely blocking decision cannot be safely resolved from the repository/configuration.
- Never perform production deployment, destructive operations, irreversible data changes, paid-service activation, or real customer email sending without explicit authorization.
- Do not claim success unless verified.

[Phase 1: Repository Audit]
Before editing:
- Inspect repository tree, README, manifests, environment examples, database schema/migrations, auth middleware, API routes, frontend forms, and tests.
- Identify framework, language, database, deployment assumptions, auth/session strategy, email dependencies, and existing conventions.
- Search for existing functions/components equivalent to:
  - `login_user`
  - `create_user`, `register_user`, or registration handler
  - invitation/access-code generation and validation
  - email/notification services
  - user schema/model and database access layer
  - auth middleware, session/JWT handling, route guards
- Map relevant files and call paths before implementation.
- Reuse existing functions, files, schemas, components, services, and utilities. If `login_user` or equivalent exists, integrate with it; do not create a competing implementation.
- Make the smallest coherent changes; do not replace working architecture without need.
- Inspect Git status. Preserve unrelated changes and never overwrite/delete unrelated work.

[Role: CLI/Agent Orchestration]
Inspect actual CLI capabilities using supported help commands, local documentation, and configuration. Do not assume commands, flags, endpoints, or settings exist.

[Task: Model Selection and Delegation]
- Use the strongest available model as coordinator for architecture, security-sensitive decisions, integration, and final review.
- Delegate bounded, low-risk tasks to the cheapest suitable available subagents/model tiers.
- Appropriate delegated tasks: repository mapping, documentation review, isolated tests, existing-function discovery, and non-sensitive implementation review.
- Keep authentication design, authorization boundaries, migrations, secrets handling, and final integration under lead-agent control.
- Give subagents concrete deliverables: files inspected, findings, proposed changes, test results, risks.
- Avoid simultaneous edits to the same files. Assign ownership and integrate deliberately.
- Use automatic model switching only if supported; otherwise use documented model selection or explicit delegation.
- Do not claim a capability is enabled unless verified.

[Task: Permissions and Unattended Execution]
- Inspect documented auto-approve, auto-allow, unattended, and permission-bypass features.
- If supported, use the documented mode for routine file edits, local builds, and tests.
- Never invent a `/btw` command, bypass flag, or configuration key.
- If unsupported, use the closest documented option and report the limitation.
- Keep execution non-interactive where safely supported.
- Do not request approval for routine steps.
- Do not expose secrets in logs, terminal output, reports, commits, or generated docs.
- Treat destructive operations, production deployments, real customer emails, paid-service activation, and irreversible data changes as protected actions requiring explicit authorization.
- Never weaken security to enable unattended execution.

[Feature A: Invitation/Access-Code Email]
- Locate and reuse current invitation/access-code generation and validation logic.
- Integrate email delivery through existing provider/abstraction if present.
- Send the correct code to the exact email associated with the invitation.
- Preserve current validation rules and email-code association.
- Add/preserve expiration, single-use behavior, and attempt limits where compatible with the current design. Assess compatibility before changing existing flows.
- Never leak codes through logs, URLs, client errors, or analytics.
- Handle provider failures gracefully: generic user-facing response, safe server-side diagnostics, no false “sent” status.
- Prevent duplicate sends where practical; rate-limit abuse.
- Preserve existing admin/developer-only restrictions on invitation generation unless current product requirements specify otherwise.

[Feature A2: Registration Confirmation Email]
- Send a confirmation email to the registered address after successful account creation.
- Trigger only after the registration transaction/account-creation operation succeeds.
- Never send success confirmation after failed registration.
- Handle transient provider errors; prefer existing queue/background-job/retry infrastructure. If absent, implement the simplest reliable solution consistent with the stack.
- Avoid duplicate accounts or duplicate confirmation messages during retries.
- Distinguish “account created” from verified email address. Sending a message alone must not mark email as verified.
- Reuse existing email-verification flow if present; do not create a competing flow.

[Feature A3: Email Provider and Configuration]
- Inspect existing provider/configuration first.
- If none exists, choose a transactional email provider compatible with the stack and project constraints.
- Store credentials in environment variables or established secret management.
- Update `.env.example` or equivalent with placeholders only; never commit real credentials.
- Document required variables, sender verification, local testing, and provider setup.
- Never hard-code API keys, SMTP passwords, tokens, or private credentials.
- Use safe templates with appropriate escaping and consistent sender identity.
- Tests must use mocks, sandbox provider, or local test transport; never send real email during tests.

[Feature B: Role-Based Access Control]
[Data Model]
- Inspect existing user schema and authorization patterns.
- Add role field or equivalent using project conventions.
- Minimum roles: `admin`, `user`.
- Public registrations must receive `user` by default on the server.
- Never trust role values supplied through public forms or request payloads.
- Add deterministic, safe migration/backfill for existing accounts; do not accidentally grant admin privileges.
- Centralize roles using existing enums/constants patterns where available.

[Initial Administrators]
- Inspect existing admin-management/seed mechanisms.
- Provide a safe, idempotent bootstrap method (seed script or documented one-time command) that promotes only explicitly configured email addresses or stable user IDs.
- Do not invent administrator identities; use only project-owner-supplied configuration.
- Normalize email addresses consistently before matching.
- Never make the first registered user an administrator.
- Never expose an unauthenticated public endpoint for granting admin privileges.
- Bootstrap must not unexpectedly downgrade existing roles.
- If identities are not configured, finish implementation and document how to configure them.

[Backend Authorization]
- Enforce roles on backend/API/server actions for every protected operation.
- Frontend visibility is not authorization.
- Reuse existing auth middleware, sessions/JWT, and user-loading functions.
- Derive role from a trusted server-side source; prevent client-forged roles.
- Implement centralized authorization helper/middleware consistent with the stack.
- Return appropriate unauthorized/forbidden responses without leaking sensitive details.
- Preserve login, logout, registration, and session-renewal behavior.
- Account for role changes according to the actual session/token architecture; do not assume stale tokens refresh automatically.

[Frontend Permissions]
- Inspect existing navigation, layouts, pages, and components.
- Show admin-only navigation/controls only to authenticated admins.
- Prevent ordinary users from accessing admin views via direct URLs.
- Preserve existing UI conventions and normal user experience.
- Do not build a full admin dashboard unless needed for existing architecture or required for functional role management.
- Avoid duplicated auth state or a second authentication system.

[Required Authorization Tests]
- Ordinary user denied admin-only endpoints/actions.
- Administrator allowed authorized admin operations.
- Unauthenticated visitor denied protected operations.
- Registration request cannot self-assign `admin`.
- Existing accounts migrate safely.
- Bootstrap promotes only explicitly configured administrators.
- Login and registration continue working.

[Security/Data Integrity Constraints]
- Validate and normalize email appropriately.
- Use parameterized queries or safe ORM mechanisms.
- Never expose invitation codes, passwords, session tokens, provider credentials, or sensitive personal data.
- Enforce authentication/authorization server-side.
- Rate-limit invitation requests and email sending.
- Prevent account enumeration where relevant using safe, consistent public responses.
- Use transactions for related DB changes where supported.
- Add migrations; do not manually alter deployed databases.
- Keep dependencies minimal and compatible.
- Never disable auth, validation, tests, or security middleware to pass builds.
- Never commit provider credentials.
- Never send real emails or deploy to production during tests.

[Execution Workflow]
1. INSPECT: map codebase and identify real entry points for registration, login, invitations, database operations, and authorization.
2. PLAN: create concise internal task breakdown with dependencies, likely files, migration considerations, and tests. Delegate isolated research/testing when useful. Avoid excessive documentation before understanding the code.
3. IMPLEMENT:
   - Extend existing invitation flow to send email.
   - Add registration confirmation email.
   - Add roles, safe migration, and admin bootstrap.
   - Add backend authorization and frontend visibility/route protection.
   - Add configuration documentation and automated tests.
   - Follow existing language, naming, formatting, and architecture.
4. VERIFY:
   - Run relevant tests, lint, type checks, migration validation, and build commands supported by the project.
   - Use mocks/sandbox transport for email tests.
   - Test authorization at API/server layer, not only UI.
   - Review diff for unrelated changes, duplicate functionality, secrets, insecure defaults, and privilege escalation.
   - Fix implementation-caused regressions.
   - Explain tests that could not run; never claim they passed.
5. REPORT: provide concise final report with:
   - Features implemented.
   - Existing functions/files reused and important files changed.
   - Required migrations/setup.
   - Environment variables and provider configuration.
   - How to configure the three initial administrators.
   - Tests/build checks actually run and results.
   - Known limitations/manual steps.

[Acceptance Criteria]
- Existing login and registration remain functional.
- Authorized operator can generate an invitation code and trigger delivery to its associated email.
- Successful registration triggers a confirmation email through configured provider/reliable delivery mechanism.
- Email failures are handled without false success messages.
- Public registrations cannot choose their own role.
- Three explicitly configured people can be promoted through safe documented bootstrap.
- Backend protected operations enforce roles.
- Frontend admin-only elements are appropriately restricted.
- Migration and setup instructions are included.
- Relevant tests are added and run where environment permits.
- No secrets are committed and no unrelated functionality is overwritten.

[Non-Negotiable Constraints]
- Do not recreate existing authentication functions if they can be reused.
- Do not assume filenames, frameworks, CLI commands, providers, or configuration keys before inspecting the repository.
- Do not fabricate test results.
- Do not grant admin privileges by default.
- Do not rely on frontend-only permission checks.
- Do not expose credentials or invitation codes in logs.
- Do not stop after producing a plan; implement the changes.
- Do not wait for routine approvals when safe autonomous execution is supported.
- Lead agent remains responsible for architecture, security decisions, integration, and final quality control.

[Start]
Inspect the repository and actual CLI capabilities. Execute the workflow end-to-end.
