# Maintenance

Read this when an update fails, the browser will not start, a channel reports an error, or the user wants to uninstall.

- Update: `agent-reach update` upgrades Agent Reach, the tools of every added channel and the skill; `agent-reach update --check` only checks whether a newer version exists. Run it only after the user agrees.
- Status: `agent-reach doctor --text` reads local state without the network; `agent-reach check <channel> --text` runs one live test over the network (`--search` tests search/jobs only). A successful install is not a passed live test.
- Browser: `agent-reach browser status` shows the state, `browser setup` prepares the engine and extension, `browser stop` closes it; after a CloakBrowser download failure, fix the network and run `browser setup --retry-cloak`.
- Tell the failing stages apart: dependency download, browser connection, login, page load and platform rate limiting are separate things; never describe a network timeout as an expired login.
- Upstream tool errors: note the error and version, then run `agent-reach update` once after the user agrees; never edit an upstream tool's installed files, never retry in a loop.
- On `PLATFORM_BLOCKED`, `RATE_LIMITED`, `NEED_LOGIN` or `BUSY`, stop this attempt and continue only after the user has handled it; do not reopen windows repeatedly.
- Keys and proxy: `agent-reach configure groq-key | openai-key | proxy | github-token`; the user provides the value themselves.
- Uninstall: show the user the scope with `agent-reach uninstall --dry-run` first, then run `agent-reach uninstall` once they confirm. Only what Reach installed itself is removed; the user's other files and browsers are kept.
