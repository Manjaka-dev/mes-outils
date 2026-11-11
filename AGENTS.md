# Mes outils — Agent instructions

## Mandatory Agent Rules

Any development agent working on this repository must strictly adhere to the following rules:

1. **Mandatory implementation plan**: Always provide a detailed implementation plan that the user must explicitly validate BEFORE any modification (no file may be modified without prior validation).
2. **No assumptions or improvisation**: Never make assumptions or improvise without explicit approval from the user.
3. **Systematic clarification**: In case of error, inconsistency, ambiguity, lack of information, or missing details in the request, always ask the user for clarification before taking action.
4. **Git commits and pushes**: Execute `git commit` or `git push` only after obtaining the user's explicit and formal approval for the specific action.
5. **No Docker deployment**: Never execute Docker deployments (`docker run`, `docker compose up`, etc.).

## Project context

- Mes outils is a personal Windows dashboard for developers. A floating Tkinter bubble opens the dashboard in an Edge app window. The interface supports French and English, light and dark themes, and a command palette (`Ctrl+K`).
- The Python server in `outil/hub.py` listens on `127.0.0.1:8760` by default. The interface uses plain HTML and JavaScript in `outil/hub.html` and `outil/web/`. GitHub, mail and other optional integrations contact their respective external services.
- Features include shortcuts, project and development server management, GitHub, Docker container management, port inspection, API requests, SSH keys, mail, notes, agenda, a password vault, snippets, clipboard history and time tracking.
- Tabs are modular. A tab's JavaScript registers its view, and its optional Python module exposes actions through `ROUTES` under `/api/<module>/<action>`. Follow [the module guide](docs/MODULES.md) for routing, UI conventions, translation and tests.
- Installed copies keep settings and data under `%APPDATA%\Mes outils`. Source checkouts use local `outils.json` and `donnees/`. The app uses the Windows Credential Manager for GitHub and mail credentials and a separate encrypted vault for saved passwords. Keep personal settings, data and secrets out of the repository.
- The source setup uses Python 3.10 or newer with Tkinter and the dependencies in `requirements.txt`. Run the existing test suite with `python -m unittest discover -s tests`. Windows-specific behavior, such as the desktop clipboard and Credential Manager, requires Windows to verify.
- The Windows installer is built with PyInstaller and Inno Setup via `packaging/construire.ps1`. The release workflow is in `.github/workflows/version.yml`. See the [README](README.md) and the [illustrated guide](docs/GUIDE.md) for setup and usage.

## Skills

Use these [ECC skills](https://github.com/affaan-m/ECC/tree/main/skills) in Codex when relevant to an approved task:

- `python-patterns` for Python implementation and maintenance.
- `coding-standards` for JavaScript changes that fit the existing plain JavaScript interface.
- `security-review` for defensive review of authorization, secrets, inputs and external boundaries.
- `tdd-workflow` for regression coverage using the repository's existing `unittest` suite.
- `verification-loop` for selecting and reporting checks appropriate to the change.

The mandatory repository rules take precedence over skill workflows. Use the repository's existing commands and conventions when adapting a skill.

## Security and operational behavior

Authentication at the transport layer does not replace authorization in the use case. Enforce ownership and role checks before returning, mutating, exporting, or downloading a resource. Treat payment callbacks, uploads, documents, and external integrations as hostile boundaries: validate inputs, authenticate callbacks, preserve idempotency, and avoid logging secrets or sensitive payloads.

Report unexpected operational failures through the existing reporter while returning sanitized API errors. A failure in reporting must never replace the original client response. Do not report expected 4xx outcomes, normal SSE expiry, deliberate cancellation, or other documented lifecycle signals as server incidents.

## Change discipline

- Inspect `git status` before editing. Existing modifications belong to the user unless clearly created during the current task.
- Preserve unrelated changes and do not reformat or reorganize files outside the requested scope.
- Search all references before moving, renaming, or deleting a public type, route, configuration key, event, or migration artifact.
- Prefer focused changes that solve the demonstrated cause. Avoid speculative abstractions and silent compatibility changes.
- Keep code, tests, documentation, and configuration aligned in the same change.
- Summarize changed files and verification results at handoff, including any residual risk or required frontend follow-up.
