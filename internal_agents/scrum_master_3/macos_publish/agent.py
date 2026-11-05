"""MACOS PUBLISH, the NIGHT's last step (SM2 agent030): the walked Mac build installed in the apps folder, byte for byte (the app
before it kept beside the build); never over the app while it is open (red: quit it). From the freeze day the step after it is RELEASE's
Freeze. Dry: it reads the kept build, its walk, the installed app (byte for byte) and whether it is open, and names what it would copy."""
import filecmp
import os
import shutil
import subprocess

import night
import office
from night import F, tail, ready


def same(a, b):
    """two app bundles equal file for file, byte for byte"""
    if not (os.path.isdir(a) and os.path.isdir(b)):
        return False
    for here, _dirs, files in os.walk(a):
        there = os.path.join(b, os.path.relpath(here, a))
        if not os.path.isdir(there) or sorted(os.listdir(here)) != sorted(os.listdir(there)):
            return False
        for f in files:
            p, q = os.path.join(here, f), os.path.join(there, f)
            if os.path.islink(p) or os.path.islink(q):
                if not (os.path.islink(p) and os.path.islink(q) and os.readlink(p) == os.readlink(q)):
                    return False
            elif not filecmp.cmp(p, q, shallow=False):
                return False
    return True


def next_step():
    return F('next') if office.now().date().isoformat() >= F('freeze_day') else ''


def own(given, dry):
    k, why = ready('macos')
    if why:
        return {'why': f'the kept Mac build is not ready: {why}', 'step': 'RUN macOS build (its build, walk and pixel compare), then RUN here'}
    bundle = k['bundle']
    app = os.path.join(F('apps'), os.path.basename(bundle))
    if same(bundle, app):
        return {'lines': [f"macos · publish · installed already: {k['commit'][:12]}"]}
    if subprocess.run(['pgrep', '-f', app + '/Contents/MacOS/'], capture_output=True, timeout=30).returncode == 0:
        return {'why': f'{os.path.basename(app)} is open on this Mac: it is never replaced while open', 'step': f'quit {os.path.basename(app)}, then RUN here'}
    new, old = app + '.installing', os.path.join(os.path.dirname(bundle), F('kept_before'))
    if dry:
        return {'lines': [f"macos · publish · {k['commit'][:12]} ready, not installed"],
                'would': [f'ditto "{bundle}" "{new}"', f'mv "{app}" "{old}"', f'mv "{new}" "{app}"', 'then byte for byte against the kept build']}
    shutil.rmtree(new, ignore_errors=True)
    got = subprocess.run(['ditto', bundle, new], capture_output=True, text=True, timeout=600)
    if got.returncode != 0:
        shutil.rmtree(new, ignore_errors=True)
        return {'why': f'the copy into {F("apps")} failed: {tail(got.stderr, 200)}', 'step': f'ditto "{bundle}" "{app}", then RUN here'}
    os.utime(new, None)
    if os.path.isdir(app):
        shutil.rmtree(old, ignore_errors=True)
        os.rename(app, old)
    os.rename(new, app)
    if not same(bundle, app):
        return {'why': 'the installed app is not the kept build byte for byte', 'step': f'ditto "{bundle}" "{app}", then RUN here'}
    return {'lines': [f"macos · publish · installed {k['commit'][:12]} in {app}; the app before it kept at {old}"]}


if __name__ == '__main__':
    night.main(own, next_step)
