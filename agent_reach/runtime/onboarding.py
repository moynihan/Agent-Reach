"""Read-only session discovery and explicit connection choices. Never logs a user in."""
import json
import urllib.request
from datetime import datetime
from urllib.parse import urlsplit

from agent_reach.utils.url import host_matches

from .result import BAD_INPUT, ReachError

# These describe public routes an agent can try, not authenticated Reach readiness.
# A successful sample depends on the tool, network exit, content and platform response.
_PUBLIC_ACCESS = {
    'web': "Use the agent's own web search and reading first; call Reach only for the remaining gaps.",
    'github': 'Public repos, READMEs, issues/PRs and public comments can be read first via the web or the public API.',
    'youtube': 'Public search and descriptions can be read first; native tools may get comments, subtitles and timestamps for some samples.',
    'reddit': 'Public search, post bodies and some comments can be read first; some public JSON samples include comments with parent_id.',
    'twitter': 'Public search snippets and some single-post full text can be tried first; public embeds do not provide reply streams.',
    'xiaohongshu': 'The public explore page may expose note IDs and authors; do not infer from it that bodies or comments are readable.',
    'instagram': 'Public search or profile info can be tried first; the HTML may be only an app shell, and captions and comments are not uniformly verified.',
    'facebook': 'Public search snippets can be tried first; post bodies and comments depend on the page and access path.',
    'linkedin': 'Public jobs can be searched and read first; a login-free job sample was obtained on 2026-10-21, but not every job is guaranteed readable.',
    'boss': 'Public job indexes and pages can be tried first; anonymous access was not verified at fine granularity this round.',
    'xueqiu': 'Public stock quotes and name search can be tried first; community content is judged by the selected path.',
}

_CAPABILITY_LIMITS = {
    'youtube': ['read returns metadata and the description; there is no separate comments action.',
                'Subtitles depend on the available tracks; transcription also needs a configured provider and quota, and login does not guarantee subtitles.'],
    'reddit': ['read promises only the post and comments it returns; no complete comment tree is guaranteed and there is no posting action.'],
    'twitter': ['thread covers only the replies actually returned; no complete reply stream is guaranteed and there is no posting action.'],
    'xiaohongshu': ['Reports only the body text, loaded comments and replies actually read; no complete export is promised.'],
    'instagram': ['search finds users; there is no arbitrary post read or separate comments action.'],
    'facebook': ['Only search/profile are declared; no separate post reading or comment export is promised.'],
    'linkedin': ['Only job search and JD reading are declared; no contact or feed scraping is promised.'],
    'boss': ['Only job search and JD reading are declared; login does not guarantee the platform always allows access.'],
}


# Public web options and authenticated Reach actions; detailed limits stay in capability_summary.
_QUICK_ACCESS = {
    'github': ('✅ Find projects, read docs, view discussions and comments', '—'),
    'youtube': ('✅ Find videos, read descriptions and subtitles', '—'),
    'web': ('✅ Search and read web pages', '—'),
    'reddit': ('✅ Search posts, read bodies, view comments', '—'),
    'twitter': ('✅ Search snippets, try reading originals', '❌ Search tweets, view feeds and replies'),
    'xiaohongshu': ('✅ Search snippets, find links', '❌ On-site search, read bodies, view comments'),
    'instagram': ('✅ Search bios', '❌ Find users, view profiles and posts'),
    'facebook': ('✅ Search snippets', '❌ On-site search, view pages'),
    'linkedin': ('✅ Find jobs, read public details', '❌ On-site search'),
    'boss': ('✅ Search titles, find links', '❌ On-site search, read details'),
    'xueqiu': ('✅ Find stocks, check quotes', '❌ View hot posts and hot stocks'),
}

_DISPLAY_NAMES = {
    'github': 'GitHub', 'youtube': 'YouTube',
    'web': 'Web', 'reddit': 'Reddit', 'twitter': 'X / Twitter', 'facebook': 'Facebook',
    'instagram': 'Instagram', 'xiaohongshu': 'Xiaohongshu', 'linkedin': 'LinkedIn',
    'boss': 'Boss Zhipin', 'xueqiu': 'Xueqiu',
}

