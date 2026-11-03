# Sessions and the dedicated browser

Read this when the user wants to log in, log out or switch accounts, or when a result returns `NEED_LOGIN`.

## The dedicated browser

- All browser channels share one dedicated browser profile, separate from the user's everyday Chrome; the program never closes or modifies the user's everyday browser.
- The engine is CloakBrowser by preference; when its download or installation fails, the installed system Chrome is used and that fallback is remembered rather than re-downloading every time. Once the network is fixed, `agent-reach browser setup --retry-cloak` retries.
- `agent-reach add <channel>` prepares Node, OpenCLI, the engine and the extension automatically. Tools are installed at the versions tested for this release. On Windows with the Chrome fallback, the user may need to click "Add to Chrome" once.
- Headless by default, no windows. Only `agent-reach login <channel>` shows a window; while the window is open, queries use that window and never close it. While the user is logging in, wait until they say they are done before querying. After the window closes, later queries go back to headless.
- Closes after 10 idle minutes and reopens on the next call; real page activity and Reach calls reset the timer. Logins live inside the browser profile and survive the idle close, so the user does not need to close the window.
- Calls may run in parallel: up to 2 per platform and 4 in total at once; the rest wait in line for up to 2 minutes and return `BUSY` only if no slot frees up. Two searches on the same platform start at least 10 seconds apart. Opening a login window, logging out and reinstalling the browser wait for running queries to finish first.
- `agent-reach browser status` shows the state, `browser setup` prepares the engine and extension, `browser stop` closes the browser the program manages.

## Automatic reuse of an existing login

1. The first time a site is used, if the user's Chrome is connected to the OpenCLI extension, the program copies that site's login (that site's cookies only) once into the dedicated browser. It does not copy the whole browser directory, other sites or the password store, and it does not modify the source browser.
2. After a successful copy, the saved session is reused indefinitely; it is not re-copied on a schedule. A cookie being present does not mean the login is valid; the result of a real action decides.
3. When the user's Chrome is not connected to the extension, do not promise automatic reuse, and do not conclude from this that the user is not logged in; use the session Reach has already saved.
4. When several browsers on this machine are logged in to the site: `agent-reach browser profiles` lists the sources and `agent-reach browser use <ID>` selects one; never switch at random.
5. `agent-reach login <channel> --import-existing` re-copies that site's login once, without opening a window.
6. Once the user has logged in themselves in the dedicated window, or has run `logout` / `remove`, automatic copying stops for that site, so a login the user ended cannot come back.

## When the user must log in themselves

- Ask the user to log in only when a result actually returns `NEED_LOGIN` and the remaining task really needs that path. A login button next to the body text does not mean login is required.
- `agent-reach login <channel>` opens the dedicated browser on that site's login page and the user logs in themselves. Never log in for them, never ask for a password, never print cookies.
- If the result's `next` field describes a follow-up step, do it; some native-tool channels (such as Xueqiu) need `agent-reach login <channel> --sync` after the login.
- Once the user is done, run the original action again to verify.

## Platform differences

- Boss Zhipin in-site search goes through OpenCLI and shares the dedicated browser. If a job detail asks for login because of an upstream false positive, do not make the user log in repeatedly.
- Xueqiu community actions need a login; the session expires within hours, and the login steps are repeated after it expires.

## Logging out and removing

- `agent-reach logout <channel>`: clears that site's login in the dedicated browser and the channel's own state; other sites are kept.
- `agent-reach remove <channel>`: removes the channel and clears that site's login and storage at the same time; other sites are kept. If cleanup fails, the channel record is kept and an error is returned so the user can retry.
- After either command, that site's login is no longer copied automatically.
