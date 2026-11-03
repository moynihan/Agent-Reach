# Capability scope

Read this when the user asks what can be fetched or how complete a result is. The table lists declared capabilities; it does not mean every network, account and piece of content has been tested.

## Three levels

- **Public, worth trying**: the agent's existing web tools, native tools or public APIs may already cover the task; no browser install or login is required. Answer from the evidence actually obtained.
- **Reach adds**: the actions declared by the current release, see `agent-reach channels`. When setup is needed, reuse the session already saved in the dedicated browser first; the user logs in themselves only when the chosen path actually requires it.
- **Verified on this machine**: only the specific actions that recently passed a live check on this machine. Installation, a saved session and network reachability are not a passed live check.

## Channels in this release

| Channel | Public paths worth trying | What Reach adds, and its limits |
|---|---|---|
| GitHub | Public repos, README, issues/PRs | Repo search, repo/issue/PR reading with the returned comments; private access is judged separately |
| YouTube | Search, title, description; native tools may return some comments and subtitle text | search/read/subtitle/transcribe; no unified comments action yet; a track list is not subtitle text, and without subtitles transcription depends on the configured tool |
| Reddit | Search, body text, some comments; some public JSON includes parent/child IDs | Browser search/read/subreddit; login depends on the chosen path; no guarantee of a complete comment tree or every reply; no posting of comments |
| X/Twitter | Public single posts found by search; some official public embeds return the full text | search/profile/tweets/thread; a readable post does not mean its reply stream is readable; no guarantee of a complete comment tree |
| Xiaohongshu | Public lists or indexes may show a note ID, author and title; empty fields must not be guessed | search/read/comments; text description, top-level comments and loaded replies; not all comments are guaranteed, and never claim to understand images or video |
| Instagram | Some index and shallow profile data; an HTML app shell is not a post | search finds users, profile reads a profile, posts reads a given user's post descriptions; no unified comments action, never claim to understand images or video |
| Facebook | Some index or HTML snippets; snippets may be truncated | search/profile; no unified detail or comments action; never treat a search snippet as the full text |
| LinkedIn | Search public jobs, read public job descriptions | jobs/read try the public web first; only `--backend opencli` goes straight to the site; not every job is guaranteed readable |
| BOSS | Search indexes may contain job snippets | search/read for job lists and job descriptions; never guess digits from an encoded salary; detail fallback follows the channel declaration |
| Xueqiu | Some public quotes and index data | quote/search/hot_posts/hot_stocks; the quote path and the community path are verified separately |
| Web | The agent's own search/read | Reach web search/read is an anonymous fallback; snippets, page shells and verification pages are not full text |

Describe logged-in capability as "can enable / try the browser actions above", never as "supports all comments after login". When the user skips login, deliver the public evidence already gathered.