_STATUS_LABELS = {
    'not_added': 'not added; add on demand', 'needs_setup': 'needs setup', 'unverified': 'added, not yet live-tested',
    'ready': 'verified', 'search_ready': 'search verified only',
    'needs_login': 'tested actions need login', 'cooldown': 'paused',
    'needs_user_action': 'awaiting manual verification', 'broken': 'current path broken',
}


def _local_greeting():
    """Use the installing computer's clock and timezone, without a network lookup."""
    hour = datetime.now().hour
    if 5 <= hour < 11:
        return 'Good morning! What would you like to look up? ☀️'
    if 11 <= hour < 14:
        return 'Hello! What would you like to look up?'
    if 14 <= hour < 18:
        return 'Good afternoon! What would you like to look up?'
    if 18 <= hour < 22:
        return 'Good evening! What would you like to look up?'
    return 'Up late? What would you like to look up? 🌙'

def _upgrade_lines(result):
    """Only for users coming from 1.5: what was kept, what changed, what is left to do."""
    migration = result.get('migration')
    if not migration:
        return []
    lines = ['**This was an upgrade from an older version (1.5):**', '',
             '- Your keys and settings were kept.',
             '- RSS feeds and Exa web search are no longer separate; use "Web" to search and read pages.',
             "- Platforms that need a login, such as X and Xiaohongshu, now use Agent Reach's own dedicated browser; on first use it tries to reuse the login from your Chrome.",
             '- Command-line tools you installed yourself (such as twitter-cli) were left as they were.']
    suggested = [_DISPLAY_NAMES.get(n, n) for n in migration.get('suggested_channels') or []]
    if suggested:
        lines.append('- You used ' + ', '.join(suggested) + ' before; to keep using them, just say "add XX".')
    old = result.get('old_copies') or {}
    if old.get('removed'):
        lines.append('- The old program was removed, so it will not conflict with the new version.')
    for item in old.get('failed') or []:
        from .legacy import manual_command
        lines.append(f"- The old program could not be removed; please run: `{manual_command(item)}`")
    return lines + ['']



def installation_report(result):
    """Render one short receipt; keep detailed evidence in the structured summary."""
    def cell(value):
        return str(value).replace('|', r'\|').replace('\n', ' ')

    entries = result['capability_summary']['channels']
    installs = {row['channel']: row for row in result['default_channels']}
    installed = sum(bool(row['ok']) for row in installs.values())
    completed = all(row['ok'] for row in installs.values())
    lines = [
        _local_greeting(), '',
        f"**Agent Reach {result['version']} {'is installed' if completed else 'is almost installed'}.** "
        f'Default features: {installed}/{len(installs)} ready.', '',
        *_upgrade_lines(result),
        '✅ no login needed; ❌ try after logging in; 🔑 needs a key; — no extra login.', '',
        '| Platform | Without login | After login |', '|---|---|---|',
    ]
    for entry in sorted(entries, key=lambda item: item['level'] != 'default'):
        name = entry['channel']
        label = _DISPLAY_NAMES.get(name, name)
        item = installs.get(name)
        if entry['level'] == 'default':
            if item and not item['ok']:
                label += ' (install failed: ' + item.get('error', {}).get('code', 'UNKNOWN') + ')'
            elif not item:
                label += ' (removed by user)'
        elif entry['reach_status'] in {'needs_setup', 'needs_login', 'cooldown', 'needs_user_action', 'broken'}:
            label += ' (' + _STATUS_LABELS[entry['reach_status']] + ')'
        public, login = _QUICK_ACCESS.get(name, (entry['public_access'], '—'))
        lines.append('| ' + ' | '.join(cell(value) for value in (label, public, login)) + ' |')
    verified = [entry for entry in entries if entry['verified_actions']]
    if verified:
        names = '; '.join(_DISPLAY_NAMES.get(entry['channel'], entry['channel']) + ': ' +
                         '/'.join(entry['verified_actions']) for entry in verified)
        lines += ['', 'Tested and working: ' + names + '. The rest has not been live-tested item by item.']
    else:
        lines += ['', 'Not yet live-tested item by item.']
    lines += ['Snippets, titles and links come from search engines first; comments reflect what was actually read; subtitles must exist on the video.', '',
              '**Tell me what you want to look up.** Existing logins are reused first; a window opens only when you really need to log in.']
    return '\n'.join(lines) + '\n'



