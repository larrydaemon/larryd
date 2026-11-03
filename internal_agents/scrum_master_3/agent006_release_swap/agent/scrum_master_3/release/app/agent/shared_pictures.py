"""THE PICTURES A HIRED READ SEES (the owner 2026-10-24: "the builder needs to make everything on its own"; R-0043 was
refused three times for "no screenshot proof", and the controller's own builder had to take the pictures by hand).
After a platform change that touches the look passes its tests, the Developer itself (outside the builder's box)
pictures the pages: BEFORE (main) and AFTER (the build's tree, as a snapshot commit that moves no branch), each on a
copy of live (pictures_run.py, the signed walk's copy: scratch PINs, fresh ports, removed after), at a desktop and a
phone width. The pages: the addresses in his words, and the ones the builder names on its Pictures: line. The read is
given the files and opens them. Every tool and path is in settings develop.pictures, never here."""
import json
import os
import re
import subprocess
import tempfile

from agent import shared_where as where

LOOK = re.compile(r'(^|/)(templates|static|themes)/|\.(css|html|svg)$')
ADDRESS = re.compile(r'https?://[^\s"\'<>]+|(?<![\w/])/(?:wid|so|fs|cc|lryllm)/[a-z]+/[a-z]{2}/app/[^\s"\'<>]+')


def conf():
    got = dict((where.SETTINGS.get('develop') or {}).get('pictures') or {})
    for k in ('python', 'runner'):
        if got.get(k):
            got[k] = os.path.abspath(os.path.expanduser(got[k]))
    return got


def looks(paths):
    """Whether a change touches the look (a template, a sheet, a theme, a static file)."""
    return any(LOOK.search(p) for p in paths)


def pages_of(words, said=''):
    """The pages to picture: every platform address in his words, then every one the builder named on its Pictures:
    line; each as its path and query (the host is the copy's), at most four."""
    named = ' '.join(l.split(':', 1)[1] for l in str(said or '').splitlines() if l.strip().lower().startswith('pictures:'))
    out = []
    for m in ADDRESS.finditer(f'{words}\n{named}'):
        page = m.group(0).rstrip('.,);')
        if '://' in page:
            page = '/' + page.split('://', 1)[1].split('/', 1)[-1] if '/' in page.split('://', 1)[1] else ''
        if re.match(r'^/(wid|so|fs|cc|lryllm)/[a-z]+/[a-z]{2}/app/', page) and page not in out:
            out.append(page)
    return out[:4]


def snapshot(root):
    """THE TREE AS IT STANDS, a commit object of its own (a throwaway index: no branch moves, nothing staged in the
    tree). -> its sha, or '' when git would not make it"""
    with tempfile.TemporaryDirectory(prefix='pictures_index_') as t:
        env = {**os.environ, 'GIT_INDEX_FILE': os.path.join(t, 'index')}
        run = lambda *a: subprocess.run(['git', '-C', root, *a], capture_output=True, text=True, env=env)
        if run('read-tree', 'HEAD').returncode or run('add', '-A', '.').returncode:
            return ''
        tree = run('write-tree')
        if tree.returncode:
            return ''
        made = run('-c', 'user.name=THE DEVELOPER', '-c', 'user.email=developer@localhost', 'commit-tree', tree.stdout.strip(), '-p', 'HEAD', '-m', 'pictures snapshot')
        return made.stdout.strip() if made.returncode == 0 else ''


def take(rid, approach, root, pages, folder=None, runner=subprocess.run):
    """BEFORE (main) and AFTER (the tree) pictured. -> (files [{label, page, width, file}], what was said)"""
    c = conf()
    if not pages:
        return [], ['no page to picture: his words name no platform address and the builder named none on a Pictures: line']
    if not (c.get('python') and c.get('runner')):
        return [], ['settings develop.pictures names no picture tool']
    sha = snapshot(root)
    if not sha:
        return [], ['the tree could not be snapshotted for its pictures']
    out = os.path.join(folder or where.LOGS, 'develop', 'pictures', rid, str(approach))   # under his own logs (reports.json names them)
    os.makedirs(out, exist_ok=True)
    try:
        done = runner([c['python'], '-I', c['runner'], out, f"before={c.get('before', 'main')}", f'after={sha}', '--', *pages],
                      capture_output=True, text=True, timeout=int(c.get('minutes', 10)) * 60)
    except subprocess.TimeoutExpired:
        return [], [f"the pictures ran past {c.get('minutes', 10)} minutes"]
    lines = [l for l in (done.stdout or '').strip().splitlines() if l.startswith('{')]
    try:
        got = json.loads(lines[-1]) if lines else {}
    except ValueError:
        got = {}
    said = list(got.get('said') or []) or ([] if got else [' '.join((done.stdout + done.stderr).split())[-300:] or f'exit {done.returncode}'])
    return list(got.get('pictures') or []), said


def said_to_read(files, said):
    """The read's words about the pictures."""
    if not files:
        return ('THE PICTURES: none could be taken (' + '; '.join(said)[:400] + '). Judge the look from the code; never refuse only '
                'because no picture was given.\n\n') if said else ''
    rows = '\n'.join(f"  {f['label'].upper()} {f['width']}px {f['page'][:120]}: {f['file']}" for f in files)
    return ('THE PICTURES (taken by the Developer on a copy of live, signed in as the owner: BEFORE is main, AFTER is this change; '
            'they are the screenshot proof). Open each with Read and judge the look from them against his words:\n' + rows +
            ('\n  ' + '; '.join(said)[:300] if said else '') + '\n\n')