def capability_summary(channels, statuses):
    """Describe public options, declared actions and local evidence without any I/O.

    Management supplies status records so this summary cannot initiate discovery,
    installation, login or a live request. Actions always come from the registry.
    """
    by_name = {entry['channel']: entry for entry in statuses}
    entries = []
    for ch in channels:
        current = by_name.get(ch.name, {})
        names = [action.name for action in ch.actions]
        can_login = bool(ch.login_url or ch.login_argv)
        auth_actions = {'xueqiu': ['hot_posts', 'hot_stocks']}.get(
            ch.name, names if can_login else [])
        entries.append({
            'channel': ch.name,
            'level': ch.level,
            'reach_status': current.get('status', 'unverified'),
            'verified_actions': current.get('verified_actions', []),
            'actions': [{'action': action.name, 'detail': action.help} for action in ch.actions],
            'public_access': _PUBLIC_ACCESS.get(ch.name, "Try the agent's existing public search and reading first."),
            'authentication': {
                'when': 'only_if_required',
                'may_enable_actions': [name for name in auth_actions if name in names],
                'note': 'When the selected path for the remaining task actually requires authentication, reuse an authorized session first, then ask the user to log in; actions still need verification afterwards.',
            },
            'limits': _CAPABILITY_LIMITS.get(ch.name, []),
        })
    message = ["Use the agent's existing public search and reading first; Reach adds capabilities on demand, and installation does not require logging in to each platform."]
    for entry in entries:
        actions = '/'.join(action['action'] for action in entry['actions'])
        status_label = _STATUS_LABELS.get(entry['reach_status'], entry['reach_status'])
        limits = ' '.join(entry['limits'])
        message.append(f"{entry['channel']}: {entry['public_access']} Reach {actions} ({status_label}). {limits}")
    return {
        'policy': 'public_first; login_only_for_remaining_task_when_required',
        'evidence_note': 'Public path notes come from samples and access conditions and do not replace local Reach acceptance; network errors, 403s, timeouts or captchas alone do not prove that login is required.',
        'channels': entries,
        'message': '\n'.join(message),
    }


def cdp_url():
    value = 'http://127.0.0.1:9222'
    return validate_cdp(value)


def validate_cdp(value):
    try:
        u = urlsplit(value)
        valid = (u.scheme == 'http' and u.hostname in {'localhost', '127.0.0.1', '::1'}
                 and u.port and not u.username and not u.password and not u.query
                 and not u.fragment and u.path in ('', '/'))
    except (TypeError, ValueError):
        valid = False
    if not valid:
        raise ReachError(BAD_INPUT, 'CDP must be a loopback HTTP address with an explicit port')
    return value.rstrip('/')


def cdp_status():
    url = cdp_url()
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    try:
        with opener.open(url + '/json/list', timeout=2) as resp:
            tabs = json.loads(resp.read(1024 * 1024))
        found = isinstance(tabs, list) and any(
            isinstance(t, dict) and t.get('type') == 'page'
            and host_matches(t.get('url', ''), 'zhipin.com') for t in tabs)
        return {'endpoint': url, 'connected': isinstance(tabs, list), 'boss_tab_present': bool(found)}
    except (OSError, ValueError):
        return {'endpoint': url, 'connected': False, 'boss_tab_present': False}


def require_boss_cdp():
    from . import browser, session_reuse
    session_reuse.prepare("boss")
    if not cdp_status()['boss_tab_present']:
        browser.open_url('https://www.zhipin.com/web/geek/jobs')
    browser.touch()
    return browser.CDP_URL
