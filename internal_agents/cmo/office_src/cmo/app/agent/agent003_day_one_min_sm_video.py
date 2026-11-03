"""AGENT 003 · ONE MIN SM VIDEO (the CMO's first sub agent, the owner 2026-10-28: "one min sm video" (sm for social media); "8 prompts for 8
clips and it gets combined at the end for 1 min of video"): his title and one prompt (or up to 8), his reference pictures from Downloads, then ON
RUN AGENT ONLY (the owner: "we dont want it running on its own") one film of exactly 60 seconds.

THE FILM, STEP BY STEP, each step written to this office's own tables (films, clips in instance/cmo.db) so a RED stops where it broke:
 1. THE LENGTHS: eight different whole seconds, each 1 to 30, adding up to exactly 60, in a random order (the owner: "random but no value the
    same and all must equal 1 min in total and each in whole seconds"; "1 to 30 seconds range with 8 clips").
 2. THE PROMPT DOCTOR: Claude (Opus 5.5, the marketing plugin's way) writes the 8-shot storyboard from his one prompt, or doctors his own lines,
    one look for all 8, fitted to each clip's length, nothing Seedance refuses (real faces); a second, BLIND Claude grades each GREEN or RED
    against his words; a RED one is rewritten once. His words are kept as typed.
 3. THE KEY PICTURES: Nano Banana 2 through the timeline lab's own door (/make), his reference picture as its key frame; with none, clip 1's
    picture guides the other seven so the look holds.
 4. THE CLIPS: Seedance 2.5 through the timeline lab's /make, cut by the lab to the clip's own seconds (1 to 10); longer, the lab's own
    continuation (extend, up to 9 s a call) until the clip's length. The labs are only started and used, never changed (the owner 2026-10-28:
    "an agent can never change any lab code just restart and use the labs").
 5. THE CUT, THEN THE LAYERS, only when all 8 clips are made (the owner: "we keep it split and only assemble at the end"): each clip trimmed to
    its exact frames and joined; SUBTITLES (one line a clip, a clip too short to read joins the next), the LOGO on top (a corner, then the end
    card), the MUSIC under it (a free track, faded, leveled to -16 LUFS); the .srt and .vtt beside it and inside the file.
 6. THE CHECK: exactly 60 s, 8 cuts of 8 different lengths, a picture, the music and the subtitles in the file; the film copied to ~/Downloads.
REDO on one clip makes that clip again (his new words, or a new take of the same ones), its old takes kept, then the cut again; nothing else."""
import datetime
import fcntl
import json
import os
import random
import re
import shutil
import sqlite3
import subprocess
import threading
import time
import traceback
import urllib.request

KEY = 'one_min_sm_video'
SLOT = 'DAY'   # its group: DAY, worn at its block's top right
INTERFACE = True   # its own form (the original's ADD REQUEST TO BACKLOG markup), its presses working on both faces
ROW = 3
NAME = 'one min sm video'   # his words as typed (the owner 2026-10-28: "one min sm video (sm for social media)")
PITCH = 'One prompt in, one 60 second social media film out: 8 clips, the logo, subtitles and music'
WHAT = 'Writes 8 shots from his prompt, makes each clip through the labs, cuts them to exactly 60 seconds and lays the logo, subtitles and music on'
SCHEDULE = {'location': 'NEW YORK', 'schedule_type': 'manual', 'time': '', 'timezone': 'America/New_York'}   # ON RUN AGENT ONLY: never due
ROW_FILE = 'agent003_day_one_min_sm_video.py'
BACKGROUND = True   # a film works for many minutes: in its own thread, the page answers RUN AGENT at once

HOME = os.path.expanduser('~')
OFFICE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))   # ~/virtual_sanity/cmo
SCRATCH = os.path.join(HOME, 'scratch', 'cmo')   # EVERYTHING IT MAKES LIVES OUTSIDE THE LOCKED FOLDER (the owner 2026-10-28: "virtual sanity is a locked down folder and all reports and scratch is located outside this"): only its database stays in the office
CONF = {'lab': 'http://127.0.0.1:8822', 'lab_dir': os.path.join(HOME, 'civilization_cluster', 'timeline_lab'),
        'films': os.path.join(SCRATCH, 'work'), 'films_url': '/media/work', 'scratch_url': '/media',
        'shot_samples': os.path.join(SCRATCH, 'shot_samples'),   # THE SHOT LIST'S SAMPLES (the owner 2026-10-28: "generic refence samples for each type ... like bookend it shows samples before we had a full shot list made somewhere"): production's psshots, 64, 8 a shot group   # THE WORKING FOLDERS (scratch), one a project, played by the page's media route
        'music': os.path.join(SCRATCH, 'music'),
        'references': os.path.join(SCRATCH, 'references'),   # HIS REFERENCE PICTURES' OWN FOLDER (the owner 2026-10-28: "we need a dedicated folder to put the reference images not the last downloads")
        'source': os.path.join(SCRATCH, 'source'),   # PLAN CLIP's folder (the owner 2026-10-28: "will break up a video from the folder ... a clear button that will clear out the folder"): one video at a time
        'projects': os.path.join(SCRATCH, 'projects'),   # THE SAVED COPIES (the owner 2026-10-28: "when you click save its actually saving a copy in a folder that can be loaded... the main folder is a working scratch folder"): <project>/<date-time>/ = its folder + its rows
        'audio_python': os.path.join(SCRATCH, 'tools', 'audio', 'bin', 'python'),   # THE MUSIC's own tools (Demucs, beat_this, librosa, Whisper); the page never loads them
        'storyboard': os.path.join(HOME, 'civilization_cluster', 'timeline_lab', 'reference', 'storyboard.json'),   # HIS PROVEN SEQUENCES (SB_VIBES, SB_GROUPS), read where they are, never changed
        'music_seconds': 3600,
        'downloads': os.path.join(HOME, 'Downloads'),
        'logo': os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'static', 'images', 'positive_feedback_logo.png'),   # moved into LARRYD RUNTIME INTERNAL 2026-11-03: the logo is its own copy
        'claude': ['claude', '-p', '--model', 'claude-opus-5-5', '--output-format', 'text', '--allowedTools', 'Read'],
        'claude_seconds': 600, 'make_seconds': 1800}
FPS, W, H, TOTAL, CLIPS, LONGEST = 30, 1280, 720, 60, 8, 30
LAB_MOST = 10   # the lab cuts a Seedance clip to any length up to 10 s; longer is its continuation
EXTEND_MOST = 9   # the lab's continuation adds up to 9 s a call
READ_LEAST = 1.5   # a subtitle shorter than this on screen is joined to the next clip's
BEAT = 60
HAND = 'YOUR 3 MIN: '
PICTURES = re.compile(r'\.(png|jpe?g|webp|heic)$', re.I)
PRESSES = ('add', 'redo', 'remove', 'clear', 'minute', 'sequence', 'music', 'process', 'open', 'save', 'load', 'inspire', 'find', 'types', 'posters', 'swap', 'face', 'donor', 'mark', 'skin', 'skinmix', 'skinmark', 'skinbake', 'skinall', 'teethmark', 'teethpaint', 'teethtool', 'teethtest', 'teethbake', 'teethsave', 'teethlayer', 'hairpaint', 'hairauto', 'hairbake', 'hairsave', 'hairpreview', 'cleanbake', 'colorpreview', 'colorbake', 'colorpaint', 'colorauto', 'colormovesave', 'colormovebake', 'restorebake', 'movetime', 'movebake', 'moveauto', 'movereset', 'lipsswitch', 'lipsmake', 'compsave', 'compbake', 'exportsave', 'exportmake')
TYPES = ('I', 'II', 'III')
TONE_OF = {'I': '', 'II': 'two', 'III': 'insert'}   # III green, II red (the owner 2026-10-28: "you should color the I II and III with III green and II red")   # THE THREE CLIP TYPES (the owner 2026-10-28: "TYPE I, TYPE II, TYPE III (insert) ... they dont follow each other"; "other clips might not have a group shot so the generic names work for all")
SONGS = re.compile(r'\.(mp3|m4a|wav|aiff?|flac)$', re.I)
VIDEOS = re.compile(r'\.(mp4|mov|m4v|mkv|webm)$', re.I)
LISTS = ('refs', 'layers', 'music', 'song')

TABLES = """
CREATE TABLE IF NOT EXISTS films (id TEXT PRIMARY KEY, title TEXT, words TEXT, refs TEXT, layers TEXT, music TEXT, lengths TEXT, look TEXT,
  state TEXT, why TEXT, asked_at TEXT, state_at TEXT, final TEXT, downloads TEXT, track TEXT, source TEXT, swap TEXT, music_start REAL);
CREATE TABLE IF NOT EXISTS clips (film TEXT, n INTEGER, seconds INTEGER, words TEXT, ref TEXT, doctored_frame TEXT, doctored_clip TEXT,
  line TEXT, grade TEXT, grade_why TEXT, take INTEGER DEFAULT 0, picture TEXT, clip TEXT, made_by TEXT, state TEXT, why TEXT, takes TEXT, source_at REAL,
  PRIMARY KEY (film, n));
CREATE TABLE IF NOT EXISTS inspiration (film TEXT, n INTEGER, line TEXT, code TEXT, source TEXT, second REAL, frame TEXT, tag TEXT, made_at TEXT,
  PRIMARY KEY (film, n));
CREATE TABLE IF NOT EXISTS posters (film TEXT, n INTEGER, prompt TEXT, picture TEXT, file TEXT, take INTEGER DEFAULT 0, state TEXT, why TEXT, made_at TEXT,
  PRIMARY KEY (film, n));
CREATE TABLE IF NOT EXISTS faceswap (film TEXT, n INTEGER, line TEXT, face INTEGER, file TEXT, state TEXT, why TEXT, made_at TEXT, PRIMARY KEY (film, n));
CREATE TABLE IF NOT EXISTS skin (film TEXT, n INTEGER, strength REAL, file TEXT, state TEXT, why TEXT, made_at TEXT, opacity REAL, saturation REAL, raw TEXT, crop TEXT, dot_x REAL, dot_y REAL, cut TEXT, filter TEXT, baked TEXT, lightness REAL, whites REAL, blacks REAL, PRIMARY KEY (film, n));
CREATE TABLE IF NOT EXISTS teeth (film TEXT, n INTEGER, strokes TEXT, tool TEXT, mouth_x REAL, mouth_y REAL, zoom REAL, mask TEXT, view TEXT, file TEXT, oview TEXT, baked TEXT,
  size REAL, mx REAL, my REAL, turn REAL, match REAL, light REAL, soft REAL, edge REAL, grow REAL, state TEXT, why TEXT, made_at TEXT, PRIMARY KEY (film, n));
CREATE TABLE IF NOT EXISTS hair (film TEXT, n INTEGER, strokes TEXT, paint_at REAL, mask TEXT, file TEXT, oview TEXT, baked TEXT, strength REAL, edge REAL,
  state TEXT, why TEXT, made_at TEXT, PRIMARY KEY (film, n));
CREATE TABLE IF NOT EXISTS cleanup (film TEXT, n INTEGER, proposed TEXT, source TEXT, note TEXT, state TEXT, made_at TEXT, decided_at TEXT, reference TEXT, fixmask TEXT, PRIMARY KEY (film, n));
CREATE TABLE IF NOT EXISTS color (film TEXT, n INTEGER, strength REAL, light REAL, file TEXT, state TEXT, why TEXT, made_at TEXT, PRIMARY KEY (film, n));
CREATE TABLE IF NOT EXISTS colormove (film TEXT PRIMARY KEY, settings TEXT, at REAL, state TEXT, made_at TEXT);
CREATE TABLE IF NOT EXISTS restore (film TEXT, n INTEGER, color REAL, original REAL, state TEXT, why TEXT, made_at TEXT, PRIMARY KEY (film, n));
CREATE TABLE IF NOT EXISTS movetime (film TEXT, n INTEGER, offset REAL, speed REAL, made_at TEXT, PRIMARY KEY (film, n));
CREATE TABLE IF NOT EXISTS lipsset (film TEXT, n INTEGER, lips INTEGER, made_at TEXT, PRIMARY KEY (film, n));
CREATE TABLE IF NOT EXISTS composition (film TEXT, n INTEGER, vals TEXT, mask TEXT, made_at TEXT, PRIMARY KEY (film, n));
CREATE TABLE IF NOT EXISTS versions (id INTEGER PRIMARY KEY AUTOINCREMENT, film TEXT, step TEXT, n INTEGER, settings TEXT, file TEXT, made_at TEXT);
CREATE INDEX IF NOT EXISTS versions_slot ON versions (film, step, n, id);
CREATE TABLE IF NOT EXISTS exportset (film TEXT PRIMARY KEY, layout TEXT, offset REAL, logo INTEGER, style TEXT, variant TEXT, start REAL, seconds REAL, made_at TEXT);
CREATE TABLE IF NOT EXISTS lessons (id INTEGER PRIMARY KEY AUTOINCREMENT, film TEXT, step INTEGER, lesson TEXT, why TEXT, made_at TEXT);
CREATE TABLE IF NOT EXISTS music (film TEXT PRIMARY KEY, song TEXT, start REAL, seconds REAL, tempo REAL, beats_by TEXT, analysis TEXT, lyrics TEXT,
  peaks TEXT, map TEXT, state TEXT, why TEXT, made_at TEXT);
"""


# ============ THE TABLES (this office's own, in its own store)
def _db(store_or_path):
    path = store_or_path if isinstance(store_or_path, str) else store_or_path.db_path
    con = sqlite3.connect(path, timeout=15)
    con.row_factory = sqlite3.Row
    con.executescript(TABLES)
    for table, col, kind in (('films', 'source', 'TEXT'), ('films', 'swap', 'TEXT'), ('films', 'music_start', 'REAL'), ('clips', 'source_at', 'REAL'),
                             ('films', 'opened_at', 'TEXT'), ('films', 'types', 'TEXT'), ('films', 'posters_state', 'TEXT'), ('films', 'cast_look', 'TEXT'), ('films', 'swap_state', 'TEXT'), ('films', 'swap_donor', 'TEXT'),
                             ('faceswap', 'donor', 'TEXT'), ('faceswap', 'face_x', 'REAL'), ('faceswap', 'face_y', 'REAL'), ('faceswap', 'person_x', 'REAL'), ('faceswap', 'person_y', 'REAL'), ('films', 'song', 'TEXT'), ('films', 'song_start', 'REAL'), ('skin', 'opacity', 'REAL'), ('skin', 'saturation', 'REAL'), ('skin', 'raw', 'TEXT'), ('skin', 'crop', 'TEXT'), ('skin', 'dot_x', 'REAL'), ('skin', 'dot_y', 'REAL'), ('skin', 'cut', 'TEXT'), ('skin', 'filter', 'TEXT'), ('skin', 'baked', 'TEXT'), ('skin', 'lightness', 'REAL'), ('skin', 'whites', 'REAL'), ('skin', 'blacks', 'REAL'), ('films', 'sequence', 'TEXT'), ('films', 'music_state', 'TEXT'), ('films', 'music_why', 'TEXT'), ('teeth', 'paint_at', 'REAL'), ('teeth', 'layer', 'TEXT'), ('teeth', 'layer_at', 'REAL'), ('teeth', 'band', 'REAL'), ('hair', 'matte', 'TEXT'), ('hair', 'light', 'REAL'), ('cleanup', 'reference', 'TEXT'), ('cleanup', 'fixmask', 'TEXT'), ('color', 'strokes', 'TEXT'), ('color', 'paint_at', 'REAL'), ('color', 'matte', 'TEXT'), ('color', 'protect', 'REAL'), ('color', 'edge', 'REAL'), ('exportset', 'frame', 'TEXT'), ('exportset', 'audio', 'INTEGER'), ('exportset', 'fill', 'INTEGER')):   # a table made before PLAN CLIP: its new columns added
        if col not in [c[1] for c in con.execute(f'PRAGMA table_info({table})')]:
            con.execute(f'ALTER TABLE {table} ADD COLUMN {col} {kind}')
    return con


def _now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds')


def _film(con, fid):
    return con.execute('SELECT * FROM films WHERE id = ?', (fid,)).fetchone()


def _clips(con, fid):
    return con.execute('SELECT * FROM clips WHERE film = ? ORDER BY n', (fid,)).fetchall()


def _set_film(con, fid, **v):
    v['state_at'] = _now()
    con.execute(f"UPDATE films SET {', '.join(k + ' = ?' for k in v)} WHERE id = ?", (*v.values(), fid))
    con.commit()


def _set_clip(con, fid, n, **v):
    con.execute(f"UPDATE clips SET {', '.join(k + ' = ?' for k in v)} WHERE film = ? AND n = ?", (*v.values(), fid, n))
    con.commit()


# ============ 1. THE LENGTHS
def lengths(rng=random):
    """eight different whole seconds, each 1 to 30, adding up to exactly 60, in a random order"""
    picked = list(range(1, CLIPS + 1))   # 1..8 add up to 36: the 24 seconds left are handed out one at a time
    while sum(picked) < TOTAL:
        i = rng.randrange(CLIPS)
        if picked[i] + 1 <= LONGEST and picked[i] + 1 not in picked:
            picked[i] += 1
    rng.shuffle(picked)
    assert len(set(picked)) == CLIPS and sum(picked) == TOTAL and all(1 <= s <= LONGEST for s in picked)
    return picked


# ============ HIS FORM: the title, his prompt or prompts, his references
def reference_pictures(conf=None, most=40):
    """every picture in his references folder, by name"""
    conf = conf or CONF
    try:
        return sorted(f for f in os.listdir(conf['references']) if PICTURES.search(f) and os.path.isfile(os.path.join(conf['references'], f)))[:most]
    except OSError:
        return []


def source_videos(conf=None):
    """the videos in PLAN CLIP's folder, by name"""
    conf = conf or CONF
    try:
        return sorted(f for f in os.listdir(conf['source']) if VIDEOS.search(f) and os.path.isfile(os.path.join(conf['source'], f)))
    except OSError:
        return []


def find_source(name, conf=None):
    """PLAN CLIP: the video in its folder whose name holds his words (the owner: "you give it a name it finds it in the folder"), or ''"""
    want = re.sub(r'[^a-z0-9]', '', str(name or '').lower())
    found = [f for f in source_videos(conf) if want and want in re.sub(r'[^a-z0-9]', '', f.lower())]
    return found[0] if len(found) >= 1 else ''


def parse(words):
    """his box -> (title, [the lines he typed]): line 1 the title, then one prompt (the agent writes the 8) or up to 8 ("N: words" ties his
    reference N to that clip)"""
    lines = [ln.strip() for ln in str(words or '').replace('\r\n', '\n').split('\n') if ln.strip()]
    return (lines[0] if lines else ''), lines[1:1 + CLIPS]


def add_film(db, words, refs, layers, music, conf=None, now=None, sources=(), song=''):
    conf = conf or CONF
    title, prompts = parse(words)
    typed = next((ln for ln in prompts if SONGS.search(ln.strip())), '')   # THE SONG BY ITS FILE NAME (the owner 2026-10-28: "have an input with the music name and its easy to copy and paste a file name ... sorta works like a dam key but its the file name")
    found = find_song(typed or song, conf)
    if typed and not found:
        return f'ADD refused · no file named "{typed}" in {conf["music"]} or {conf["downloads"]}'
    if found:
        song = os.path.basename(found)
    if song:   # PART 1 · THE MUSIC: a film that starts from a song (his title, the song; the rest of its words wait for part 2)
        if not title:
            return 'ADD refused · line 1 is the title'
        con = _db(db)
        try:
            top = max([int(r['id'][2:]) for r in con.execute('SELECT id FROM films') if re.fullmatch(r'F-\d+', r['id'])] or [0])
            fid = f'F-{top + 1:04d}'
            con.execute('INSERT INTO films (id, title, words, refs, layers, music, state, why, asked_at, state_at, song, music_state) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)',
                        (fid, title, str(words), json.dumps([r for r in refs if r in reference_pictures(conf)]), json.dumps(layers), '[]', 'asked', '', now or _now(), now or _now(), song, 'asked'))
            con.commit()
            con.execute('UPDATE films SET opened_at = ? WHERE id = ?', (_now(), fid))   # a new project is the one open
            con.commit()
            home = os.path.join(conf['films'], fid)   # THE FILM'S ONE PROJECT FOLDER (the owner: "everything can be in 1 folder for the project"): his song copied in under its own name
            os.makedirs(home, exist_ok=True)
            shutil.copyfile(found, os.path.join(home, song))
        finally:
            con.close()
        return f'ADDED · {fid} · {title} · THE MUSIC from {song} · press RUN AGENT: it splits the vocals, finds the beats, the sections, the words and the map'
    named = next((m.group(1) for ln in prompts for m in [re.match(r'^(?:plan|video|source)\s*:\s*(.+)$', ln, re.I)] if m), '')
    source = (find_source(named, conf) if named else '') or next((v for v in sources if v in source_videos(conf)), '')
    if named and not source:
        return f'ADD refused · no video in {conf["source"]} holds the name "{named}"'
    swap = ' '.join(ln for ln in prompts if not re.match(r'^(?:plan|video|source)\s*:', ln, re.I))
    if source and not swap:
        return 'ADD refused · PLAN CLIP: line 2 says who replaces the guy (for example: riff raff rumpelstiltskin)'
    if not title or not prompts:
        return 'ADD refused · line 1 is the title, then one prompt (or up to 8, one a line), or plan: <video name> and who replaces the guy'
    con = _db(db)
    try:
        top = max([int(r['id'][2:]) for r in con.execute('SELECT id FROM films') if re.fullmatch(r'F-\d+', r['id'])] or [0])
        fid = f'F-{top + 1:04d}'
        con.execute('INSERT INTO films (id, title, words, refs, layers, music, state, why, asked_at, state_at, source, swap) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)',
                    (fid, title, str(words), json.dumps([r for r in refs if r in reference_pictures(conf)]), json.dumps(layers), json.dumps(music),
                     'asked', '', now or _now(), now or _now(), source, swap if source else ''))
        con.commit()
    finally:
        con.close()
    if source:
        return f'ADDED · {fid} · {title} · PLAN CLIP from {source} · the guy becomes: {swap} · press RUN AGENT to make it'
    return f'ADDED · {fid} · {title} · {len(prompts)} prompt(s), {len(refs)} reference(s) · press RUN AGENT to make it'


def press(store, job_key, do, fields=None, now=None, conf=None):
    if do not in PRESSES:
        raise ValueError(f'not one of its presses: {do!r}')
    fields, conf = fields or {}, conf or CONF
    one = lambda k: (fields.get(k) or [''])[0] if isinstance(fields.get(k), list) else (fields.get(k) or '')   # noqa: E731
    many = lambda k: [fields[k]] if isinstance(fields.get(k), str) and fields[k] else list(fields.get(k) or [])   # noqa: E731
    if do == 'add':   # the form's one box name (refs) carries three lists: a bare reference, 'layers:<layer>', 'music:<track>'
        refs, layers, music, sources, picked = _split(many('refs'))
        return add_film(store.db_path, one('words'), refs, layers if one('refs_said') else [], music, conf, now, sources, (picked or [''])[0])   # no layer unless he ticks it (the owner 2026-10-28: "remove the logos ... we can always add logos but hard to remove")
    if do == 'music':   # STEP 1's own form (the owner 2026-10-28: "then a button process music then it makes the music"): his title and the song's file name, the film made and its music started at once
        said = add_film(store.db_path, one('words'), [], [], [], conf, now, (), (many('song') or [''])[0])   # the song he ticked (or the file name he pasted)
        if not said.startswith('ADDED'):
            return said
        return said.split(' · press RUN AGENT')[0] + ' · PROCESS MUSIC: ' + start_run(store, job_key) + ' (about 6 minutes for a new song)'
    if do == 'mark':   # A MARKER ON A POSTER: FACE (the face to swap) or PERSON (for the head and hair pass), its spot as fractions
        con = _db(store)
        try:
            fid, _, n = one('value').partition(':')
            kind = 'face'   # ONE MARKER, THE SWAP PERSON (the owner 2026-10-28: "we only need to pick 1 person that is the swap person")
            try:
                x, y = max(0.0, min(1.0, float(one('x')))), max(0.0, min(1.0, float(one('y'))))
            except ValueError:
                return 'MARK refused · no spot'
            con.execute('INSERT OR IGNORE INTO faceswap (film, n, state, made_at) VALUES (?,?,?,?)', (fid, int(n), 'asked', _now()))
            con.execute(f'UPDATE faceswap SET {kind}_x = ?, {kind}_y = ?, state = ? WHERE film = ? AND n = ?', (x, y, 'asked', fid, int(n)))
            con.commit()
            return f"MARKED · {fid} slot {n} · the swap person at {x:.2f}, {y:.2f} · press SWAP FACES to swap it again"
        finally:
            con.close()
    if do in ('swap', 'face', 'donor'):   # PART 3's presses: SWAP FACES, a slot's face line (it is swapped again), another face picture
        con = _db(store)
        try:
            if do == 'donor':   # THE FACES: '+' adds his typed file name, '-name' removes that one; every poster is swapped again
                fid, _, what = one('value').partition('|')
                f_ = _film(con, fid)
                if not f_:
                    return f'DONOR refused · no project {fid}'
                refs = donors_of(f_)
                if what.startswith('-'):
                    refs = [x for x in refs if x != what[1:]]
                    said = f'REMOVED · {what[1:]}'
                else:
                    name = ' '.join(one('words').split())
                    if not find_file(name, conf):
                        return f'ADD refused · no picture named "{name}" in the CMO\'s folders'
                    refs = refs + ([name] if name not in refs else [])
                    said = f'ADDED · {name}'
                _set_film(con, fid, swap_donor=json.dumps(refs))
                con.execute("UPDATE faceswap SET state = 'stale' WHERE film = ?", (fid,))
                con.commit()
                return f'{said} · {len(refs)} face references · press SWAP FACES to swap every poster again'
            fid, _, n = one('value').partition(':')
            if not _film(con, fid):
                return f'{do.upper()} refused · no project {fid}'
            if do == 'face':
                _swap_row(con, fid, int(n), line=' '.join(one('words').split()), state='asked')
            elif do == 'swap':
                con.execute("UPDATE faceswap SET state = 'stale' WHERE film = ? AND state != 'done'", (fid,))
                con.commit()
            _set_film(con, fid, swap_state='asked', state='asked', music_state='stale')
        finally:
            con.close()
        return f'{do.upper()} · {fid} · ' + start_run(store, job_key) + ' · about 15 seconds a poster'
    if do == 'skinall':   # ONE COSMOS RUN FOR THE FILM (the owner 2026-10-29: "we only need to run the first one to get this data the rest should just be adjustments based
        # on the first exxact run"): the golden tone of one slot (he is the same person in every slot) and its five numbers laid on every other slot, seconds each
        con = _db(store)
        try:
            fid, _, n0 = one('value').partition(':')
            src_ = con.execute('SELECT * FROM skin WHERE film = ? AND n = ?', (fid, int(n0))).fetchone()
            if not (src_ and src_['filter']):
                return f'APPLY refused · slot {n0} has no golden tone yet · press ◇ SKIN on it first'
            done_, why_ = [], []
            for (m,) in con.execute("SELECT n FROM faceswap WHERE film = ? AND state = 'done' AND file IS NOT NULL ORDER BY n", (fid,)).fetchall():
                if m == int(n0):
                    continue
                r_ = con.execute('SELECT state FROM skin WHERE film = ? AND n = ?', (fid, m)).fetchone()
                if r_ and r_['state'] == 'baked':
                    continue   # a slot he baked keeps its own
                con.execute('INSERT OR IGNORE INTO skin (film, n, state, made_at) VALUES (?, ?, ?, ?)', (fid, m, 'new', _now()))
                con.execute('UPDATE skin SET filter = ?, lightness = ?, opacity = ?, saturation = ?, whites = ?, blacks = ? WHERE film = ? AND n = ?',
                            (src_['filter'], src_['lightness'], src_['opacity'], src_['saturation'], src_['whites'], src_['blacks'], fid, m))
                ok_, said_ = skin_mix(con, conf, fid, m)
                con.commit()
                (done_ if ok_ else why_).append(f'{m}' if ok_ else f'{m}: {said_}')
            return f"APPLIED · slot {n0}'s golden tone on slots {', '.join(done_) or 'none'}" + (f" · not made: {'; '.join(why_)}" if why_ else '') + ' · fine-tune each live, then BAKE'
        finally:
            con.close()
    if do in ('skinmark', 'skinbake'):   # PART 4's dot (the person we correct, as the swap's) and BAKE (the filtered picture made final)
        con = _db(store)
        try:
            fid, _, n = one('value').partition(':')
            n = int(n)
            con.execute('INSERT OR IGNORE INTO skin (film, n, state, made_at) VALUES (?, ?, ?, ?)', (fid, n, 'new', _now()))
            if do == 'skinmark':
                try:
                    x, y = max(0.0, min(1.0, float(one('x')))), max(0.0, min(1.0, float(one('y'))))
                except ValueError:
                    return 'DOT refused · no spot'
                con.execute("UPDATE skin SET dot_x = ?, dot_y = ?, state = 'new', why = 'the dot moved · press ◇ SKIN', cut = NULL, raw = NULL, filter = NULL, file = NULL, baked = NULL WHERE film = ? AND n = ?", (x, y, fid, n))
                con.commit()
                return f'DOT · {fid} slot {n} · the person at {x:.2f}, {y:.2f} · press ◇ SKIN'
            # BAKE ALL (the owner 2026-10-29: "if you click any bake it bakes them all"): every row's sliders come with the press as <name>@<film>:<slot>; each slot is
            # set to them and baked, so a change on one row is never lost by pressing another row's BAKE
            rows_ = sorted({int(k.rsplit(':', 1)[1]) for k in fields if '@' in k and k.split('@', 1)[1].startswith(fid + ':')}) or [n]
            home = os.path.join(conf['films'], fid, 'skin')
            baked_, why_ = [], []
            for m in rows_:
                con.execute('INSERT OR IGNORE INTO skin (film, n, state, made_at) VALUES (?, ?, ?, ?)', (fid, m, 'new', _now()))
                for k_ in ('lightness', 'opacity', 'saturation', 'whites', 'blacks'):
                    raw_ = one(f'{k_}@{fid}:{m}') or (one(k_) if m == n else '')
                    if raw_:
                        try:
                            v_ = float(raw_)
                        except ValueError:
                            return 'BAKE refused · the sliders are not numbers'
                        con.execute(f'UPDATE skin SET {k_} = ? WHERE film = ? AND n = ?', (round(max(-30, min(30, v_)), 1) if k_ == 'lightness' else round(max(0, min({'whites': 300, 'saturation': 200}.get(k_, 200), v_)) / 100, 2), fid, m))
                ok_, said_ = skin_mix(con, conf, fid, m)
                con.commit()
                if not ok_:
                    why_.append(f'{m}: {said_}')
                    continue
                r = con.execute('SELECT * FROM skin WHERE film = ? AND n = ?', (fid, m)).fetchone()
                shutil.copyfile(os.path.join(home, r['file']), os.path.join(home, f'baked_{m}.png'))
                con.execute("UPDATE skin SET baked = ?, state = 'baked', why = ? WHERE film = ? AND n = ?", (f'baked_{m}.png', (r['why'] or '').replace('not baked', 'BAKED'), fid, m))
                _keep(con, conf, fid, 'skin', m, f'skin/baked_{m}.png', 'skin', files=(f'skin/mask_{m}.png', f'skin/cut_{m}.png'))
                con.commit()
                baked_.append(str(m))
            carried_ = carry_down(con, conf, fid, [int(x) for x in baked_], 'skin')   # every step below made again where the slot has reached it
            return f"BAKED ALL · {fid} · slots {', '.join(baked_) or 'none'} at the numbers you see" + (f" · not baked: {'; '.join(why_)}" if why_ else '') + carried_
        finally:
            con.close()
    if do in ('skin', 'skinmix'):   # PART 4 · SKIN, ONE SLOT AT A TIME (the owner 2026-10-29: "dont do them all at once"; "its the gold one we need only"): SKIN = its
        # golden hour Cosmos run (minutes, once); REPROCESS = its OPACITY and SATURATION laid again over its face swap (seconds, no new run)
        con = _db(store)
        try:
            fid, _, n = one('value').partition(':')
            if not _film(con, fid):
                return f'SKIN refused · no project {fid}'
            n = int(n)
            try:   # a slider not sent (◇ SKIN has none) keeps the slot's own number
                op = round(max(1, min(100, float(one('opacity')))) / 100, 2) if one('opacity') else None
                sat = round(max(0, min(200, float(one('saturation')))) / 100, 2) if one('saturation') else None
                lt = round(max(-30, min(30, float(one('lightness')))), 1) if one('lightness') else None
                wh = round(max(0, min(300, float(one('whites')))) / 100, 2) if one('whites') else None
                bl = round(max(0, min(200, float(one('blacks')))) / 100, 2) if one('blacks') else None
            except ValueError:
                return 'SKIN refused · the sliders are not numbers'
            con.execute('INSERT INTO skin (film, n, opacity, saturation, state, made_at) VALUES (?, ?, ?, ?, ?, ?) ON CONFLICT(film, n) DO UPDATE SET '
                        'opacity = COALESCE(excluded.opacity, skin.opacity), saturation = COALESCE(excluded.saturation, skin.saturation)',
                        (fid, n, op, sat, 'new', _now()))
            if lt is not None:
                con.execute('UPDATE skin SET lightness = ? WHERE film = ? AND n = ?', (lt, fid, n))
            if wh is not None:
                con.execute('UPDATE skin SET whites = ? WHERE film = ? AND n = ?', (wh, fid, n))
            if bl is not None:
                con.execute('UPDATE skin SET blacks = ? WHERE film = ? AND n = ?', (bl, fid, n))
            if op is None or sat is None:
                con.execute('UPDATE skin SET opacity = COALESCE(opacity, ?), saturation = COALESCE(saturation, ?) WHERE film = ? AND n = ?', (SKIN_GOLD['opacity'], SKIN_GOLD['saturation'], fid, n))
            row = con.execute('SELECT * FROM skin WHERE film = ? AND n = ?', (fid, n)).fetchone()
            if do == 'skinmix':
                if not row['filter'] and film_tone(con, fid)[0] is None:
                    con.commit()
                    return 'REPROCESS refused · the film has no golden tone yet · press ◇ SKIN on one slot first'
                ok, said = skin_mix(con, conf, fid, n)
                con.commit()
                return f'REPROCESS · {fid} slot {n} · {said}'
            con.execute("UPDATE skin SET state = 'asked', why = '', made_at = ? WHERE film = ? AND n = ?", (_now(), fid, n))
            con.commit()
            _set_film(con, fid, state='asked', music_state='stale')
        finally:
            con.close()
        return f'SKIN · {fid} slot {n} · ' + start_run(store, job_key) + ' · Cosmos paints it in golden hour, about 4 minutes'
    if do in ('hairpaint', 'hairauto', 'hairbake', 'hairsave', 'hairpreview'):
        return hair_press(store, do, one, conf)
    if do == 'cleanbake':
        return clean_press(store, do, one, conf)
    if do in ('colorpreview', 'colorbake', 'colorpaint', 'colorauto'):
        return color_press(store, do, one, conf)
    if do in ('colormovesave', 'colormovebake'):
        return move_press(store, do, one, conf)
    if do == 'restorebake':
        return restore_press(store, do, one, conf)
    if do in ('movetime', 'movebake', 'moveauto', 'movereset'):
        return movetime_press(store, do, one, conf)
    if do in ('lipsswitch', 'lipsmake'):
        return lips_press(store, do, one, conf)
    if do in ('compsave', 'compbake'):
        return comp_press(store, do, one, conf)
    if do in ('exportsave', 'exportmake'):
        return export_press(store, do, one, conf)
    if do in ('teethmark', 'teethpaint', 'teethtool', 'teethtest', 'teethbake', 'teethsave', 'teethlayer'):   # PART 5 · TEETH (the owner 2026-10-29: "normalize all the teeth to match"; "a mask on the reference itself and
        # on the images each so its very isolated and very targeted"): a click marks the teeth (WAND, BRUSH, ERASE) or centres the close view, a tool press undoes, clears or
        # zooms, TEST lays the master's grill on one slot, BAKE ALL on every slot; every row's sliders come with each press (as SKIN's BAKE ALL), so none is lost
        con = _db(store)
        try:
            fid, _, rest = one('value').partition(':')
            n_, _, act = rest.partition(':')
            if not _film(con, fid):
                return f'TEETH refused · no project {fid}'
            try:
                n = int(n_)
            except ValueError:
                return 'TEETH refused · no slot'
            if not os.path.exists(_teeth_src(conf, fid, n)):
                return f'TEETH refused · slot {n} has no baked skin picture yet (step 4)'
            con.execute('INSERT OR IGNORE INTO teeth (film, n, state, made_at) VALUES (?, ?, ?, ?)', (fid, n, 'new', _now()))
            for m in sorted({int(k.rsplit(':', 1)[1]) for k in fields if '@' in k and k.split('@', 1)[1].startswith(fid + ':')} | {n}):
                con.execute('INSERT OR IGNORE INTO teeth (film, n, state, made_at) VALUES (?, ?, ?, ?)', (fid, m, 'new', _now()))
                for k_, lo_, hi_, _d in TEETH_SLIDERS:
                    raw_ = one(f'{k_}@{fid}:{m}') or (one(k_) if m == n else '')
                    if raw_:
                        try:
                            con.execute(f'UPDATE teeth SET {k_} = ? WHERE film = ? AND n = ?', (round(max(lo_, min(hi_, float(raw_))), 1), fid, m))
                        except ValueError:
                            return 'TEETH refused · the sliders are not numbers'
            con.commit()
            r = con.execute('SELECT * FROM teeth WHERE film = ? AND n = ?', (fid, n)).fetchone()
            strokes = json.loads(r['strokes'] or '[]')
            if do == 'teethsave':   # SAVE MASKS (the owner 2026-10-29: "i made all the masks we need to save these. we should have a save masks button"): every slot's
                # marks drawn into its mask picture on the box and brought home (teeth/mask_N.png), and every slot's marks kept as they are now in one dated file
                home = os.path.join(conf['films'], fid, 'teeth', 'masks_saved')
                os.makedirs(home, exist_ok=True)
                rows_ = con.execute("SELECT n, strokes FROM teeth WHERE film = ? AND strokes IS NOT NULL AND strokes != '[]' ORDER BY n", (fid,)).fetchall()
                stamp_ = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
                with open(os.path.join(home, f'marks_{stamp_}.json'), 'w') as fh:
                    json.dump({str(x['n']): json.loads(x['strokes']) for x in rows_}, fh)
                saved_, why_ = [], []
                for x in rows_:
                    ok_, said_ = teeth_mask(con, conf, fid, x['n'])
                    con.commit()
                    (saved_ if ok_ else why_).append(f"{x['n']}" if ok_ else f"{x['n']}: {said_}")
                ok_, said_ = teeth_grill(con, conf, fid)   # the grill layer from the master as it is now
                con.commit()
                if not ok_:
                    why_.append(f'the grill layer: {said_}')
                return (f"SAVED MASKS · {fid} · slots {', '.join(saved_) or 'none'} (teeth/mask_N.png) · the marks also in teeth/masks_saved/marks_{stamp_}.json"
                        + (f" · not saved: {'; '.join(why_)}" if why_ else ''))
            if do == 'teethlayer':   # THE GRILL LAYER as he placed it on the page (the owner 2026-10-29: "it should be able to put a custom overlay layer and move it around
                # and its just a layer on top of an image. then when you modify it and like it then you bake it"; "you need the squish"): its centre, width, height and turn as
                # fractions of the slot picture, MATCH, LIGHT and EDGE; sent in the background on each release, the newest kept
                try:
                    lay = json.loads(one('layer') or '{}')
                    lay = {'cx': max(-1.0, min(2.0, float(lay['cx']))), 'cy': max(-1.0, min(2.0, float(lay['cy']))), 'w': max(0.002, min(3.0, float(lay['w']))),
                           'h': max(0.002, min(3.0, float(lay['h']))), 'rot': max(-180.0, min(180.0, float(lay.get('rot') or 0)))}
                    at_ = float(one('at') or 0)
                    tone = {k: max(lo_, min(hi_, float(one(k)))) for k, lo_, hi_ in (('match', 0, 100), ('light', -50, 50), ('edge', 0, 10)) if one(k) != ''}
                except (ValueError, TypeError, KeyError, AttributeError):
                    return 'LAYER refused · the layer is not readable'
                if r['layer_at'] is not None and at_ < r['layer_at']:
                    return f'LAYER · {fid} slot {n} · an older send, the newer layer kept'
                con.execute('UPDATE teeth SET layer = ?, layer_at = ? WHERE film = ? AND n = ?', (json.dumps({k: round(v, 5) for k, v in lay.items()}), at_, fid, n))
                for k, v in tone.items():
                    con.execute(f'UPDATE teeth SET {k} = ? WHERE film = ? AND n = ?', (round(v, 1), fid, n))
                con.commit()
                return f"LAYER · {fid} slot {n} · at {lay['cx']:.3f}, {lay['cy']:.3f} · {lay['w']:.3f} x {lay['h']:.3f} · {lay['rot']:+.1f}°"
            if do == 'teethpaint':   # THE PAINT BOARD's stroke list, whole, as the page holds it (sent on each release, in the background): the newest kept
                try:
                    got, at_ = json.loads(one('path') or '[]'), float(one('at') or 0)
                    strokes = [{'x': round(max(0.0, min(1.0, float(g['x']))), 5), 'y': round(max(0.0, min(1.0, float(g['y']))), 5), 'm': 'e' if g.get('m') == 'e' else 'p',
                                'tol': 0, 'r': round(max(0.0005, min(0.1, float(g['r']))), 5)} for g in got][:20000]
                except (ValueError, TypeError, KeyError, AttributeError):
                    return 'PAINT refused · the marks are not readable'
                if r['paint_at'] is not None and at_ < r['paint_at']:
                    return f'PAINT · {fid} slot {n} · an older send, the newer marks kept'
                con.execute('UPDATE teeth SET strokes = ?, paint_at = ?, state = ?, why = ? WHERE film = ? AND n = ?',
                            (json.dumps(strokes), at_, 'masked' if strokes else 'new', '', fid, n))
                con.commit()
                return f'PAINT · {fid} slot {n} · {len(strokes)} marks'
            if do == 'teethmark':
                try:
                    fx, fy = max(0.0, min(1.0, float(one('x')))), max(0.0, min(1.0, float(one('y'))))
                except ValueError:
                    return 'MARK refused · no spot'
                kind = one('words') if one('words') in TEETH_KINDS else 'zoom here'
                if n == TEETH_REF:   # the master: a brush and an eraser only, on the whole picture
                    kind = kind if kind in ('brush', 'erase') else 'brush'
                x0, y0, x1, y1, Wp, Hp = _teeth_box(conf, fid, n, r)
                x, y = (x0 + fx * (x1 - x0)) / Wp, (y0 + fy * (y1 - y0)) / Hp   # the spot on the close view, as a spot on the whole picture
                if kind == 'zoom here':   # THE CLOSE VIEW centred there (zoomed in the first time)
                    con.execute('UPDATE teeth SET mouth_x = ?, mouth_y = ?, zoom = ? WHERE film = ? AND n = ?', (x, y, r['zoom'] or (1.0 if n == TEETH_REF else 3.0), fid, n))
                    said = f'the close view centred at {x:.2f}, {y:.2f}'
                else:
                    m_, tol_, size_ = TEETH_KINDS[kind]
                    strokes.append({'x': round(x, 5), 'y': round(y, 5), 'm': m_, 'tol': tol_, 'r': round(size_ * (x1 - x0) / Wp, 5)})   # a brush the same size on the view at any zoom
                    con.execute("UPDATE teeth SET strokes = ?, tool = ?, state = 'masked', why = '' WHERE film = ? AND n = ?", (json.dumps(strokes), kind, fid, n))
                    said = f'{kind.upper()} at {x:.2f}, {y:.2f}'
            elif do == 'teethtool':
                if act == 'undo':
                    strokes = strokes[:-1]
                elif act == 'clear':
                    strokes = []
                elif act in ('in', 'out'):
                    z = max(1.0, min(8.0, (r['zoom'] or 1.0) * (1.5 if act == 'in' else 1 / 1.5)))
                    con.execute('UPDATE teeth SET zoom = ?, mouth_x = COALESCE(mouth_x, 0.5), mouth_y = COALESCE(mouth_y, 0.5) WHERE film = ? AND n = ?', (round(z, 2), fid, n))
                elif act == 'whole':
                    con.execute('UPDATE teeth SET mouth_x = NULL, mouth_y = NULL, zoom = NULL WHERE film = ? AND n = ?', (fid, n))
                else:
                    return 'TEETH refused · not one of its tools'
                if act in ('undo', 'clear'):
                    con.execute("UPDATE teeth SET strokes = ?, state = ?, why = '' WHERE film = ? AND n = ?", (json.dumps(strokes), 'masked' if strokes else 'new', fid, n))
                said = {'undo': 'the last mark taken back', 'clear': 'every mark cleared', 'in': 'zoomed in', 'out': 'zoomed out', 'whole': 'the whole picture'}[act]
            if do in ('teethmark', 'teethtool'):
                con.commit()
                ok_, why_ = teeth_mask(con, conf, fid, n)
                con.commit()
                return f'TEETH · {fid} slot {n} · {said} · ' + (why_ if ok_ else f'not drawn: {why_}')
            if do == 'teethtest':
                if n == TEETH_REF:
                    return f'TEST refused · slot {n} is the master: its grill is what every slot gets'
                ok_, why_ = teeth_swap(con, conf, fid, n)
                con.commit()
                return f'TEST · {fid} slot {n} · {why_}' + ('' if ok_ else ' · nothing made')
            home = os.path.join(conf['films'], fid, 'teeth')   # BAKE ALL: every slot made final, a slot with no teeth marked kept exactly as it is (a closed mouth: no change)
            os.makedirs(home, exist_ok=True)
            baked_, kept_, why_ = [], [], []
            for (m,) in con.execute("SELECT n FROM skin WHERE film = ? AND state = 'baked' ORDER BY n", (fid,)).fetchall():
                if act == 'one' and m != n:   # BAKE on the editor: this slot alone
                    continue
                if not os.path.exists(_teeth_src(conf, fid, m)):
                    continue
                con.execute('INSERT OR IGNORE INTO teeth (film, n, state, made_at) VALUES (?, ?, ?, ?)', (fid, m, 'new', _now()))
                rm_ = con.execute('SELECT * FROM teeth WHERE film = ? AND n = ?', (fid, m)).fetchone()
                if m != TEETH_REF and json.loads(rm_['strokes'] or '[]'):
                    ok_, said_ = teeth_swap(con, conf, fid, m)
                    if not ok_:
                        why_.append(f'{m}: {said_}')
                        continue
                    shutil.copyfile(os.path.join(home, f'teeth_{m}.png'), os.path.join(home, f'baked_{m}.png'))
                    con.execute("UPDATE teeth SET baked = ?, state = 'baked', why = ? WHERE film = ? AND n = ?", (f'baked_{m}.png', said_, fid, m))
                    _keep(con, conf, fid, 'teeth', m, f'teeth/baked_{m}.png', 'teeth', files=(f'teeth/mask_{m}.png', f'teeth/mask_{TEETH_REF}.png', 'teeth/grill.png'), also=(('teeth', TEETH_REF),))
                    baked_.append(str(m))
                else:
                    shutil.copyfile(_teeth_src(conf, fid, m), os.path.join(home, f'baked_{m}.png'))
                    con.execute("UPDATE teeth SET baked = ?, state = 'baked', why = ? WHERE film = ? AND n = ?",
                                (f'baked_{m}.png', 'the master: kept as it is' if m == TEETH_REF else 'no teeth marked: kept exactly as it is', fid, m))
                    _keep(con, conf, fid, 'teeth', m, f'teeth/baked_{m}.png', 'teeth', extra={'kept': 'as it is', 'source': os.path.relpath(_teeth_src(conf, fid, m), os.path.join(conf['films'], fid))})
                    kept_.append(str(m))
                con.commit()
            carried_ = carry_down(con, conf, fid, [int(x) for x in baked_ + kept_], 'teeth')
            return (f"{'BAKED' if act == 'one' else 'BAKED ALL'} · {fid} · the grill on slots {', '.join(baked_) or 'none'}" + (f" · kept as they are: {', '.join(kept_)}" if kept_ else '')
                    + (f" · not baked: {'; '.join(why_)}" if why_ else '') + carried_)
        finally:
            con.close()
    if do == 'posters':   # MAKE POSTERS: its run makes the 8 posters (about 6 minutes)
        con = _db(store)
        try:
            fid = one('value')
            if not _film(con, fid):
                return f'MAKE POSTERS refused · no project {fid}'
            _set_film(con, fid, posters_state='asked', state='asked', music_state='stale')
        finally:
            con.close()
        return f'MAKE POSTERS · {fid} · ' + start_run(store, job_key) + ' · about 6 minutes for the 8'
    if do in ('inspire', 'find', 'types'):   # PART 2's presses: a slot's line, FIND INSPIRATION, the types option
        con = _db(store)
        try:
            fid, _, n = one('value').partition(':')
            if not _film(con, fid):
                return f'{do.upper()} refused · no project {fid}'
            if do == 'find':
                said = find_inspiration(con, conf, fid)
            elif do == 'types':
                _set_film(con, fid, types=str(int(n or 0)))
                said = f'TYPES · {fid} · option {int(n or 0) + 1} in use'
            else:
                said = set_inspiration(con, conf, fid, int(n), one('words'))
            return said
        except (RuntimeError, ValueError) as e:
            return f'{do.upper()} not done · {str(e)[:200]}'
        finally:
            con.close()
    if do == 'save':
        return save_project(store, one('value'), conf)
    if do == 'load':
        return load_project(store, one('value'), conf)
    if do == 'open':   # OPEN A SAVED PROJECT (the owner 2026-10-28: "in the db make sure it saves the project so in the future you can open it again"): the page shows it, at every step
        con = _db(store)
        try:
            f = _film(con, one('value'))
            if not f or f['state'] == 'removed':
                return f"OPEN refused · no project {one('value')}"
            con.execute('UPDATE films SET opened_at = ? WHERE id = ?', (_now(), f['id']))
            con.commit()
            return f"OPENED · {f['id']} · {f['title']}"
        finally:
            con.close()
    if do == 'process':   # PROCESS MUSIC again on a film (its minute or sequence changed): the split, beats and words are kept, the minute and map cut again
        con = _db(store)
        try:
            f = _film(con, one('value'))
            if not f or not f['song']:
                return f"PROCESS MUSIC refused · {one('value')} is not a film from a song"
            _set_film(con, f['id'], state='asked', music_state='stale')
        finally:
            con.close()
        return f"PROCESS MUSIC · {one('value')} · " + start_run(store, job_key)
    if do in ('minute', 'sequence'):   # PART 1's own presses: SET MINUTE (the slider's start, in seconds) and the sequence he picks over the map's
        con = _db(store)
        try:
            fid = one('value').partition('|')[0]
            f = _film(con, fid)
            if not f or not f['song']:
                return f'{do.upper()} refused · {fid} is not a film from a song'
            if do == 'minute':
                try:
                    start = round(float(one('start')), 3)
                except ValueError:
                    return 'SET MINUTE refused · no start time'
                _set_film(con, fid, song_start=start, music_state='stale', state='asked', opened_at=_now())
                return f'MINUTE SET · {fid} · {_mmss(start)}-{_mmss(start + TOTAL)} · the minute and its map are being cut again now (the split, beats and words are kept) · ' + start_run(store, job_key)
            want = ' '.join(one('words').split()) or (one('value').partition('|')[2] if '|' in one('value') else '')
            known = {f'{v} {o}'.lower() for v, o, _s in sequences(conf)} | {v.lower() for v, _o, _s in sequences(conf)}
            if want and want.lower() not in known:
                return f'SEQUENCE refused · "{want}" is not one of his: ' + ', '.join(sorted({v for v, _o, _s in sequences(conf)}))
            _set_film(con, fid, sequence=want, music_state='stale', state='asked', opened_at=_now(), types='0')
            return f"SEQUENCE · {fid} · {want or 'the best fit again'} · the map is being made again now · " + start_run(store, job_key)
        finally:
            con.close()
    if do == 'clear':   # CLEAR (the owner: "a clear button that will clear out the folder and then we place the new video inside"): the files in PLAN CLIP's folder, gone
        gone = []
        for f in os.listdir(conf['source']) if os.path.isdir(conf['source']) else []:
            path = os.path.join(conf['source'], f)
            if os.path.isfile(path) and not os.path.islink(path):
                os.remove(path)
                gone.append(f)
        return f"CLEARED · {conf['source']} · {len(gone)} file(s) removed" + (f" ({', '.join(gone)[:200]})" if gone else '')
    con = _db(store)
    try:
        if do == 'remove':
            fid = one('value')
            if not _film(con, fid):
                return f'REMOVE refused · no film {fid}'
            _set_film(con, fid, state='removed', why='removed by the owner')
            return f'REMOVED · {fid}'
        fid, _, n = one('value').partition(':')
        row = con.execute('SELECT * FROM clips WHERE film = ? AND n = ?', (fid, int(n or 0))).fetchone()
        if not row:
            return f'REDO refused · no clip {one("value")}'
        new = ' '.join(one('words').split())
        _set_clip(con, fid, row['n'], words=new or row['words'], take=int(row['take'] or 0) + 1, state='redo', why='',
                  **({'doctored_frame': '', 'doctored_clip': '', 'grade': ''} if new else {}))
        _set_film(con, fid, state='redo', why=f'clip {row["n"]} to make again')
        return f'REDO · {fid} clip {row["n"]} · ' + ('your new words' if new else 'a new take of the same words') + ' · press RUN AGENT: only this clip is made again'
    finally:
        con.close()


# ============ 2. THE PROMPT DOCTOR (Claude Code, Opus 5.5, read only)
def _claude(words, conf, hire=None):
    if hire:
        return hire(conf['claude'], words, OFFICE, conf['claude_seconds'])
    try:
        from frame import frame_red
        return frame_red.hire(conf['claude'], words, OFFICE, conf['claude_seconds'])
    except ImportError:
        p = subprocess.run(conf['claude'], input=words, capture_output=True, text=True, timeout=conf['claude_seconds'], cwd=OFFICE)
        return p.returncode, p.stdout


def _json_of(said):
    m = re.search(r'\{.*\}', said or '', re.S)
    if not m:
        raise ValueError('no JSON in what Claude said')
    return json.loads(m.group(0))


DOCTOR = """You are the PROMPT DOCTOR of a 60 second social media film (the CMO's "one min sm video"). Use your marketing know-how (the marketing
plugin's content-creation and campaign skills): a hook in the first seconds, one clear story, an ending that lands.

TITLE: {title}
THE OWNER'S WORDS (kept as typed, never lose what he meant):
{words}
THE 8 CLIPS, IN ORDER, WITH THEIR FIXED LENGTHS IN SECONDS: {lengths}
REFERENCE PICTURES (look at each with Read before writing; clip -> file): {refs}
{redo}
Write the storyboard: if he gave one prompt, invent 8 shots that tell it; if he gave lines, doctor each line into its clip (line N is clip N).
For every clip give:
- frame_prompt: a still key picture for Nano Banana 2, 16:9: subject, setting, composition, lens, light, color, style. Match its reference.
- clip_prompt: the motion for Seedance 2.5 from that picture, sized to its seconds (1-3 s one simple action; 4-10 s one clear move; 11-30 s one
  continuous take with a slow evolving move). ONE continuous shot, no cuts inside it, no text on screen.
- line: one subtitle, at most 42 characters, that tells the story over that clip.
Rules: one shared LOOK for all 8 (the same palette, light, lens and film grain) so they cut together; never a realistic human face (Seedance
refuses faces: show people from behind, in silhouette, hands, or far away); no logos or brand names inside the picture; no words on screen.
Answer with JSON only: {{"look": "<the shared look in one sentence>", "clips": [{{"n": 1, "frame_prompt": "...", "clip_prompt": "...", "line": "..."}}, ... 8]}}"""

GRADER = """You are a BLIND reviewer. You did not write these prompts. For each clip, grade the rewritten prompts GREEN or RED.
GREEN: it keeps what the owner meant, it is one continuous shot that fits its seconds, it shows no realistic human face, it puts no words on screen.
RED: anything else; say why in one line.
TITLE: {title}
THE OWNER'S WORDS: {words}
THE CLIPS: {clips}
Answer with JSON only: {{"grades": [{{"n": 1, "grade": "GREEN", "why": "..."}}, ... one per clip]}}"""


# ============ SAVE AND LOAD (the owner 2026-10-28: "when you click save its actually saving a copy in a folder that can be loaded... so the main folder is
# a working scratch folder and then you can load multple projects like if you find a problem tomorrow you can "load" the files"): SAVE copies the
# open project's working folder (macOS clones: no space taken until a file changes) and its rows (films, clips, music) into projects/<id>/<date-time>/;
# LOAD puts a saved copy back: its folder becomes the working folder again, its rows the database's, and it is the project open.
def saved_copies(conf=None, most=40):
    conf = conf or CONF
    out = []
    for fid in sorted(os.listdir(conf['projects'])) if os.path.isdir(conf['projects']) else []:
        for at in sorted(os.listdir(os.path.join(conf['projects'], fid)), reverse=True):
            rows = _read(os.path.join(conf['projects'], fid, at, 'rows.json'), None)
            if rows:
                out.append({'key': f'{fid}/{at}', 'film': fid, 'at': at, 'title': (rows.get('film') or {}).get('title', ''), 'state': (rows.get('film') or {}).get('state', '')})
    return sorted(out, key=lambda x: x['at'], reverse=True)[:most]


def _with_lessons(con, fid, parts):
    """LESSONS LEARNED, A STEP AT A TIME (the owner 2026-10-30: "each step 1 to 12 or whatever should have a lessons learned notes and stored in the db and tied to
    the project. this can later be put into the knowdledge store"): each step's lessons (the lessons table, the film's own) right under its title"""
    got = {}
    for r in con.execute('SELECT step, lesson, why FROM lessons WHERE film = ? ORDER BY id', (fid,)):
        got.setdefault(r['step'], []).append(r)
    out = []
    if got.get(0):   # the film's own lessons, for every step: on top
        out.append({'kind': 'table', 'title': f"THE WHOLE FILM · LESSONS LEARNED · {len(got[0])}", 'columns': ['#', 'Lesson', 'Why'],
                    'rows': [{'key': f'{fid}:0:{i}', 'cells': [str(i), r['lesson'], r['why'] or '']} for i, r in enumerate(got[0], 1)]})
    for p in parts:
        out.append(p)
        if p.get('kind') == 'step' and got.get(p.get('n')):
            out.append({'kind': 'table', 'title': f"{p['n']} · LESSONS LEARNED · {len(got[p['n']])}", 'columns': ['#', 'Lesson', 'Why'],
                        'rows': [{'key': f"{fid}:{p['n']}:{i}", 'cells': [str(i), r['lesson'], r['why'] or '']} for i, r in enumerate(got[p['n']], 1)]})
    return out


def save_project(store, fid, conf):
    con = _db(store)
    try:
        f = _film(con, fid)
        if not f:
            return f'SAVE refused · no project {fid}'
        at = datetime.datetime.now().strftime('%Y-%m-%d_%H%M%S')
        dest = os.path.join(conf['projects'], fid, at)
        os.makedirs(dest, exist_ok=True)
        work = os.path.join(conf['films'], fid)
        if os.path.isdir(work):
            p = subprocess.run(['cp', '-c', '-R', work + '/', os.path.join(dest, 'files')], capture_output=True, text=True)   # APFS clones
            if p.returncode != 0:
                shutil.copytree(work, os.path.join(dest, 'files'), dirs_exist_ok=True)
        music = con.execute('SELECT * FROM music WHERE film = ?', (fid,)).fetchone()
        # EVERY TABLE OF THE FILM (the owner 2026-10-30: "make sure all controls and versions are saving data"; "im saying this as a global issue"): each step's rows
        # and every version (in the order they were written), so a saved copy opens again exactly as it was
        tables = {t: [dict(r) for r in con.execute(f'SELECT * FROM {t} WHERE film = ? ORDER BY rowid', (fid,))] for (t,) in con.execute("SELECT name FROM sqlite_master WHERE type = 'table'")
                  if t not in ('films', 'clips', 'music') and 'film' in [c[1] for c in con.execute(f'PRAGMA table_info({t})')]}
        _write(os.path.join(dest, 'rows.json'), {'film': dict(f), 'clips': [dict(r) for r in _clips(con, fid)], 'music': dict(music) if music else None, 'tables': tables, 'saved_at': _now()})
        return f"SAVED · {fid} · {f['title']} · {at} · {dest}"
    finally:
        con.close()


def load_project(store, key, conf):
    fid, _, at = str(key or '').partition('/')
    src = os.path.join(conf['projects'], fid, at)
    rows = _read(os.path.join(src, 'rows.json'), None) if fid and at and '..' not in key else None
    if not rows:
        return f'LOAD refused · no saved copy {key}'
    work = os.path.join(conf['films'], fid)
    if os.path.isdir(os.path.join(src, 'files')):
        if os.path.isdir(work):
            shutil.rmtree(work)
        p = subprocess.run(['cp', '-c', '-R', os.path.join(src, 'files') + '/', work], capture_output=True, text=True)
        if p.returncode != 0:
            shutil.copytree(os.path.join(src, 'files'), work, dirs_exist_ok=True)
    con = _db(store)
    try:
        cols = lambda t: [c[1] for c in con.execute(f'PRAGMA table_info({t})')]   # noqa: E731  (a column saved by an older agent and gone now is left out)
        put = lambda t, row: con.execute(f"INSERT OR REPLACE INTO {t} ({', '.join(k for k in row if k in cols(t))}) VALUES ({', '.join('?' for k in row if k in cols(t))})", [v for k, v in row.items() if k in cols(t)])   # noqa: E731
        con.execute('DELETE FROM clips WHERE film = ?', (fid,))
        con.execute('DELETE FROM music WHERE film = ?', (fid,))
        put('films', {**rows['film'], 'opened_at': _now()})
        for r in rows.get('clips') or ():
            put('clips', r)
        if rows.get('music'):
            put('music', rows['music'])
        known = {t for (t,) in con.execute("SELECT name FROM sqlite_master WHERE type = 'table'")}
        for t, rs in (rows.get('tables') or {}).items():   # every step's rows and versions, as saved (a copy saved before this keeps the rows the tables have)
            if t not in known:
                continue
            con.execute(f'DELETE FROM {t} WHERE film = ?', (fid,))
            for r in rs:
                put(t, {k: v for k, v in r.items() if k != 'id'} if t in ('versions', 'lessons') else r)   # numbered by this database
        con.commit()
    finally:
        con.close()
    return f"LOADED · {fid} · {rows['film'].get('title', '')} · the copy saved {at} · it is the project open now"


# ============ PART 1 · THE MUSIC (the owner 2026-10-28: "music first ... the first section of the tool needs to figure out the music and get it ready
# before we do anythign else... or the rest is a waste of time"; "1. pick a song with mp3 reference 2. split the vocals out and keep as a new version
# for lip sync and subtitles and others 3. document and save the beats 4. match the beats to the sequence as a map"; "it should have layers like a
# multitrack with the data ready to go for the end... plus a start and end time (est)"; "a slider for 1 min and you can slide to the min you want";
# "all in the same agent"). The heavy work (Demucs, beat_this, librosa, Whisper) runs from THIS file under the office's own audio tools
# (instance/tools/audio), never inside the page; every step saved in the film's music/ folder and skipped when its file is there.
def songs(conf=None):
    """the songs in the music folder (MP3, M4A, WAV, AIFF, FLAC), by name"""
    conf = conf or CONF
    try:
        return sorted(f for f in os.listdir(conf['music']) if SONGS.search(f) and os.path.isfile(os.path.join(conf['music'], f)))
    except OSError:
        return []


def found_songs(conf=None, most=14):
    """STEP 1's tick boxes (the owner 2026-10-28: "it could detect the mp3 files and you just check it with the check mark for the one you want"):
    the songs in the music folder, then the newest in Downloads, each name once"""
    conf, seen, out = conf or CONF, set(), []
    for folder, newest in ((conf['music'], False), (conf['downloads'], True)):
        try:
            names = [f for f in os.listdir(folder) if SONGS.search(f) and not f.lower().endswith('.wav') and os.path.isfile(os.path.join(folder, f))]
        except OSError:
            continue
        names.sort(key=(lambda f: -os.path.getmtime(os.path.join(folder, f))) if newest else str.lower)
        for f in names:
            if f.lower() not in seen and len(out) < most:
                seen.add(f.lower())
                out.append(f)
    return out


def find_song(name, conf=None):
    """his song by its exact file name: the music folder first, then Downloads (the name as typed, then the same name in any case) -> its path or ''"""
    conf, name = conf or CONF, os.path.basename(str(name or '').strip().strip('"').strip("'"))
    if not name or not SONGS.search(name):
        return ''
    for folder in (conf['music'], conf['downloads']):
        path = os.path.join(folder, name)
        if os.path.isfile(path):
            return path
        try:
            near = next((f for f in os.listdir(folder) if f.lower() == name.lower()), '')
        except OSError:
            near = ''
        if near:
            return os.path.join(folder, near)
    return ''


def start_run(store, job_key):
    """its own RUN taken as RUN AGENT takes it, and run in its own thread (the page answers at once); a RUN refused because the last one is still
    closing is asked again for up to 30 s, so one press always rebuilds (the owner 2026-10-28: "i just want to click use and it should rebuild") -> the line said"""
    def go():
        for _ in range(20):
            sh, ok, text = None, False, ''
            try:
                sh = next((x for x in store.board() if x.get('job_key') == job_key), None)
                if not sh or not hasattr(store, 'run'):
                    return
                ok, text = store.run(sh['id'])
            except Exception:   # noqa: BLE001  (a busy store: asked again)
                ok = False
            if ok:
                m = re.search(r'RUN (\d+)', str(text))
                run(store, job_key, int(m.group(1)) if m else int(((sh or {}).get('job') or {}).get('data_job_run') or 0))
                return
            time.sleep(1.5)
    threading.Thread(target=go, daemon=True).start()
    return 'its run starts now (asked again for up to 30 s while the last one closes)'


def music_dir(conf, fid):
    return os.path.join(conf['films'], fid, 'music')


def _read(path, default=None):
    try:
        with open(path, encoding='utf-8') as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return default


def _write(path, data):
    part = f'{path}.{os.getpid()}.{threading.get_ident()}.part'   # each writer its own part: two at once never take each other's (a SAVE's compose beside a BAKE ALL)
    with open(part, 'w', encoding='utf-8') as fh:
        json.dump(data, fh, ensure_ascii=False)
    os.replace(part, path)


WORKER = r"""# THE MUSIC'S HEAVY WORK, a program of its own run by the office's audio tools (never imported by the page): <python> -c WORKER <song> <out>.
# The song decoded, the vocals split out (Demucs), the beats as heard (beat_this, librosa its backup), the sections, the loudest minute, the
# lyrics with their times (Whisper large-v3), the waveforms; each step skipped when its file is there. The agent fits the steady grid after.
import datetime, json, os, shutil, subprocess, sys
song, out = sys.argv[1], sys.argv[2]
os.makedirs(out, exist_ok=True)
log = open(os.path.join(out, 'worker.log'), 'a', encoding='utf-8')
def say(t):
    log.write(datetime.datetime.now().strftime('%H:%M:%S') + ' ' + t + '\n'); log.flush()
def read(p, d):
    try:
        return json.load(open(p, encoding='utf-8'))
    except (OSError, ValueError):
        return d
def write(p, data):
    json.dump(data, open(p + '.part', 'w', encoding='utf-8'), ensure_ascii=False); os.replace(p + '.part', p)
wav = os.path.join(out, 'song.wav')
if not os.path.exists(wav):
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', song, '-vn', '-ar', '44100', '-ac', '2', '-c:a', 'pcm_s16le', wav], check=True)
say('song ready')
vocals, inst = os.path.join(out, 'vocals.wav'), os.path.join(out, 'instrumental.wav')
if not (os.path.exists(vocals) and os.path.exists(inst)):
    split = os.path.join(out, 'demucs')
    for device in ('mps', 'cpu'):
        p = subprocess.run([sys.executable, '-m', 'demucs', '--two-stems=vocals', '-n', 'htdemucs', '-d', device, '-o', split, wav], capture_output=True, text=True)
        got = os.path.join(split, 'htdemucs', 'song')
        if p.returncode == 0 and os.path.exists(os.path.join(got, 'vocals.wav')):
            shutil.move(os.path.join(got, 'vocals.wav'), vocals); shutil.move(os.path.join(got, 'no_vocals.wav'), inst); shutil.rmtree(split, ignore_errors=True)
            say('split on ' + device); break
        say('split on ' + device + ' failed: ' + str((p.stderr or '').strip().splitlines()[-1:]))
    if not os.path.exists(vocals):
        sys.exit('the vocals could not be split out (Demucs)')
import librosa
import numpy as np
y, sr = librosa.load(wav, sr=22050, mono=True)
seconds = len(y) / sr
raw_path = os.path.join(out, 'heard.json')
raw = read(raw_path, {})
if not raw.get('beats_heard'):
    beats = downbeats = None; by = ''
    try:
        from beat_this.inference import File2Beats
        for device in ('mps', 'cpu'):
            try:
                beats, downbeats = File2Beats(checkpoint_path='final0', device=device, dbn=False)(wav); by = 'beat_this (' + device + ')'; break
            except Exception as e:
                say('beat_this on ' + device + ' failed: ' + str(e))
    except ImportError as e:
        say('beat_this not there: ' + str(e))
    if beats is None or len(beats) < 8:
        _t, frames = librosa.beat.beat_track(y=y, sr=sr)
        beats = librosa.frames_to_time(frames, sr=sr)
        onset = librosa.onset.onset_strength(y=y, sr=sr)
        downbeats = beats[int(np.argmax([float(np.sum(onset[frames[k::4]])) for k in range(4)]))::4]; by = 'librosa'
    raw.update({'seconds': round(seconds, 3), 'beats_heard': [round(float(b), 3) for b in beats], 'downbeats_heard': [round(float(b), 3) for b in downbeats], 'beats_by': by})
    write(raw_path, raw); say('beats heard: ' + str(len(raw['beats_heard'])) + ' by ' + by)
if not raw.get('sections'):
    hop = 512
    chroma = librosa.feature.chroma_cqt(y=y, sr=sr, hop_length=hop)
    mfcc = librosa.feature.mfcc(y=y, sr=sr, hop_length=hop, n_mfcc=13)
    feats = np.vstack([librosa.util.normalize(chroma, axis=1), librosa.util.normalize(mfcc, axis=1)])
    bt = raw['beats_heard']
    synced = librosa.util.sync(feats, librosa.time_to_frames(bt, sr=sr, hop_length=hop))
    bounds = librosa.segment.agglomerative(synced, max(4, min(16, int(round(seconds / 20)))))
    times = sorted(set([0.0] + [float(bt[max(0, b - 1)]) if b > 0 else 0.0 for b in bounds] + [seconds]))
    rms = librosa.feature.rms(y=y, hop_length=hop)[0]
    rt = librosa.frames_to_time(np.arange(len(rms)), sr=sr, hop_length=hop)
    sections = []
    for a, b in zip(times, times[1:]):
        if b - a >= 2:
            m = (rt >= a) & (rt < b)
            sections.append({'start': round(a, 3), 'end': round(b, 3), 'energy': round(float(np.mean(rms[m])) if m.any() else 0.0, 5)})
    loud = sorted(x['energy'] for x in sections)
    for i, x in enumerate(sections, 1):
        rank = loud.index(x['energy']) / max(1, len(loud) - 1)
        x['name'] = ('HIGH' if rank >= 0.66 else 'MID' if rank >= 0.33 else 'LOW') + ' ' + str(i)
    per = [float(np.mean(rms[(rt >= t) & (rt < t + 1)])) if ((rt >= t) & (rt < t + 1)).any() else 0.0 for t in range(int(seconds))]
    best, hook = -1.0, 0.0
    for t in range(5, max(6, int(seconds) - 60 + 1)):
        v = sum(per[t:t + 60])
        if v > best:
            best, hook = v, float(t)
    raw.update({'sections': sections, 'loudest': hook}); write(raw_path, raw); say('sections: ' + str(len(sections)) + ', loudest minute at ' + str(hook))
if not os.path.exists(os.path.join(out, 'peaks.json')):
    peaks = {}
    for name, path in (('mix', wav), ('vocals', vocals), ('instrumental', inst)):
        z, _r = librosa.load(path, sr=8000, mono=True)
        vals = [float(np.max(np.abs(z[i:i + 2000]))) if len(z[i:i + 2000]) else 0.0 for i in range(0, len(z), 2000)]
        top = max(vals) or 1.0
        peaks[name] = [round(v / top, 3) for v in vals]
    write(os.path.join(out, 'peaks.json'), peaks); say('peaks drawn')
if not os.path.exists(os.path.join(out, 'lyrics.json')):
    words, lines, lang = [], [], ''
    try:   # Whisper large-v3 on the Apple GPU (mlx): the page's background process holds the CPU to a third of a core (2026-10-28: 30+ minutes on the CPU, 36 s here)
        import mlx_whisper
        r = mlx_whisper.transcribe(vocals, path_or_hf_repo='mlx-community/whisper-large-v3-mlx', word_timestamps=True)
        lang = r.get('language') or ''
        for sg in r.get('segments') or ():
            for w in sg.get('words') or ():
                words.append({'start': round(float(w['start']), 3), 'end': round(float(w['end']), 3), 'word': str(w['word']).strip()})
        say('lyrics by mlx-whisper on the GPU')
    except Exception as e:
        say('mlx-whisper failed (' + str(e)[:120] + '): faster-whisper on the CPU')
        from faster_whisper import WhisperModel
        try:
            model = WhisperModel('large-v3', device='cpu', compute_type='int8', local_files_only=True)
        except Exception:
            model = WhisperModel('large-v3', device='cpu', compute_type='int8')
        segs, info = model.transcribe(vocals, word_timestamps=True, vad_filter=True)
        lang = info.language
        for sg in segs:
            for w in sg.words or ():
                words.append({'start': round(w.start, 3), 'end': round(w.end, 3), 'word': w.word.strip()})
    cur = []
    for w in words:   # the lines, made from the words: a new line where the voice pauses or after 8 words
        if cur and (w['start'] - cur[-1]['end'] > 0.6 or len(cur) >= 8):
            lines.append({'start': cur[0]['start'], 'end': cur[-1]['end'], 'text': ' '.join(x['word'] for x in cur)}); cur = []
        cur.append(w)
    if cur:
        lines.append({'start': cur[0]['start'], 'end': cur[-1]['end'], 'text': ' '.join(x['word'] for x in cur)})
    write(os.path.join(out, 'lyrics.json'), {'language': lang, 'lines': lines, 'words': words}); say('lyrics: ' + str(len(words)) + ' words, ' + str(len(lines)) + ' lines')
say('THE HEAVY WORK IS DONE')
"""


def music_analysis(out):
    """THE BEATS MADE STEADY AND THE HOOK ON A DOWNBEAT, in this agent (plain Python): heard.json (the worker's) -> analysis.json"""
    raw = _read(os.path.join(out, 'heard.json'), {}) or {}
    if not raw.get('beats_heard') or not raw.get('sections'):
        raise RuntimeError('the worker left no beats or sections (heard.json)')
    beats, downbeats, tempo = steady_grid(raw['beats_heard'], raw['downbeats_heard'], raw['seconds'])   # a tracker skips beats; a song made on a drum machine keeps one tempo
    before = [d for d in downbeats if d <= raw['loudest'] + 0.01]
    an = {**raw, 'beats': beats, 'downbeats': downbeats, 'tempo': tempo, 'beats_by': raw.get('beats_by', '') + ' + one steady grid', 'hook': round(before[-1] if before else raw['loudest'], 3)}
    _write(os.path.join(out, 'analysis.json'), an)
    return an

def steady_grid(heard, heard_down, seconds):
    """ONE STEADY BEAT GRID FITTED TO WHAT THE TRACKER HEARD (learned 2026-10-28 on Tip Toe: beat_this skipped beats, its gaps 0.5 s and 1.0 s,
    3.09 beats a bar): the beat length from the short gaps, refined by a straight-line fit of every heard beat to its place on the grid; bar 1
    where most heard downbeats fall. -> (beats, downbeats, tempo)"""
    if len(heard) < 8:
        return heard, heard_down, 0.0
    gaps = sorted(y - x for x, y in zip(heard, heard[1:]) if y > x)
    short = [g for g in gaps if g <= gaps[len(gaps) // 4] * 1.5] or gaps   # the plain beat: the short gaps, never the skipped ones
    p = short[len(short) // 2]
    t0 = heard[0]
    for _ in range(3):   # least squares of time against beat number; each beat numbered from the one before it (gap by gap), so a small
        ks = [0]         # error in the beat length never slips a whole beat over a long song (learned on a 100 BPM click track)
        for x, y in zip(heard, heard[1:]):
            ks.append(ks[-1] + max(1, round((y - x) / p)))
        n, sk, st, skk, skt = len(ks), sum(ks), sum(heard), sum(k * k for k in ks), sum(k * t for k, t in zip(ks, heard))
        den = n * skk - sk * sk
        if not den:
            break
        p = (n * skt - sk * st) / den
        t0 = (st - p * sk) / n
    while t0 - p >= 0:
        t0 -= p
    beats = [round(t0 + k * p, 3) for k in range(int((seconds - t0) / p) + 1) if t0 + k * p <= seconds]
    best, phase = -1, 0
    for ph in range(4):
        hit = sum(1 for d in heard_down if any(abs(d - beats[k]) < 0.1 for k in range(ph, len(beats), 4)))
        if hit > best:
            best, phase = hit, ph
    return beats, beats[phase::4], round(60.0 / p, 2)


def sequences(conf):
    """HIS PROVEN SEQUENCES (the timeline lab's storyboard: SB_VIBES x SB_GROUPS): every vibe in its minute 1 order (primary) and its minute 2 order
    (secondary) -> [(vibe, order, [(group, seconds), ... 8])]; each adds up to 60 with 8 different lengths"""
    sb = _read(conf['storyboard'], {}) or {}
    groups = sb.get('SB_GROUPS') or {}
    out = []
    for vibe in sb.get('SB_VIBES') or ():
        for order, key in (('minute 1', 'primary'), ('minute 2', 'secondary')):
            slots = [(name, int(g['vibes'][vibe])) for name, g in sorted(groups.items(), key=lambda kv: kv[1][key])]
            if len(slots) == CLIPS and sum(s_ for _, s_ in slots) == TOTAL:
                out.append((vibe, order, slots))
    return out


def _near(t, marks):
    return min((abs(t - m) for m in marks), default=99.0)


def best_map(conf, an, lyrics, start, prefer=''):
    """THE MAP: the proven sequence whose slot changes land closest to the beats in this minute (a downbeat best, a section change a bonus), or the
    one he picked; each slot with its start and end, its beats and downbeats, how far its end sits from the nearest beat, its section, its words"""
    end = start + TOTAL
    beats = [b for b in an['beats'] if start - 1 <= b <= end + 1]
    downs = [b for b in an['downbeats'] if start - 1 <= b <= end + 1]
    changes = [s_['start'] for s_ in an.get('sections') or () if start < s_['start'] < end]
    scored = []
    for vibe, order, slots in sequences(conf):
        at, cost = start, 0.0
        for _g, sec in slots[:-1]:
            at += sec
            cost += min(_near(at, downs), _near(at, beats) + 0.05) - (0.1 if _near(at, changes) < 0.5 else 0.0)
        scored.append((round(cost, 3), vibe, order, slots))
    if not scored:
        raise RuntimeError(f"his proven sequences could not be read ({conf['storyboard']})")
    scored.sort(key=lambda x: x[0])
    want = prefer.lower().strip()
    pick = next((x for x in scored if want and want == f'{x[1]} {x[2]}'.lower()), None) or next((x for x in scored if want and want == x[1].lower()), None) or scored[0]
    cost, vibe, order, slots = pick
    out, at = [], start
    for n, (group, sec) in enumerate(slots, 1):
        a, b = at, at + sec
        sect = next((s_['name'] for s_ in an.get('sections') or () if s_['start'] <= a < s_['end']), '')
        out.append({'n': n, 'group': group, 'insert': 'INSERT' in group, 'seconds': sec, 'start': round(a, 3), 'end': round(b, 3),
                    'at': round(a - start, 3), 'beats': [round(x - start, 3) for x in beats if a <= x < b], 'downbeats': [round(x - start, 3) for x in downs if a <= x < b],
                    'off': round(_near(b, beats), 3) if n < CLIPS else 0.0, 'section': sect,
                    'words': ' '.join(w['word'] for w in lyrics.get('words') or () if a <= w['start'] < b)})
        at = b
    return {'sequence': vibe, 'order': order, 'score': cost, 'start': round(start, 3), 'end': round(end, 3), 'tempo': an['tempo'], 'slots': out,
            'others': [{'sequence': v, 'order': o, 'score': c, 'lengths': [x for _g, x in sl], 'inserts': [i for i, (g, _x) in enumerate(sl, 1) if 'INSERT' in g]} for c, v, o, sl in scored]}


def _seconds_of(path):
    return float((_probe(path).get('format') or {}).get('duration') or 0)


def music_stage(con, film, conf):
    """PART 1 FOR ONE FILM: the worker when its files are not all there, then the chosen minute cut from all three tracks, the map, and the check.
    -> (ok, the line)"""
    fid, out = film['id'], music_dir(conf, film['id'])
    os.makedirs(out, exist_ok=True)
    song = os.path.join(conf['films'], fid, film['song'])   # the copy in the film's own project folder, else where he named it
    if not os.path.exists(song):
        song = find_song(film['song'], conf)
    if not song:
        return False, f"the song {film['song']} is not in the film's folder, {conf['music']} or {conf['downloads']}"
    need = ('song.wav', 'vocals.wav', 'instrumental.wav', 'heard.json', 'peaks.json', 'lyrics.json')
    if not all(os.path.exists(os.path.join(out, f)) for f in need) or not (_read(os.path.join(out, 'heard.json'), {}) or {}).get('sections'):
        _set_film(con, fid, music_state='working', music_why='splitting, beats, sections, lyrics')
        if not os.path.exists(conf['audio_python']):
            return False, f"the music tools are not installed ({conf['audio_python']})"
        p = subprocess.run([conf['audio_python'], '-c', WORKER, song, out], capture_output=True, text=True, timeout=conf['music_seconds'],
                           env={**os.environ, 'HF_HUB_DISABLE_TELEMETRY': '1', 'HF_HUB_ETAG_TIMEOUT': '10', 'HF_HUB_DOWNLOAD_TIMEOUT': '60'})   # a hung network check never holds the music for long
        if p.returncode != 0:
            tail = ((p.stderr or '') + (p.stdout or '')).strip().splitlines()[-1:] or ['no word']
            return False, f'the music worker failed ({tail[0][:200]}; its log: {out}/worker.log)'
    an, lyrics = music_analysis(out), _read(os.path.join(out, 'lyrics.json'), {})
    start = film['song_start'] if film['song_start'] is not None else an['hook']
    start = max(0.0, min(float(start), an['seconds'] - TOTAL))
    on = [d for d in an.get('downbeats') or () if d <= an['seconds'] - TOTAL]
    start = round(min(on, key=lambda d: abs(d - start)) if on else start, 3)   # the minute starts on a downbeat, whatever time was asked
    cut = _read(os.path.join(out, 'minute.json'), {}) or {}
    if cut.get('start') != start or not all(os.path.exists(os.path.join(out, f'minute_{k}.wav')) for k in ('mix', 'vocals', 'instrumental')):
        for k, src in (('mix', 'song.wav'), ('vocals', 'vocals.wav'), ('instrumental', 'instrumental.wav')):
            _ff(['-ss', f'{start:.3f}', '-t', str(TOTAL), '-i', os.path.join(out, src), '-c:a', 'pcm_s16le', os.path.join(out, f'minute_{k}.wav')], f'the minute ({k})')
        _write(os.path.join(out, 'minute.json'), {'start': start})
    bar = round(4 * 60.0 / float(an['tempo']), 3)   # THE SMOOTH START AND END (the owner 2026-10-28: "use the instrumental only to fade in from zero going up then fade the vocals in ... and same at the end too"): by bars, the music's own time
    final = os.path.join(out, 'minute_final.wav')
    if (cut.get('start') != start or (_read(os.path.join(out, 'minute.json'), {}) or {}).get('bar') != bar or not os.path.exists(final)):
        _ff(['-i', os.path.join(out, 'minute_instrumental.wav'), '-i', os.path.join(out, 'minute_vocals.wav'), '-filter_complex',
             f'[0:a]afade=t=in:st=0:d={bar},afade=t=out:st={TOTAL - bar}:d={bar}[i];'   # the instrumental rises over the first bar and falls over the last
             f'[1:a]afade=t=in:st={bar}:d={bar},afade=t=out:st={TOTAL - 2 * bar}:d={bar}[v];'   # the vocals silent through the first bar, up over the second; down over the one before the last, silent in the last
             '[i][v]amix=inputs=2:normalize=0:duration=first', '-t', str(TOTAL), '-c:a', 'pcm_s16le', final], 'the smooth minute')
        _ff(['-i', final, '-c:a', 'libmp3lame', '-b:a', '320k', final[:-4] + '.mp3'], 'the final song as an MP3')
        _write(os.path.join(out, 'minute.json'), {'start': start, 'bar': bar})
    the_map = best_map(conf, an, lyrics, start, film['sequence'] or '')
    _write(os.path.join(out, 'map.json'), the_map)
    words = [w for w in lyrics.get('words') or () if start <= w['start'] < start + TOTAL]
    with open(os.path.join(out, 'minute_lyrics.srt'), 'w', encoding='utf-8') as fh:   # the minute's words, a line a slot-safe group of up to 6 words
        groups = [words[i:i + 6] for i in range(0, len(words), 6)]
        fh.write(''.join(f"{i}\n{_stamp(g[0]['start'] - start)} --> {_stamp(g[-1]['end'] - start)}\n{' '.join(w['word'] for w in g)}\n\n" for i, g in enumerate(groups, 1)))
    wrong = check_music(out, an, the_map, conf)
    if wrong:
        return False, wrong
    _set_film(con, fid, song_start=start, music_state='ready', music_why='', lengths=json.dumps([x['seconds'] for x in the_map['slots']]))
    con.execute('INSERT OR REPLACE INTO music (film, song, start, seconds, tempo, beats_by, analysis, lyrics, peaks, map, state, why, made_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)',
                (fid, film['song'], start, an['seconds'], an['tempo'], an.get('beats_by', ''), json.dumps(an), json.dumps(lyrics), json.dumps(_read(os.path.join(out, 'peaks.json'), {})),
                 json.dumps(the_map), 'ready', '', _now()))   # THE CMO'S OWN DATABASE holds the music's data (the owner 2026-10-28: "the cmo has its own database and you can store everything in there too"); the tracks stay files, served to the page
    _keep(con, conf, fid, 'music', 0, 'music/minute_final.wav', extra={'song': film['song'], 'start': start, 'tempo': an['tempo'], 'sequence': the_map.get('sequence'), 'order': the_map.get('order'), 'slots': [x['seconds'] for x in the_map['slots']], 'beats_by': an.get('beats_by', ''), 'song_sha': _sha(os.path.join(conf['films'], fid, film['song']))})
    con.commit()
    return True, (f"THE MUSIC READY · {film['song']} · {_mmss(start)}-{_mmss(start + TOTAL)} · {an['tempo']} BPM · {len(an['beats'])} beats · "
                  f"{len(words)} words in the minute · {the_map['sequence']} ({the_map['order']}) {', '.join(str(x['seconds']) for x in the_map['slots'])}")


def check_music(out, an, the_map, conf):
    """PART 1'S CHECK: the three tracks of the minute exactly 60 s, the beats and a tempo found, the map one of his proven sequences (8 different
    lengths adding up to 60), every slot holding at least one beat -> '' or what is wrong"""
    if not os.path.exists(os.path.join(out, 'minute_final.mp3')):
        _ff(['-i', os.path.join(out, 'minute_final.wav'), '-c:a', 'libmp3lame', '-b:a', '320k', os.path.join(out, 'minute_final.mp3')], 'the final song as an MP3')
    for k in ('mix', 'vocals', 'instrumental', 'final'):
        got = _seconds_of(os.path.join(out, f'minute_{k}.wav'))
        if abs(got - TOTAL) > 0.05:
            return f'the minute\'s {k} track is {got:.2f} s, not {TOTAL}'
    if len(an.get('beats') or ()) < 16 or not 40 <= float(an.get('tempo') or 0) <= 220:
        return f"the beats were not found ({len(an.get('beats') or ())} beats, tempo {an.get('tempo')})"
    lens = [x['seconds'] for x in the_map['slots']]
    proven = {(v, o): [s_ for _g, s_ in sl] for v, o, sl in sequences(conf)}
    if proven.get((the_map['sequence'], the_map['order'])) != lens or sum(lens) != TOTAL or len(set(lens)) != CLIPS:
        return f"the map is not one of his proven sequences ({the_map['sequence']} {the_map['order']}: {lens})"
    empty = [x['n'] for x in the_map['slots'] if not x['beats']]
    if empty:
        return f"slot {', '.join(map(str, empty))} holds no beat"
    return ''


# ============ PLAN CLIP'S PROMPT DOCTOR, ONE PIECE AT A TIME (learned 2026-10-28 on F-0003: one session reading all 24 frames mixed the pieces up,
# writing a piece from its neighbor's shot): first one session reads his character's pictures and writes the one fixed LOOK; then each piece its own
# session that sees only its own 3 frames, and its own blind reviewer; a RED one rewritten once with its reviewer's words.
LOOK_ASK = """Read every picture listed (Read each one). They show the character who will replace the main man of a music video: {swap}.
Pictures: {who}
Write ONE fixed description of him as a STYLIZED 3D ANIMATED CHARACTER (a fairy-tale feature-animation look, never a realistic human; the video
model refuses realistic faces): face, head, hair, body and height, wardrobe, colors, expression; then the film's grade in one sentence.
It is pasted word for word into all 8 picture prompts so he looks the same in every clip.
Answer with JSON only: {{"look": "..."}}"""

PIECE_ASK = """You write ONE clip of a 60 second music video that copies an original music video shot for shot, its main man replaced by:
{look}
THIS PIECE: clip {n}, {seconds} s, {words}.
Read these three frames of the piece with Read first: frame 1 {f1} | frame 2 {f2} | frame 3 {f3}
Frame 1 is where the clip starts and the picture it is made from. Copy ONLY frame 1's shot as one continuous take; frames 2 and 3 only show its
motion while they are still that shot (if they are another shot, ignore them: our random lengths cut across the original's cuts).
{note}
Describe frame 1 truthfully first (who is in it, where, how framed); if the main man is NOT in frame 1, put no one new in: the shot is restyled only.
- frame_prompt: an EDIT of frame 1 for the picture model: if the man is in it, "Replace the man with the character in the small inset picture at the
  top right" plus the look above; always "keep the exact composition, camera angle, background, props, lighting and colors", every other person a
  stylized animated character too, and end with "Remove the inset picture completely; the output is the scene alone, full frame".
- clip_prompt: frame 1's motion for {seconds} s, ONE continuous shot, no cuts, no text on screen.
- line: a short subtitle (at most 42 characters) in the song's mood.
Answer with JSON only: {{"frame1": "<what frame 1 shows>", "frame_prompt": "...", "clip_prompt": "...", "line": "..."}}"""

PIECE_REVIEW = """You are a BLIND reviewer; you did not write this. Read the piece's frame 1 with Read: {f1}
The clip must copy ONLY frame 1's shot (other shots of the piece are left out on purpose) and replace the main man, if he is in frame 1, with a
stylized animated character; nobody a realistic human face; one continuous shot for {seconds} s; no words on screen.
THE PROMPTS: {prompts}
Answer with JSON only: {{"grade": "GREEN" or "RED", "why": "<one line>"}}"""


def doctor_plan(con, film, conf, hire=None):
    rows = _clips(con, film['id'])
    need = [r for r in rows if not r['doctored_clip']]
    if not need:
        return ''
    home = os.path.join(conf['films'], film['id'])
    if not film['look']:
        who = ', '.join(os.path.join(conf['references'], r) for r in json.loads(film['refs'] or '[]')) or 'none: describe him from the words'
        code, said = _claude(LOOK_ASK.format(swap=film['swap'], who=who), conf, hire)
        try:
            _set_film(con, film['id'], look=str(_json_of(said).get('look') or film['swap']))
        except ValueError:
            _set_film(con, film['id'], look=film['swap'])
        film = _film(con, film['id'])
    results = {}

    def one(r, note):
        frames = [os.path.join(home, f"source_{r['n']}_{i}.jpg") for i in (1, 2, 3)]
        try:
            code, said = _claude(PIECE_ASK.format(look=film['look'], n=r['n'], seconds=r['seconds'], words=r['words'], f1=frames[0], f2=frames[1], f3=frames[2], note=note), conf, hire)
            got = _json_of(said)
            prompts = json.dumps({'frame_prompt': got.get('frame_prompt', ''), 'clip_prompt': got.get('clip_prompt', '')})
            code, said = _claude(PIECE_REVIEW.format(f1=frames[0], seconds=r['seconds'], prompts=prompts), conf, hire)
            grade = _json_of(said)
            results[r['n']] = (got, str(grade.get('grade', 'RED')).upper(), str(grade.get('why', ''))[:300])
        except Exception as e:   # noqa: BLE001
            results[r['n']] = ({}, 'RED', f'no answer ({str(e)[:120]})')
    notes = {r['n']: '' for r in need}
    for attempt in (1, 2):
        threads = [threading.Thread(target=one, args=(r, notes[r['n']]), daemon=True) for r in need]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        red = []
        for r in need:
            got, grade, why = results.get(r['n'], ({}, 'RED', 'no answer'))
            _set_clip(con, film['id'], r['n'], doctored_frame=str(got.get('frame_prompt', ''))[:3500], doctored_clip=str(got.get('clip_prompt', ''))[:3500] if grade == 'GREEN' else '',
                      line=str(got.get('line', ''))[:84], grade=grade, grade_why=why)
            if grade != 'GREEN':
                red.append(r)
                notes[r['n']] = f'A BLIND REVIEWER GRADED YOUR LAST TRY RED, FIX EXACTLY THIS: {why}'
        if not red:
            return ''
        need = red
    return f"clip {', '.join(str(r['n']) for r in need)} still RED after one rewrite ({results[need[0]['n']][2][:120]})"


def doctor(con, film, conf, hire=None):
    """the storyboard written (only the clips still without one), graded blind, a RED one rewritten once; -> '' or why it is RED"""
    if film['source']:   # PLAN CLIP: one piece at a time
        return doctor_plan(con, film, conf, hire)
    rows = _clips(con, film['id'])
    need = [r for r in rows if not r['doctored_clip']]
    if not need:
        return ''
    refs = {r['n']: r['ref'] for r in rows if r['ref']}
    redo = ''
    for attempt in (1, 2):
        film = _film(con, film['id'])
        only = (f"ONLY REWRITE CLIPS {', '.join(str(r['n']) for r in need)}; keep the shared look: {film['look']}" if film['look'] and len(need) < len(rows) else '')
        if film['source']:
            who = ', '.join(os.path.join(conf['references'], r) for r in json.loads(film['refs'] or '[]')) or 'none (describe him from the words)'
            words = PLAN_DOCTOR.format(title=film['title'], swap=film['swap'], who=who, pieces=_pieces(conf, film, rows), redo='\n'.join(x for x in (only, redo) if x))
        else:
            words = DOCTOR.format(title=film['title'], words=film['words'].split('\n', 1)[-1].strip(), lengths=', '.join(f"{r['n']}: {r['seconds']} s" for r in rows),
                                  refs=', '.join(f'{n} -> {p}' for n, p in refs.items()) or 'none', redo='\n'.join(x for x in (only, redo) if x))
        code, said = _claude(words, conf, hire)
        try:
            board = _json_of(said)
        except ValueError as e:
            return f'the Prompt Doctor gave no storyboard ({e}; exit {code})'
        got = {int(c['n']): c for c in board.get('clips') or [] if str(c.get('n', '')).isdigit()}
        if not film['look'] or len(need) == len(rows):
            _set_film(con, film['id'], look=str(board.get('look') or ''))
        for r in need:
            c = got.get(r['n'])
            if c:
                _set_clip(con, film['id'], r['n'], doctored_frame=str(c.get('frame_prompt', ''))[:3500], doctored_clip=str(c.get('clip_prompt', ''))[:3500],
                          line=str(c.get('line', ''))[:84])
        rows = _clips(con, film['id'])
        graded = [r for r in rows if r['n'] in {x['n'] for x in need}]
        shown = json.dumps([{'n': r['n'], 'seconds': r['seconds'], 'frame_prompt': r['doctored_frame'], 'clip_prompt': r['doctored_clip']} for r in graded])
        code, said = _claude(PLAN_GRADER.format(swap=film['swap'], pieces=_pieces(conf, film, graded), clips=shown) if film['source'] else
                             GRADER.format(title=film['title'], words=film['words'].split('\n', 1)[-1].strip(), clips=shown), conf, hire)
        try:
            grades = {int(g['n']): g for g in _json_of(said).get('grades') or []}
        except (ValueError, TypeError, KeyError):
            grades = {}
        red = []
        for r in graded:
            g = grades.get(r['n']) or {'grade': 'RED', 'why': 'the blind reviewer gave no grade'}
            _set_clip(con, film['id'], r['n'], grade=str(g.get('grade', 'RED')).upper(), grade_why=str(g.get('why', ''))[:300])
            if str(g.get('grade', '')).upper() != 'GREEN' or not r['doctored_clip']:
                red.append(r)
        if not red:
            return ''
        need = red
        redo = 'THE BLIND REVIEWER GRADED THESE RED, FIX EXACTLY THIS: ' + '; '.join(f"clip {r['n']}: {grades.get(r['n'], {}).get('why', 'no grade')}" for r in red)
        for r in red:
            _set_clip(con, film['id'], r['n'], doctored_clip='')
    return f"clip {', '.join(str(r['n']) for r in need)} still RED after one rewrite ({(grades.get(need[0]['n']) or {}).get('why', '')[:120]})"


# ============ PLAN CLIP (the owner 2026-10-28: "will break up a video from the folder. you give it a name it finds it in the folder and breaks it up
# and replaces the 8 automatically and uses our unique sequence timing"; "the hook, found automatically"): the loudest 60 seconds of its song (the
# hook) cut into this film's 8 lengths; each piece's own frames become its clip's reference, so the film follows the original shot for shot, its
# music under it in sync.
def hook_start(path, seconds):
    """the start (whole seconds) of the 60 seconds of the song with the most sound in it: the hook"""
    p = subprocess.run(['ffmpeg', '-v', 'error', '-i', path, '-vn', '-af', 'aresample=8000,asetnsamples=n=8000:p=0,astats=metadata=1:reset=1,'
                        'ametadata=print:key=lavfi.astats.Overall.RMS_level:file=-', '-f', 'null', '-'], capture_output=True, text=True)
    levels = [max(-90.0, float(v)) if v not in ('-inf', 'inf', 'nan') else -90.0 for v in re.findall(r'RMS_level=(\S+)', p.stdout)]
    power = [10 ** (v / 10) for v in levels]
    last = int(min(len(power), seconds)) - TOTAL
    if last <= 0:
        return 0
    best, at = -1.0, 0
    run_sum = sum(power[:TOTAL])
    for start in range(0, last + 1):
        if start:
            run_sum += power[start + TOTAL - 1] - power[start - 1]
        if start >= 5 and run_sum > best:   # never the first seconds (an intro is never the hook)
            best, at = run_sum, start
    return at


def seed_plan(con, film, conf):
    """PLAN CLIP's 8 clips: the hook found, the 60 seconds cut into this film's random lengths, each piece's frames kept as its reference,
    the song's 60 seconds kept as this film's own music"""
    src = os.path.join(conf['source'], film['source'])
    if not os.path.exists(src):
        raise RuntimeError(f"the video {film['source']} is no longer in {conf['source']} (CLEAR empties it)")
    home = os.path.join(conf['films'], film['id'])
    os.makedirs(home, exist_ok=True)
    seconds = float((_probe(src).get('format') or {}).get('duration') or 0)
    start = hook_start(src, seconds)
    pics = [os.path.join(conf['references'], r) for r in json.loads(film['refs'] or '[]') if os.path.exists(os.path.join(conf['references'], r))]
    who = ''
    if pics:   # his character: its first picture (a png copy, so any picture kind is read)
        who = os.path.join(home, 'character.png')
        subprocess.run(['sips', '-s', 'format', 'png', pics[0], '--out', who], capture_output=True)
        who = who if os.path.exists(who) else ''
    _ff(['-ss', str(start), '-t', str(TOTAL), '-i', src, '-vn', '-ar', '48000', '-ac', '2', os.path.join(home, 'music_src.wav')], 'the song\'s hook')
    at = start
    for n, length in enumerate(lengths(), 1):
        first = at + min(0.4, length * 0.2)   # the moment the clip starts from: its reference AND Claude's frame 1, the same frame
        for i, t in enumerate((first, at + length * 0.5, at + length * 0.85), 1):   # three looks at the piece: Claude reads its motion from them
            _ff(['-ss', f'{t:.2f}', '-i', src, '-frames:v', '1', '-vf', 'scale=640:-2', os.path.join(home, f'source_{n}_{i}.jpg')], f'piece {n} frame {i}')
        ref = os.path.join(home, f'source_{n}.png')
        _ff(['-ss', f'{first:.2f}', '-i', src, '-frames:v', '1', ref], f'piece {n} reference')
        if who:   # HIS CHARACTER'S PICTURE IN THE CORNER (the lab's picture door takes one picture): the frame with the character set in at its right edge
            with_who = os.path.join(home, f'source_{n}_with_character.png')
            _ff(['-i', ref, '-i', who, '-filter_complex', f'[0:v]scale={W}:{H}[f];[1:v]scale=-2:{H // 2 - 24},pad=iw+12:ih+12:6:6:white[c];[f][c]overlay=W-w-16:16',
                 '-frames:v', '1', with_who], f'piece {n} with the character')
            ref = with_who
        con.execute('INSERT INTO clips (film, n, seconds, words, ref, state, takes, source_at) VALUES (?,?,?,?,?,?,?,?)',
                    (film['id'], n, length, f"the original {_mmss(at - start)}-{_mmss(at - start + length)} ({_mmss(at)}-{_mmss(at + length)} of the video)", ref, 'asked', '[]', at))
        at += length
    con.commit()
    _set_film(con, film['id'], lengths=json.dumps([r['seconds'] for r in _clips(con, film['id'])]), state='doctor', music_start=start, track='film:music_src.wav')


PLAN_DOCTOR = """You are the PROMPT DOCTOR of a 60 second music video made by copying an original music video shot for shot, with its main man replaced.
TITLE: {title}
WHO REPLACES THE MAN: {swap}
HIS PICTURES OF THAT CHARACTER (Read every one first; copy his look exactly): {who}
Make him a STYLIZED 3D ANIMATED CHARACTER (a fairy-tale feature-animation look), never a realistic human: the video model refuses realistic faces.
Keep the original's wardrobe idea, attitude and moves, so a viewer sees the same video with a new star.
THE 8 PIECES, IN ORDER (read every frame with Read before you write; frame 1 is where the clip starts). Our clip lengths are random, so a piece
may hold more than one of the original's shots: each clip copies ONLY the shot its frame 1 shows (its picture is made from frame 1), as one
continuous take; the piece's other shots are left out on purpose. Never take a shot from another piece.
{pieces}
{redo}
First write "look": ONE fixed description of the new character (face, body, hair, wardrobe, colors, style) and the film's grade; it is pasted into every
picture prompt word for word, so all 8 clips show the same character.
For every piece give:
- frame_prompt: an EDIT of the piece's own first frame (it is given to the picture model): "Replace the man with <the character>; keep the exact
  composition, camera angle, background, props, lighting and colors"; any other people in the frame become stylized animated characters too.
  When he gave pictures, the frame given to the model carries the character's picture inset at its top right edge: say "the character in the
  small inset picture at the top right" and end with "Remove the inset picture completely; the output is the scene alone, full frame".
- clip_prompt: the motion of frame 1's shot (his moves, the camera move; frames 2 and 3 help only while they show the same shot), sized to its
  seconds, ONE continuous shot, no cuts, no text on screen.
- line: a short subtitle (at most 42 characters) in the song's mood.
Answer with JSON only: {{"look": "...", "clips": [{{"n": 1, "frame_prompt": "...", "clip_prompt": "...", "line": "..."}}, ... 8]}}"""

PLAN_GRADER = """You are a BLIND reviewer. You did not write these prompts. They copy an original music video shot for shot, replacing its main man with: {swap}.
Look at each piece's frames (Read them) and grade each clip GREEN or RED. Our clip lengths are random, so a piece may hold more than one of the
original's shots: each clip copies ONLY the shot its frame 1 shows, as one continuous take; leaving the piece's other shots out is RIGHT, never a fault.
GREEN: it keeps frame 1's shot (its composition and motion), it swaps the man for the stylized animated character, nobody is a realistic human face, it is one
continuous shot that fits its seconds, no words on screen. RED: anything else; say why in one line.
THE PIECES: {pieces}
THE CLIPS: {clips}
Answer with JSON only: {{"grades": [{{"n": 1, "grade": "GREEN", "why": "..."}}, ... one per clip]}}"""


def _pieces(conf, film, rows):
    home = os.path.join(conf['films'], film['id'])
    return '\n'.join(f"piece {r['n']}: {r['seconds']} s · {r['words']} · frames: " + ', '.join(os.path.join(home, f"source_{r['n']}_{i}.jpg") for i in (1, 2, 3)) for r in rows)


# ============ 3 AND 4. THE LAB'S OWN DOORS (started, never changed)
def lab_up(conf):
    try:
        with urllib.request.urlopen(conf['lab'] + '/make?job=none', timeout=3):
            return True
    except Exception:   # noqa: BLE001
        pass
    subprocess.Popen(['python3', 'lab.py'], cwd=conf['lab_dir'], stdout=open(os.path.join(conf['lab_dir'], 'lab.log'), 'a'), stderr=subprocess.STDOUT,
                     stdin=subprocess.DEVNULL, start_new_session=True)   # the lab's own start (start.sh's line), detached, from its own folder
    for _ in range(30):
        time.sleep(1)
        try:
            with urllib.request.urlopen(conf['lab'] + '/make?job=none', timeout=3):
                return True
        except Exception:   # noqa: BLE001
            continue
    return False


def _ask(conf, body):
    req = urllib.request.Request(conf['lab'] + '/make', data=json.dumps(body).encode(), method='POST', headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(r.read().decode())


def _wait(conf, said, most):
    """a lab job until it is done -> its file name; a refusal or a failure raises its words"""
    if not said.get('ok'):
        raise RuntimeError(said.get('why') or 'the lab refused')
    job, until = said['job'], time.time() + most
    while said.get('state') != 'done':
        if said.get('state') == 'failed':
            raise RuntimeError(said.get('why') or 'the lab could not make it')
        if time.time() > until:
            raise RuntimeError(f'the lab took longer than {most // 60} minutes')
        time.sleep(5)
        with urllib.request.urlopen(conf['lab'] + '/make?job=' + job, timeout=30) as r:
            said = json.loads(r.read().decode())
    return said.get('name') or job, said.get('by') or ''


def _into_lab(conf, src, name):
    """HIS REFERENCE INTO THE LAB'S OWN INPUT FOLDER (inserts/: "any .jpg or .png put in inserts/"), as a png; -> its address in the lab"""
    target = os.path.join(conf['lab_dir'], 'inserts', name)
    if not os.path.exists(target):
        subprocess.run(['sips', '-s', 'format', 'png', src, '--out', target], capture_output=True)
    if not os.path.exists(target):
        raise RuntimeError(f'the reference {os.path.basename(src)} could not be read as a picture')
    return '/inserts/' + name


def _key_frame(conf, address):
    said = _ask(conf, {'keyframe': address})
    if not said.get('ok'):
        raise RuntimeError(said.get('why') or 'no key frame')
    return said['name']


def make_picture(conf, film, r, guide):
    """Nano Banana 2 through the lab: his reference (or clip 1's picture) as the key frame -> the lab address of the picture"""
    ref = _key_frame(conf, guide) if guide else ''
    name, _by = _wait(conf, _ask(conf, {'model': 'nano-banana-2', 'prompt': f"{r['doctored_frame']} {film['look'] or ''}".strip(), 'ref': ref, 'take': int(r['take'] or 0)}), 600)
    return ('/images/' if ref else '/inserts/') + name


def make_clip(conf, film, r, picture, said_step=None):
    """Seedance 2.5 through the lab, cut by the lab to min(seconds, 10); longer, the lab's own continuation to the clip's seconds"""
    first = min(r['seconds'], LAB_MOST)
    name, by = _wait(conf, _ask(conf, {'model': 'seedance-2.5', 'prompt': r['doctored_clip'], 'seconds': first, 'from': picture, 'take': int(r['take'] or 0)}), conf['make_seconds'])
    have = first
    while have < r['seconds']:
        need = min(r['seconds'], have + EXTEND_MOST)
        if said_step:
            said_step(f"clip {r['n']}: continuing {have} s to {need} s")
        name, by = _wait(conf, _ask(conf, {'extend': {'video': name, 'need': need, 'prompt': r['doctored_clip'], 'take': int(r['take'] or 0)}}), conf['make_seconds'])
        have = need
    return name, by


# ============ 5. THE CUT AND THE LAYERS (ffmpeg on this Mac; the subtitles drawn by the Mac's own text)
def _ff(args, what):
    p = subprocess.run(['ffmpeg', '-v', 'error', '-y'] + args, capture_output=True, text=True)
    if p.returncode != 0:
        raise RuntimeError(f'{what} failed ({(p.stderr or "").strip().splitlines()[-1:] or ["no word"]})')


def _probe(path):
    p = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration:stream=codec_type,nb_frames', '-of', 'json', path], capture_output=True, text=True)
    return json.loads(p.stdout or '{}')


def cues(rows):
    """one subtitle a clip, in its own window; a clip too short to read gives its line to the next clip's window (the last to the one before)"""
    out, start, carry = [], 0, None
    for i, r in enumerate(rows):
        a, b = (carry[0] if carry else start), start + r['seconds']
        text = ' · '.join(x for x in ((carry[1] if carry else ''), r['line'] or '') if x)
        start = b
        if b - a < READ_LEAST and i < len(rows) - 1:
            carry = (a, text)
            continue
        carry = None
        if text:
            out.append([a, b, text])
    if carry and out:
        out[-1][2] = out[-1][2] + ' · ' + carry[1]
    return out


def _stamp(s):
    return f'{int(s // 3600):02d}:{int(s % 3600 // 60):02d}:{int(s % 60):02d},{int(round((s - int(s)) * 1000)):03d}'


SWIFT = r"""import AppKit
let a = CommandLine.arguments
var i = 1
while i + 1 < a.count {
  let rep = NSBitmapImageRep(bitmapDataPlanes: nil, pixelsWide: %d, pixelsHigh: %d, bitsPerSample: 8, samplesPerPixel: 4, hasAlpha: true, isPlanar: false, colorSpaceName: .deviceRGB, bytesPerRow: 0, bitsPerPixel: 0)!
  NSGraphicsContext.saveGraphicsState()
  NSGraphicsContext.current = NSGraphicsContext(bitmapImageRep: rep)
  let style = NSMutableParagraphStyle(); style.alignment = .center
  let shadow = NSShadow(); shadow.shadowColor = NSColor.black.withAlphaComponent(0.9); shadow.shadowBlurRadius = 6; shadow.shadowOffset = NSSize(width: 0, height: -2)
  let attrs: [NSAttributedString.Key: Any] = [.font: NSFont(name: "Helvetica Neue Bold", size: 38) ?? NSFont.boldSystemFont(ofSize: 38), .foregroundColor: NSColor.white, .paragraphStyle: style, .shadow: shadow]
  NSString(string: a[i]).draw(in: NSRect(x: 80, y: 36, width: %d, height: 110), withAttributes: attrs)
  NSGraphicsContext.restoreGraphicsState()
  try! rep.representation(using: .png, properties: [:])!.write(to: URL(fileURLWithPath: a[i + 1]))
  i += 2
}
""" % (W, H, W - 160)


def assemble(con, film, conf):
    """the 8 clips cut to their exact frames and joined, then the layers: subtitles, the logo, the music; -> the final file"""
    rows = _clips(con, film['id'])
    home = os.path.join(conf['films'], film['id'])
    os.makedirs(home, exist_ok=True)
    layers, picked = json.loads(film['layers'] or '[]'), json.loads(film['music'] or '[]')
    parts = []
    for r in rows:
        part = os.path.join(home, f"part_{r['n']}.mp4")
        _ff(['-i', os.path.join(home, r['clip']), '-an', '-vf', f'fps={FPS},scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},setsar=1,tpad=stop_mode=clone:stop_duration=1',
             '-frames:v', str(r['seconds'] * FPS), '-c:v', 'libx264', '-crf', '16', '-pix_fmt', 'yuv420p', part], f"clip {r['n']}'s trim")
        parts.append(part)
    cut = os.path.join(home, 'cut.mp4')
    _ff(sum((['-i', p] for p in parts), []) + ['-filter_complex', ''.join(f'[{i}:v]' for i in range(len(parts))) + f'concat=n={len(parts)}:v=1:a=0[v]',
        '-map', '[v]', '-c:v', 'libx264', '-crf', '16', '-pix_fmt', 'yuv420p', '-r', str(FPS), cut], 'the cut')
    said = cues(rows)
    srt = os.path.join(home, 'subtitles.srt')
    with open(srt, 'w', encoding='utf-8') as f:
        f.write(''.join(f'{i}\n{_stamp(a)} --> {_stamp(b)}\n{t}\n\n' for i, (a, b, t) in enumerate(said, 1)))
    with open(os.path.join(home, 'subtitles.vtt'), 'w', encoding='utf-8') as f:
        f.write('WEBVTT\n\n' + ''.join(f"{_stamp(a).replace(',', '.')} --> {_stamp(b).replace(',', '.')}\n{t}\n\n" for a, b, t in said))
    inputs, chain, last, k = ['-i', cut], [], '0:v', 1
    if 'subtitles' in layers and said:
        script = os.path.join(home, 'subtitles.swift')
        with open(script, 'w') as f:
            f.write(SWIFT)
        pngs = [os.path.join(home, f'sub_{i}.png') for i in range(len(said))]
        subprocess.run(['swift', script] + sum(([t, p] for (_a, _b, t), p in zip(said, pngs)), []), capture_output=True, timeout=300)
        for (a, b, _t), p in zip(said, pngs):
            if os.path.exists(p):
                inputs += ['-i', p]
                chain.append(f"[{last}][{k}:v]overlay=0:0:enable='between(t,{a},{b - 0.04})'[s{k}]")
                last, k = f's{k}', k + 1
    if 'logo' in layers and os.path.exists(conf['logo']):
        inputs += ['-loop', '1', '-framerate', str(FPS), '-t', str(TOTAL), '-i', conf['logo'], '-loop', '1', '-framerate', str(FPS), '-t', str(TOTAL), '-i', conf['logo']]
        chain.append(f'[{k}:v]scale=150:-1,format=rgba,colorchannelmixer=aa=0.85[lc]')
        chain.append(f'[{k + 1}:v]scale=520:-1,format=rgba,fade=t=in:st={TOTAL - 2.5}:d=0.6:alpha=1[le]')
        chain.append(f"[{last}]drawbox=x=0:y=0:w=iw:h=ih:color=black@0.55:t=fill:enable='gte(t,{TOTAL - 2.5})'[dk]")
        chain.append(f"[dk][lc]overlay=W-w-36:36:enable='lt(t,{TOTAL - 2.5})'[l1]")
        chain.append("[l1][le]overlay=(W-w)/2:(H-h)/2:eof_action=pass[l2]")
        last, k = 'l2', k + 2
    track = ''
    if 'music' in layers:
        tracks = sorted(f for f in os.listdir(conf['music']) if f.endswith('.wav')) if os.path.isdir(conf['music']) else []
        chosen = [t for t in tracks if t in picked] or tracks
        own = (film['track'] or '').startswith('film:') and os.path.exists(os.path.join(home, film['track'][5:]))
        if own or chosen:
            track = film['track'] if own else random.choice(chosen)
            inputs += ['-i', os.path.join(home, track[5:]) if own else os.path.join(conf['music'], track)]
            chain.append(f'[{k}:a]atrim=0:{TOTAL},asetpts=N/SR/TB,afade=t=in:st=0:d=1,afade=t=out:st={TOTAL - 3}:d=3,loudnorm=I=-16:TP=-1.5:LRA=11,aresample=48000[a]')
            k += 1
            _ff(['-i', os.path.join(home, track[5:]) if own else os.path.join(conf['music'], track), '-af', f'atrim=0:{TOTAL},asetpts=N/SR/TB,afade=t=in:st=0:d=1,afade=t=out:st={TOTAL - 3}:d=3,loudnorm=I=-16:TP=-1.5:LRA=11,aresample=48000',
                 '-c:a', 'aac', '-b:a', '192k', os.path.join(home, 'music.m4a')], 'the music on its own')
    if chain:   # the last frame held, never one short: the layers end exactly at 1800 frames (-frames:v below)
        chain.append(f'[{last}]tpad=stop_mode=clone:stop_duration=1[vend]')
        last = 'vend'
    final = os.path.join(home, 'final.mp4')
    maps = ['-map', f'[{last}]' if chain and last != '0:v' else '0:v'] + (['-map', '[a]'] if track else [])
    inputs += ['-i', srt]
    maps += ['-map', f'{k}:s']
    _ff(inputs + (['-filter_complex', ';'.join(chain)] if chain else []) + maps + ['-c:v', 'libx264', '-crf', '17', '-pix_fmt', 'yuv420p', '-r', str(FPS),
        '-c:a', 'aac', '-b:a', '192k', '-c:s', 'mov_text', '-metadata:s:s:0', 'language=eng', '-frames:v', str(TOTAL * FPS), '-movflags', '+faststart', final], 'the layers')   # exactly 1800 frames (a cut at 60.0 s dropped the last one)
    return final, track


def check(final, rows, layers, track):
    """THE CHECK: 60 s, 8 cuts of 8 different lengths, the picture, the music and the subtitles in the file -> '' or what is wrong"""
    got = _probe(final)
    kinds = [s.get('codec_type') for s in got.get('streams') or []]
    seconds = float((got.get('format') or {}).get('duration') or 0)
    frames = next((int(s.get('nb_frames') or 0) for s in got.get('streams') or [] if s.get('codec_type') == 'video'), 0)
    lens = [r['seconds'] for r in rows]
    if len(lens) != CLIPS or len(set(lens)) != CLIPS or sum(lens) != TOTAL:
        return f'the lengths are not 8 different seconds adding up to 60 ({lens})'
    if frames != TOTAL * FPS:
        return f'the picture holds {frames} frames, not {TOTAL * FPS} ({seconds:.2f} s)'
    if 'video' not in kinds or 'subtitle' not in kinds or (track and 'audio' not in kinds) or ('music' in layers and not track):
        return f'the file holds {kinds}: the picture, the music and the subtitles must all be there'
    return ''


# ============ THE RUN (ON RUN AGENT ONLY)
class Beat:
    """a long step's heartbeat: its job's RUN written RUNNING every minute, so THE RED never takes a working film for a stuck one"""
    def __init__(self, store, job_key):
        self.store, self.job_key, self.stop, self.thread = store, job_key, threading.Event(), None

    def __enter__(self):
        def beat():
            while not self.stop.wait(BEAT):
                try:
                    self.store._edit(self.job_key, {'run_state': 'RUNNING'}, run=True)
                except Exception:   # noqa: BLE001
                    pass
        if self.job_key and hasattr(self.store, '_edit'):
            self.thread = threading.Thread(target=beat, daemon=True)
            self.thread.start()
        return self

    def __exit__(self, *exc):
        self.stop.set()
        if self.thread:
            self.thread.join()


def _seed(con, film, conf):
    """the film's 8 clips, once: the lengths drawn, his lines and references placed"""
    if _clips(con, film['id']):
        return
    if film['source']:
        return seed_plan(con, film, conf)
    _title, prompts = parse(film['words'])
    refs = json.loads(film['refs'] or '[]')
    tied, lines = {}, {}
    if len(prompts) > 1:
        for i, p in enumerate(prompts, 1):
            m = re.match(r'^(\d+)\s*:\s*(.+)$', p)
            if m and 1 <= int(m.group(1)) <= len(refs):
                tied[i] = refs[int(m.group(1)) - 1]
                p = m.group(2)
            lines[i] = p
    for n, s in enumerate(lengths(), 1):
        ref = tied.get(n) or (refs[(n - 1) % len(refs)] if refs and not tied else '')
        con.execute('INSERT INTO clips (film, n, seconds, words, ref, state, takes) VALUES (?,?,?,?,?,?,?)',
                    (film['id'], n, s, lines.get(n, prompts[0] if len(prompts) == 1 else ''), os.path.join(conf['references'], ref) if ref else '', 'asked', '[]'))
    con.commit()
    _set_film(con, film['id'], lengths=json.dumps([r['seconds'] for r in _clips(con, film['id'])]), state='doctor')


def make(store, conf=None, hire=None, step=lambda s: None):
    """ONE FILM: the newest film not done -> (ok, the line said)"""
    conf = conf or CONF
    con = _db(store)
    try:
        film = con.execute("SELECT * FROM films WHERE state NOT IN ('done', 'removed') AND NOT (state = 'music ready' AND music_state = 'ready') ORDER BY asked_at DESC LIMIT 1").fetchone()
        if not film:
            return True, 'nothing to make: every film is done · add one in ADD FILM TO BACKLOG'
        fid = film['id']
        if film['song']:   # PART 1 · THE MUSIC first: nothing else starts until it is ready (the owner: "or the rest is a waste of time")
            step(f'{fid}: the music')
            ok, line = music_stage(con, film, conf)
            if not ok:
                _set_film(con, fid, music_state='red', music_why=line)
                con.execute("UPDATE music SET state = 'red', why = ? WHERE film = ?", (line, fid))
                con.commit()
                return False, f'{fid} · {line} · {HAND}fix what it names (the song in {conf["music"]}, the tools in {os.path.dirname(os.path.dirname(conf["audio_python"]))}), then RUN AGENT'
            asked_skin = con.execute("SELECT n FROM skin WHERE film = ? AND state = 'asked' ORDER BY n", (fid,)).fetchall()
            if asked_skin:   # SKIN pressed on a slot: that slot alone
                return skin_one(con, conf, _film(con, fid), [r['n'] for r in asked_skin], step)
            if (film['swap_state'] or '') == 'asked':   # SWAP FACES pressed: the swaps after the music
                _set_film(con, fid, swap_state='working')
                return swap_faces(con, conf, _film(con, fid), step)
            if (film['posters_state'] or '') == 'asked':   # MAKE POSTERS pressed: the posters after the music
                _set_film(con, fid, posters_state='working')
                return make_posters(con, conf, _film(con, fid), step)
            _set_film(con, fid, state='music ready', why='')
            return True, f'{fid} · {line} · part 2 (the posters) is next'
        _seed(con, film, conf)
        step(f'{fid}: the Prompt Doctor')
        why = doctor(con, _film(con, fid), conf, hire)
        if why:
            _set_film(con, fid, state='red', why=why)
            return False, f'{fid} · {why} · {HAND}edit that line (REDO with new words), then RUN AGENT'
        if not lab_up(conf):
            _set_film(con, fid, state='red', why='the timeline lab did not start')
            return False, f"{fid} · the timeline lab (8822) did not start · {HAND}cd {conf['lab_dir']} && ./start.sh, then RUN AGENT"
        film, home = _film(con, fid), os.path.join(conf['films'], fid)
        os.makedirs(home, exist_ok=True)
        todo = [r for r in _clips(con, fid) if r['state'] != 'done']
        guides = {}
        for r in todo:   # his references into the lab's input folder
            if r['ref']:
                guides[r['n']] = _into_lab(conf, r['ref'], f"cmo_{fid}_{r['n']}_{re.sub(r'[^A-Za-z0-9]', '', os.path.basename(r['ref']))[:40]}.png")
        rows = _clips(con, fid)
        first = next((r for r in rows if r['n'] == 1), None)
        errors = {}

        def one(r, guide, picture=''):
            try:
                _c = _db(store)
                if not picture:
                    _set_clip(_c, fid, r['n'], state='picture')
                    picture = make_picture(conf, film, r, guide)
                _set_clip(_c, fid, r['n'], picture=picture, state='clip')
                name, by = make_clip(conf, film, r, picture, step)
                src = os.path.join(conf['lab_dir'], 'media', name)
                own = f"clip_{r['n']}_take{int(r['take'] or 0)}.mp4"
                shutil.copyfile(src, os.path.join(home, own))
                pic = os.path.join(conf['lab_dir'], picture.lstrip('/'))
                if os.path.exists(pic):
                    shutil.copyfile(pic, os.path.join(home, f"picture_{r['n']}_take{int(r['take'] or 0)}.png"))
                takes = json.loads(r['takes'] or '[]') + [own]
                _set_clip(_c, fid, r['n'], clip=own, made_by=by, state='done', why='', takes=json.dumps(takes))
                _c.close()
            except Exception as e:   # noqa: BLE001
                errors[r['n']] = str(e)[:200]
                c = _db(store)
                _set_clip(c, fid, r['n'], state='red', why=str(e)[:200])
                c.close()
        step(f'{fid}: the pictures and clips ({len(todo)} to make)')
        first_picture = ''
        if first in todo and not guides:   # clip 1's picture first: it guides the other seven, which start the moment it exists
            try:
                _set_clip(con, fid, 1, state='picture')
                first_picture = make_picture(conf, film, first, '')
                _set_clip(con, fid, 1, picture=first_picture, state='clip')
            except Exception as e:   # noqa: BLE001
                _set_clip(con, fid, 1, state='red', why=str(e)[:200])
                _set_film(con, fid, state='red', why=f'clip 1: {str(e)[:200]}')
                return False, f'{fid} · clip 1 picture not made ({str(e)[:160]}) · {HAND}REDO clip 1, then RUN AGENT'
        threads = []
        style = first_picture or (_clips(con, fid)[0]['picture'] if not guides else '')
        for r in [x for x in _clips(con, fid) if x['n'] in {t['n'] for t in todo}]:
            t = threading.Thread(target=one, args=(r, guides.get(r['n']) or (style if style and r['n'] != 1 else ''), first_picture if r['n'] == 1 else ''), daemon=True)
            t.start()
            threads.append(t)
        for t in threads:
            t.join()
        if errors:
            n = min(errors)
            _set_film(con, fid, state='red', why=f'clip {n}: {errors[n]}')
            return False, f'{fid} · clip {n} not made ({errors[n]}) · {HAND}REDO clip {n} (new words if it was refused), then RUN AGENT'
        step(f'{fid}: the cut and the layers')
        film = _film(con, fid)
        final, track = assemble(con, film, conf)
        rows = _clips(con, fid)
        wrong = check(final, rows, json.loads(film['layers'] or '[]'), track)
        if wrong:
            _set_film(con, fid, state='red', why=wrong, final=final)
            return False, f'{fid} · the check: {wrong} · {HAND}RUN AGENT (the cut and layers again, no new clips)'
        out = os.path.join(conf['downloads'], f"{re.sub(r'[^A-Za-z0-9 _-]', '', film['title']).strip() or fid} · one min sm video · {fid}.mp4")
        shutil.copyfile(final, out)
        _set_film(con, fid, state='done', why='', final=final, downloads=out, track=track)
        return True, f"{fid} · {film['title']} · 60 s · 8 clips {', '.join(str(r['seconds']) for r in rows)} · in Downloads"
    finally:
        con.close()


def _lock(conf):
    os.makedirs(conf['films'], exist_ok=True)
    fh = open(os.path.join(conf['films'], '.lock'), 'a+')
    try:
        fcntl.flock(fh, fcntl.LOCK_EX | fcntl.LOCK_NB)
        return fh
    except OSError:
        fh.close()
        return None


def run(store, job_key, n, agent=None, shells=(), chain=(), conf=None, hire=None, **_):
    """ONE RUN (RUN AGENT): one film at a time, its run written DONE (exit 0) or FAILED (exit 1) with his one step"""
    conf = {**CONF, **(conf or {})}
    started = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    lock = _lock(conf)
    try:
        if lock is None:
            ok, line = True, 'another film is being made now: this press makes nothing (one film at a time)'
        else:
            try:
                with Beat(store, job_key):
                    ok, line = make(store, conf, hire, lambda s: None)
            except Exception as fault:   # noqa: BLE001  (a crash is red, named as one)
                at = traceback.extract_tb(fault.__traceback__)[-1] if fault.__traceback__ else None
                where = f'{os.path.basename(at.filename)} line {at.lineno}' if at else 'its own code'
                ok, line = False, f'it crashed at {where} ({type(fault).__name__}: {str(fault)[:160]}) · {HAND}open {where}, fix what it names, then RUN AGENT'
    finally:
        if lock is not None:
            lock.close()
    said = {'summary': ('' if ok else 'FAILED · ') + line, 'ok': ok, 'lines': [line]}
    store.ran(job_key, n, started, datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 0 if ok else 1, json.dumps(said), 'DONE' if ok else 'FAILED')
    return said


def latest(store, job_key):
    for r in sorted(store.runs(job_key, 1000), key=lambda r: r['started_at'], reverse=True)[:1]:
        try:
            return json.loads(r['said'])
        except (TypeError, ValueError):
            return None
    return None


def until_next(now=None, schedule=None):
    """ON RUN AGENT ONLY: never due by itself"""
    return 365 * 86400


def clock(schedule=None):
    schedule = schedule or SCHEDULE
    return {'zone': schedule['location'], 'at': '', 'said': 'ON RUN AGENT', 'when': 'ON RUN AGENT', 'repeat': 'MANUAL', 'hour_deg': 0, 'minute_deg': 0}


# ============ ITS BLOCK: the form, the films, the newest film's clips
def content(store, job_key, block=None, conf=None):
    conf = conf or CONF
    pics = reference_pictures(conf)
    tracks = sorted(f for f in os.listdir(conf['music']) if f.endswith('.wav')) if os.path.isdir(conf['music']) else []
    boxes = [{'key': 'refs', 'label': 'REFERENCES (~/scratch/cmo/references)', 'note': '(N: words ties reference N to clip N)',
              'boxes': [{'value': p, 'label': f'{i}. {p[:38]}', 'checked': False} for i, p in enumerate(pics, 1)]},
             {'key': 'layers', 'label': 'LAYERS (none ticked = none)', 'boxes': [{'value': v, 'label': v.upper(), 'checked': False} for v in ('logo', 'subtitles', 'music')]},
             {'key': 'source', 'label': 'PLAN CLIP (~/scratch/cmo/source)', 'note': '(or a line: plan: <name>; line 2 who replaces the guy)',
              'boxes': [{'value': v, 'label': v[:46], 'checked': False} for v in source_videos(conf)]},
             {'key': 'music', 'label': 'MUSIC (free, none ticked = any; PLAN CLIP: the song itself)', 'boxes': [{'value': t, 'label': t[:-4].replace('_', ' ')[:34], 'checked': False} for t in tracks]}]
    form = {'kind': 'form', 'title': 'ADD FILM TO BACKLOG', 'do': 'add', 'name': 'words', 'rows': 6, 'label': 'Add',
            'placeholder': 'line 1: the title · line 2: the song, its file name pasted as it is (for example RiFF RAFF - Tip Toe Wing In My Jawwdinz (CLEAN BASS BOOST) - ZupaZ.mp3) · Shift+Enter starts a new line',
            'boxes': {'title': 'ONE MIN SM VIDEO · 8 CLIPS · 60 SECONDS', 'name': 'refs', 'rows': [{**b, 'boxes': [{**x, 'value': x['value']} for x in b['boxes']]} for b in boxes]}}
    # each box row carries its own field name: the form draws one name for all boxes, so the value says which list it is
    for row in form['boxes']['rows']:
        for x in row['boxes']:
            x['value'] = x['value'] if row['key'] == 'refs' else f"{row['key']}:{x['value']}"
    try:
        con = _db(store)
    except sqlite3.Error as e:
        return [form, {'kind': 'note', 'title': 'THE FILMS', 'text': f'the films cannot be read ({type(e).__name__})'}]
    try:
        films = con.execute("SELECT * FROM films WHERE state != 'removed' ORDER BY COALESCE(opened_at, asked_at) DESC, asked_at DESC LIMIT 30").fetchall()   # the project opened last first
        table = {'kind': 'table', 'title': f'THE PROJECTS · {len(films)} · OPEN one to see it at every step', 'columns': ['Project', 'Title', 'Seconds', 'State', 'Where'],
                 'rows': [{'key': f['id'], 'cells': [f['id'], f['title'], f['lengths'] and ', '.join(map(str, json.loads(f['lengths']))) or '',
                                                     (f['state'] or '').upper() + (f" · {f['why']}" if f['why'] else ''), f['downloads'] or f['final'] or ''],
                           'presses': [{'do': 'open', 'label': 'OPEN', 'cell': 0}, {'do': 'remove', 'label': 'REMOVE', 'confirm': f"Remove {f['id']}?", 'cell': 0}]} for f in films],
                 'empty': 'no film yet: add one above, then press RUN AGENT'}
        clear = {'kind': 'press', 'do': 'clear', 'label': f'CLEAR SOURCE FOLDER ({len(source_videos(conf))} video)', 'confirm': f"Delete every file in {conf['source']}?"}
        song_film = films[0] if films and films[0]['song'] else None   # the project open now (opened last), when it starts from a song
        step1 = [{'kind': 'step', 'n': 1, 'title': 'THE MUSIC', 'under': 'paste the song\'s file name, press PROCESS MUSIC: it splits the vocals, finds the beats, the sections and the words, and maps them to one of your proven sequences'},
                 {'kind': 'form', 'title': 'THE SONG', 'do': 'music', 'name': 'words', 'rows': 2, 'label': 'PROCESS MUSIC',
                  'placeholder': 'line 1: the title · tick the song above (or paste its file name on line 2)',
                  'boxes': {'title': 'THE SONGS FOUND · THE MUSIC FOLDER, THEN THE NEWEST IN DOWNLOADS · TICK ONE', 'name': 'song',
                            'rows': [{'key': f'song{i}', 'label': str(i), 'boxes': [{'value': v, 'label': v[:90] + (f"  ← {films[0]['id']} (open)" if films and films[0]['song'] == v else ''), 'checked': bool(films and films[0]['song'] == v)}]} for i, v in enumerate(found_songs(conf), 1)]}}]
        if song_film:
            step1 += music_parts(con, song_film, conf)
            step1.append({'kind': 'press', 'do': 'process', 'value': song_film['id'], 'label': f"PROCESS MUSIC AGAIN · {song_film['id']}"})
            row = con.execute('SELECT tempo FROM music WHERE film = ?', (song_film['id'],)).fetchone()
            if row and row['tempo']:   # THE FINAL SONG, ONE BUTTON (the owner 2026-10-28: "a button after this to say play final song and it has the start and end slight edit")
                bar = 4 * 60.0 / float(row['tempo'])
                at = lambda x: f'{int(x) // 60}:{x % 60:04.1f}'   # noqa: E731
                name = re.sub(r'[^A-Za-z0-9 ·._-]', '', song_film['title']).strip() or song_film['id']
                step1.append({'kind': 'listen', 'label': '▶ PLAY THE FINAL SONG', 'audio': _src(conf, f"{song_film['id']}/music", 'minute_final.wav'), 'empty': 'the final song is made by PROCESS MUSIC',
                              'download': [['⬇ DOWNLOAD SONG (MP3)', _src(conf, f"{song_film['id']}/music", 'minute_final.mp3'), f'{name} · final song.mp3'],
                                           ['WAV', _src(conf, f"{song_film['id']}/music", 'minute_final.wav'), f'{name} · final song.wav']],   # the owner 2026-10-28: "can you have a downlaod song button to download this audio clip"
                              'under': (f'instrumental fades in {at(0)}-{at(bar)} · vocals fade in {at(bar)}-{at(2 * bar)} · full song {at(2 * bar)}-{at(TOTAL - 2 * bar)} · '
                                        f'vocals fade out {at(TOTAL - 2 * bar)}-{at(TOTAL - bar)} · instrumental fades out {at(TOTAL - bar)}-{at(TOTAL)} (one bar each, {row["tempo"]:.0f} BPM)')})
        if song_film:
            step1 += posters_parts(con, song_film, conf)
            step1 += faceswap_parts(con, song_film, conf)
            step1 += skin_parts(con, song_film, conf)
            step1 += teeth_parts(con, song_film, conf)
            step1 += hair_parts(con, song_film, conf)
            step1 += clean_parts(con, song_film, conf)
            step1 += color_parts(con, song_film, conf)
            step1 += move_parts(con, song_film, conf)
            step1 += restore_parts(con, song_film, conf)
            step1 += movetime_parts(con, song_film, conf)
            step1 += lips_parts(con, song_film, conf)
            step1 += comp_parts(con, song_film, conf)
            step1 += export_parts(con, song_film, conf)   # the last step, on the very bottom
            step1 = _with_lessons(con, song_film['id'], step1)
        old = [form, clear]
        other = films[0] if films and not films[0]['song'] else None
        if other:
            old += film_parts(con, other, conf)
        if films:
            step1.insert(0, {'kind': 'press', 'do': 'save', 'value': films[0]['id'], 'label': f"SAVE {films[0]['id']} · {films[0]['title']}"})
        copies = saved_copies(conf)
        loads = {'kind': 'table', 'title': f'THE SAVED COPIES · {len(copies)} · LOAD one to work on it again', 'columns': ['Saved copy', 'Project', 'Title', 'State then'],
                 'rows': [{'key': c['key'], 'cells': [c['at'].replace('_', ' '), c['film'], c['title'], (c['state'] or '').upper()],
                           'presses': [{'do': 'load', 'label': 'LOAD', 'confirm': f"Load {c['film']} as saved {c['at']}? Its working folder is replaced by this copy.", 'cell': 0}]} for c in copies],
                 'empty': 'nothing saved yet: press SAVE on the open project'}
        parts = step1 + [table, loads, {'kind': 'note', 'title': 'THE FIRST VERSION · prompt films and plan clip, kept as they are', 'text': 'step 2 (the posters) is built next, in its own section'}] + old
        return parts
    finally:
        con.close()


# ============ THE FILM'S OWN ROWS (the owner 2026-10-28: "have a row for logo, row for music, subitles and then row to see the video with markers
# for each clip as it plays ... keep it simple"; "number the segments 1 to 8"; "each row can play its own little clip"): words and addresses only,
# drawn by the page (a cell's video, audio, image or links; the film part with its numbered timeline); its files served from this office's static folder.
def _src(conf, fid, name):
    path = os.path.join(conf['films'], fid, name) if name else ''
    return f"{conf['films_url']}/{fid}/{name}?v={int(os.path.getmtime(path))}" if path and os.path.exists(path) else ''


def _mmss(s):
    return f'{int(s) // 60}:{int(s) % 60:02d}'


def film_parts(con, f, conf):
    rows, fid = _clips(con, f['id']), f['id']
    layers = json.loads(f['layers'] or '[]')
    table = []
    for r in rows:
        state = (r['state'] or '').upper() + (f" · take {r['take']}" if r['take'] else '') + (f" · {r['why']}" if r['why'] else '')
        clip = _src(conf, fid, r['clip'])
        table.append({'key': f"{fid}:{r['n']}", 'cells': [
            str(r['n']), {'video': clip, 'poster': _src(conf, fid, f"picture_{r['n']}_take{int(r['take'] or 0)}.png"), 'text': '' if clip else 'not made yet'},
            f"{r['seconds']} s", r['words'] or '(written from his prompt)', (r['doctored_clip'] or '')[:260] + (f" · {r['grade']}" if r['grade'] else ''), r['made_by'] or '', state],
            'presses': [{'do': 'redo', 'label': 'REDO', 'text': True, 'placeholder': 'new words, or empty for a new take', 'cell': 3}]})
    credit = ''
    if f['track']:
        try:
            credit = json.load(open(os.path.join(conf['music'], f['track'][:-4] + '.json'))).get('credit', '')
        except (OSError, ValueError):
            pass
    subs = cues(rows) if rows and all(r['line'] for r in rows) else []
    table.append({'key': f'{fid}:logo', 'cells': ['LOGO', {'image': '/positive-feedback-logo.png'}, '', 'ON · top right, then the end card for the last 2.5 s' if 'logo' in layers else 'OFF', '', '', '']})
    music = _src(conf, fid, 'music.m4a')
    named = (f"the song's hook from {f['source']}, {_mmss(f['music_start'] or 0)}-{_mmss((f['music_start'] or 0) + TOTAL)}" if (f['track'] or '').startswith('film:')
             else (f['track'] or '')[:-4].replace('_', ' ') if f['track'] else ('ON' if 'music' in layers else 'OFF'))
    table.append({'key': f'{fid}:music', 'cells': ['MUSIC', {'audio': music, 'text': '' if music else 'at the cut'}, f'{TOTAL} s', named, credit, '', '']})
    srt, vtt = _src(conf, fid, 'subtitles.srt'), _src(conf, fid, 'subtitles.vtt')
    table.append({'key': f'{fid}:subtitles', 'cells': ['SUBTITLES', {'links': [['.srt', srt], ['.vtt', vtt]], 'text': '' if srt else 'at the cut'}, f'{len(subs)} lines',
                                                       ' | '.join(f'{_mmss(a)}-{_mmss(b)} {t}' for a, b, t in subs) or ('ON' if 'subtitles' in layers else 'OFF'), '', '', '']})
    segs, at = [], 0
    for r in rows:
        segs.append({'n': r['n'], 'at': at, 'end': at + r['seconds']})
        at += r['seconds']
    return [{'kind': 'table', 'title': f"{fid} · {f['title']} · THE 8 CLIPS · REDO one: only it is made again",
             'columns': ['#', 'Clip', 'Seconds', 'His words', 'Doctored', 'Made by', 'State'], 'rows': table, 'empty': 'its clips are written at its first RUN AGENT'},
            {'kind': 'film', 'title': f"{fid} · THE FILM · 60 s · click a number to jump to its clip", 'src': _src(conf, fid, 'final.mp4'), 'segments': segs,
             'under': f"clips {', '.join(str(r['seconds']) for r in rows)} · {f['downloads'] or ''}", 'empty': 'the film is cut when all 8 clips are made'}]

# ============ PART 2 · THE POSTERS · INSPIRATION (the owner 2026-10-28: "lets start with clips form our original and call it inspiration and make it a
# layer this is the composition and concept but not characters and not color"; "you pick 8 posters and the slots need to say insert"; "TYPE I,
# TYPE II, TYPE III (insert) ... they dont follow each other ... it can basically be auto calculated ... recommend the options if more than 1";
# "the user can pick ... these are inspiration so there is more flexiblity"; "if it lists the videos and images then you put in the clip second
# it can make the poster"; "it needs to be tagged with a type i ii or iii"). The sources are the files in the inspiration folder (the plan clip
# folder), each a short code (V1 a video, P1 a picture); a slot's line is "V1 1:41 II" (the source, its second, its type tag) or "P2 III".
def inspiration_sources(conf):
    """the videos (V1, V2...) and pictures (P1, P2...) in the inspiration folder, by name -> [{'code', 'name', 'path', 'kind'}]"""
    try:
        names = sorted(f for f in os.listdir(conf['source']) if os.path.isfile(os.path.join(conf['source'], f)))
    except OSError:
        names = []
    vids = [f for f in names if VIDEOS.search(f)]
    pics = [f for f in names if PICTURES.search(f)]
    return ([{'code': f'V{i}', 'name': f, 'path': os.path.join(conf['source'], f), 'kind': 'video'} for i, f in enumerate(vids, 1)]
            + [{'code': f'P{i}', 'name': f, 'path': os.path.join(conf['source'], f), 'kind': 'picture'} for i, f in enumerate(pics, 1)])


def find_file(name, conf):
    """a picture or video by its exact file name, in the CMO's own folders: the inspiration folder, NB Style, the transitions, the GTA 6 color,
    the references (any depth) -> its path or ''"""
    name = os.path.basename(str(name or '').strip().strip('"').strip("'"))
    if not name or not (PICTURES.search(name) or VIDEOS.search(name)):
        return ''
    if os.path.isfile(os.path.join(conf['downloads'], name)):   # Downloads, its top only (the owner's films land there)
        return os.path.join(conf['downloads'], name)
    for top in (conf['source'], os.path.join(SCRATCH, 'nb_style'), os.path.join(SCRATCH, 'transitions'), os.path.join(SCRATCH, 'gta6_color'), conf['references'], conf['films']):
        for root, _dirs, files in os.walk(top):
            if name in files:
                return os.path.join(root, name)
    return ''


def type_options(slots):
    """EVERY WAY TO TYPE THE SLOTS: the inserts fixed by the sequence (III), the rest I or II, no two neighbours the same; best first: opens on I,
    ends on I, I and II balanced -> [[type of slot 1..8], ...]"""
    import itertools
    fixed = {x['n']: 'III' for x in slots if x['insert']}
    free = [x['n'] for x in slots if x['n'] not in fixed]
    out = []
    for combo in itertools.product(('I', 'II'), repeat=len(free)):
        t = {**fixed, **dict(zip(free, combo))}
        seq = [t[x['n']] for x in slots]
        if all(a != b for a, b in zip(seq, seq[1:])):
            out.append(seq)
    score = lambda q: (q[0] == 'I') * 4 + (q[-1] == 'I') * 2 - abs(q.count('I') - q.count('II'))   # noqa: E731
    return sorted(out, key=score, reverse=True)


def _seconds(text):
    """'1:41' or '101' or '1:41.5' -> seconds, or None"""
    m = re.fullmatch(r'(?:(\d+):)?(\d+(?:\.\d+)?)', str(text or '').strip())
    return (int(m.group(1) or 0) * 60 + float(m.group(2))) if m else None


def set_inspiration(con, conf, fid, n, line):
    """ONE SLOT'S INSPIRATION from his line ("V1 1:41 II", "P2", "V2 12 III"): the frame grabbed (a picture used as it is) into the project folder
    -> the line said"""
    words = str(line or '').split()
    end = next((i for i, w in enumerate(words) if PICTURES.search(w) or VIDEOS.search(w)), -1)   # a file name with spaces in it ("Tip Toe Rumpel · one min sm video · F-0003.mp4 0:02"): its words up to its extension
    if end > 0:
        words = [' '.join(words[:end + 1])] + words[end + 1:]
    if not words:
        con.execute('DELETE FROM inspiration WHERE film = ? AND n = ?', (fid, n))
        con.commit()
        return f'INSPIRATION · {fid} slot {n} cleared'
    src = {x['code']: x for x in inspiration_sources(conf)}
    code = words[0].upper()
    named = find_file(words[0], conf)   # A FILE BY ITS NAME (the owner 2026-10-28: "2026-03-15_18-00-36_UTC_4.jpg insert"): any of the CMO's folders
    if named:
        code = os.path.basename(named)
        src[code] = {'code': code, 'name': code, 'path': named, 'kind': 'video' if VIDEOS.search(named) else 'picture'}
    if code not in src:
        return f"INSPIRATION refused · {code} is not a source (the codes: {', '.join(src) or 'none: put videos or pictures in ' + conf['source']})"
    tag = next((w.upper() for w in words[1:] if w.upper() in TYPES), '')
    second = next((_seconds(w) for w in words[1:] if _seconds(w) is not None), None)
    s_ = src[code]
    home = os.path.join(conf['films'], fid, 'inspiration')
    os.makedirs(home, exist_ok=True)
    frame = os.path.join(home, f'slot_{n}.jpg')
    if s_['kind'] == 'video':
        length = _seconds_of(s_['path'])
        second = max(0.0, min(second if second is not None else length / 2, max(0.0, length - 0.05)))
        _ff(['-ss', f'{second:.3f}', '-i', s_['path'], '-frames:v', '1', '-vf', 'scale=1280:-2', '-q:v', '3', frame], f'slot {n} inspiration frame')
    else:
        second = None
        _ff(['-i', s_['path'], '-frames:v', '1', '-vf', 'scale=1280:-2', '-q:v', '3', frame], f'slot {n} inspiration picture')
    con.execute('INSERT OR REPLACE INTO inspiration (film, n, line, code, source, second, frame, tag, made_at) VALUES (?,?,?,?,?,?,?,?,?)',
                (fid, n, ' '.join(words), code, s_['name'], second, os.path.basename(frame), tag, _now()))
    con.commit()
    return f"INSPIRATION · {fid} slot {n} · {code} {s_['name']}" + (f' at {_mmss(second)}' if second is not None else '') + (f' · TYPE {tag}' if tag else '')


def find_inspiration(con, conf, fid):
    """FIND INSPIRATION: first guesses only (he picks): the first video's cuts found, one different scene a slot, spread through the video, its
    middle frame; tagged with the slot's planned type -> the line said"""
    vids = [x for x in inspiration_sources(conf) if x['kind'] == 'video']
    row = con.execute('SELECT map FROM music WHERE film = ?', (fid,)).fetchone()
    if not vids or not row:
        return 'FIND INSPIRATION refused · ' + ('no video in ' + conf['source'] if not vids else 'its music is not ready (step 1)')
    v = vids[0]
    p = subprocess.run(['ffmpeg', '-v', 'info', '-i', v['path'], '-vf', "select='gt(scene,0.3)',showinfo", '-an', '-f', 'null', '-'], capture_output=True, text=True)
    cuts = [0.0] + [float(t) for t in re.findall(r'pts_time:([0-9.]+)', p.stderr)]
    length = _seconds_of(v['path'])
    scenes = [(a, b) for a, b in zip(cuts, cuts[1:] + [length]) if b - a >= 0.6] or [(0.0, length)]
    slots = json.loads(row['map'])['slots']
    types = _types(con, fid, slots)
    picked = [scenes[min(len(scenes) - 1, int((i + 0.5) * len(scenes) / len(slots)))] for i in range(len(slots))]
    for x, (a, b), t in zip(slots, picked, types):
        set_inspiration(con, conf, fid, x['n'], f"{v['code']} {_mmss((a + b) / 2)}.{int(((a + b) / 2 % 1) * 10)}")   # a first guess carries no type tag: only his typed tag overrides the types
    return f"FIND INSPIRATION · {fid} · {len(scenes)} scenes in {v['name']} · a first guess in every slot: type a slot's line to change it"


def _types(con, fid, slots):
    """the film's slot types: his pick of the options (films.types: an option's number), else the best option"""
    opts = type_options(slots)
    f = _film(con, fid)
    k = int(f['types']) if f and str(f['types'] or '').isdigit() and int(f['types']) < len(opts) else 0
    return opts[k] if opts else ['I'] * len(slots)


# ============ PART 2 · MAKE POSTERS (the owner 2026-10-28: "go for it"): each slot's inspiration frame (its composition only) made into a lifelike
# 16:9 poster: the cast's real look (Rumpel: his own pictures; tattoos, coloured hair and a silver and gold grill, his notes 3, 11, 12), the NB
# Style edge and the GTA VI pink-and-teal grade (his notes 22); TYPE III an object alone. The lab's picture door takes one picture: the frame with
# the character's picture set in at its top right (the inserts carry none). Claude writes each slot's prompt reading its frame; no logos, no text.
CAST = {'rumpel': ['rumpel_4_fullbody.png', 'rumpel_3_closeup.png', 'rumpel_2.png']}
CAST_ASK = """Read every picture listed (Read each one): {pics}
They show RUMPEL, a viral AI-made character (not a real person). Write ONE fixed description of him for a LIFELIKE, photoreal music video (never a
cartoon): face, head, curly hair, height and build, the velvet tailcoat and bow tie, cropped trousers, curled pointed shoes. Add, as the owner asked:
visible tattoos on his hands and neck, his hair dyed a bold colour, a silver and gold grill on his teeth. Then the girls who appear with him: a
fixed look for three of them (each a different bright hair colour, white fur and ice-queen styling). It is pasted word for word into every poster.
Answer with JSON only: {{"look": "..."}}"""
POSTER_ASK = """You write the picture prompt for ONE poster of a 60 second rap music video (16:9, lifelike, photoreal: never a cartoon, never a drawing).
Read its inspiration frame first with Read: {frame}
The frame gives ONLY the composition and the idea: the framing, the camera angle, where things sit. Not the people, not the colours, not the place.
THE SLOT: {n} of 8, {seconds} s, TYPE {type} ({meaning}). Its words in the song: "{words}".
THE CAST (paste the parts you use word for word): {look}
THE LOOK OF THE FILM: the NB Style edge (gritty, flash-lit, grainy, ghetto-luxury details, an artistic odd angle) in the GTA VI Vice City grade:
pink and teal, coral and turquoise, hot-pink and cyan neon against teal shadow, sun-bleached pastels, heightened photorealism.
{inset}
Rules: 16:9 full frame; no logos, no brand names, no words or letters anywhere; {type_rule}
Answer with JSON only: {{"frame1": "<what the inspiration frame shows>", "prompt": "<the picture prompt, 60 to 120 words>"}}"""
MEANING = {'I': 'the group: everyone in the full scene', 'II': 'one person alone', 'III': 'an insert: an object or a detail, no face'}
TYPE_RULE = {'I': 'Rumpel and the three girls together, all lifelike.', 'II': 'Rumpel alone (or one of the girls alone if the frame shows a woman), lifelike.',
             'III': 'an object or a detail only (hands, jewellery, a grill, a cup, a chain): no face, no full person.'}


def make_posters(con, conf, film, step=lambda s: None):
    """PART 2's posters for one film -> (ok, the line)"""
    fid = film['id']
    row = con.execute('SELECT map FROM music WHERE film = ?', (fid,)).fetchone()
    insp = {r['n']: r for r in con.execute('SELECT * FROM inspiration WHERE film = ?', (fid,))}
    if not row or len(insp) < CLIPS:
        return False, f'MAKE POSTERS waits: every slot needs its inspiration ({len(insp)} of {CLIPS} set)'
    slots = json.loads(row['map'])['slots']
    types = _types(con, fid, slots)
    tag_of = lambda x: insp[x['n']]['tag'] or types[x['n'] - 1]   # noqa: E731
    pics = [os.path.join(conf['references'], f) for f in CAST['rumpel'] if os.path.exists(os.path.join(conf['references'], f))]
    if not film['cast_look']:
        step(f'{fid}: the cast look')
        code, said = _claude(CAST_ASK.format(pics=', '.join(pics)), conf)
        try:
            look = str(_json_of(said).get('look') or '')
        except ValueError:
            look = ''
        if not look:
            return False, f'the cast look was not written (Claude exit {code})'
        _set_film(con, fid, cast_look=look)
        film = _film(con, fid)
    home = os.path.join(conf['films'], fid, 'posters')
    os.makedirs(home, exist_ok=True)
    who = pics[0] if pics else ''
    prompts, errors = {}, {}

    def write_prompt(x):
        t = tag_of(x)
        frame = os.path.join(conf['films'], fid, 'inspiration', insp[x['n']]['frame'])
        try:
            code, said = _claude(POSTER_ASK.format(frame=frame, n=x['n'], seconds=x['seconds'], type=t, meaning=MEANING[t], words=x['words'][:300] or '(no words)',
                                                   look=film['cast_look'], type_rule=TYPE_RULE[t],
                                                   inset='The picture model is given the frame with Rumpel\'s own picture set in at its top right: say "Rumpel, exactly as the man in the small inset picture at the top right" and end with "Remove the inset picture completely; the output is the scene alone, full frame".' if t != 'III' else 'The picture model is given the frame alone (no inset).'), conf)
            prompts[x['n']] = str(_json_of(said).get('prompt') or '')
        except Exception as e:   # noqa: BLE001
            errors[x['n']] = f'no prompt ({str(e)[:100]})'
    step(f'{fid}: 8 poster prompts')
    threads = [threading.Thread(target=write_prompt, args=(x,), daemon=True) for x in slots]
    for t_ in threads:
        t_.start()
    for t_ in threads:
        t_.join()
    if not lab_up(conf):
        return False, f"the timeline lab (8822) did not start · {HAND}cd {conf['lab_dir']} && ./start.sh, then MAKE POSTERS again"
    made = 0
    for x in slots:
        n = x['n']
        if n not in prompts or not prompts[n]:
            con.execute('INSERT OR REPLACE INTO posters (film, n, state, why, made_at) VALUES (?,?,?,?,?)', (fid, n, 'red', errors.get(n, 'no prompt'), _now()))
            con.commit()
            continue
        step(f'{fid}: poster {n} of {len(slots)}')
        frame = os.path.join(conf['films'], fid, 'inspiration', insp[n]['frame'])
        board = os.path.join(home, f'board_{n}.png')   # the one picture the lab takes: the frame filling 16:9, the character set in at the top right
        if tag_of(x) != 'III' and who:
            _ff(['-i', frame, '-i', who, '-filter_complex', f'[0:v]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H}[f];[1:v]scale=-2:{H // 2 - 24},pad=iw+12:ih+12:6:6:white[c];[f][c]overlay=W-w-16:16',
                 '-frames:v', '1', board], f'poster {n} board')
        else:
            _ff(['-i', frame, '-vf', f'scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H}', '-frames:v', '1', board], f'poster {n} board')
        take = int((con.execute('SELECT take FROM posters WHERE film = ? AND n = ?', (fid, n)).fetchone() or [0])[0] or 0)
        try:
            address = _into_lab(conf, board, f'cmo_{fid}_poster_{n}_{take}.png')
            picture = make_picture(conf, {'look': ''}, {'doctored_frame': prompts[n], 'take': take}, address)
            src = os.path.join(conf['lab_dir'], picture.lstrip('/'))
            own = f'poster_{n}_take{take}.png'
            shutil.copyfile(src, os.path.join(home, own))
            con.execute('INSERT OR REPLACE INTO posters (film, n, prompt, picture, file, take, state, why, made_at) VALUES (?,?,?,?,?,?,?,?,?)',
                        (fid, n, prompts[n], picture, own, take, 'done', '', _now()))
            _keep(con, conf, fid, 'posters', n, f'posters/{own}', 'posters', also=(('inspiration', n),), extra={'made_by': 'Nano Banana 2 (the lab)'})
            made += 1
        except Exception as e:   # noqa: BLE001
            con.execute('INSERT OR REPLACE INTO posters (film, n, prompt, take, state, why, made_at) VALUES (?,?,?,?,?,?,?)', (fid, n, prompts[n], take, 'red', str(e)[:200], _now()))
        con.commit()
    _set_film(con, fid, posters_state='done' if made == len(slots) else 'red', state='music ready')
    return made == len(slots), f'{fid} · MAKE POSTERS · {made} of {len(slots)} posters made' + ('' if made == len(slots) else ' · the red ones say why in their row')


# ============ PART 3 · FACE SWAP (the owner 2026-10-28: "swap the guy with our rumpel face ... right now each clip looks different and not like him
# ... keep the vibe and keep it all but face swap to the real face ... keep the original and have the face swap next to it ... a brand new process
# for face swap"): the Exxact box's own face-swap worker (faceswap/worker.py, port 5036: InsightFace inswapper + the box's GFPGAN / Real-ESRGAN
# restore), started if it is down and never changed; his real face (a reference picture) onto Rumpel's face in every poster; in a group shot Claude
# reads the poster and the faces found and names Rumpel's (never a girl's); a slot's own line ("face 2", "none") overrides.
BOX = 'exx@192.168.12.88'
BOX_DIR = 'frost/virtual_workspace/cmo_faceswap'   # its own folder on the box, beside amLLM, never inside it
SWAP_URL = 'http://192.168.12.88:5036'
DONOR = 'rumpel_5_head_full_hair.png'
DONORS = ['rumpel_5_head_full_hair.png', 'rumpel_8_front_14s.png', 'rumpel_9_side_2s.png']   # the sharp side profile at 0:02.25 (the owner 2026-10-28: "around 2 seconds there is a better one")   # the blurred three-quarter out (the owner 2026-10-28: "7 we had a better side pic")   # every one with his whole head and hair (the owner 2026-10-28: "it needs the hair": the close-up cut it off)   # HIS FACES FROM EVERY ANGLE (the owner 2026-10-28: "it should have multiple refernces so it can use what matches the clip best")   # his whole head and hair, front-on (the owner 2026-10-28: "your reference image cuts off the hair")
HEAD_ASK = ("Replace {who} whole head (his face, his head shape, his hair, his ears) with EXACTLY the man shown in the reference photos at the top right "
            "(front and side): his large rounded forehead, his small childlike face, his wide-set eyes, his thin lips, his pale skin, and HIS HAIR: thin, wispy, "
            "light strawberry-blond, receding at the temples, NOT curly. He must be instantly recognisable as that man. Keep everything else exactly: his pose, "
            "his hands and tattoos, his clothes, anything he holds, the grill on his teeth if he shows one, every other person, the background, the light and "
            "the colours. Remove the reference photos completely; the output is the scene alone, full frame, photoreal.")
PART_FACE = ("An extreme close-up of part of a face. Make it clearly A MAN'S mouth and chin: the man in the small inset picture at the top right, his skin "
             "tone and texture, his lips, his jaw, clean-shaven (no beard, no stubble). Keep everything else exactly: the grill, any tattoo, the fingers and hands, "
             "the framing, the lighting and the colours. Remove the inset picture completely; the output is the scene alone, full frame.")
PICK_ASK = """Read this poster with Read: {img}
The faces found in it, numbered (left, top, width, height as fractions of the picture): {faces}
Which one is RUMPEL: the small man in the black velvet tuxedo (never a woman)? If none of them is his face (no man there, or only lips, hands or an object),
answer 0. Answer with JSON only: {{"face": <its number from 1, or 0>, "why": "<a few words>"}}"""


def _box(args, timeout=120, data=None):
    return subprocess.run(['ssh', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=8', BOX] + args, capture_output=True, text=True, timeout=timeout, input=data)


def _swap_ask(path, body, timeout=600):
    req = urllib.request.Request(SWAP_URL + path, data=json.dumps(body).encode(), method='POST', headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode())


def swap_up():
    """the box's face-swap worker, started (detached, from its own folder) when it does not answer -> True when it answers"""
    for k in range(40):
        try:
            with urllib.request.urlopen(SWAP_URL + '/health', timeout=5):
                return True
        except Exception:   # noqa: BLE001
            if k == 0:
                _box(['cd frost/virtual_workspace/faceswap && (nohup venv/bin/python worker.py >> logs/worker.log 2>&1 < /dev/null &)'], 60)
            time.sleep(3)
    return False


def _swap_row(con, fid, n, **vals):
    """a slot's face-swap row updated, never replaced (his markers and line stay)"""
    con.execute('INSERT OR IGNORE INTO faceswap (film, n, state, made_at) VALUES (?,?,?,?)', (fid, n, 'asked', _now()))
    vals['made_at'] = _now()
    con.execute(f"UPDATE faceswap SET {', '.join(k + ' = ?' for k in vals)} WHERE film = ? AND n = ?", (*vals.values(), fid, n))
    con.commit()


def donors_of(film):
    """the film's face references: its own list (films.swap_donor, JSON), else his five"""
    try:
        got = json.loads(film['swap_donor'] or '')
        if isinstance(got, list) and got:
            return [str(x) for x in got]
    except ValueError:
        if film['swap_donor']:
            return [film['swap_donor']]
    return list(DONORS)


def yaw_of(face):
    """which way a face is turned, from its five points (eyes, nose, mouth): the nose's offset from between the eyes, in eye widths; 0 front, - his left, + his right"""
    k = face.get('kps') or []
    if len(k) < 3:
        return None
    ex = (k[0][0] + k[1][0]) / 2
    w = abs(k[1][0] - k[0][0]) or 1e-6
    return round((k[2][0] - ex) / w, 3)


def angle_word(y):
    return 'no face found (hair pass only)' if y is None else 'front' if abs(y) < 0.12 else f"turned {'right' if y > 0 else 'left'} {min(90, int(abs(y) * 120))}°"


def swap_faces(con, conf, film, step=lambda s: None):
    """PART 3 for one film: every poster's Rumpel given his real face -> (ok, the line)"""
    fid = film['id']
    posts = {r['n']: r for r in con.execute("SELECT * FROM posters WHERE film = ? AND file IS NOT NULL AND file != ''", (fid,))}
    if not posts:
        return False, 'FACE SWAP waits: make the posters first (step 2)'
    donors = [d for d in (find_file(x, conf) for x in donors_of(film)) if d]
    if not donors:
        return False, "none of the face pictures is in the CMO's folders"
    if not swap_up():
        return False, 'the box\'s face-swap worker (port 5036) did not answer · YOUR 3 MIN: ssh exx@192.168.12.88, cd frost/virtual_workspace/faceswap, nohup venv/bin/python worker.py &'
    home = os.path.join(conf['films'], fid, 'faceswap')
    os.makedirs(home, exist_ok=True)
    _box([f'mkdir -p {BOX_DIR}/in {BOX_DIR}/out'], 30)
    lines = {r['n']: r for r in con.execute('SELECT * FROM faceswap WHERE film = ?', (fid,))}
    todo = [n for n in sorted(posts) if not (n in lines and lines[n]['state'] == 'done' and lines[n]['file'] and lines[n]['donor'] and os.path.exists(os.path.join(home, f'head_{n}.png')))]   # a swap made before the head rebuild (C) is made again   # a swap made before the references (no donor kept) is made again
    names = [os.path.join(conf['films'], fid, 'posters', posts[n]['file']) for n in todo] + donors
    p = subprocess.run(['scp', '-q', '-o', 'BatchMode=yes'] + names + [f'{BOX}:{BOX_DIR}/in/'], capture_output=True, text=True, timeout=600)
    if p.returncode != 0:
        return False, f'the posters could not be sent to the box ({p.stderr.strip()[:120]})'
    remote = lambda f: f'/home/exx/{BOX_DIR}/in/{os.path.basename(f)}'   # noqa: E731
    angles = {}
    for d in donors:   # each reference's angle, once
        try:
            fs = _swap_ask('/landmarks', {'image': remote(d)}, 300).get('faces') or []
            angles[d] = yaw_of(max(fs, key=lambda f_: f_['bbox'][2] * f_['bbox'][3])) if fs else None
        except Exception:   # noqa: BLE001
            angles[d] = None
    usable = [d for d in donors if angles.get(d) is not None]
    if not usable:
        return False, 'no face was found in any of the face pictures'
    front = find_file('rumpel_5_head_full_hair.png', conf) or usable[0]
    side = find_file('rumpel_9_side_2s.png', conf) or front
    refboard = os.path.join(home, 'refboard.png')   # his front and his side, big, for the head rebuild
    _ff(['-i', front, '-i', side, '-filter_complex', '[0]scale=-2:640[a];[1]scale=-2:640[b];[a][b]hstack,pad=iw+16:ih+16:8:8:white', '-frames:v', '1', refboard], 'the reference board')
    picks = {}

    def pick(n):
        line = ((lines.get(n) or {}) and lines[n]['line'] or '').strip().lower()
        try:
            faces = _swap_ask('/landmarks', {'image': remote(posts[n]['file'])}, 300).get('faces') or []
        except Exception as e:   # noqa: BLE001
            picks[n] = (0, faces if False else [], f'no faces read ({str(e)[:80]})')
            return
        if line in ('none', 'skip', 'no'):
            picks[n] = (0, faces, 'none, by your line')
            return
        row_ = lines.get(n)
        if row_ is not None and row_['face_x'] is not None and faces:   # HIS FACE MARKER (the owner 2026-10-28: "a tool to tag the face of the guy and it puts a marker on it"): the face under it, else the nearest
            fx, fy = float(row_['face_x']), float(row_['face_y'])
            inside = [i for i, f_ in enumerate(faces, 1) if f_['bbox'][0] <= fx <= f_['bbox'][0] + f_['bbox'][2] and f_['bbox'][1] <= fy <= f_['bbox'][1] + f_['bbox'][3]]
            near = min(range(1, len(faces) + 1), key=lambda i: (faces[i - 1]['bbox'][0] + faces[i - 1]['bbox'][2] / 2 - fx) ** 2 + (faces[i - 1]['bbox'][1] + faces[i - 1]['bbox'][3] / 2 - fy) ** 2)
            picks[n] = ((inside or [near])[0], faces, 'by your swap marker')
            return
        m = re.fullmatch(r'(?:face\s*)?(\d+)', line)
        if m:
            picks[n] = (int(m.group(1)), faces, 'by your line')
            return
        if not faces:
            picks[n] = (0, faces, 'no face in it')
            return
        listed = '; '.join(f"{i}: left {f_['bbox'][0]:.2f}, top {f_['bbox'][1]:.2f}, width {f_['bbox'][2]:.2f}, height {f_['bbox'][3]:.2f}" for i, f_ in enumerate(faces, 1))
        try:
            code, said = _claude(PICK_ASK.format(img=os.path.join(conf['films'], fid, 'posters', posts[n]['file']), faces=listed), conf)
            got = _json_of(said)
            picks[n] = (int(got.get('face') or 0), faces, str(got.get('why') or '')[:120])
        except Exception as e:   # noqa: BLE001
            picks[n] = (0, faces, f'Claude did not pick ({str(e)[:80]})')
    step(f'{fid}: finding Rumpel in {len(todo)} posters')
    threads = [threading.Thread(target=pick, args=(n,), daemon=True) for n in todo]
    for t_ in threads:
        t_.start()
    for t_ in threads:
        t_.join()
    made = 0
    for n in todo:
        k, faces, why = picks.get(n, (0, [], 'not read'))
        line = (lines[n]['line'] if n in lines else '') or ''
        row_ = lines.get(n)
        if (not k or k > len(faces)) and row_ is not None and row_['face_x'] is not None:   # HIS MARKER ON A FACE THE SWAP CANNOT READ (a mouth, a cheek: the owner 2026-10-28: "you need the first insert too"): Nano Banana makes it his
            step(f'{fid}: poster {n}, part of a face, by Nano Banana')
            try:
                ref = find_file('rumpel_5_head_full_hair.png', conf) or donors[0]
                poster = os.path.join(conf['films'], fid, 'posters', posts[n]['file'])
                board = os.path.join(home, f'board_{n}.png')
                _ff(['-i', poster, '-i', ref, '-filter_complex', f'[0:v]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H}[f];[1:v]scale=-2:{H // 2 - 24},pad=iw+12:ih+12:6:6:white[c];[f][c]overlay=W-w-16:16',
                     '-frames:v', '1', board], f'slot {n} board')
                if not lab_up(conf):
                    raise RuntimeError('the timeline lab (8822) did not start')
                take = int(time.time())
                picture = make_picture(conf, {'look': ''}, {'doctored_frame': PART_FACE, 'take': take % 100000}, _into_lab(conf, board, f'cmo_{fid}_swap_{n}_{take}.png'))
                own = f'swap_{n}.png'
                shutil.copyfile(os.path.join(conf['lab_dir'], picture.lstrip('/')), os.path.join(home, own))
                _swap_row(con, fid, n, face=0, file=own, state='done', donor=os.path.basename(ref), why='part of a face: made his by Nano Banana, from your marker')
                _keep(con, conf, fid, 'faceswap', n, f'faceswap/{own}', 'faceswap', also=(('posters', n),), extra={'how': 'part of a face, Nano Banana', 'ref': os.path.basename(ref)})
                made += 1
            except Exception as e:   # noqa: BLE001
                _swap_row(con, fid, n, face=0, file='', state='red', why=f'part of a face: {str(e)[:160]}')
            continue
        if not k or k > len(faces):
            _swap_row(con, fid, n, face=0, file='', state='skipped', why=why)
            continue
        step(f'{fid}: swapping poster {n}')
        try:
            ty = yaw_of(faces[k - 1])
            forced = next((find_file(w, conf) for w in line.split() if PICTURES.search(w) and find_file(w, conf)), '')   # his line may name the reference ("rumpel_6_side_profile.png")
            if forced and forced not in angles:
                subprocess.run(['scp', '-q', '-o', 'BatchMode=yes', forced, f'{BOX}:{BOX_DIR}/in/'], capture_output=True, timeout=300)
                angles[forced] = 0.0
            donor = forced or min(usable, key=lambda d: abs(angles[d] - (ty or 0.0)))   # else the reference turned most like the poster's face
            # C (the owner 2026-10-28: "C looks the best"): 1. Nano Banana rebuilds his head from the big front + side board, 2. the face swap, no smoothing, locks his face
            bx = faces[k - 1]['bbox']
            cx, cy = bx[0] + bx[2] / 2, bx[1] + bx[3] / 2
            who = "the man's" if len(faces) == 1 else f"the man's ({'left' if cx < 0.38 else 'right' if cx > 0.62 else 'centre'} of the picture, {'top' if cy < 0.38 else 'bottom' if cy > 0.62 else 'middle'}, the one in the black tuxedo)"
            poster = os.path.join(conf['films'], fid, 'posters', posts[n]['file'])
            step(f'{fid}: poster {n}, his head by Nano Banana')
            board = os.path.join(home, f'head_board_{n}.png')
            _ff(['-i', poster, '-i', refboard, '-filter_complex', f'[0:v]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H}[f];[1:v]scale=-2:400[c];[f][c]overlay=W-w-12:12',
                 '-frames:v', '1', board], f'slot {n} head board')
            if not lab_up(conf):
                raise RuntimeError('the timeline lab (8822) did not start')
            stamp_ = int(time.time())
            picture = make_picture(conf, {'look': ''}, {'doctored_frame': HEAD_ASK.format(who=who), 'take': stamp_ % 100000}, _into_lab(conf, board, f'cmo_{fid}_head_{n}_{stamp_}.png'))
            head = os.path.join(home, f'head_{n}.png')
            shutil.copyfile(os.path.join(conf['lab_dir'], picture.lstrip('/')), head)
            step(f'{fid}: poster {n}, his face locked')
            subprocess.run(['scp', '-q', '-o', 'BatchMode=yes', head, f'{BOX}:{BOX_DIR}/in/'], capture_output=True, timeout=300)
            hfaces = _swap_ask('/landmarks', {'image': remote(head)}, 300).get('faces') or []
            target = min(hfaces, key=lambda f_: (f_['bbox'][0] + f_['bbox'][2] / 2 - cx) ** 2 + (f_['bbox'][1] + f_['bbox'][3] / 2 - cy) ** 2)['bbox'] if hfaces else None
            got = _swap_ask('/generate', {'source_image': remote(donor), 'target_image': remote(head), 'target_box': target, 'enhance': 'natural'}) if target else {'file': ''}
            own = f'swap_{n}.png'
            if got.get('file'):
                q = subprocess.run(['scp', '-q', '-o', 'BatchMode=yes', f"{BOX}:{got['file']}", os.path.join(home, own)], capture_output=True, text=True, timeout=300)
                if q.returncode != 0:
                    raise RuntimeError(q.stderr.strip()[:120] or 'not fetched')
            else:
                shutil.copyfile(head, os.path.join(home, own))   # no face to lock after the rebuild: the rebuilt head as it is
            _swap_row(con, fid, n, face=k, file=own, state='done', donor=os.path.basename(donor),
                      why=f'face {k} of {len(faces)} ({angle_word(ty)}) · {why} · head rebuilt from his front and side, face locked with {os.path.basename(donor)}')
            _keep(con, conf, fid, 'faceswap', n, f'faceswap/{own}', 'faceswap', also=(('posters', n),), extra={'how': 'head rebuilt, face locked', 'face': k, 'donor': os.path.basename(donor)})
            made += 1
        except Exception as e:   # noqa: BLE001
            _swap_row(con, fid, n, face=k, file='', state='red', why=str(e)[:200])
    _set_film(con, fid, swap_state='done', state='music ready')
    _write(os.path.join(home, 'angles.json'), {os.path.basename(d): angles.get(d) for d in donors})   # each reference's angle, for the page
    done = con.execute("SELECT count(*) FROM faceswap WHERE film = ? AND state = 'done'", (fid,)).fetchone()[0]
    return True, f'{fid} · FACE SWAP · {done} posters with his face · {len(todo) - made} skipped or red this run (their rows say why)'


# ============ PART 4 · SKIN, THE GOLD ONE, THE LAB'S WAY (the owner 2026-10-29: "the dot we already have identifies the person we are correcting its the same
# as the swap / and we cut out that person and then the correction is on the full image / and we do not worry about the girls or anyone else in the scene";
# "then it gets applied to the full image as a filter and once done and happy we have a step to bake it"; "show all the steps together in a table").
# The steps, each a column: 1 THE DOT (his face, found by the box, or his click) 2 CUT OUT (SAM 2 from the dot, laid on the lab's green, as the lab cuts a
# person) 3 COSMOS (the lab's amLLM Skin, NVIDIA Cosmos-Transfer 2.5, golden hour, free, its own check ON, painting HIM alone) 4 THE FILTER (how far his skin
# moved, applied over the FULL picture at OPACITY and SATURATION, live: seconds) 5 BAKE (the filtered picture made final for the next step).
COSMOS = '/home/exx/frost/virtual_workspace/amLLM/cosmos_transfer'
LOOK_DIR = 'frost/virtual_workspace/cmo_look'   # the CMO's own folder on the box, beside amLLM, never inside it
SAM_PY = '/home/exx/frost/virtual_workspace/wan22i2v/venv/bin/python'   # a Python with the box's CUDA torch, borrowed read only; SAM 2's program is in cmo_look/pylib
SKIN_PY = '/home/exx/frost/virtual_workspace/avatarskin/venv/bin/python'
COSMOS_WORDS = ('Real documentary film footage of a person standing outdoors at golden hour, in warm low sun, looking into the camera and speaking. Real photographic '
                'detail: natural skin with pores, real hair strands, warm low golden sun on the skin and shoulders, matching the light of the place behind, soft natural '
                'shadows. Filmed on a cinema camera with a 50mm lens.')   # the lab's own words for golden hour (COSMOS_LIGHT 1)
COSMOS_ROOM = 50000   # MiB a Cosmos run needs free on its card
SKIN_REF = 'skin_reference_aksel.png'   # THE SKIN REFERENCE WE ALWAYS USE (the owner 2026-10-29: "a screenshot of aksel from the movie i work alone"), face and neck only
SKIN_GOLD = {'opacity': 0.1, 'saturation': 0.9, 'hold': 0, 'lightness': 0, 'whites': 0, 'blacks': 0}   # THE LAB'S OWN DEFAULT (timeline.js COS_OPACITY 0.1, COS_SAT 0.9, COS_HOLD 0, golden hour)
CUT_PROGRAM = """# THE PERSON UNDER THE DOT, as the timeline lab cuts a person (SAM 2 from the dot, then laid on the lab's green): SAM 2's own weights on the box
# (wan22animate's process_checkpoint), its program in cmo_look/pylib. use: cut_sam.py <picture> <x> <y> <cutout.png> <mask.png>  (x, y as fractions)
import os, sys
import numpy as np, torch
from PIL import Image, ImageFilter
from sam2.build_sam import build_sam2
from sam2.sam2_image_predictor import SAM2ImagePredictor
CK = os.path.expanduser('~/frost/virtual_workspace/wan22animate/models/Wan2.2-Animate-14B/process_checkpoint/sam2/sam2_hiera_large.pt')
GREEN = (0x00, 0xB1, 0x40)   # the lab's green
img = np.asarray(Image.open(sys.argv[1]).convert('RGB')); H, W = img.shape[:2]
x, y = float(sys.argv[2]) * W, float(sys.argv[3]) * H
pred = SAM2ImagePredictor(build_sam2('configs/sam2/sam2_hiera_l.yaml', CK, device='cuda'))
with torch.inference_mode(), torch.autocast('cuda', dtype=torch.bfloat16):
    pred.set_image(img)
    masks, scores, _ = pred.predict(point_coords=np.array([[x, y]]), point_labels=np.array([1]), multimask_output=True)
m = masks[int(np.argsort([mk.sum() for mk in masks])[-1])] if False else masks[int(np.argmax(scores))]   # the mask SAM is surest of
# the dot on a face gives the face: grow to the whole person by asking again with the face's bottom and a point below it
ys, xs = np.nonzero(m)
if len(ys):
    pts = np.array([[x, y], [xs.mean(), ys.max() + 0.08 * H], [xs.mean(), min(H - 1, ys.max() + 0.25 * H)]])
    with torch.inference_mode(), torch.autocast('cuda', dtype=torch.bfloat16):
        masks, scores, _ = pred.predict(point_coords=pts, point_labels=np.ones(len(pts)), multimask_output=False)
    m = masks[0]
mask = np.asarray(Image.fromarray((m * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.2))).astype(np.float32) / 255
cut = img * mask[..., None] + np.array(GREEN, np.float32) * (1 - mask[..., None])
Image.fromarray(cut.clip(0, 255).astype(np.uint8)).save(sys.argv[4]); Image.fromarray((mask * 255).astype(np.uint8)).save(sys.argv[5])
print('cut · the person is %.0f%% of the picture' % (100 * (mask > 0.5).mean()))
"""
TOOL_PROGRAM = """# THE SKIN TOOL ON THE BOX (the CMO's own, beside amLLM; the box's tools used as they are). Two jobs:
#   cut   <picture> <x> <y> <cutout.png> <mask.png>   the person under the dot, alone on the studio grey (rembg's human matte, the piece at the dot)
#   apply <picture> <filter.json> <opacity> <saturation> <out.png>   the filter over the FULL picture: its light and colour moved as his moved
#   learn <cutout.png> <mask.png> <cosmos.mp4> <filter.json>   how far Cosmos's golden hour moved HIS skin (CIELAB, inside his mask)
import json, sys
import cv2, numpy as np
from PIL import Image

def lab(rgb):
    x = cv2.cvtColor(rgb, cv2.COLOR_RGB2LAB).astype(np.float32)
    return np.dstack([x[..., 0] * 100 / 255, x[..., 1] - 128, x[..., 2] - 128])

def rgb_of(L):
    x = np.dstack([L[..., 0] * 255 / 100, L[..., 1] + 128, L[..., 2] + 128]).clip(0, 255).astype(np.uint8)
    return cv2.cvtColor(x, cv2.COLOR_LAB2RGB)

job = sys.argv[1]
if job == 'cut':
    from rembg import new_session, remove
    img = Image.open(sys.argv[2]).convert('RGB'); W, H = img.size
    x, y = int(float(sys.argv[3]) * W), int(float(sys.argv[4]) * H)
    m = np.asarray(remove(img, session=new_session('u2net_human_seg'), only_mask=True)) > 127
    r = max(5, W // 90) | 1   # people touching (fur against hair) are pulled apart first, the piece at the dot grown back after
    thin = cv2.erode(m.astype(np.uint8), cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (r, r)))
    n, lbl = cv2.connectedComponents(thin)
    k = lbl[min(H - 1, y), min(W - 1, x)]
    if k == 0:   # the dot just off the matte: the piece nearest to it
        ys, xs = np.nonzero(lbl); i = np.argmin((xs - x) ** 2 + (ys - y) ** 2) if len(xs) else None
        k = lbl[ys[i], xs[i]] if i is not None else 0
    if k == 0:
        print('NO PERSON under the dot'); sys.exit(2)
    grown = cv2.dilate((lbl == k).astype(np.uint8), cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (r + 4, r + 4))) & m.astype(np.uint8)
    mask = cv2.GaussianBlur(grown.astype(np.float32), (0, 0), 2)
    a = np.asarray(img).astype(np.float32); grey = np.full_like(a, 128)
    cut = a * mask[..., None] + grey * (1 - mask[..., None])
    Image.fromarray(cut.clip(0, 255).astype(np.uint8)).save(sys.argv[5]); Image.fromarray((mask * 255).astype(np.uint8)).save(sys.argv[6])
    print('cut · the person is %.0f%% of the picture' % (100 * (mask > 0.5).mean()))
elif job == 'learn':
    cut = np.asarray(Image.open(sys.argv[2]).convert('RGB')); H, W = cut.shape[:2]
    mask = np.asarray(Image.open(sys.argv[3]).convert('L')).astype(np.float32) / 255
    cap = cv2.VideoCapture(sys.argv[4]); frames = []
    while True:
        ok, f = cap.read()
        if not ok: break
        frames.append(f)
    if not frames:
        print('NO FRAMES from Cosmos'); sys.exit(2)
    g = cv2.cvtColor(cv2.resize(frames[len(frames) // 2], (W, H)), cv2.COLOR_BGR2RGB)
    inside = mask > 0.8
    d = (np.median(lab(g)[inside], axis=0) - np.median(lab(cut)[inside], axis=0)).tolist()
    json.dump({'shift': d}, open(sys.argv[5], 'w'))
    print('learned · his skin moved L %+.1f a %+.1f b %+.1f' % tuple(d))
elif job == 'apply':
    img = np.asarray(Image.open(sys.argv[2]).convert('RGB')); d = json.load(open(sys.argv[3]))['shift']
    op, sat = float(sys.argv[4]), float(sys.argv[5])
    L = lab(img); layer = L.copy()
    layer[..., 0] += d[0]; layer[..., 1] = (L[..., 1] + d[1]) * sat; layer[..., 2] = (L[..., 2] + d[2]) * sat
    Image.fromarray(rgb_of(L * (1 - op) + layer * op)).save(sys.argv[6])
    print('applied · opacity %d%% · saturation %d%%' % (round(op * 100), round(sat * 100)))
elif job == 'labmix':
    # THE LAB'S MIX, 1 TO 1 (timeline lab cosmos_run, "THE SKIN IS A FILTER"): Cosmos's light AND colour map, read past detail inside his mask only, added to
    # the picture; every edge, strand and face stays the picture's own; then SATURATION; then laid over the picture at OPACITY inside his mask.
    # use: labmix <picture> <cosmos.mp4> <mask.png> <opacity> <saturation> <out.png>
    b = np.asarray(Image.open(sys.argv[2]).convert('RGB')).astype(np.float32); H, W = b.shape[:2]
    cap = cv2.VideoCapture(sys.argv[3]); frames = []
    while True:
        ok, f = cap.read()
        if not ok: break
        frames.append(f)
    c = cv2.cvtColor(cv2.resize(frames[len(frames) // 2], (W, H)), cv2.COLOR_BGR2RGB).astype(np.float32)
    m = np.asarray(Image.open(sys.argv[4]).convert('L').resize((W, H))).astype(np.float32) / 255
    op, sat = float(sys.argv[5]), float(sys.argv[6])
    s = 10 * W / 1280.0   # the lab's SKIN_READ (10 px at 1280), at this picture's size
    def mblur(x):   # read inside his mask only, so the place behind never leaks in
        num = cv2.GaussianBlur(x * m[..., None], (0, 0), s); den = cv2.GaussianBlur(m, (0, 0), s)[..., None]
        return num / np.maximum(den, 1e-3)
    top = np.clip(b + mblur(c - b), 0, 255)
    if sat != 1:
        hsv = cv2.cvtColor(top.astype(np.uint8), cv2.COLOR_RGB2HSV).astype(np.float32); hsv[..., 1] = np.clip(hsv[..., 1] * sat, 0, 255)
        top = cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2RGB).astype(np.float32)
    a = (m * op)[..., None]
    Image.fromarray(np.clip(b * (1 - a) + top * a, 0, 255).astype(np.uint8)).save(sys.argv[7])
    print('applied · the lab mix · opacity %d%% · saturation %d%%' % (round(op * 100), round(sat * 100)))
elif job == 'colourmix':
    # COLOUR ONLY (the owner 2026-10-29: "before we only took the color data not the actual image"; "a step where the lightness darkness adjusts the skin first"):
    # 1 LIGHTNESS: his own lightness moved darker or lighter inside his mask (the picture's own shading kept) 2 COLOUR: only Cosmos's hue and saturation
    # (CIELAB a, b), read wide inside his mask so no shape of its picture comes across, laid on his own lightness 3 SATURATION, then OPACITY.
    # use: colourmix <picture> <cosmos.mp4> <mask.png> <lightness -50..50> <opacity> <saturation> <out.png>
    b = np.asarray(Image.open(sys.argv[2]).convert('RGB')); H, W = b.shape[:2]
    cap = cv2.VideoCapture(sys.argv[3]); frames = []
    while True:
        ok, f = cap.read()
        if not ok: break
        frames.append(f)
    c = cv2.cvtColor(cv2.resize(frames[len(frames) // 2], (W, H)), cv2.COLOR_BGR2RGB)
    m = np.asarray(Image.open(sys.argv[4]).convert('L').resize((W, H))).astype(np.float32) / 255
    sys.path.insert(0, __import__('os').path.expanduser('~/frost/virtual_workspace/avatarskin'))
    import skin_norm as SK   # the box's own skin finder, used as it is: his SKIN only, never his hair, clothes or the cap Cosmos painted
    hair_, _bg, body_, face_ = SK.W.avatar_classes(np.dstack([b, np.full(b.shape[:2], 255, np.uint8)]))
    skin_ = np.clip(np.maximum(body_, face_) - hair_, 0, 1)   # the segmenter's SMOOTH face and body skin (its fine colour test leaves gaps at every pore)
    m = cv2.GaussianBlur((m * skin_).astype(np.float32), (0, 0), max(2, W / 640))
    light, op, sat = float(sys.argv[5]), float(sys.argv[6]), float(sys.argv[7])
    s = 34 * W / 1280.0   # read WIDE (the lab's face read, 34 px at 1280): colour, never shapes
    def mblur(x):
        num = cv2.GaussianBlur(x * m[..., None], (0, 0), s); den = cv2.GaussianBlur(m, (0, 0), s)[..., None]
        return num / np.maximum(den, 1e-3)
    Lb, Lc = lab(b), lab(c)
    top = Lb.copy()
    top[..., 0] = np.clip(Lb[..., 0] + light * m, 0, 100)                      # 1 his lightness, darker or lighter
    inside = m > 0.5
    shift = (np.median(Lc[..., 1:][inside], axis=0) - np.median(Lb[..., 1:][inside], axis=0)) if inside.any() else np.zeros(2)
    ab = Lb[..., 1:] + shift                                                   # 2 Cosmos's colour only: ONE golden tone for all his skin (its blurred face square never maps)
    top[..., 1:] = ab * sat                                                    # 3 saturation
    a = (m * op)[..., None]
    out = Lb * (1 - a) + top * a
    Image.fromarray(rgb_of(out)).save(sys.argv[8])
    print('applied · colour only · lightness %+d · opacity %d%% · saturation %d%%' % (round(light), round(op * 100), round(sat * 100)))
elif job == 'fullmix':
    # NO MASK (the owner 2026-10-29: "no mask lets try that"): the golden tone MEASURED on his skin (inside his cut out, the segmenter's smooth skin), then
    # LIGHTNESS, the colour, SATURATION and OPACITY over the ENTIRE image, every pixel the same: a filter, no edges.
    # use: fullmix <picture> <cosmos.mp4> <mask.png> <lightness -30..30> <opacity> <saturation> <out.png> [whites 0..1] [blacks 0..1]
    # WHITES / BLACKS (the owner 2026-10-29, a colourist's step: "a color filter to adjust whites to remove saturation and dark to remove saturation ... we remove the
    # yellow from the white and black"): the colour taken out of the bright and the dark parts only, the skin in the middle tones kept golden.
    b = np.asarray(Image.open(sys.argv[2]).convert('RGB')); H, W = b.shape[:2]
    cap = cv2.VideoCapture(sys.argv[3]); frames = []
    while True:
        ok, f = cap.read()
        if not ok: break
        frames.append(f)
    c = cv2.cvtColor(cv2.resize(frames[len(frames) // 2], (W, H)), cv2.COLOR_BGR2RGB)
    m = np.asarray(Image.open(sys.argv[4]).convert('L').resize((W, H))).astype(np.float32) / 255
    sys.path.insert(0, __import__('os').path.expanduser('~/frost/virtual_workspace/avatarskin'))
    import skin_norm as SK
    hair_, _bg, body_, face_ = SK.W.avatar_classes(np.dstack([b, np.full(b.shape[:2], 255, np.uint8)]))
    inside = (m * np.clip(np.maximum(body_, face_) - hair_, 0, 1)) > 0.5
    light, op, sat = float(sys.argv[5]), float(sys.argv[6]), float(sys.argv[7])
    Lb, Lc = lab(b), lab(c)
    shift = (np.median(Lc[..., 1:][inside], axis=0) - np.median(Lb[..., 1:][inside], axis=0)) if inside.any() else np.zeros(2)
    top = Lb.copy()
    top[..., 0] = np.clip(Lb[..., 0] + light, 0, 100)
    top[..., 1:] = (Lb[..., 1:] + shift) * sat
    out = Lb * (1 - op) + top * op
    whites = float(sys.argv[9]) if len(sys.argv) > 9 else 0.0
    blacks = float(sys.argv[10]) if len(sys.argv) > 10 else 0.0
    L_ = out[..., 0]
    # HIGHLIGHTS AND SHADOWS, BY LIGHTNESS ALONE (the owner 2026-10-29: "the white can really make highlights on the skin like blow out the white"; "the dark should cut
    # and boost too"; "they need more range"): measured on the reference, his highlights reach L 78-84 and his shadows L 4: WHITES lifts the bright half and takes
    # some yellow out, BLACKS deepens the dark half and takes some yellow out; each 0..2 (200%)
    hi = np.clip((L_ - 50) / 25, 0, 1) ** 1.5       # the bright half: from L 50, full at 75
    lo = np.clip((40 - L_) / 25, 0, 1) ** 1.2       # the dark half: from L 40, full at 15
    keep = np.clip(1 - 0.9 * hi - 0.9 * lo, 0, 1)   # THE YELLOW CUT IS ALWAYS ON (the owner 2026-10-29: "should just basically be ON and cuts all the yellow almost"): the sliders only lift the highlights and deepen the lowlights
    out[..., 1:] *= keep[..., None]
    out[..., 0] = np.clip(L_ + 22 * whites * hi - 12 * blacks * lo, 0, 100)
    Image.fromarray(rgb_of(out)).save(sys.argv[8])
    print('applied · whites %d%% · blacks %d%% · ' % (round(whites * 100), round(blacks * 100)) + 'no mask, the entire image · golden tone a %+.2f b %+.2f · lightness %+d · opacity %d%% · saturation %d%%' % (shift[0], shift[1], round(light), round(op * 100), round(sat * 100)))
elif job in ('measure', 'tonemix'):
    # ONE COSMOS RUN FOR THE FILM (the owner 2026-10-29: "we only need to run the first one to get this data the rest should just be adjustments"):
    #   measure <picture> <cosmos.mp4> <mask.png> <tone.json>   the golden tone of his skin, once
    #   tonemix <picture> <a> <b> <lightness> <opacity> <saturation> <out.png> <highlights 0..2> <lowlights 0..2>   that tone on ANY slot, no Cosmos
    b = np.asarray(Image.open(sys.argv[2]).convert('RGB')); H, W = b.shape[:2]; Lb = lab(b)
    if job == 'measure':
        cap = cv2.VideoCapture(sys.argv[3]); frames = []
        while True:
            ok, f = cap.read()
            if not ok: break
            frames.append(f)
        c = cv2.cvtColor(cv2.resize(frames[len(frames) // 2], (W, H)), cv2.COLOR_BGR2RGB)
        m = np.asarray(Image.open(sys.argv[4]).convert('L').resize((W, H))).astype(np.float32) / 255
        sys.path.insert(0, __import__('os').path.expanduser('~/frost/virtual_workspace/avatarskin'))
        import skin_norm as SK
        hair_, _bg, body_, face_ = SK.W.avatar_classes(np.dstack([b, np.full(b.shape[:2], 255, np.uint8)]))
        inside = (m * np.clip(np.maximum(body_, face_) - hair_, 0, 1)) > 0.5
        Lc = lab(c)
        shift = (np.median(Lc[..., 1:][inside], axis=0) - np.median(Lb[..., 1:][inside], axis=0)) if inside.any() else np.zeros(2)
        json.dump({'shift': [round(float(shift[0]), 3), round(float(shift[1]), 3)]}, open(sys.argv[5], 'w'))
        print('measured · golden tone a %+.2f b %+.2f' % (shift[0], shift[1]))
    else:
        sa, sb, light, op, sat = (float(v) for v in sys.argv[3:8])
        whites, blacks = float(sys.argv[9]), float(sys.argv[10])
        top = Lb.copy()
        top[..., 0] = np.clip(Lb[..., 0] + light, 0, 100)
        top[..., 1] = (Lb[..., 1] + sa) * sat; top[..., 2] = (Lb[..., 2] + sb) * sat
        out = Lb * (1 - op) + top * op
        L_ = out[..., 0]
        hi = np.clip((L_ - 50) / 25, 0, 1) ** 1.5
        lo = np.clip((40 - L_) / 25, 0, 1) ** 1.2
        keep = np.clip(1 - 0.9 * hi - 0.9 * lo, 0, 1)   # the yellow cut always on
        out[..., 1:] *= keep[..., None]
        out[..., 0] = np.clip(L_ + 22 * whites * hi - 12 * blacks * lo, 0, 100)
        Image.fromarray(rgb_of(out)).save(sys.argv[8])
        print('applied · the golden tone a %+.2f b %+.2f · lightness %+d · opacity %d%% · saturation %d%% · highlights %d%% · lowlights %d%%' % (sa, sb, round(light), round(op * 100), round(sat * 100), round(whites * 100), round(blacks * 100)))
"""


def _ssh_bytes(cmd, data=None, timeout=300):
    return subprocess.run(['ssh', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=8', BOX, cmd], input=data, capture_output=True, timeout=timeout)


def _card_with_room():
    """-> the box's card with room for Cosmos, or (None, the words why not)"""
    said = _box(['nvidia-smi --query-gpu=index,memory.used,memory.total --format=csv,noheader,nounits'], timeout=30).stdout
    cards = [[int(x) for x in ln.split(',')] for ln in said.strip().splitlines() if ln.count(',') == 2]
    free = sorted(((t - u, i) for i, u, t in cards), reverse=True)
    if free and free[0][0] >= COSMOS_ROOM:
        return free[0][1], ''
    return None, 'no card on the Exxact has room for Cosmos (' + ', '.join(f'card {i}: {f // 1024} GB free' for f, i in sorted(free, key=lambda x: x[1])) + f', it needs {COSMOS_ROOM // 1024})'


def _look_tools():
    """the CMO's two box programs written into its own box folder (they are the agent's own; the box's tools are only used)"""
    _ssh_bytes(f'mkdir -p ~/{LOOK_DIR}/in ~/{LOOK_DIR}/out && cat > ~/{LOOK_DIR}/cut_sam.py', CUT_PROGRAM.encode())
    _ssh_bytes(f'cat > ~/{LOOK_DIR}/skin_tool.py', TOOL_PROGRAM.encode())


def skin_dot(con, conf, fid, n, src):
    """-> (x, y) as fractions: his click, else the biggest face the box finds (him: the women stand back), kept in the row as his dot"""
    r = con.execute('SELECT dot_x, dot_y FROM skin WHERE film = ? AND n = ?', (fid, n)).fetchone()
    if r and r['dot_x'] is not None:
        return r['dot_x'], r['dot_y']
    faces, why = None, ''
    for _try in range(3):
        try:
            subprocess.run(['scp', '-q', '-o', 'BatchMode=yes', src, f'{BOX}:{BOX_DIR}/in/skin_{fid}_{n}.png'], capture_output=True, timeout=300, check=True)
            faces = _swap_ask('/landmarks', {'image': f'/home/exx/{BOX_DIR}/in/skin_{fid}_{n}.png'}, 300).get('faces') or []
            break
        except Exception as e:   # noqa: BLE001
            why = str(e)[:120]
            time.sleep(5)
    if faces is None:
        raise RuntimeError(f'could not read the faces on the box ({why}) · click him on the Original to set the dot')
    if not faces:
        raise RuntimeError('no face found · click him on the Original to set the dot')
    f_ = max(faces, key=lambda q: q['bbox'][2] * q['bbox'][3])
    x, y = round(f_['bbox'][0] + f_['bbox'][2] / 2, 4), round(f_['bbox'][1] + f_['bbox'][3] * 0.45, 4)
    con.execute('UPDATE skin SET dot_x = ?, dot_y = ? WHERE film = ? AND n = ?', (x, y, fid, n)); con.commit()
    return x, y


def skin_one(con, conf, film, slots, step=lambda s: None):
    fid = film['id']
    home = os.path.join(conf['films'], fid, 'skin')
    os.makedirs(home, exist_ok=True)

    def say(n, words, start=False):   # THE ROW'S STATUS (the owner 2026-10-29: "we need a status for this")
        con.execute("UPDATE skin SET state = 'working', why = ?" + (', made_at = ?' if start else '') + ' WHERE film = ? AND n = ?', (words, _now(), fid, n) if start else (words, fid, n))
        con.commit()
        step(f'{fid}: skin, slot {n}: {words}')
    made = []
    for n in slots:
        w_ = con.execute("SELECT file FROM faceswap WHERE film = ? AND n = ? AND state = 'done'", (fid, n)).fetchone()
        src = os.path.join(conf['films'], fid, 'faceswap', w_['file']) if w_ and w_['file'] else ''
        if not src or not os.path.exists(src):
            con.execute("UPDATE skin SET state = 'red', why = 'no face swap in this slot yet (step 3)' WHERE film = ? AND n = ?", (fid, n)); con.commit()
            continue
        try:
            say(n, '1 · the dot: finding him', start=True)
            _look_tools()
            x, y = skin_dot(con, conf, fid, n, src)
            say(n, f'2 · cutting him out from the dot ({x:.2f}, {y:.2f})')
            box_in, cut_, mask_ = f'~/{LOOK_DIR}/in/{fid}_{n}.png', f'~/{LOOK_DIR}/out/{fid}_{n}_cut.png', f'~/{LOOK_DIR}/out/{fid}_{n}_mask.png'
            subprocess.run(['scp', '-q', '-o', 'BatchMode=yes', src, f'{BOX}:{LOOK_DIR}/in/{fid}_{n}.png'], capture_output=True, timeout=300, check=True)
            said = _box([f'cd ~/{LOOK_DIR} && PYTHONPATH=pylib CUDA_VISIBLE_DEVICES=1 {SAM_PY} cut_sam.py {box_in} {x} {y} {cut_} {mask_} 2>&1 | tail -1'], timeout=600).stdout
            if 'cut ·' not in said:
                raise RuntimeError('the cut out did not work: ' + said.strip()[-140:])
            for there_f, here_f in ((cut_, f'cut_{n}.png'), (mask_, f'mask_{n}.png')):
                subprocess.run(['scp', '-q', '-o', 'BatchMode=yes', f'{BOX}:{there_f.replace("~/", "")}', os.path.join(home, here_f)], capture_output=True, timeout=300, check=True)
            con.execute('UPDATE skin SET cut = ? WHERE film = ? AND n = ?', (f'cut_{n}.png', fid, n)); con.commit()
            while _box([f'ls {COSMOS}/lab/*.running 2>/dev/null'], timeout=30).stdout.strip():   # ONE COSMOS RUN AT A TIME (the lab's own rule)
                say(n, '3 · Cosmos: waiting for the run before it')
                time.sleep(15)
            card, why = _card_with_room()
            if card is None:
                raise RuntimeError(why)
            say(n, f'3 · Cosmos: sending him alone (card {card})')
            clip, tag = os.path.join(home, f'in_{n}.mp4'), f'cmo_{fid}_{n}'
            subprocess.run(['ffmpeg', '-v', 'error', '-y', '-loop', '1', '-i', os.path.join(home, f'cut_{n}.png'), '-t', '2', '-r', '16', '-c:v', 'libx264', '-crf', '12', '-pix_fmt', 'yuv420p', clip], check=True, timeout=120)
            there = f'{COSMOS}/lab/{tag}'
            with open(clip, 'rb') as fh:
                if _ssh_bytes(f'mkdir -p {COSMOS}/lab && cat > {there}.in.mp4', fh.read()).returncode:
                    raise RuntimeError('the Exxact did not take the cut out')
            _ssh_bytes(f'cat > {there}.txt', COSMOS_WORDS.encode())
            _box([f'cd {COSMOS}/lab && rm -f {there}.said && touch {there}.running && (COSMOS_CARD={card} nohup sh -c "{COSMOS}/cosmos.sh {there}.in.mp4 {there}.mp4 {there}.txt {SKIN_GOLD['hold']} > {there}.said.part 2>&1; '
                  f'mv {there}.said.part {there}.said; rm -f {there}.running" > /dev/null 2>&1 &)'], timeout=60)
            t0 = time.time()
            while True:
                time.sleep(15)
                seen = _box([f'cat {there}.said 2>/dev/null; echo ::; tail -c 300 {COSMOS}/jobs/{tag}/run.log 2>/dev/null | tr "\\r" "\\n" | tail -1'], timeout=30).stdout
                said, _, bar = seen.partition('::')
                if said.strip():
                    break
                pct = re.search(r'(\d+)/(\d+) \[', bar)
                say(n, f'3 · Cosmos is painting him in golden hour: step {pct.group(1)} of {pct.group(2)}' if pct else '3 · Cosmos is loading its model (a few minutes)')
                if time.time() - t0 > 3600:
                    raise RuntimeError('no answer from Cosmos after an hour')
            if 'cosmos done' not in said:
                log_ = _box([f'tr "\\r" "\\n" < {COSMOS}/jobs/{tag}/run.log 2>/dev/null | grep -i guardrail | tail -2'], timeout=30).stdout
                if 'check on video' in log_ and 'Passed guardrail on generated video' not in log_:
                    raise RuntimeError("NVIDIA's own check in Cosmos refused the painted picture")
                raise RuntimeError(said.strip()[-180:] or 'Cosmos stopped without a word')
            got = _ssh_bytes(f'cat {there}.mp4', timeout=600).stdout
            if got[4:8] != b'ftyp':
                raise RuntimeError('what came back is not a video')
            with open(os.path.join(home, f'cos_{n}.mp4'), 'wb') as fh:
                fh.write(got)
            subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', '1', '-i', os.path.join(home, f'cos_{n}.mp4'), '-frames:v', '1', '-vf', 'scale=1920:1080', os.path.join(home, f'gold_{n}.png')], capture_output=True, timeout=120)
            _box([f'rm -f {there}.in.mp4 {there}.mp4 {there}.mp4.keep.mp4 {there}.txt {there}.said; rm -rf {COSMOS}/jobs/{tag}'], timeout=30)
            os.remove(clip)
            say(n, '4 · learning the filter from his skin')
            subprocess.run(['scp', '-q', '-o', 'BatchMode=yes', os.path.join(home, f'cos_{n}.mp4'), f'{BOX}:{LOOK_DIR}/out/{fid}_{n}_cos.mp4'], capture_output=True, timeout=300, check=True)
            said = _box([f'cd ~/{LOOK_DIR} && {SKIN_PY} skin_tool.py measure in/{fid}_{n}.png out/{fid}_{n}_cos.mp4 {mask_} out/{fid}_{n}_filter.json 2>&1 | grep -E "measured" | tail -1; cat out/{fid}_{n}_filter.json'], timeout=300).stdout
            if 'measured' not in said:
                raise RuntimeError('the golden tone could not be measured: ' + said.strip()[-140:])
            con.execute('UPDATE skin SET raw = ?, filter = ? WHERE film = ? AND n = ?', (f'gold_{n}.png', said.strip().splitlines()[-1], fid, n)); con.commit()
            ok, said = skin_mix(con, conf, fid, n)
            if not ok:
                raise RuntimeError(said)
            made.append(str(n))
        except Exception as e:   # noqa: BLE001
            con.execute("UPDATE skin SET state = 'red', why = ? WHERE film = ? AND n = ?", (str(e)[:200], fid, n))
        con.commit()
    _set_film(con, fid, state='music ready')
    return (True, f"{fid} · golden hour skin for slot {', '.join(made)}") if made else (False, f'{fid} · the skin was not made · see its row')


def film_tone(con, fid):
    """THE FILM'S ONE GOLDEN TONE (the owner 2026-10-29: "we dont need to process the job more than 1 time"): the first slot with a Cosmos run gives it;
    every other slot uses it -> (slot, {'shift': [a, b]}, its row) or (None, None, None)"""
    r = con.execute("SELECT * FROM skin WHERE film = ? AND filter IS NOT NULL AND raw IS NOT NULL ORDER BY n LIMIT 1", (fid,)).fetchone()
    if not r:
        return None, None, None
    try:
        return r['n'], json.loads(r['filter']), r
    except ValueError:
        return None, None, None


def skin_mix(con, conf, fid, n):
    """4 · THE FILTER over the FULL picture at the row's OPACITY and SATURATION (seconds, no new Cosmos run) -> (ok, words)"""
    r = con.execute('SELECT * FROM skin WHERE film = ? AND n = ?', (fid, n)).fetchone()
    w_ = con.execute("SELECT file FROM faceswap WHERE film = ? AND n = ? AND state = 'done'", (fid, n)).fetchone()
    src = os.path.join(conf['films'], fid, 'faceswap', w_['file']) if w_ and w_['file'] else ''
    if not (src and os.path.exists(src) and r):
        return False, 'its face swap is missing'
    op = r['opacity'] if r['opacity'] is not None else SKIN_GOLD['opacity']
    sat = r['saturation'] if r['saturation'] is not None else SKIN_GOLD['saturation']
    home = os.path.join(conf['films'], fid, 'skin')
    _look_tools()
    subprocess.run(['scp', '-q', '-o', 'BatchMode=yes', src, f'{BOX}:{LOOK_DIR}/in/{fid}_{n}.png'], capture_output=True, timeout=300)
    # THE LAB'S MIX, 1 TO 1 (the owner 2026-10-29: "look at how we did it in the lab becasue we got 1 to 1 matching"): Cosmos's light and colour map, pixel by pixel, inside his mask
    try:
        tone_ = json.loads(r['filter'])['shift'][-2:] if r['filter'] else (film_tone(con, fid)[1] or {}).get('shift', [])[-2:] or None   # its own, else the film's one tone
    except (ValueError, KeyError, TypeError):
        tone_ = None
    light = r['lightness'] if r['lightness'] is not None else SKIN_GOLD['lightness']
    # COLOUR ONLY, HIS SKIN ONLY (the owner 2026-10-29: "before we only took the color data not the actual image"; the darkness step first): LIGHTNESS, then Cosmos's colour
    wh = r['whites'] if r['whites'] is not None else SKIN_GOLD['whites']
    bl = r['blacks'] if r['blacks'] is not None else SKIN_GOLD['blacks']
    if not tone_:
        return False, 'its golden tone is missing'
    said = _box([f'cd ~/{LOOK_DIR} && {SKIN_PY} skin_tool.py tonemix in/{fid}_{n}.png {tone_[0]} {tone_[1]} {light} {op} {sat} out/{fid}_{n}_skin.png {wh} {bl} 2>&1 | grep applied | tail -1'], timeout=300).stdout
    if 'applied' not in said:
        con.execute("UPDATE skin SET state = 'red', why = 'the filter could not be laid on the picture' WHERE film = ? AND n = ?", (fid, n))
        return False, 'the filter could not be laid on the picture'
    subprocess.run(['scp', '-q', '-o', 'BatchMode=yes', f'{BOX}:{LOOK_DIR}/out/{fid}_{n}_skin.png', os.path.join(home, f'skin_{n}.png')], capture_output=True, timeout=300, check=True)

    con.execute("UPDATE skin SET file = ?, state = 'done', baked = NULL, why = ?, made_at = ? WHERE film = ? AND n = ?",
                (f'skin_{n}.png', f'no mask, the entire image · lightness {round(light):+d} · opacity {round(op * 100)}% · saturation {round(sat * 100)}% · highlights {round(wh * 100)}% · lowlights {round(bl * 100)}% · not baked', _now(), fid, n))
    _keep(con, conf, fid, 'skin_mix', n, f'skin/skin_{n}.png', 'skin', files=(f'skin/mask_{n}.png', f'skin/cut_{n}.png'))
    return True, f'opacity {round(op * 100)}% · saturation {round(sat * 100)}%'


def _plain_png(src, dst):
    """the picture's own pixels with its colour tags taken out (cICP, cHRM, gAMA, iCCP, sRGB): a browser then shows it as the box reads it, so the LIVE
    preview and the saved picture match (2026-10-29: the step 3 stills carry the video's BT.709 tag and showed darker in the page than on the box)"""
    import struct
    d = open(src, 'rb').read()
    out, i = [d[:8]], 8
    while i < len(d):
        n = struct.unpack('>I', d[i:i + 4])[0]
        kind = d[i + 4:i + 8]
        if kind not in (b'cICP', b'cHRM', b'gAMA', b'iCCP', b'sRGB'):
            out.append(d[i:i + 12 + n])
        i += 12 + n
        if kind == b'IEND':
            break
    with open(dst + '.part', 'wb') as fh:
        fh.write(b''.join(out))
    os.replace(dst + '.part', dst)


def skin_parts(con, f, conf):
    """PART 4 ON THE PAGE · SKIN: one row a slot, every step its own column (the owner 2026-10-29: "show all the steps together in a table ... so its clear")"""
    fid = f['id']
    swaps = {r['n']: r for r in con.execute("SELECT * FROM faceswap WHERE film = ? AND state = 'done' AND file IS NOT NULL", (fid,))}
    head = {'kind': 'step', 'n': 4, 'title': 'LOOK MATCH · SKIN', 'under': 'the lab\'s amLLM Skin, the gold one · 1 the dot picks him (as the swap) · 2 he is cut out · 3 Cosmos paints him alone in golden hour · 4 the filter goes over the full picture, OPACITY and SATURATION down until it matches the reference · 5 BAKE'}
    if not swaps:
        return [head, {'kind': 'note', 'title': '4 · waits for step 3', 'text': 'swap the faces first'}]
    sk = {r['n']: r for r in con.execute('SELECT * FROM skin WHERE film = ?', (fid,))}
    tone_n, tone, tone_row = film_tone(con, fid)
    ref_at = os.path.join(conf['references'], SKIN_REF) if os.path.exists(os.path.join(conf['references'], SKIN_REF)) else ''
    img = lambda name, width=300: {'image': _src(conf, f'{fid}/skin', name), 'width': width, 'full': True} if name and os.path.exists(os.path.join(conf['films'], fid, 'skin', name)) else ''   # noqa: E731
    rows = []
    for n in sorted(swaps):
        r = sk.get(n)
        st = r['state'] if r is not None else 'new'
        done = r is not None and st in ('done', 'baked') and r['file']
        mine = lambda k, d: (r[k] if r is not None and r[k] is not None else (tone_row[k] if tone_row is not None and tone_row[k] is not None else d))   # noqa: E731   its own number, else the first slot's
        op = round(mine('opacity', SKIN_GOLD['opacity']) * 100)
        sat = round(mine('saturation', SKIN_GOLD['saturation']) * 100)
        lt = round(mine('lightness', SKIN_GOLD['lightness']))
        sliders = [{'name': 'lightness', 'label': 'LIGHTNESS', 'min': -30, 'max': 30, 'value': lt, 'unit': ''},   # THE DARKNESS STEP FIRST (the owner 2026-10-29)
                   {'name': 'opacity', 'label': 'OPACITY', 'min': 1, 'max': 100, 'value': op, 'unit': '%'}, {'name': 'saturation', 'label': 'SATURATION', 'min': 0, 'max': 200, 'value': sat, 'unit': '%'},
                   {'name': 'whites', 'label': 'HIGHLIGHTS', 'min': 0, 'max': 300, 'value': round(mine('whites', 0) * 100), 'unit': '%'},   # (the owner 2026-10-29)
                   {'name': 'blacks', 'label': 'LOWLIGHTS', 'min': 0, 'max': 200, 'value': round(mine('blacks', 0) * 100), 'unit': '%'}]
        dot = {'image': _src(conf, f'{fid}/faceswap', swaps[n]['file']), 'do': 'skinmark', 'value': f'{fid}:{n}', 'kinds': ['him'], 'width': 300, 'full': True,
               'marks': [[r['dot_x'], r['dot_y'], 'him']] if r is not None and r['dot_x'] is not None else []}
        status = ({'word': 'BAKED', 'text': r['why'] or ''} if st == 'baked' else {'word': 'DONE', 'text': r['why'] or ''} if done else
                  {'word': 'READY', 'text': f"slot {tone_n}'s golden tone · set it live, then BAKE"} if tone is not None and st in ('new',) else
                  {'word': 'WAITING', 'text': 'its turn in the agent\'s run', 'since': r['made_at'], 'label': 'for', 'working': True} if st == 'asked' else
                  {'word': 'PROCESSING', 'text': r['why'] or '', 'since': r['made_at'], 'label': 'for', 'working': True} if st == 'working' else
                  {'word': 'RED', 'text': r['why'] or ''} if st == 'red' else {'word': 'NOT MADE', 'text': 'press ◇ SKIN'})
        ref_cell = {'image': f"{conf['scratch_url']}/{os.path.relpath(ref_at, SCRATCH)}", 'width': 160, 'full': True} if ref_at else f'missing: {SKIN_REF}'
        try:   # 4 · LIVE (the owner 2026-10-29: "can it adjust with the slider so you see the results live"): the original filtered in the page as the sliders move
            shift = json.loads(r['filter'])['shift'] if r is not None and r['filter'] else (tone or {}).get('shift')   # its own tone, else the film's one
        except (ValueError, KeyError, TypeError):
            shift = None
        plain = os.path.join(conf['films'], fid, 'skin', f'plain_{n}.png')
        if shift and not os.path.exists(plain):
            _plain_png(os.path.join(conf['films'], fid, 'faceswap', swaps[n]['file']), plain)
        live_cell = {'live': {'src': _src(conf, f'{fid}/skin', f'plain_{n}.png'), 'shift': shift[-2:]}, 'width': 420} if shift and len(shift) >= 2 else None
        rows.append({'key': f'{fid}:{n}', 'cells': [str(n), {'marker': dot}, img(r['cut'] if r is not None else ''), img(r['raw'] if r is not None else ''),
                                                   (live_cell or img(r['file'] if done else '', 420)), ref_cell, '', status],
                     'presses': ([{'do': 'skinbake', 'value': f'{fid}:{n}', 'label': 'BAKE ALL (saves what you see, every row)', 'sliders': sliders, 'gather': True, 'cell': 6}] if (tone or (r is not None and r['filter'])) else [])
                     + ([] if tone_n is not None and tone_n != n else [{'do': 'skin', 'value': f'{fid}:{n}', 'label': '◇ SKIN · the film\'s one Cosmos run' if tone_n is None else '◇ SKIN AGAIN (a new Cosmos run)', 'cell': 6}])})
    return [head, {'kind': 'table', 'title': '4 · SKIN · every step · click him on the Original to move the dot',
                   'columns': ['Slot', '1 · Original (the dot)', '2 · Cut out', '3 · Cosmos golden hour', '4 · Filtered (entire image)', 'Skin reference', 'Controls', 'Status'], 'rows': rows}]


# ============ PART 5 · TEETH (the owner 2026-10-29: "the biggest things is the teeth and not the mouth itself ... we dont want to change from a closed mouth to an open
# one or change lips basically we want to normalize all the teeth to match"; "image 4 ... the 4th last skin color baked image"; "we should make a mask on the reference
# itself and on the images each so its very isolated and very targeted"): the old Pace Shift boards' proven maths, no AI (the wid psawp bench: the mask of
# _hair_mask_raster, the heal board's Telea, the patch board's feathered paste). The master's grill cut by ITS mask, laid on each slot inside THAT slot's mask,
# graded to the shot's light: a closed mouth has nothing marked and is kept as it is, a half open one shows the grill only where its own teeth showed.
TEETH_REF = 4   # THE MASTER (the owner 2026-10-29): slot 4's baked skin picture, the insert shot of the grill
TEETH_KINDS = {'wand': ('w', 18, 0), 'wand loose': ('w', 36, 0), 'brush': ('p', 0, 0.012), 'brush big': ('p', 0, 0.035),
               'erase': ('e', 0, 0.012), 'erase big': ('e', 0, 0.035)}   # a click: WAND the like colour round the spot (its tolerance), BRUSH and ERASE a dot (its size on the view)
TEETH_SLIDERS = (('size', 50, 160, 100), ('mx', -50, 50, 0), ('my', -50, 50, 0), ('turn', -30, 30, 0), ('match', 0, 100, 60), ('light', -30, 30, 0),
                 ('soft', 0, 30, 0), ('edge', 0, 20, 2), ('grow', -10, 10, 0))   # name, least, most, the first number
TEETH_LABELS = {'size': ('SIZE', '%'), 'mx': ('MOVE ←→', ''), 'my': ('MOVE ↑↓', ''), 'turn': ('TURN', '°'), 'match': ('MATCH LIGHT', '%'), 'light': ('BRIGHTNESS', ''),
                'soft': ('SOFT', ''), 'edge': ('EDGE', 'px'), 'grow': ('GROW MASK', 'px')}
TEETH_PROGRAM = """
# THE TEETH TOOL ON THE BOX (the CMO's own, beside amLLM): the old Pace Shift boards' proven no-AI maths (wid psawp bench: _hair_mask_raster, the
# heal board's Telea, the patch board's feathered paste), the grill taken from the master picture by ITS OWN MASK, laid on a slot inside THE SLOT'S MASK.
#   mask <picture> <strokes.json> <x0,y0,x1,y1> <mask.png> <view.png>   the mask from his clicks (wand, brush, erase in order), the view = the crop, mask in green
#   grill <ref.png> <refmask.png> <grill.png>   the master's grill alone (its mask's box, see-through round the teeth): the layer the page moves
#   swap <picture> <mask.png> <ref.png> <refmask.png> <params.json> <out.png> <view.png>   the grill laid as he placed it, nothing outside the mask moved
import json, sys
import cv2, numpy as np
from PIL import Image

GREEN = np.array([0x00, 0xB1, 0x40], np.float32)   # the lab's green


def rgb(p):
    return np.asarray(Image.open(p).convert('RGB'))


def save(a, p):
    Image.fromarray(a.clip(0, 255).astype(np.uint8)).save(p)


def raster(img, strokes):
    # his clicks replayed in order (the old boards' _hair_mask_raster): WAND = the region of like colour around the spot, BRUSH paints, ERASE takes away
    H, W = img.shape[:2]
    m = np.zeros((H, W), np.uint8)
    for s in strokes:
        cx, cy = max(0, min(W - 1, int(round(s['x'] * W)))), max(0, min(H - 1, int(round(s['y'] * H))))
        if s['m'] == 'w':
            tol = max(4, min(80, int(s.get('tol') or 24)))
            fm = np.zeros((H + 2, W + 2), np.uint8)
            cv2.floodFill(img.copy(), fm, (cx, cy), 0, loDiff=(tol,) * 3, upDiff=(tol,) * 3,
                          flags=cv2.FLOODFILL_MASK_ONLY | cv2.FLOODFILL_FIXED_RANGE | (255 << 8) | 4)
            m |= (fm[1:-1, 1:-1] > 0).astype(np.uint8)
        else:
            cv2.circle(m, (cx, cy), max(1, int(round(s['r'] * W))), 0 if s['m'] == 'e' else 1, -1)
    return m


def view(img, m, box, out):
    # the crop he works on, his mask laid on it in the lab's green with its edge drawn, made 1920 wide so a tooth is big enough to click
    x0, y0, x1, y1 = box
    c = img[y0:y1, x0:x1].astype(np.float32)
    mm = m[y0:y1, x0:x1].astype(bool) if m is not None else np.zeros(c.shape[:2], bool)
    c[mm] = c[mm] * 0.55 + GREEN * 0.45
    k = 1920 / c.shape[1]
    c = cv2.resize(c, (1920, max(1, int(round(c.shape[0] * k)))), interpolation=cv2.INTER_CUBIC if k > 1 else cv2.INTER_AREA)
    edge = cv2.resize(mm.astype(np.uint8), (c.shape[1], c.shape[0]), interpolation=cv2.INTER_NEAREST)
    cs, _ = cv2.findContours(edge, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    c = np.ascontiguousarray(c.clip(0, 255).astype(np.uint8))
    cv2.drawContours(c, cs, -1, (0, 255, 90), 2)
    save(c, out)


def bbox(m):
    ys, xs = np.nonzero(m)
    return xs.min(), ys.min(), xs.max() + 1, ys.max() + 1


def band(im, m):
    # the shot's brightness round a mask: the box round it grown by a quarter of its width, outside the mask (the page measures the same)
    x0, y0, x1, y1 = bbox(m)
    g_ = int(round((x1 - x0) * 0.25))
    b_ = np.zeros_like(m); b_[max(0, y0 - g_):y1 + g_, max(0, x0 - g_):x1 + g_] = 1
    sel = (b_ > 0) & (m == 0)
    return float((im[sel].astype(np.float32) @ np.array([0.299, 0.587, 0.114], np.float32)).mean()) if sel.any() else 128.0


job = sys.argv[1]
if job == 'mask':
    img = rgb(sys.argv[2])
    m = raster(img, json.load(open(sys.argv[3])))
    box = [int(v) for v in sys.argv[4].split(',')]
    save(m.astype(np.float32) * 255, sys.argv[5])
    view(img, m, box, sys.argv[6])
    print('mask · %d pixels marked' % int(m.sum()))
elif job == 'grill':   # THE GRILL LAYER: the master cut by its own mask, its box only, the rest see-through (the page lays it on a slot)
    ref, rm = rgb(sys.argv[2]), (rgb(sys.argv[3])[..., 0] > 127).astype(np.uint8)
    if not rm.any():
        print('refused · the master has no grill marked'); sys.exit(2)
    rx0, ry0, rx1, ry1 = bbox(rm)
    Image.fromarray(np.dstack([ref[ry0:ry1, rx0:rx1], rm[ry0:ry1, rx0:rx1] * 255]).astype(np.uint8), 'RGBA').save(sys.argv[4])
    print('grill · %d x %d px · band %.2f' % (rx1 - rx0, ry1 - ry0, band(ref, rm)))
elif job == 'swap':
    img, tm = rgb(sys.argv[2]), (rgb(sys.argv[3])[..., 0] > 127).astype(np.uint8)
    ref, rm = rgb(sys.argv[4]), (rgb(sys.argv[5])[..., 0] > 127).astype(np.uint8)
    p = {'match': 60, 'light': 0, 'edge': 2, **json.load(open(sys.argv[6]))}
    H, W = img.shape[:2]
    if not tm.any():
        print('refused · the slot has no teeth marked'); sys.exit(2)
    if not rm.any():
        print('refused · the master has no grill marked'); sys.exit(2)
    tx0, ty0, tx1, ty1 = bbox(tm)
    rx0, ry0, rx1, ry1 = bbox(rm)
    gw, gh = rx1 - rx0, ry1 - ry0
    # 1 THE LAYER (the PF REFERENCE MATCH stage, as avatarskin/wrap.py bakes it): the grill's centre, width and height (each its own: the squish) as fractions of
    # the slot picture and its turn in degrees, as he placed it on the page; never placed: the slot's teeth width, the grill's own shape, hung from their top
    L = p.get('layer') or {}
    if not L.get('w'):
        w_ = (tx1 - tx0) / W
        L = {'cx': (tx0 + tx1) / 2 / W, 'w': w_, 'h': w_ * W * gh / gw / H, 'rot': 0}
        L['cy'] = ty0 / H + L['h'] / 2
    pw, ph = max(1, int(round(L['w'] * W))), max(1, int(round(L['h'] * H)))
    patch = cv2.resize(ref[ry0:ry1, rx0:rx1].astype(np.float32), (pw, ph), interpolation=cv2.INTER_AREA)   # area-true first, so a tooth stays crisp
    alpha = cv2.resize(rm[ry0:ry1, rx0:rx1].astype(np.float32), (pw, ph), interpolation=cv2.INTER_AREA)
    # 2 THE LIGHT, ONE FACTOR (the page draws the same): the shot's brightness round the slot's teeth against the master's round its grill (the box round each
    # mask grown by a quarter of its width, outside the mask), at MATCH, times LIGHT
    ratio = band(img, tm) / max(1.0, band(ref, rm))
    f = (1 + (ratio - 1) * p['match'] / 100.0) * (1 + p['light'] / 100.0)
    patch = patch * f
    # 3 THE PLACE: turned about its own centre (the page's CSS rotate, clockwise on the screen), its centre on the spot
    M = cv2.getRotationMatrix2D((pw / 2, ph / 2), -float(L.get('rot') or 0), 1.0)
    M[0, 2] += L['cx'] * W - pw / 2
    M[1, 2] += L['cy'] * H - ph / 2
    patch = cv2.warpAffine(patch, M, (W, H), flags=cv2.INTER_LINEAR, borderValue=0)
    alpha = cv2.warpAffine(alpha, M, (W, H), flags=cv2.INTER_LINEAR, borderValue=0)
    # 4 THE HEAL (the old heal board's Telea): the slot's old teeth filled from the mouth around them, so none show where the grill does not cover
    healed = cv2.inpaint(img, tm * 255, max(3, int(round(0.004 * W))), cv2.INPAINT_TELEA).astype(np.float32)
    # 5 THE LANDING: inside the slot's mask only, its EDGE softened inward; every pixel outside is the picture's own, by construction
    a = alpha * tm
    if p['edge'] > 0:
        a = cv2.GaussianBlur(a, (0, 0), max(0.4, p['edge'] / 2.0)) * tm
    out = healed * (1 - a[..., None]) + patch * a[..., None]
    out = np.where(tm[..., None] > 0, out.clip(0, 255).round(), img).astype(np.uint8)
    moved = int((out[tm == 0] != img[tm == 0]).any(axis=1).sum())
    save(out, sys.argv[7])
    vw = min(W, max(240, 3 * (tx1 - tx0)))   # the close view: the teeth with room round them, 16:9
    vh = min(H, int(round(vw * 9 / 16)))
    vx = max(0, min(W - vw, int(round((tx0 + tx1) / 2 - vw / 2))))
    vy = max(0, min(H - vh, int(round((ty0 + ty1) / 2 - vh / 2))))
    view(out, None, (vx, vy, vx + vw, vy + vh), sys.argv[8])
    print('swapped · the grill %d x %d px, turned %+.1f° · light x%.2f · %d%% covered · outside the mask: %d pixels changed · layer %s'
          % (pw, ph, float(L.get('rot') or 0), f, round(100 * (alpha[tm > 0] > 0.5).mean()), moved, json.dumps({k: round(float(v), 5) for k, v in L.items()})))
"""


def _teeth_src(conf, fid, n):
    """the slot's picture this step works on: its baked skin picture (step 4)"""
    return os.path.join(conf['films'], fid, 'skin', f'baked_{n}.png')


def _png_size(path):
    import struct
    with open(path, 'rb') as fh:
        head = fh.read(24)
    return struct.unpack('>II', head[16:24])


def _teeth_box(conf, fid, n, r):
    """-> the close view's corners in pixels and the picture's size: the whole picture, or 1/zoom of it centred on his ZOOM HERE"""
    Wp, Hp = _png_size(_teeth_src(conf, fid, n))
    if r is None or r['mouth_x'] is None or n == TEETH_REF:   # the master: always the whole picture
        return 0, 0, Wp, Hp, Wp, Hp
    z = max(1.0, float(r['zoom'] or 1.0))
    cw, ch = int(round(Wp / z)), int(round(Hp / z))
    x0 = max(0, min(Wp - cw, int(round(r['mouth_x'] * Wp - cw / 2))))
    y0 = max(0, min(Hp - ch, int(round(r['mouth_y'] * Hp - ch / 2))))
    return x0, y0, x0 + cw, y0 + ch, Wp, Hp


def _teeth_run(job, files, args, fetch, conf, fid, n, folder='teeth', tool='teeth_tool.py'):
    """one job of the teeth or hair tool on the box: its files sent, it run, its pictures brought back into the film's folder -> (ok, its answer line)"""
    home = os.path.join(conf['films'], fid, folder)
    os.makedirs(home, exist_ok=True)
    _ssh_bytes(f'mkdir -p ~/{LOOK_DIR}/in ~/{LOOK_DIR}/out && cat > ~/{LOOK_DIR}/teeth_tool.py', TEETH_PROGRAM.encode())
    _ssh_bytes(f'cat > ~/{LOOK_DIR}/hair_tool.py', HAIR_PROGRAM.encode())
    _ssh_bytes(f'cat > ~/{LOOK_DIR}/color_tool.py', COLOR_PROGRAM.encode())
    _ssh_bytes(f'cat > ~/{LOOK_DIR}/move_tool.py', MOVE_PROGRAM.encode())
    for local, there in files:
        if isinstance(local, bytes):
            _ssh_bytes(f'cat > ~/{LOOK_DIR}/in/{there}', local)
        else:
            subprocess.run(['scp', '-q', '-o', 'BatchMode=yes', local, f'{BOX}:{LOOK_DIR}/in/{there}'], capture_output=True, timeout=300, check=True)
    said = _box([f'cd ~/{LOOK_DIR} && {SKIN_PY} {tool} {job} {args} 2>&1 | tail -40'], timeout=300).stdout.strip()
    ans = [ln for ln in said.splitlines() if ln.startswith(('mask ·', 'swapped ·', 'grill ·', 'auto ·', 'paste ·', 'graded ·', 'refused ·'))]   # its own words, never a library's
    last = ans[-1] if ans else (said.splitlines()[-1] if said else 'the box did not answer')
    if not last.startswith(('mask ·', 'swapped ·', 'grill ·', 'auto ·', 'paste ·', 'graded ·')):
        return False, last.removeprefix('refused · ')
    for there, local in fetch:
        subprocess.run(['scp', '-q', '-o', 'BatchMode=yes', f'{BOX}:{LOOK_DIR}/out/{there}', os.path.join(home, local)], capture_output=True, timeout=300, check=True)
    return True, last


def teeth_mask(con, conf, fid, n):
    """his marks made the slot's mask, and the close view drawn with it in green -> (ok, words)"""
    r = con.execute('SELECT * FROM teeth WHERE film = ? AND n = ?', (fid, n)).fetchone()
    x0, y0, x1, y1, _w, _h = _teeth_box(conf, fid, n, r)
    tag = f'teeth_{fid}_{n}'
    ok, said = _teeth_run('mask', [(_teeth_src(conf, fid, n), f'{tag}.png'), ((r['strokes'] or '[]').encode(), f'{tag}_strokes.json')],
                          f'in/{tag}.png in/{tag}_strokes.json {x0},{y0},{x1},{y1} out/{tag}_mask.png out/{tag}_view.png',
                          [(f'{tag}_mask.png', f'mask_{n}.png'), (f'{tag}_view.png', f'view_{n}.png')], conf, fid, n)
    if ok:
        con.execute('UPDATE teeth SET mask = ?, view = ? WHERE film = ? AND n = ?', (f'mask_{n}.png', f'view_{n}.png', fid, n))
    return ok, said


def teeth_grill(con, conf, fid):
    """the grill layer: the master cut by its own mask (teeth/grill.png, see-through round the teeth) and the master's light band kept in its row -> (ok, words)"""
    ref = con.execute('SELECT * FROM teeth WHERE film = ? AND n = ?', (fid, TEETH_REF)).fetchone()
    if ref is None or not json.loads(ref['strokes'] or '[]'):
        return False, f'the master (slot {TEETH_REF}) has no grill marked yet'
    ok, said = teeth_mask(con, conf, fid, TEETH_REF)
    if not ok:
        return False, said
    rt = f'teeth_{fid}_{TEETH_REF}'
    ok, said = _teeth_run('grill', [(_teeth_src(conf, fid, TEETH_REF), f'{rt}_ref.png'), (os.path.join(conf['films'], fid, 'teeth', f'mask_{TEETH_REF}.png'), f'{rt}_refmask.png')],
                          f'in/{rt}_ref.png in/{rt}_refmask.png out/{rt}_grill.png', [(f'{rt}_grill.png', 'grill.png')], conf, fid, TEETH_REF)
    if ok:
        con.execute('UPDATE teeth SET band = ? WHERE film = ? AND n = ?', (float(said.rsplit('band ', 1)[1]), fid, TEETH_REF))
    return ok, said


def teeth_swap(con, conf, fid, n):
    """the master's grill laid on the slot inside the slot's mask, at its sliders -> (ok, words); the picture outside the mask is never touched"""
    for m in (TEETH_REF, n):   # both masks drawn from the marks as they are now (the paint board saves marks only)
        if json.loads((con.execute('SELECT strokes FROM teeth WHERE film = ? AND n = ?', (fid, m)).fetchone() or [None])[0] or '[]'):
            ok_, said_ = teeth_mask(con, conf, fid, m)
            if not ok_:
                return False, f'the mask of slot {m} could not be drawn: {said_}'
    r = con.execute('SELECT * FROM teeth WHERE film = ? AND n = ?', (fid, n)).fetchone()
    ref = con.execute('SELECT * FROM teeth WHERE film = ? AND n = ?', (fid, TEETH_REF)).fetchone()
    home = os.path.join(conf['films'], fid, 'teeth')
    if not (ref is not None and json.loads(ref['strokes'] or '[]') and ref['mask'] and os.path.exists(os.path.join(home, ref['mask']))):
        return False, f'the master (slot {TEETH_REF}) has no grill marked yet · mark its teeth first'
    if not (r is not None and json.loads(r['strokes'] or '[]') and r['mask'] and os.path.exists(os.path.join(home, r['mask']))):
        return False, 'no teeth marked on this slot'
    params = {'match': r['match'] if r['match'] is not None else 60, 'light': r['light'] if r['light'] is not None else 0, 'edge': r['edge'] if r['edge'] is not None else 2,
              'layer': json.loads(r['layer']) if r['layer'] else None}   # the layer as he placed it; never placed: the box fits it to the slot's teeth
    tag, rt = f'teeth_{fid}_{n}', f'teeth_{fid}_{TEETH_REF}'
    ok, said = _teeth_run('swap', [(_teeth_src(conf, fid, n), f'{tag}.png'), (os.path.join(home, r['mask']), f'{tag}_mask.png'),
                                   (_teeth_src(conf, fid, TEETH_REF), f'{rt}_ref.png'), (os.path.join(home, ref['mask']), f'{rt}_refmask.png'),
                                   (json.dumps(params).encode(), f'{tag}_p.json')],
                          f'in/{tag}.png in/{tag}_mask.png in/{rt}_ref.png in/{rt}_refmask.png in/{tag}_p.json out/{tag}_out.png out/{tag}_oview.png',
                          [(f'{tag}_out.png', f'teeth_{n}.png'), (f'{tag}_oview.png', f'oview_{n}.png')], conf, fid, n)
    if not ok:
        con.execute("UPDATE teeth SET state = 'red', why = ? WHERE film = ? AND n = ?", (said, fid, n))
        return False, said
    said = said.removeprefix('swapped · ')
    con.execute("UPDATE teeth SET file = ?, oview = ?, state = 'tested', why = ?, made_at = ? WHERE film = ? AND n = ?",
                (f'teeth_{n}.png', f'oview_{n}.png', said + ' · not baked', _now(), fid, n))
    _keep(con, conf, fid, 'teeth_test', n, f'teeth/teeth_{n}.png', 'teeth', files=(f'teeth/mask_{n}.png', f'teeth/mask_{TEETH_REF}.png', 'teeth/grill.png'), also=(('teeth', TEETH_REF),))
    return True, said


def teeth_parts(con, f, conf):
    """PART 5 ON THE PAGE · TEETH: the master's board and SAVE MASKS, then each slot's board (MASK to paint its teeth, GRILL to lay the master's grill on it by
    hand and BAKE, RESULT to see it baked) with its status, then BAKE ALL"""
    fid = f['id']
    head = {'kind': 'step', 'n': 5, 'title': 'TEETH',
            'under': f'the grill of slot {TEETH_REF} on every slot, no AI · 1 paint the master\'s grill · 2 paint each slot\'s teeth (nothing painted: kept as it is) · '
                     '3 SAVE MASKS · 4 ⛶ BIG, GRILL: move, size, squish and turn the grill on the slot, BAKE · only the painted teeth change'}
    slots = [r['n'] for r in con.execute("SELECT n FROM skin WHERE film = ? AND state = 'baked' ORDER BY n", (fid,)) if os.path.exists(_teeth_src(conf, fid, r['n']))]
    if TEETH_REF not in slots:
        return [head, {'kind': 'note', 'title': '5 · waits for step 4', 'text': f'bake the skin first (slot {TEETH_REF} is the master grill)'}]
    tt = {r['n']: r for r in con.execute('SELECT * FROM teeth WHERE film = ?', (fid,))}
    home = os.path.join(conf['films'], fid, 'teeth')
    ref = tt.get(TEETH_REF)
    grill = _src(conf, f'{fid}/teeth', 'grill.png') if os.path.exists(os.path.join(home, 'grill.png')) else ''
    rows, master = [], []
    for n in [TEETH_REF] + [m for m in slots if m != TEETH_REF]:
        r = tt.get(n)
        st = r['state'] if r is not None else 'new'
        marks = [g for g in (json.loads(r['strokes'] or '[]') if r is not None else []) if g.get('m') in ('p', 'e')]   # the old clicks' WAND marks cannot be drawn on a board: not handed
        board = {'image': _src(conf, f'{fid}/skin', f'baked_{n}.png'), 'do': 'teethpaint', 'value': f'{fid}:{n}', 'kinds': ['brush', 'erase'], 'full': False, 'marks': []}
        if n == TEETH_REF:   # THE MASTER ON ITS OWN (the owner 2026-10-29: "the reference on the top should be in its own row no columns and only a brush, an eraser and a reset")
            master = [{'kind': 'marker', **board, 'width': 1600, 'paint': {'size': 0.008, 'strokes': marks},
                       'title': f'THE MASTER · slot {n} · paint the grill\'s teeth, erase what is not teeth · green = what every slot gets'},
                      {'kind': 'press', 'do': 'teethsave', 'value': f'{fid}:{n}', 'label': 'SAVE MASKS (every slot, and the grill layer)'}]
            continue
        # ONE PICTURE A SLOT, NO ZOOM (the owner 2026-10-29): MASK paints its teeth; GRILL lays the master's grill on it as a layer he moves, sizes, squishes and turns by
        # hand, seen inside the mask as it will bake (the PF REFERENCE MATCH stage); BAKE makes it; RESULT shows the baked picture
        done = r is not None and r['file'] and st in ('tested', 'baked') and os.path.exists(os.path.join(home, r['file']))
        board['paint'] = {'size': 0.004, 'strokes': marks, 'result': _src(conf, f'{fid}/teeth', r['file']) if done else '', 'result_url': f"{conf['films_url']}/{fid}/teeth/teeth_{n}.png",
                          'grill': grill, 'reference': _src(conf, f'{fid}/skin', f'baked_{TEETH_REF}.png'), 'band': ref['band'] if ref is not None and ref['band'] is not None else None,
                          'layer': json.loads(r['layer']) if r is not None and r['layer'] else None,
                          'tone': {'match': r['match'] if r is not None and r['match'] is not None else 60, 'light': r['light'] if r is not None and r['light'] is not None else 0,
                                   'edge': r['edge'] if r is not None and r['edge'] is not None else 2},
                          'show': 'result' if done and st == 'baked' else 'grill' if grill and marks else 'mask'}   # a painted slot opens on GRILL, the grill and its handles on it
        board['width'] = 1280
        board['title'] = f'SLOT {n}'
        status = ({'word': 'BAKED', 'text': r['why'] or ''} if st == 'baked' else {'word': 'TESTED', 'text': r['why'] or ''} if st == 'tested' else
                  {'word': 'RED', 'text': r['why'] or ''} if st == 'red' else {'word': 'PAINTED', 'text': f'{len(marks)} marks · ⛶ BIG, GRILL, place it, BAKE'} if marks else
                  {'word': 'NOT PAINTED', 'text': 'kept exactly as it is (a closed mouth) · or paint its teeth'})
        rows.append({'key': f'{fid}:{n}', 'wide': {'marker': board}, 'cells': [str(n), status]})
    return [head] + master + [{'kind': 'table', 'title': '5 · TEETH · each slot: MASK paints its teeth · GRILL places the grill · RESULT shows it baked · nothing painted: kept as it is',
                               'columns': ['Slot', 'Status'], 'rows': rows},
                              {'kind': 'press', 'do': 'teethbake', 'value': f'{fid}:{slots[0] if slots[0] != TEETH_REF else slots[-1]}:all', 'label': 'BAKE ALL (every slot as placed)'}]

# ============ PART 6 · HAIR (the owner 2026-10-29: "next is hair. teeth are done"; "research the hair color we made this before in larry 5 already / same thing as
# before"; "the hair use the original hair from the original reference"): the avatar's proven hair match (avatarskin/hair_norm.py, no AI) on the same paint board
# as the teeth: his hair painted on the reference picture (the master), each slot's hair painted (AUTO: the box's hair finder gives a first mask to clean up), BAKE
# matches the slot's hair to his strand by strand, nothing outside the mask moved
HAIR_REF_PIC = 'rumpel_5_head_full_hair.png'   # THE HAIR MASTER: his head with full hair, from his references (the owner may name another); its row is slot 0
HAIR_PROGRAM = """
# THE HAIR TOOL ON THE BOX (the CMO's own, beside amLLM): the avatar's proven hair match, used as it is (avatarskin/hair_norm.py, frost-b9 2026-10-03:
# "ONE avatar has one hair colour", no AI): the master's hair, measured inside ITS mask, is the reference; each slot's hair, inside ITS mask, keeps every strand's
# place from dark to light and takes the reference's brightness at that place and the reference's colour for that brightness (his base and his highlights).
#   auto <picture> <matte.png>   the lab's own hair selection (the owner 2026-10-29: "in the lab we had an automatic hair selection also that actually worked better
#        than the mask made by a human"): the box's MediaPipe hair segmenter (hair_norm.hair_weight), its SOFT matte kept as it is, green with the matte as its alpha
#   paste <picture> <fix.png> <mask.png> <out.png>   a cleanup fix laid again on a new picture from up the chain: the fix inside its mask, the new picture everywhere else
#   swap <picture> <matte.png|-> <strokes.json> <ref.png> <refmatte.png|-> <refstrokes.json> <params.json> <out.png> <view.png>   the hair: the matte, his brush
#        adding and his eraser taking away in the order he painted (as the page draws it); the slot's hair matched to the master's, nothing outside it moved
import json, os, sys
import cv2, numpy as np
from PIL import Image
sys.path.insert(0, os.path.expanduser('~/frost/virtual_workspace/avatarskin'))
import hair_norm as HN   # used as it is: hair_weight, reference_from_layers; and through it skin_norm's lab() and rgb_of()
S = HN.S


def rgb(p):
    return np.asarray(Image.open(p).convert('RGB'))


def bbox(m):
    ys, xs = np.nonzero(m)
    return xs.min(), ys.min(), xs.max() + 1, ys.max() + 1


def weight(img, matte_p, strokes_p):
    # the hair selection as the page shows it: the matte (or nothing), then each mark in order, a brush adds its disc, an eraser takes its disc away
    H, W = img.shape[:2]
    w = (np.asarray(Image.open(matte_p).convert('RGBA'))[..., 3].astype(np.float32) / 255) if matte_p != '-' else np.zeros((H, W), np.float32)
    if w.shape != (H, W):
        w = cv2.resize(w, (W, H), interpolation=cv2.INTER_LINEAR)
    for s in json.load(open(strokes_p)):
        d = np.zeros((H, W), np.uint8)
        cv2.circle(d, (int(round(s['x'] * W)), int(round(s['y'] * H))), max(1, int(round(s['r'] * W))), 1, -1)
        w = np.maximum(w, d) if s.get('m') != 'e' else w * (1 - d)
    return w


def feather(w0, edge):
    # EDGE (the owner 2026-10-29: "edge still does nothing"; a blur of thin hair only thins it out): the selection at full inside, and outside it a fade over EDGE px,
    # (1 - distance/EDGE) squared, the soft falloff the page draws the same way
    e = max(1.0, min(200.0, edge))
    d = cv2.distanceTransform((w0 <= 0.5).astype(np.uint8), cv2.DIST_L2, 3)
    return np.maximum(w0, np.clip(1 - d / e, 0, 1) ** 2)


job = sys.argv[1]
if job == 'paste':   # THE CHAIN CARRIES DOWN (the owner 2026-10-29: "if you click bake then go back up the chain and make a change then rebake it moves the change down the chain")
    img, fix = rgb(sys.argv[2]), rgb(sys.argv[3])
    m = np.asarray(Image.open(sys.argv[4]).convert('L')) > 127
    if fix.shape != img.shape or m.shape != img.shape[:2]:
        print('refused · the fix and the picture differ in size'); sys.exit(2)
    out = np.where(m[..., None], fix, img).astype(np.uint8)
    Image.fromarray(out).save(sys.argv[5])
    print('paste · the fix laid again on %d px · %d px from the new picture' % (int(m.sum()), int((~m).sum())))
    sys.stdout.flush(); os._exit(0)
elif job == 'auto':
    img = rgb(sys.argv[2])
    w = np.clip(HN.hair_weight(img), 0, 1)
    rgba = np.zeros(img.shape[:2] + (4,), np.uint8); rgba[..., 1] = 0xB1; rgba[..., 2] = 0x40; rgba[..., 3] = (w * 255).round().astype(np.uint8)   # the lab's green
    Image.fromarray(rgba, 'RGBA').save(sys.argv[3])
    print('auto · the finder says %.1f%% of the picture is hair' % (100 * (w > 0.5).mean()))
    sys.stdout.flush(); os._exit(0)   # the finder's library complains as it shuts down: its words never come after the answer
elif job == 'swap':
    img, ref = rgb(sys.argv[2]), rgb(sys.argv[5])
    w0, rw = weight(img, sys.argv[3], sys.argv[4]), weight(ref, sys.argv[6], sys.argv[7])
    p = {'strength': 100, 'edge': 0, 'light': 0, **json.load(open(sys.argv[8]))}
    H, W = img.shape[:2]
    if not (w0 > 0.02).any():
        print('refused · the slot has no hair selected'); sys.exit(2)
    R = HN.reference_from_layers([(ref, rw)])   # his hair inside its selection: its brightness, sorted, and its colour for each brightness
    if R is None:
        print('refused · the master has too little hair selected (AUTO or paint more of it)'); sys.exit(2)
    Lsorted, centers, ab = R
    m = w0 > 0.05
    L = S.lab(img)
    src = np.sort(L[..., 0][m])
    newL = np.interp(np.linspace(0, 1, len(src)), np.linspace(0, 1, len(Lsorted)), Lsorted)   # hair_norm.normalize's rank match, as a curve: his brightness at each place
    # THE REACH (the owner 2026-10-29: "the edge ... needs to feather the edge more or less"; "edge still does nothing"): every pixel within 200 px of the selection, the
    # most EDGE can feather out; inside it every pixel takes the same curve (its brightness to his), so a feather has colour to land; outside it nothing is ever touched
    reach = cv2.distanceTransform((w0 <= 0).astype(np.uint8), cv2.DIST_L2, 5) <= 200
    Lr = L[..., 0][reach]
    curve = np.interp(Lr, src, newL)
    o = L.copy()
    # COLOUR, THE SHOT'S OWN LIGHT (the skin's lesson, the owner 2026-10-29: "before we only took the color data not the actual image"): each pixel takes his colour for
    # its place from dark to light, and keeps the shot's brightness; LIGHT brings in that much of his brightness too
    o[..., 0][reach] = Lr + (curve - Lr) * max(0.0, min(1.0, p['light'] / 100.0))
    o[..., 1][reach] = np.interp(curve, centers, ab[:, 0]); o[..., 2][reach] = np.interp(curve, centers, ab[:, 1])
    if p.get('pure'):   # A PREVIEW LAYER: his colour over the whole reach at full strength; the page lays it through the feathered selection itself
        w = reach.astype(np.float32)
    else:
        w = np.clip(w0 if float(p['edge']) <= 0 else feather(w0, float(p['edge'])), 0, 1) * reach * max(0.0, min(1.0, p['strength'] / 100.0))   # STRENGTH: how far to go
    res = S.rgb_of(L * (1 - w[..., None]) + o * w[..., None])
    sel = w > 0
    out = np.where(sel[..., None], res, img).astype(np.uint8)   # every pixel outside the feathered selection is the picture's own, by construction
    moved = int((out[~sel] != img[~sel]).any(axis=1).sum())
    Image.fromarray(out).save(sys.argv[9])
    x0, y0, x1, y1 = bbox(w0 > 0.05)
    vw = min(W, max(320, int(1.4 * (x1 - x0)))); vh = min(H, int(round(vw * 9 / 16)))
    vx = max(0, min(W - vw, (x0 + x1) // 2 - vw // 2)); vy = max(0, min(H - vh, (y0 + y1) // 2 - vh // 2))
    Image.fromarray(cv2.resize(out[vy:vy + vh, vx:vx + vw], (1280, int(round(1280 * vh / vw))), interpolation=cv2.INTER_AREA)).save(sys.argv[10])
    Image.fromarray((sel * 255).astype(np.uint8)).save(sys.argv[9][:-4] + '_sel.png')   # where it was allowed to change: for the own check
    print('swapped · his hair colour on %d px at %d%%, his light %d%%, edge %d px · outside the selection: %d pixels changed' % (int(m.sum()), round(p['strength']), round(p['light']), round(float(p['edge'])), moved))
"""


def _hair_src(conf, fid, n):
    """the picture this step works on: slot 0 the reference; a slot its teeth bake (step 5), else its skin bake (step 4)"""
    if n == 0:
        return os.path.join(conf['references'], HAIR_REF_PIC)
    t = os.path.join(conf['films'], fid, 'teeth', f'baked_{n}.png')
    return t if os.path.exists(t) else _teeth_src(conf, fid, n)


def _hair_url(conf, fid, n):
    p = _hair_src(conf, fid, n)
    if n == 0:
        return f"{conf['scratch_url']}/{os.path.relpath(p, SCRATCH)}?v={int(os.path.getmtime(p))}" if os.path.exists(p) else ''
    return _src(conf, f"{fid}/{os.path.basename(os.path.dirname(p))}", os.path.basename(p))


def hair_mask(con, conf, fid, n):
    """his marks drawn into the picture's hair mask on the box (the teeth tool's mask job, the same brush) -> (ok, words)"""
    r = con.execute('SELECT * FROM hair WHERE film = ? AND n = ?', (fid, n)).fetchone()
    Wp, Hp = _png_size(_hair_src(conf, fid, n))
    tag = f'hair_{fid}_{n}'
    ok, said = _teeth_run('mask', [(_hair_src(conf, fid, n), f'{tag}.png'), ((r['strokes'] or '[]').encode(), f'{tag}_strokes.json')],
                          f'in/{tag}.png in/{tag}_strokes.json 0,0,{Wp},{Hp} out/{tag}_mask.png out/{tag}_view.png', [(f'{tag}_mask.png', f'mask_{n}.png')], conf, fid, n, 'hair')
    if ok:
        con.execute('UPDATE hair SET mask = ? WHERE film = ? AND n = ?', (f'mask_{n}.png', fid, n))
    return ok, said


def hair_auto(con, conf, fid, n):
    """the lab's own hair selection (the owner 2026-10-29: "in the lab we had an automatic hair selection also that actually worked better than the mask made by a
    human"): the box's hair segmenter's SOFT matte, kept as it is (hair/matte_N.png); his marks stay on top of it, a brush adding and an eraser taking away -> (ok, words)"""
    tag = f'hair_{fid}_{n}'
    ok, said = _teeth_run('auto', [(_hair_src(conf, fid, n), f'{tag}.png')], f'in/{tag}.png out/{tag}_matte.png', [(f'{tag}_matte.png', f'matte_{n}.png')], conf, fid, n, 'hair', 'hair_tool.py')
    if not ok:
        return False, said
    con.execute("UPDATE hair SET matte = ?, state = 'masked', why = '' WHERE film = ? AND n = ?", (f'matte_{n}.png', fid, n))
    return True, said.removeprefix('auto · ')


def _hair_sel(r):
    """-> whether this row holds any hair selection: the finder's matte or his marks"""
    return r is not None and (bool(r['matte']) or bool(json.loads(r['strokes'] or '[]')))


def hair_swap(con, conf, fid, n, params=None, out=None):
    """the slot's hair given his colour inside its selection (the matte, then his marks in order) -> (ok, words); nothing outside the selection moved.
    params and out given: a PREVIEW layer at those numbers into that file, the row's result untouched"""
    r = con.execute('SELECT * FROM hair WHERE film = ? AND n = ?', (fid, n)).fetchone()
    ref = con.execute('SELECT * FROM hair WHERE film = ? AND n = 0', (fid,)).fetchone()
    home = os.path.join(conf['films'], fid, 'hair')
    if not _hair_sel(ref):
        return False, 'the master has no hair selected yet · AUTO or paint his hair on it first'
    if not _hair_sel(r):
        return False, 'no hair selected on this slot'
    params = params or {'strength': r['strength'] if r['strength'] is not None else 100, 'edge': r['edge'] if r['edge'] is not None else 0, 'light': r['light'] if r['light'] is not None else 0}
    tag, rt = f'hair_{fid}_{n}', f'hair_{fid}_0'
    files = [(_hair_src(conf, fid, n), f'{tag}.png'), ((r['strokes'] or '[]').encode(), f'{tag}_strokes.json'), (_hair_src(conf, fid, 0), f'{rt}_ref.png'),
             ((ref['strokes'] or '[]').encode(), f'{rt}_strokes.json'), (json.dumps(params).encode(), f'{tag}_p.json')]
    for row_, t_ in ((r, tag), (ref, rt)):
        if row_['matte']:
            files.append((os.path.join(home, row_['matte']), f'{t_}_matte.png'))
    mt = lambda row_, t_: f'in/{t_}_matte.png' if row_['matte'] else '-'   # noqa: E731
    ok, said = _teeth_run('swap', files, f'in/{tag}.png {mt(r, tag)} in/{tag}_strokes.json in/{rt}_ref.png {mt(ref, rt)} in/{rt}_strokes.json in/{tag}_p.json out/{tag}_out.png out/{tag}_oview.png',
                          [(f'{tag}_out.png', out or f'hair_{n}.png')] + ([] if out else [(f'{tag}_oview.png', f'oview_{n}.png'), (f'{tag}_out_sel.png', f'sel_{n}.png')]),
                          conf, fid, n, 'hair', 'hair_tool.py')
    if out:
        return ok, said
    if not ok:
        con.execute("UPDATE hair SET state = 'red', why = ? WHERE film = ? AND n = ?", (said, fid, n))
        return False, said
    said = said.removeprefix('swapped · ')
    con.execute("UPDATE hair SET file = ?, oview = ?, state = 'tested', why = ?, made_at = ? WHERE film = ? AND n = ?",
                (f'hair_{n}.png', f'oview_{n}.png', said + ' · not baked', _now(), fid, n))
    _keep(con, conf, fid, 'hair_test', n, f'hair/hair_{n}.png', 'hair', files=(f'hair/mask_{n}.png', f'hair/matte_{n}.png', 'hair/mask_0.png', 'hair/matte_0.png'), also=(('hair', 0),))
    return True, said


def hair_press(store, do, one, conf):
    """PART 6's presses: PAINT (his marks, in the background), AUTO (the finder's first mask), BAKE (one slot or every slot), SAVE MASKS"""
    con = _db(store)
    try:
        fid, _, rest = one('value').partition(':')
        n_, _, act = rest.partition(':')
        if not _film(con, fid):
            return f'HAIR refused · no project {fid}'
        try:
            n = int(n_)
        except ValueError:
            return 'HAIR refused · no slot'
        if not os.path.exists(_hair_src(conf, fid, n)):
            return f'HAIR refused · {"the master picture " + HAIR_REF_PIC + " is missing" if n == 0 else f"slot {n} has no baked picture yet (steps 4 and 5)"}'
        con.execute('INSERT OR IGNORE INTO hair (film, n, state, made_at) VALUES (?, ?, ?, ?)', (fid, n, 'new', _now()))
        r = con.execute('SELECT * FROM hair WHERE film = ? AND n = ?', (fid, n)).fetchone()
        if do == 'hairpaint':
            try:
                got, at_ = json.loads(one('path') or '[]'), float(one('at') or 0)
                strokes = [{'x': round(max(0.0, min(1.0, float(g['x']))), 5), 'y': round(max(0.0, min(1.0, float(g['y']))), 5), 'm': 'e' if g.get('m') == 'e' else 'p',
                            'tol': 0, 'r': round(max(0.0005, min(0.1, float(g['r']))), 5)} for g in got][:20000]
            except (ValueError, TypeError, KeyError, AttributeError):
                return 'PAINT refused · the marks are not readable'
            if r['paint_at'] is not None and at_ < r['paint_at']:
                return f'PAINT · {fid} slot {n} · an older send, the newer marks kept'
            con.execute('UPDATE hair SET strokes = ?, paint_at = ?, state = ?, why = ? WHERE film = ? AND n = ?', (json.dumps(strokes), at_, 'masked' if strokes else 'new', '', fid, n))
            con.commit()
            return f'PAINT · {fid} slot {n} · {len(strokes)} marks'
        if do == 'hairauto':
            ok_, said_ = hair_auto(con, conf, fid, n)
            con.commit()
            return f'AUTO · {fid} slot {n} · ' + (said_ if ok_ else f'not made: {said_}')
        if do == 'hairpreview':   # THE PREVIEW (the owner 2026-10-29: "it should show the resutl to fine tune before then when perfect bake / you can bake once before just to get
            # the overlay"): two full layers, his colour at the shot's own light and with all his light; the page mixes them live as HIS LIGHT and STRENGTH move
            if n == 0:
                return 'PREVIEW refused · the master is the hair every slot gets'
            for light_, name_ in ((0, f'tune0_{n}.png'), (100, f'tune100_{n}.png')):
                ok_, said_ = hair_swap(con, conf, fid, n, {'strength': 100, 'edge': 0, 'light': light_, 'pure': 1}, name_)   # his colour over the reach: the page feathers it
                if not ok_:
                    return f'PREVIEW · {fid} slot {n} · not made: {said_}'
            return f'PREVIEW · {fid} slot {n} · tune it live, then BAKE'
        if do == 'hairsave':
            rows_ = con.execute("SELECT n FROM hair WHERE film = ? AND strokes IS NOT NULL AND strokes != '[]' ORDER BY n", (fid,)).fetchall()
            saved_, why_ = [], []
            for (m,) in rows_:
                ok_, said_ = hair_mask(con, conf, fid, m)
                con.commit()
                (saved_ if ok_ else why_).append(('the master' if m == 0 else f'{m}') if ok_ else f'{m}: {said_}')   # his marks as a mask picture (the matte is one already)
            return f"SAVED MASKS · {fid} · hair of {', '.join(saved_) or 'none'}" + (f" · not saved: {'; '.join(why_)}" if why_ else '')
        if n == 0:
            return 'BAKE refused · the master is the hair every slot gets: bake a slot'
        for k_, lo_, hi_ in (('strength', 0, 100), ('edge', 0, 200), ('light', 0, 100)):   # BAKE: its numbers as the board sends them
            if one(k_) != '':
                try:
                    con.execute(f'UPDATE hair SET {k_} = ? WHERE film = ? AND n = ?', (round(max(lo_, min(hi_, float(one(k_)))), 1), fid, n))
                except ValueError:
                    return 'BAKE refused · the numbers are not numbers'
        con.commit()
        home = os.path.join(conf['films'], fid, 'hair')
        os.makedirs(home, exist_ok=True)
        baked_, kept_, why_ = [], [], []
        for (m,) in con.execute("SELECT n FROM skin WHERE film = ? AND state = 'baked' ORDER BY n", (fid,)).fetchall():
            if act == 'one' and m != n:
                continue
            if not os.path.exists(_hair_src(conf, fid, m)):
                continue
            con.execute('INSERT OR IGNORE INTO hair (film, n, state, made_at) VALUES (?, ?, ?, ?)', (fid, m, 'new', _now()))
            rm_ = con.execute('SELECT * FROM hair WHERE film = ? AND n = ?', (fid, m)).fetchone()
            if _hair_sel(rm_):
                ok_, said_ = hair_swap(con, conf, fid, m)
                if not ok_:
                    why_.append(f'{m}: {said_}')
                    continue
                shutil.copyfile(os.path.join(home, f'hair_{m}.png'), os.path.join(home, f'baked_{m}.png'))
                con.execute("UPDATE hair SET baked = ?, state = 'baked', why = ? WHERE film = ? AND n = ?", (f'baked_{m}.png', said_, fid, m))
                _keep(con, conf, fid, 'hair', m, f'hair/baked_{m}.png', 'hair', files=(f'hair/mask_{m}.png', f'hair/matte_{m}.png', 'hair/mask_0.png', 'hair/matte_0.png'), also=(('hair', 0),))
                baked_.append(str(m))
            else:
                shutil.copyfile(_hair_src(conf, fid, m), os.path.join(home, f'baked_{m}.png'))
                con.execute("UPDATE hair SET baked = ?, state = 'baked', why = ? WHERE film = ? AND n = ?", (f'baked_{m}.png', 'no hair painted: kept exactly as it is', fid, m))
                _keep(con, conf, fid, 'hair', m, f'hair/baked_{m}.png', 'hair', extra={'kept': 'as it is', 'source': os.path.relpath(_hair_src(conf, fid, m), os.path.join(conf['films'], fid))})
                kept_.append(str(m))
            con.commit()
        carried_ = carry_down(con, conf, fid, [int(x) for x in baked_ + kept_], 'hair')
        return (f"{'BAKED' if act == 'one' else 'BAKED ALL'} · {fid} · his hair matched on slots {', '.join(baked_) or 'none'}" + (f" · kept as they are: {', '.join(kept_)}" if kept_ else '')
                + (f" · not baked: {'; '.join(why_)}" if why_ else '') + carried_)
    finally:
        con.close()


def hair_parts(con, f, conf):
    """PART 6 ON THE PAGE · HAIR: the master's board (his reference picture: paint his hair, AUTO), SAVE MASKS, then each slot's board (MASK: paint or AUTO, STRENGTH,
    EDGE, BAKE; RESULT) with his hair in its corner, then BAKE ALL"""
    fid = f['id']
    head = {'kind': 'step', 'n': 6, 'title': 'HAIR',
            'under': f'his own hair ({HAIR_REF_PIC}) on every slot, no AI (the avatar\'s hair match) · 1 paint his hair on the master (AUTO gives a first mask) · 2 paint each slot\'s hair · '
                     '3 BAKE · each strand keeps its place from dark to light and takes his colour · only the painted hair changes'}
    slots = [r['n'] for r in con.execute("SELECT n FROM skin WHERE film = ? AND state = 'baked' ORDER BY n", (fid,)) if os.path.exists(_hair_src(conf, fid, r['n']))]
    if not slots:
        return [head, {'kind': 'note', 'title': '6 · waits for steps 4 and 5', 'text': 'bake the skin and the teeth first'}]
    if not os.path.exists(_hair_src(conf, fid, 0)):
        return [head, {'kind': 'note', 'title': '6 · its master is missing', 'text': f'{HAIR_REF_PIC} is not in {conf["references"]}'}]
    hh = {r['n']: r for r in con.execute('SELECT * FROM hair WHERE film = ?', (fid,))}
    home = os.path.join(conf['films'], fid, 'hair')
    r0 = hh.get(0)
    master = [{'kind': 'marker', 'image': _hair_url(conf, fid, 0), 'do': 'hairpaint', 'value': f'{fid}:0', 'kinds': ['brush', 'erase'], 'full': False, 'marks': [], 'width': 900,
               'paint': {'size': 0.012, 'strokes': json.loads(r0['strokes'] or '[]') if r0 is not None else [], 'auto': 'hairauto',
                         'matte': _src(conf, f'{fid}/hair', r0['matte']) if r0 is not None and r0['matte'] else ''},
               'title': f'THE HAIR MASTER · {HAIR_REF_PIC} · paint his hair (AUTO gives a first mask), erase what is not hair · green = the hair every slot gets'},
              {'kind': 'press', 'do': 'hairsave', 'value': f'{fid}:0', 'label': 'SAVE MASKS (his hair and every slot\'s)'}]
    rows = []
    for n in slots:
        r = hh.get(n)
        st = r['state'] if r is not None else 'new'
        marks = json.loads(r['strokes'] or '[]') if r is not None else []
        done = r is not None and r['file'] and st in ('tested', 'baked') and os.path.exists(os.path.join(home, r['file']))
        board = {'image': _hair_url(conf, fid, n), 'do': 'hairpaint', 'value': f'{fid}:{n}', 'kinds': ['brush', 'erase'], 'full': False, 'marks': [], 'width': 1280, 'title': f'SLOT {n}',
                 'paint': {'size': 0.012, 'strokes': marks, 'auto': 'hairauto', 'matte': _src(conf, f'{fid}/hair', r['matte']) if r is not None and r['matte'] else '', 'result': _src(conf, f'{fid}/hair', r['file']) if done else '',
                           'result_url': f"{conf['films_url']}/{fid}/hair/hair_{n}.png", 'reference': _hair_url(conf, fid, 0),
                           'bake': {'do': 'hairbake', 'sliders': [{'name': 'strength', 'label': 'STRENGTH', 'min': 0, 'max': 100, 'value': r['strength'] if r is not None and r['strength'] is not None else 100, 'unit': '%'},
                                                                  {'name': 'light', 'label': 'HIS LIGHT', 'min': 0, 'max': 100, 'value': r['light'] if r is not None and r['light'] is not None else 0, 'unit': '%'},
                                                                  {'name': 'edge', 'label': 'EDGE', 'min': 0, 'max': 200, 'value': r['edge'] if r is not None and r['edge'] is not None else 0, 'unit': 'px'}]},
                           'tune': {'a': f"{conf['films_url']}/{fid}/hair/tune0_{n}.png", 'b': f"{conf['films_url']}/{fid}/hair/tune100_{n}.png", 'by': 'light', 'amount': 'strength', 'feather': 'edge',
                                    'do': 'hairpreview', 'made': os.path.exists(os.path.join(home, f'tune0_{n}.png')) and os.path.exists(os.path.join(home, f'tune100_{n}.png'))},
                           'show': 'result' if done and st == 'baked' else 'mask'}}
        status = ({'word': 'BAKED', 'text': r['why'] or ''} if st == 'baked' else {'word': 'RED', 'text': r['why'] or ''} if st == 'red' else
                  {'word': 'SELECTED', 'text': ('the finder\'s matte' + (f' + {len(marks)} marks' if marks else '') if r['matte'] else f'{len(marks)} marks') + ' · BAKE'} if _hair_sel(r) else
                  {'word': 'NOT SELECTED', 'text': 'kept exactly as it is · or AUTO / paint its hair'})
        rows.append({'key': f'{fid}:{n}', 'wide': {'marker': board}, 'cells': [str(n), status]})
    return [head] + master + [{'kind': 'table', 'title': '6 · HAIR · each slot: paint its hair (AUTO for a first mask), BAKE · nothing painted: kept as it is',
                               'columns': ['Slot', 'Status'], 'rows': rows},
                              {'kind': 'press', 'do': 'hairbake', 'value': f'{fid}:{slots[0]}:all', 'label': 'BAKE ALL (every slot\'s hair)'}]


# ============ PART 7 · CLEANUP (the owner 2026-10-29: "a cleanup and its a preview ... with a direct claude code edit. so you actually do the work instead of the UI /
# where i just ask you to fix these final ones manually and the preview is an accept or reject / we dont know what issues each will have in the future so this is just a
# generic preview"): he names a fix in the chat, Claude Code makes it by hand from the slot's latest picture and lays it here as a PROPOSAL with what was done; the page
# shows it BEFORE and AFTER; ACCEPT makes it the slot's final picture (cleanup/baked_N.png), REJECT keeps the picture as it was. Nothing here makes a picture by itself.
def _clean_src(conf, fid, n):
    """the slot's latest picture: its hair bake (step 6), else its teeth bake (step 5), else its skin bake (step 4)"""
    for d in ('hair', 'teeth', 'skin'):
        p = os.path.join(conf['films'], fid, d, f'baked_{n}.png')
        if os.path.exists(p):
            return p
    return ''


def clean_propose(con, conf, fid, n, picture, note, reference=None, mask=None):
    """CLAUDE CODE'S HAND: a fixed picture laid as slot n's proposal (copied in, never moved), with the words of what was done, and (the owner 2026-10-29: "a generic
    show hide preview on each that you can populate and a button to show or hide the reference / like if we work on tattoos you load whatever we are working on") a
    reference picture of what it should look like, shown in the board's corner -> the proposal's file name"""
    src = _clean_src(conf, fid, n)
    if not src:
        raise ValueError(f'slot {n} has no baked picture yet')
    home = os.path.join(conf['films'], fid, 'cleanup')
    os.makedirs(home, exist_ok=True)
    name = f'proposed_{n}_{datetime.datetime.now().strftime("%H%M%S")}.png'
    shutil.copyfile(picture, os.path.join(home, name))
    shutil.copyfile(src, os.path.join(home, f'before_{n}.png'))   # what it was made from, kept beside it for BEFORE
    fm = None
    if mask:   # where the fix changed the picture: laid again inside it when the chain above is made again
        fm = f'fixmask_{n}.png'
        shutil.copyfile(mask, os.path.join(home, fm))
    ref = None
    if reference:
        ref = f'ref_{n}{os.path.splitext(reference)[1].lower() or ".png"}'
        shutil.copyfile(reference, os.path.join(home, ref))
    con.execute('INSERT INTO cleanup (film, n, proposed, source, note, state, made_at, reference, fixmask) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?) ON CONFLICT(film, n) DO UPDATE SET '
                'proposed = excluded.proposed, source = excluded.source, note = excluded.note, state = excluded.state, made_at = excluded.made_at, decided_at = NULL, '
                'reference = excluded.reference, fixmask = excluded.fixmask', (fid, n, name, os.path.relpath(src, os.path.join(conf['films'], fid)), note, 'proposed', _now(), ref, fm))
    con.commit()
    return name





def clean_press(store, do, one, conf):
    """BAKE ALL (the owner 2026-10-29: "i dont think we need an accept or reject just show all 8 then 1 button to bake all ... its basically saying make these the new
    official"): every slot's final picture made: Claude Code's fix where there is one, else the slot's latest picture as it is (cleanup/baked_N.png)"""
    con = _db(store)
    try:
        fid = one('value').partition(':')[0]
        if not _film(con, fid):
            return f'BAKE refused · no project {fid}'
        home = os.path.join(conf['films'], fid, 'cleanup')
        os.makedirs(home, exist_ok=True)
        fixes = {r['n']: r for r in con.execute('SELECT * FROM cleanup WHERE film = ? AND proposed IS NOT NULL', (fid,))}
        fixed_, kept_ = [], []
        for (n,) in con.execute("SELECT n FROM skin WHERE film = ? AND state = 'baked' ORDER BY n", (fid,)).fetchall():
            src = _clean_src(conf, fid, n)
            if not src:
                continue
            r = fixes.get(n)
            if r is not None and os.path.exists(os.path.join(home, r['proposed'])):
                shutil.copyfile(os.path.join(home, r['proposed']), os.path.join(home, f'baked_{n}.png'))
                con.execute("UPDATE cleanup SET state = 'baked', decided_at = ? WHERE film = ? AND n = ?", (_now(), fid, n))
                _keep(con, conf, fid, 'cleanup', n, f'cleanup/baked_{n}.png', 'cleanup', files=tuple(f'cleanup/{x}' for x in (r['proposed'], r['fixmask'], r['reference']) if x))
                fixed_.append(str(n))
            else:
                shutil.copyfile(src, os.path.join(home, f'baked_{n}.png'))
                _keep(con, conf, fid, 'cleanup', n, f'cleanup/baked_{n}.png', extra={'kept': 'as it is', 'source': os.path.relpath(src, os.path.join(conf['films'], fid))})
                kept_.append(str(n))
        con.commit()
        carried_ = carry_down(con, conf, fid, [int(x) for x in fixed_ + kept_], 'cleanup')
        return (f"BAKED ALL · {fid} · the new official pictures · Claude Code's fix on slots {', '.join(fixed_) or 'none'}"
                + (f" · as they were: {', '.join(kept_)}" if kept_ else '') + carried_)
    finally:
        con.close()


def clean_parts(con, f, conf):
    """PART 7 ON THE PAGE · CLEANUP: all 8 slots, big: Claude Code's fix (BEFORE and AFTER) where there is one, else the slot's latest picture; one BAKE ALL"""
    fid = f['id']
    head = {'kind': 'step', 'n': 7, 'title': 'CLEANUP',
            'under': 'the last fixes, made by hand by Claude Code when you ask in the chat · every slot shown, BEFORE and AFTER where there is a fix · BAKE ALL makes all 8 the new official pictures'}
    slots = [r['n'] for r in con.execute("SELECT n FROM skin WHERE film = ? AND state = 'baked' ORDER BY n", (fid,)) if _clean_src(conf, fid, r['n'])]
    if not slots:
        return [head, {'kind': 'note', 'title': '7 · waits for the bakes', 'text': 'bake the slots first'}]
    fixes = {r['n']: r for r in con.execute('SELECT * FROM cleanup WHERE film = ? AND proposed IS NOT NULL', (fid,))}
    home = os.path.join(conf['films'], fid, 'cleanup')
    rows = []
    for n in slots:
        r = fixes.get(n)
        src = _clean_src(conf, fid, n)
        fixed = r is not None and os.path.exists(os.path.join(home, r['proposed']))
        before = _src(conf, f'{fid}/cleanup', f'before_{n}.png') if fixed else _src(conf, f"{fid}/{os.path.basename(os.path.dirname(src))}", os.path.basename(src))
        board = {'image': before, 'do': 'cleanbake', 'value': f'{fid}:{n}', 'kinds': [], 'full': False, 'marks': [], 'width': 1280, 'title': f'SLOT {n}',
                 'paint': {'view': True, 'strokes': [], 'result': _src(conf, f'{fid}/cleanup', r['proposed']) if fixed else '',
                           'result_url': f"{conf['films_url']}/{fid}/cleanup/{r['proposed']}" if fixed else '', 'show': 'result' if fixed else 'mask',
                           'reference': _src(conf, f'{fid}/cleanup', r['reference']) if fixed and r['reference'] else ''}}
        done = os.path.exists(os.path.join(home, f'baked_{n}.png')) and (r is None or r['state'] == 'baked')
        status = ({'word': 'FIXED' + (' · BAKED' if done else ''), 'text': f"{r['note']} · from {r['source']}"} if fixed else
                  {'word': 'AS IT IS' + (' · BAKED' if done else ''), 'text': f"no fix · {os.path.relpath(src, os.path.join(conf['films'], fid))}"})
        rows.append({'key': f'{fid}:{n}', 'wide': {'marker': board}, 'cells': [str(n), status]})
    return [head, {'kind': 'table', 'title': '7 · CLEANUP · all 8 · AFTER is Claude Code\'s fix, BEFORE the slot as it was', 'columns': ['Slot', 'What was done'], 'rows': rows},
            {'kind': 'press', 'do': 'cleanbake', 'value': f'{fid}:0', 'label': 'BAKE ALL (make these the new official pictures)'}]


# ============ THE CHAIN CARRIES DOWN (the owner 2026-10-29: "make sure if you click bake then go back up the chain and make a change then rebake it moves the change down
# the chain so the last has all the changes up"): SKIN -> TEETH -> HAIR -> CLEANUP; a bake made again up the chain makes again, for that slot, every step below it that the
# slot has reached, each at its own saved settings (the grill as placed, the hair as selected and tuned, Claude Code's fix laid again inside its own mask). A step the slot
# never reached is left alone. The teeth master's skin made again: every slot's teeth are made again, its grill being theirs.
def _rebake_teeth(con, conf, fid, n):
    home = os.path.join(conf['films'], fid, 'teeth')
    if not os.path.exists(os.path.join(home, f'baked_{n}.png')):
        return None
    r = con.execute('SELECT * FROM teeth WHERE film = ? AND n = ?', (fid, n)).fetchone()
    if n != TEETH_REF and r is not None and json.loads(r['strokes'] or '[]'):
        ok, said = teeth_swap(con, conf, fid, n)
        if not ok:
            return f'teeth {n} not made again: {said}'
        shutil.copyfile(os.path.join(home, f'teeth_{n}.png'), os.path.join(home, f'baked_{n}.png'))
        con.execute("UPDATE teeth SET baked = ?, state = 'baked', why = ? WHERE film = ? AND n = ?", (f'baked_{n}.png', said, fid, n))
        _keep(con, conf, fid, 'teeth', n, f'teeth/baked_{n}.png', 'teeth', files=(f'teeth/mask_{n}.png', f'teeth/mask_{TEETH_REF}.png', 'teeth/grill.png'), also=(('teeth', TEETH_REF),), extra={'by': 'carried down the chain'})
    else:
        shutil.copyfile(_teeth_src(conf, fid, n), os.path.join(home, f'baked_{n}.png'))
        _keep(con, conf, fid, 'teeth', n, f'teeth/baked_{n}.png', 'teeth', extra={'kept': 'as it is', 'by': 'carried down the chain', 'source': os.path.relpath(_teeth_src(conf, fid, n), os.path.join(conf['films'], fid))})
    con.commit()
    return 'teeth'


def _rebake_hair(con, conf, fid, n):
    home = os.path.join(conf['films'], fid, 'hair')
    if not os.path.exists(os.path.join(home, f'baked_{n}.png')):
        return None
    r = con.execute('SELECT * FROM hair WHERE film = ? AND n = ?', (fid, n)).fetchone()
    if r is not None and _hair_sel(r):
        ok, said = hair_swap(con, conf, fid, n)
        if not ok:
            return f'hair {n} not made again: {said}'
        shutil.copyfile(os.path.join(home, f'hair_{n}.png'), os.path.join(home, f'baked_{n}.png'))
        con.execute("UPDATE hair SET baked = ?, state = 'baked', why = ? WHERE film = ? AND n = ?", (f'baked_{n}.png', said, fid, n))
        _keep(con, conf, fid, 'hair', n, f'hair/baked_{n}.png', 'hair', files=(f'hair/mask_{n}.png', f'hair/matte_{n}.png', 'hair/mask_0.png', 'hair/matte_0.png'), also=(('hair', 0),), extra={'by': 'carried down the chain'})
    else:
        shutil.copyfile(_hair_src(conf, fid, n), os.path.join(home, f'baked_{n}.png'))
        _keep(con, conf, fid, 'hair', n, f'hair/baked_{n}.png', 'hair', extra={'kept': 'as it is', 'by': 'carried down the chain', 'source': os.path.relpath(_hair_src(conf, fid, n), os.path.join(conf['films'], fid))})
    con.commit()
    return 'hair'


def _rebake_clean(con, conf, fid, n):
    home = os.path.join(conf['films'], fid, 'cleanup')
    r = con.execute('SELECT * FROM cleanup WHERE film = ? AND n = ?', (fid, n)).fetchone()
    fixed = r is not None and r['proposed'] and os.path.exists(os.path.join(home, r['proposed']))
    baked = os.path.exists(os.path.join(home, f'baked_{n}.png'))
    if not (fixed or baked):
        return None
    src = _clean_src(conf, fid, n)
    if fixed:
        if not (r['fixmask'] and os.path.exists(os.path.join(home, r['fixmask']))):
            return f'cleanup {n}: its fix holds no mask, ask Claude Code to make it again on the new picture'
        tag = f'clean_{fid}_{n}'
        name = f'proposed_{n}_{datetime.datetime.now().strftime("%H%M%S")}.png'
        ok, said = _teeth_run('paste', [(src, f'{tag}.png'), (os.path.join(home, r['proposed']), f'{tag}_fix.png'), (os.path.join(home, r['fixmask']), f'{tag}_mask.png')],
                              f'in/{tag}.png in/{tag}_fix.png in/{tag}_mask.png out/{tag}_out.png', [(f'{tag}_out.png', name)], conf, fid, n, 'cleanup', 'hair_tool.py')
        if not ok:
            return f'cleanup {n} not made again: {said}'
        shutil.copyfile(src, os.path.join(home, f'before_{n}.png'))
        con.execute('UPDATE cleanup SET proposed = ?, source = ? WHERE film = ? AND n = ?', (name, os.path.relpath(src, os.path.join(conf['films'], fid)), fid, n))
        _keep(con, conf, fid, 'cleanup_fix', n, f'cleanup/{name}', 'cleanup', files=tuple(f'cleanup/{x}' for x in (name, r['fixmask']) if x), extra={'by': 'carried down the chain: the fix laid again inside its mask'})
        if baked:
            shutil.copyfile(os.path.join(home, name), os.path.join(home, f'baked_{n}.png'))
    elif baked:
        shutil.copyfile(src, os.path.join(home, f'baked_{n}.png'))
        _keep(con, conf, fid, 'cleanup', n, f'cleanup/baked_{n}.png', 'cleanup', extra={'kept': 'as it is', 'by': 'carried down the chain', 'source': os.path.relpath(src, os.path.join(conf['films'], fid))})
    con.commit()
    return 'cleanup'


def _rebake_color(con, conf, fid, n):
    r = con.execute('SELECT * FROM color WHERE film = ? AND n = ?', (fid, n)).fetchone()
    home = os.path.join(conf['films'], fid, 'color')
    if r is None or r['state'] != 'baked' or not os.path.exists(os.path.join(home, f'baked_{n}.png')):
        return None
    ok, said = color_grade(conf, fid, n, r['strength'], r['light'], f'color_{n}.png', r)
    if not ok:
        return f'color {n} not made again: {said}'
    shutil.copyfile(os.path.join(home, f'color_{n}.png'), os.path.join(home, f'baked_{n}.png'))
    for lt in (0, 100):   # its TUNE layers made again from the new picture too
        color_grade(conf, fid, n, 100, lt, f'tune{lt}_{n}.png')
    con.execute("UPDATE color SET why = ?, made_at = ? WHERE film = ? AND n = ?", (said.removeprefix('graded · '), _now(), fid, n)); con.commit()
    _keep(con, conf, fid, 'color', n, f'color/baked_{n}.png', 'color', files=tuple(f'color/{x}' for x in (r['matte'] if 'matte' in r.keys() else None, r['protect'] if 'protect' in r.keys() else None) if x), extra={'reference': 'gta6_keyart.jpg', 'by': 'carried down the chain'})
    return 'color'


def _rebake_move(con, conf, fid, n):
    home = os.path.join(conf['films'], fid, 'colormove')
    r = con.execute('SELECT * FROM colormove WHERE film = ?', (fid,)).fetchone()
    if r is None or not os.path.exists(os.path.join(home, f'baked_{n}.png')):
        return None
    slots = [x['n'] for x in con.execute("SELECT n FROM skin WHERE film = ? AND state = 'baked' ORDER BY n", (fid,)) if _move_src(conf, fid, x['n'])]
    tag = f'move_{fid}_{n}'
    ok, said = _teeth_run('move', [(_move_src(conf, fid, n), f'{tag}.png'), ((r['settings'] or '{}').encode(), f'{tag}.json')], f'in/{tag}.png in/{tag}.json out/{tag}_out.png {slots.index(n)} {len(slots)}',
                          [(f'{tag}_out.png', f'baked_{n}.png')], conf, fid, n, 'colormove', 'move_tool.py')
    if ok:
        _keep(con, conf, fid, 'colormove', n, f'colormove/baked_{n}.png', 'colormove', per_film=True, extra={'by': 'carried down the chain', 'source': os.path.relpath(_move_src(conf, fid, n), os.path.join(conf['films'], fid))})
    return 'colormove' if ok else f'colormove {n} not made again: {said}'


def _rebake_restore(con, conf, fid, n):
    r = con.execute('SELECT * FROM restore WHERE film = ? AND n = ?', (fid, n)).fetchone()
    if r is None or r['state'] != 'baked':
        return None
    try:
        con.commit()
        restore_press(type('Store', (), {'db_path': con.execute('PRAGMA database_list').fetchone()[2]})(), 'restorebake', lambda k: {'value': f'{fid}:{n}:one'}.get(k, ''), conf)
    except Exception as e:   # noqa: BLE001
        return f'restore {n} not made again: {e}'
    return 'restore'


def carry_down(con, conf, fid, slots, after):
    """every step below `after` made again for these slots, where each slot has reached it -> words for the press's answer ('' when nothing was below)"""
    order = ['skin', 'teeth', 'hair', 'cleanup', 'color', 'colormove', 'restore']   # (the owner 2026-10-29: "make sure the agent will pass all the changes down the chain to this point")
    steps = order[order.index(after) + 1:]
    slots = set(slots)
    if after == 'skin' and TEETH_REF in slots:   # the grill's own picture changed: every slot's teeth with it
        slots |= {m for (m,) in con.execute("SELECT n FROM skin WHERE film = ? AND state = 'baked'", (fid,))}
    done, why = {s: [] for s in steps}, []
    for n in sorted(slots):
        for st in steps:
            res = {'teeth': _rebake_teeth, 'hair': _rebake_hair, 'cleanup': _rebake_clean, 'color': _rebake_color, 'colormove': _rebake_move, 'restore': _rebake_restore}[st](con, conf, fid, n)
            if res == st:
                done[st].append(str(n))
            elif res:
                why.append(res)
    said = ' · '.join(f"{st} {', '.join(v)}" for st, v in done.items() if v)
    return (f' · carried down the chain: {said}' if said else '') + (f" · {'; '.join(why)}" if why else '')


# ============ PART 8 · COLOR (the owner 2026-10-29: "next is color move and we have tools for this already in larry 5 / with the reference of GTA"; "make sure to look at
# our larry 5 color move agent"): the old platform's MOVE COLOR maths (mgmt_color_grade.py: the 11 TONAL_LAYERS, _perband_color_transfer, RESTORE DETAIL as STRENGTH) on every
# slot's official picture (cleanup/baked_N.png), his GTA VI key art the reference; MAKE PREVIEW once gives two layers (the shot's own light, all the reference's light) and
# TUNE mixes them live with LIGHT and STRENGTH; BAKE makes it at those numbers
COLOR_REF = 'gta6_keyart.jpg'   # his reference, in the references folder
COLOR_PROGRAM = """
# THE COLOUR MOVE (the owner 2026-10-29: "next is color move and we have tools for this already in larry 5 / with the reference of GTA"): the old platform's MOVE COLOR
# maths, line for line (mgmt_color_grade.py: TONAL_LAYERS, _perband_color_transfer): each of 11 tonal bands of the picture moved to the reference's colour in that band;
# then STRENGTH of it, and the picture's own lightness kept at LIGHT (0 = all its own, 100 = the reference's)
#   grade <picture> <reference> <strength> <light> <out.png> [<matte.png|-> <strokes.json> <protect> <edge>]   with a mask: the old MOVE COLOR's PROTECT BRUSH, the
#        masked pixels keep the picture as it was at PROTECT (0..100), the mask feathered over EDGE px
#   skin <picture> <matte.png>   his skin (the box's skin finder, skin_norm.skin_weight: face and body, never hair), green with the matte as its alpha
import sys, json
import cv2, numpy as np
from PIL import Image
TONAL_LAYERS = [
    {'index': 1,  'label': 'Black',   'l_min': 0,  'l_max': 9},
    {'index': 2,  'label': 'L 10-19', 'l_min': 10, 'l_max': 19},
    {'index': 3,  'label': 'L 20-29', 'l_min': 20, 'l_max': 29},
    {'index': 4,  'label': 'L 30-39', 'l_min': 30, 'l_max': 39},
    {'index': 5,  'label': 'L 40-49', 'l_min': 40, 'l_max': 49},
    {'index': 6,  'label': 'L 50-59', 'l_min': 50, 'l_max': 59},
    {'index': 7,  'label': 'L 60-69', 'l_min': 60, 'l_max': 69},
    {'index': 8,  'label': 'L 70-79', 'l_min': 70, 'l_max': 79},
    {'index': 9,  'label': 'L 80-89', 'l_min': 80, 'l_max': 89},
    {'index': 10, 'label': 'L 90-95', 'l_min': 90, 'l_max': 95},
    {'index': 11, 'label': 'White',   'l_min': 96, 'l_max': 100},
]


def _perband_color_transfer(src_lab, ref_rgb):
    # Per-band color transfer: each of the 11 L bands moved to the reference's mean colour in that band (the old MOVE COLOR, line for line)
    # Convert reference to Lab
    ref_bgr = cv2.cvtColor(ref_rgb, cv2.COLOR_RGB2BGR)
    ref_lab_cv = cv2.cvtColor(ref_bgr, cv2.COLOR_BGR2Lab)
    ref_lab = ref_lab_cv.astype(np.float32)
    ref_L = ref_lab[:, :, 0] * 100.0 / 255.0
    ref_A = ref_lab[:, :, 1] - 128.0
    ref_B = ref_lab[:, :, 2] - 128.0

    src_L = src_lab[:, :, 0]
    src_A = src_lab[:, :, 1]
    src_B = src_lab[:, :, 2]

    # Minimum chroma to include reference pixels (skip neutral/white moodboard areas)
    MIN_CHROMA = 5.0

    for layer in TONAL_LAYERS:
        l_lo, l_hi = layer['l_min'], layer['l_max']

        # Source pixels in this L band
        src_mask = (src_L >= l_lo) & (src_L <= l_hi)
        if np.sum(src_mask) < 10:
            continue

        # Reference pixels in this L band WITH color (exclude neutral)
        ref_l_mask = (ref_L >= l_lo) & (ref_L <= l_hi)
        ref_chroma = np.sqrt(ref_A ** 2 + ref_B ** 2)
        ref_mask = ref_l_mask & (ref_chroma >= MIN_CHROMA)

        if np.sum(ref_mask) < 10:
            # Not enough colored reference pixels — try without chroma filter
            ref_mask = ref_l_mask
            if np.sum(ref_mask) < 10:
                continue

        # Compute means
        src_mean_l = np.mean(src_L[src_mask])
        src_mean_a = np.mean(src_A[src_mask])
        src_mean_b = np.mean(src_B[src_mask])

        ref_mean_l = np.mean(ref_L[ref_mask])
        ref_mean_a = np.mean(ref_A[ref_mask])
        ref_mean_b = np.mean(ref_B[ref_mask])

        # Compute shifts
        dl = ref_mean_l - src_mean_l
        da = ref_mean_a - src_mean_a
        db = ref_mean_b - src_mean_b

        # Apply with soft L mask (feathered band edges)
        l_feather = 5.0
        weight = np.clip((src_L - l_lo + l_feather) / (2 * l_feather), 0, 1) * \\
                 np.clip((l_hi + l_feather - src_L) / (2 * l_feather), 0, 1)

        src_lab[:, :, 0] = src_lab[:, :, 0] + weight * dl
        src_lab[:, :, 1] = src_lab[:, :, 1] + weight * da
        src_lab[:, :, 2] = src_lab[:, :, 2] + weight * db

    # Clamp
    src_lab[:, :, 0] = np.clip(src_lab[:, :, 0], 0, 100)
    src_lab[:, :, 1] = np.clip(src_lab[:, :, 1], -128, 127)
    src_lab[:, :, 2] = np.clip(src_lab[:, :, 2], -128, 127)
    return src_lab


def weight(img, matte_p, strokes_p):
    # the mask as the page shows it: the matte (or nothing), then each mark in order, a brush adds its disc, an eraser takes its disc away
    H, W = img.shape[:2]
    w = (np.asarray(Image.open(matte_p).convert('RGBA'))[..., 3].astype(np.float32) / 255) if matte_p != '-' else np.zeros((H, W), np.float32)
    if w.shape != (H, W):
        w = cv2.resize(w, (W, H), interpolation=cv2.INTER_LINEAR)
    for s_ in json.load(open(strokes_p)):
        d = np.zeros((H, W), np.uint8)
        cv2.circle(d, (int(round(s_['x'] * W)), int(round(s_['y'] * H))), max(1, int(round(s_['r'] * W))), 1, -1)
        w = np.maximum(w, d) if s_.get('m') != 'e' else w * (1 - d)
    return w


def feather(w0, edge):
    e = max(1.0, min(200.0, edge))
    d = cv2.distanceTransform((w0 <= 0.5).astype(np.uint8), cv2.DIST_L2, 3)
    return np.maximum(w0, np.clip(1 - d / e, 0, 1) ** 2)


job = sys.argv[1]
if job == 'skin':
    import os
    sys.path.insert(0, os.path.expanduser('~/frost/virtual_workspace/avatarskin'))
    import skin_norm as SK
    img = np.asarray(Image.open(sys.argv[2]).convert('RGB'))
    w = np.clip(SK.skin_weight(img), 0, 1)
    rgba = np.zeros(img.shape[:2] + (4,), np.uint8); rgba[..., 1] = 0xB1; rgba[..., 2] = 0x40; rgba[..., 3] = (w * 255).round().astype(np.uint8)
    Image.fromarray(rgba, 'RGBA').save(sys.argv[3])
    print('graded · skin found on %.1f%% of the picture' % (100 * (w > 0.5).mean()))
    sys.stdout.flush(); os._exit(0)
if job == 'grade':
    img = np.asarray(Image.open(sys.argv[2]).convert('RGB'))
    ref = np.asarray(Image.open(sys.argv[3]).convert('RGB'))
    st, lt = float(sys.argv[4]) / 100.0, float(sys.argv[5]) / 100.0
    lab = cv2.cvtColor(img, cv2.COLOR_RGB2LAB).astype(np.float32)
    src_lab = np.dstack([lab[..., 0] * 100 / 255, lab[..., 1] - 128, lab[..., 2] - 128])
    moved = _perband_color_transfer(src_lab.copy(), ref)
    moved[..., 0] = src_lab[..., 0] + (moved[..., 0] - src_lab[..., 0]) * lt
    out_lab = src_lab + (moved - src_lab) * st
    if len(sys.argv) > 7:   # THE PROTECT BRUSH: the masked pixels keep the picture as it was, at PROTECT, the mask feathered over EDGE
        w = weight(img, sys.argv[7], sys.argv[8])
        pr, ed = float(sys.argv[9]) / 100.0, float(sys.argv[10])
        if ed > 0:
            w = feather(w, ed)
        k = (1 - np.clip(w, 0, 1) * pr)[..., None]
        out_lab = src_lab + (out_lab - src_lab) * k
    o = np.dstack([out_lab[..., 0] * 255 / 100, out_lab[..., 1] + 128, out_lab[..., 2] + 128]).clip(0, 255).astype(np.uint8)
    Image.fromarray(cv2.cvtColor(o, cv2.COLOR_LAB2RGB)).save(sys.argv[6])
    print('graded · strength %d%% · light %d%%' % (round(st * 100), round(lt * 100)))
"""


def _color_src(conf, fid, n):
    p = os.path.join(conf['films'], fid, 'cleanup', f'baked_{n}.png')
    return p if os.path.exists(p) else _clean_src(conf, fid, n)


def color_grade(conf, fid, n, strength, light, out, r=None):
    """the GTA colour at STRENGTH and LIGHT; with the row's mask (the old MOVE COLOR's PROTECT BRUSH): its masked pixels keep the picture at PROTECT, feathered over EDGE"""
    tag = f'color_{fid}_{n}'
    files = [(_color_src(conf, fid, n), f'{tag}.png'), (os.path.join(conf['references'], COLOR_REF), f'{tag}_ref.jpg')]
    extra = ''
    if r is not None and (r['matte'] or json.loads(r['strokes'] or '[]')):
        files.append(((r['strokes'] or '[]').encode(), f'{tag}_strokes.json'))
        if r['matte']:
            files.append((os.path.join(conf['films'], fid, 'color', r['matte']), f'{tag}_matte.png'))
        extra = f" {f'in/{tag}_matte.png' if r['matte'] else '-'} in/{tag}_strokes.json {r['protect'] if r['protect'] is not None else 100} {r['edge'] if r['edge'] is not None else 10}"
    return _teeth_run('grade', files, f'in/{tag}.png in/{tag}_ref.jpg {strength} {light} out/{tag}_{out}{extra}', [(f'{tag}_{out}', out)], conf, fid, n, 'color', 'color_tool.py')


def color_press(store, do, one, conf):
    """MAKE PREVIEW (every slot's two layers) and BAKE (one slot, or every slot at its own numbers)"""
    con = _db(store)
    try:
        fid, _, rest = one('value').partition(':')
        n_, _, act = rest.partition(':')
        if not _film(con, fid):
            return f'COLOR refused · no project {fid}'
        slots = [r['n'] for r in con.execute("SELECT n FROM skin WHERE film = ? AND state = 'baked' ORDER BY n", (fid,)) if _color_src(conf, fid, r['n'])]
        for m in slots:
            con.execute('INSERT OR IGNORE INTO color (film, n, strength, light, state, made_at) VALUES (?, ?, 100, 30, ?, ?)', (fid, m, 'new', _now()))
        con.commit()
        if do in ('colorpaint', 'colorauto'):
            n = int(n_)
            r = con.execute('SELECT * FROM color WHERE film = ? AND n = ?', (fid, n)).fetchone()
            if do == 'colorauto':   # HIS SKIN, found by the box's skin finder: the mask to start from
                tag = f'color_{fid}_{n}'
                ok, said = _teeth_run('skin', [(_color_src(conf, fid, n), f'{tag}.png')], f'in/{tag}.png out/{tag}_skin.png', [(f'{tag}_skin.png', f'matte_{n}.png')], conf, fid, n, 'color', 'color_tool.py')
                if not ok:
                    return f'AUTO SKIN · slot {n} not made: {said}'
                con.execute('UPDATE color SET matte = ? WHERE film = ? AND n = ?', (f'matte_{n}.png', fid, n)); con.commit()
                return f"AUTO SKIN · {fid} slot {n} · {said.removeprefix('graded · ')}"
            try:
                got, at_ = json.loads(one('path') or '[]'), float(one('at') or 0)
                strokes = [{'x': round(max(0.0, min(1.0, float(g['x']))), 5), 'y': round(max(0.0, min(1.0, float(g['y']))), 5), 'm': 'e' if g.get('m') == 'e' else 'p',
                            'r': round(max(0.0005, min(0.1, float(g['r']))), 5)} for g in got][:20000]
            except (ValueError, TypeError, KeyError, AttributeError):
                return 'PAINT refused · the marks are not readable'
            if r['paint_at'] is not None and at_ < r['paint_at']:
                return f'PAINT · {fid} slot {n} · an older send, the newer marks kept'
            con.execute('UPDATE color SET strokes = ?, paint_at = ? WHERE film = ? AND n = ?', (json.dumps(strokes), at_, fid, n)); con.commit()
            return f'PAINT · {fid} slot {n} · {len(strokes)} marks'
        if do == 'colorpreview':
            made = []
            for m in slots:
                for lt in (0, 100):
                    ok, said = color_grade(conf, fid, m, 100, lt, f'tune{lt}_{m}.png')
                    if not ok:
                        return f'PREVIEW · slot {m} not made: {said}'
                made.append(str(m))
            return f"PREVIEW · {fid} · slots {', '.join(made)} · tune each live, then BAKE"
        try:
            n = int(n_)
        except ValueError:
            n = 0
        for k_, hi_ in (('strength', 100), ('light', 100), ('protect', 100), ('edge', 200)):
            if one(k_) != '' and n:
                con.execute(f'UPDATE color SET {k_} = ? WHERE film = ? AND n = ?', (round(max(0, min(hi_, float(one(k_)))), 1), fid, n))
        con.commit()
        home = os.path.join(conf['films'], fid, 'color')
        done = []
        for m in slots:
            if act == 'one' and m != n:
                continue
            r = con.execute('SELECT * FROM color WHERE film = ? AND n = ?', (fid, m)).fetchone()
            ok, said = color_grade(conf, fid, m, r['strength'], r['light'], f'color_{m}.png', r)
            if not ok:
                return f'BAKE · slot {m} not made: {said}'
            shutil.copyfile(os.path.join(home, f'color_{m}.png'), os.path.join(home, f'baked_{m}.png'))
            con.execute("UPDATE color SET file = ?, state = 'baked', why = ?, made_at = ? WHERE film = ? AND n = ?", (f'baked_{m}.png', said.removeprefix('graded · '), _now(), fid, m))
            _keep(con, conf, fid, 'color', m, f'color/baked_{m}.png', 'color', files=tuple(f'color/{x}' for x in (r['matte'] if 'matte' in r.keys() else None, r['protect'] if 'protect' in r.keys() else None) if x), extra={'reference': 'gta6_keyart.jpg'})
            con.commit()
            done.append(str(m))
        return f"{'BAKED' if act == 'one' else 'BAKED ALL'} · {fid} · the GTA colour on slots {', '.join(done)}" + carry_down(con, conf, fid, [int(x) for x in done], 'color')
    finally:
        con.close()


def color_parts(con, f, conf):
    """PART 8 ON THE PAGE · COLOR: MAKE PREVIEW, then each slot: BEFORE, TUNE (LIGHT and STRENGTH live), AFTER; its BAKE; then BAKE ALL"""
    fid = f['id']
    head = {'kind': 'step', 'n': 8, 'title': 'COLOR',
            'under': f'the GTA colour ({COLOR_REF}), the old platform\'s MOVE COLOR and its PROTECT BRUSH, no AI · MAKE PREVIEW once · MASK what keeps its own colour (AUTO SKIN: his skin) · TUNE live · BAKE ALL'}
    slots = [r['n'] for r in con.execute("SELECT n FROM skin WHERE film = ? AND state = 'baked' ORDER BY n", (fid,)) if _color_src(conf, fid, r['n'])]
    if not slots:
        return [head, {'kind': 'note', 'title': '8 · waits for the bakes', 'text': 'bake the cleanup first'}]
    if not os.path.exists(os.path.join(conf['references'], COLOR_REF)):
        return [head, {'kind': 'note', 'title': '8 · its reference is missing', 'text': f'{COLOR_REF} is not in {conf["references"]}'}]
    cc = {r['n']: r for r in con.execute('SELECT * FROM color WHERE film = ?', (fid,))}
    home = os.path.join(conf['films'], fid, 'color')
    ref = f"{conf['scratch_url']}/{os.path.relpath(os.path.join(conf['references'], COLOR_REF), SCRATCH)}"
    rows = []
    for n in slots:
        r = cc.get(n)
        src = _color_src(conf, fid, n)
        made = all(os.path.exists(os.path.join(home, f'tune{lt}_{n}.png')) for lt in (0, 100))
        baked = r is not None and r['state'] == 'baked' and os.path.exists(os.path.join(home, f'baked_{n}.png'))
        board = {'image': _src(conf, f"{fid}/{os.path.basename(os.path.dirname(src))}", os.path.basename(src)), 'do': 'colorpaint', 'value': f'{fid}:{n}', 'kinds': ['brush', 'erase'], 'full': False, 'marks': [],
                 'width': 1280, 'title': f'SLOT {n}',
                 'paint': {'size': 0.012, 'strokes': json.loads(r['strokes'] or '[]') if r is not None else [], 'auto': 'colorauto', 'protectmask': True,
                           'matte': _src(conf, f'{fid}/color', r['matte']) if r is not None and r['matte'] else '', 'reference': ref, 'result': _src(conf, f'{fid}/color', f'baked_{n}.png') if baked else '',
                           'result_url': f"{conf['films_url']}/{fid}/color/baked_{n}.png",
                           'tune': {'a': f"{conf['films_url']}/{fid}/color/tune0_{n}.png", 'b': f"{conf['films_url']}/{fid}/color/tune100_{n}.png", 'by': 'light', 'amount': 'strength',
                                    'do': 'colorpreview', 'made': made, 'full': True, 'feather': 'edge', 'protect': 'protect'},
                           'bake': {'do': 'colorbake', 'sliders': [{'name': 'strength', 'label': 'STRENGTH', 'min': 0, 'max': 100, 'value': r['strength'] if r is not None and r['strength'] is not None else 100, 'unit': '%'},
                                                                   {'name': 'light', 'label': 'LIGHT', 'min': 0, 'max': 100, 'value': r['light'] if r is not None and r['light'] is not None else 30, 'unit': '%'},
                                                                   {'name': 'protect', 'label': 'PROTECT', 'min': 0, 'max': 100, 'value': r['protect'] if r is not None and r['protect'] is not None else 100, 'unit': '%'},
                                                                   {'name': 'edge', 'label': 'EDGE', 'min': 0, 'max': 200, 'value': r['edge'] if r is not None and r['edge'] is not None else 10, 'unit': 'px'}]},
                           'show': 'result' if baked else ('tune' if made else 'mask')}}
        status = {'word': 'BAKED', 'text': r['why'] or ''} if baked else {'word': 'TUNE', 'text': 'set LIGHT and STRENGTH live, then BAKE'} if made else {'word': 'NO PREVIEW', 'text': 'press MAKE PREVIEW'}
        rows.append({'key': f'{fid}:{n}', 'wide': {'marker': board}, 'cells': [str(n), status]})
    return [head, {'kind': 'press', 'do': 'colorpreview', 'value': f'{fid}:0', 'label': 'MAKE PREVIEW (every slot, once)'},
            {'kind': 'table', 'title': '8 · COLOR · BEFORE, TUNE live, AFTER (baked) · GTA in the corner', 'columns': ['Slot', 'Status'], 'rows': rows},
            {'kind': 'press', 'do': 'colorbake', 'value': f'{fid}:0:all', 'label': 'BAKE ALL (every slot at its own numbers)'}]


# ============ PART 9 · COLOR MOVE (the owner 2026-10-29: "a new color tool ... small thumbnails 4 x 4 and all in two rows all touching each other like a collage block /
# our original color move tool under it from larry 5 and it can select a color from any and apply to all at once / ... above the block of thumbnails have the gta
# reference so it can be sampled / this will make a global color shift"): the old Pace Shift MOVE COLOR, its samples moving all 8 at once; BAKE ALL at full size
MOVE_PROGRAM = """
# THE COLOR MOVE, 1 TO 1 (the owner 2026-10-29): the old Pace Shift MOVE COLOR on a picture, as its board shows it: mgmt_color_grade.py _apply_sample, line for line
# (CONTIGUOUS only on the picture its seed was clicked on), LUMINOSITY (L + lum x 40), ORIGINAL ON TOP (max of overlay and restore), the PROTECT brush (the painted area keeps
# the picture as it was, its edge feathered, sigma = max(2, 1% of the width) / 2, as _mvc_render), in true CIELAB (D65)
#   move <picture> <settings.json> <out.png> <picture index> <pictures>
import json, sys
import cv2, numpy as np
from PIL import Image


def _apply_sample(lab_f, sample):
    # one sample: its L/A/B range (FEATHER), CONTIGUOUS from its seed, the INSIDE shifts on it and the OUTSIDE shifts off it (the old MOVE COLOR, line for line)
    h, w = lab_f.shape[:2]
    L = lab_f[:, :, 0]
    A = lab_f[:, :, 1]
    B = lab_f[:, :, 2]

    # L range filter (tonal band)
    l_min = float(sample.get('l_min', 0))
    l_max = float(sample.get('l_max', 100))

    a_min = float(sample.get('a_min', -128))
    a_max = float(sample.get('a_max', 127))
    b_min = float(sample.get('b_min', -128))
    b_max = float(sample.get('b_max', 127))
    feather = float(sample.get('feather', 15)) / 100.0  # 0..1

    # Build L mask: soft edges at tonal band boundaries (±5 L units feather)
    l_feather = 5.0
    mask_l = np.clip((L - l_min + l_feather) / (2 * l_feather), 0, 1) * \\
             np.clip((l_max + l_feather - L) / (2 * l_feather), 0, 1)

    # Build A,B mask
    if feather < 0.01:
        mask_ab = ((A >= a_min) & (A <= a_max) & (B >= b_min) & (B <= b_max)).astype(np.float32)
    else:
        mask_a = np.clip((A - a_min) / max(1, (a_max - a_min) * feather + 1), 0, 1) * \\
                 np.clip((a_max - A) / max(1, (a_max - a_min) * feather + 1), 0, 1)
        mask_b = np.clip((B - b_min) / max(1, (b_max - b_min) * feather + 1), 0, 1) * \\
                 np.clip((b_max - B) / max(1, (b_max - b_min) * feather + 1), 0, 1)
        mask_ab = np.clip(mask_a * mask_b, 0, 1)

    # Combined mask: L range × A,B range
    mask = mask_l * mask_ab

    # Contiguous mode: flood-fill from seed point
    contiguous = bool(sample.get('contiguous', 0))
    if contiguous:
        seed_x = float(sample.get('seed_x', 0.5))
        seed_y = float(sample.get('seed_y', 0.5))
        h_img, w_img = mask.shape
        sx = max(0, min(w_img - 1, int(round(seed_x * w_img))))
        sy = max(0, min(h_img - 1, int(round(seed_y * h_img))))
        binary = (mask > 0.1).astype(np.uint8)
        flood_mask = np.zeros((h_img + 2, w_img + 2), np.uint8)
        if binary[sy, sx]:
            cv2.floodFill(binary, flood_mask, (sx, sy), 2)
            mask = mask * (binary == 2).astype(np.float32)
        else:
            found = False
            for r in range(1, 11):
                for dy in range(-r, r + 1):
                    for dx in range(-r, r + 1):
                        nx, ny = sx + dx, sy + dy
                        if 0 <= nx < w_img and 0 <= ny < h_img and binary[ny, nx]:
                            cv2.floodFill(binary, flood_mask, (nx, ny), 2)
                            mask = mask * (binary == 2).astype(np.float32)
                            found = True
                            break
                    if found:
                        break
                if found:
                    break
            if not found:
                mask = np.zeros_like(mask)

    inv_mask = 1.0 - mask

    # Inside LAB shifts
    in_l = float(sample.get('inside_l', 0))
    in_a = float(sample.get('inside_a_shift', 0))
    in_b = float(sample.get('inside_b_shift', 0))

    # Outside LAB shifts
    out_l = float(sample.get('outside_l', 0))
    out_a = float(sample.get('outside_a_shift', 0))
    out_b = float(sample.get('outside_b_shift', 0))

    # Apply inside shifts
    if in_l != 0:
        L = L + mask * in_l
    if in_a != 0:
        A = A + mask * in_a
    if in_b != 0:
        B = B + mask * in_b

    # Apply outside shifts
    if out_l != 0:
        L = L + inv_mask * out_l
    if out_a != 0:
        A = A + inv_mask * out_a
    if out_b != 0:
        B = B + inv_mask * out_b

    # Clamp
    L = np.clip(L, 0, 100)
    A = np.clip(A, -128, 127)
    B = np.clip(B, -128, 127)

    lab_f[:, :, 0] = L
    lab_f[:, :, 1] = A
    lab_f[:, :, 2] = B
    return lab_f


job = sys.argv[1]
if job == 'move':
    img = np.asarray(Image.open(sys.argv[2]).convert('RGB'))
    st = json.load(open(sys.argv[3]))
    k, total = int(sys.argv[5]), int(sys.argv[6])
    H, W = img.shape[:2]
    lab = cv2.cvtColor(img.astype(np.float32) / 255.0, cv2.COLOR_RGB2Lab)
    for s in st.get('samples') or []:
        if s.get('contiguous') and int(s.get('seed_pic', -1)) != k:
            continue
        lab = _apply_sample(lab, s)
    if st.get('lum'):
        lab[..., 0] = np.clip(lab[..., 0] + float(st['lum']) * 40.0, 0, 100)
    out = np.clip(cv2.cvtColor(lab, cv2.COLOR_Lab2RGB), 0, 1) * 255.0
    ov = max(float(st.get('overlay') or 0), float(st.get('restore') or 0))
    out = out * (1 - ov) + img.astype(np.float32) * ov
    strokes = ((st.get('protect') or {}).get('strokes')) or []
    if any(s.get('m') != 'e' for s in strokes):   # the PROTECT brush, its strokes on the 4-wide block turned to this picture's own place
        cols, rows = 4, (total + 3) // 4
        col, row = k % cols, k // cols
        m = np.zeros((H, W), np.uint8)
        for s in strokes:
            gx, gy = s['x'] * cols - col, s['y'] * rows - row
            cv2.circle(m, (int(round(gx * W)), int(round(gy * H))), max(1, int(round(s['r'] * cols * W))), 0 if s.get('m') == 'e' else 1, -1)
        fp = max(2.0, 0.01 * W)
        pm = cv2.GaussianBlur(m.astype(np.float32), (0, 0), fp / 2.0)[..., None]
        out = out * (1 - pm) + img.astype(np.float32) * pm
    Image.fromarray(out.clip(0, 255).round().astype(np.uint8)).save(sys.argv[4])
    print('graded · moved by %d samples · luminosity %+d · original on top %d%%' % (len(st.get('samples') or []), round(float(st.get('lum') or 0) * 100), round(ov * 100)))
"""


def _move_src(conf, fid, n):
    p = os.path.join(conf['films'], fid, 'color', f'baked_{n}.png')
    return p if os.path.exists(p) else _color_src(conf, fid, n)


def move_press(store, do, one, conf):
    """SAVE (the board's settings, on each change, the newest kept) and BAKE ALL (every slot moved at full size)"""
    con = _db(store)
    try:
        fid = one('value').partition(':')[0]
        if not _film(con, fid):
            return f'COLOR MOVE refused · no project {fid}'
        con.execute('INSERT OR IGNORE INTO colormove (film, settings, state, made_at) VALUES (?, ?, ?, ?)', (fid, '{}', 'new', _now()))
        r = con.execute('SELECT * FROM colormove WHERE film = ?', (fid,)).fetchone()
        if do == 'colormovesave':
            try:
                st, at_ = json.loads(one('settings') or '{}'), float(one('at') or 0)
                st = {'samples': [{k: float(v) for k, v in s.items() if isinstance(v, (int, float))} for s in (st.get('samples') or [])][:24],   # the original board's own record
                      'lum': max(-1.0, min(1.0, float(st.get('lum') or 0))), 'overlay': max(0.0, min(1.0, float(st.get('overlay') or 0))),
                      'restore': max(0.0, min(1.0, float(st.get('restore') or 0))), 'detail_src': str(st.get('detail_src') or '')[:40],
                      'protect': {'strokes': [{'m': 'e' if x.get('m') == 'e' else 'p', 'x': float(x['x']), 'y': float(x['y']), 'r': float(x['r'])} for x in ((st.get('protect') or {}).get('strokes') or [])][:8000]}}
            except (ValueError, TypeError, AttributeError):
                return 'SAVE refused · the settings are not readable'
            if r['at'] is not None and at_ < r['at']:
                return 'SAVE · an older send, the newer settings kept'
            con.execute("UPDATE colormove SET settings = ?, at = ?, state = 'set' WHERE film = ?", (json.dumps(st), at_, fid)); con.commit()
            return f"SAVE · {fid} · {len(st['samples'])} samples"
        slots = [x['n'] for x in con.execute("SELECT n FROM skin WHERE film = ? AND state = 'baked' ORDER BY n", (fid,)) if _move_src(conf, fid, x['n'])]
        home = os.path.join(conf['films'], fid, 'colormove')
        done = []
        for k_, m in enumerate(slots):
            tag = f'move_{fid}_{m}'
            ok, said = _teeth_run('move', [(_move_src(conf, fid, m), f'{tag}.png'), ((r['settings'] or '{}').encode(), f'{tag}.json')], f'in/{tag}.png in/{tag}.json out/{tag}_out.png {k_} {len(slots)}',
                                  [(f'{tag}_out.png', f'baked_{m}.png')], conf, fid, m, 'colormove', 'move_tool.py')
            if not ok:
                return f'BAKE · slot {m} not made: {said}'
            done.append(str(m))
            _keep(con, conf, fid, 'colormove', m, f'colormove/baked_{m}.png', 'colormove', per_film=True, extra={'source': os.path.relpath(_move_src(conf, fid, m), os.path.join(conf['films'], fid)), 'slot': k_, 'of': len(slots)})
        con.execute("UPDATE colormove SET state = 'baked', made_at = ? WHERE film = ?", (_now(), fid)); con.commit()
        return f"BAKED ALL · {fid} · the colour move on slots {', '.join(done)} · {said.removeprefix('graded · ')}" + carry_down(con, conf, fid, [int(x) for x in done], 'colormove')
    finally:
        con.close()


def move_parts(con, f, conf):
    """PART 9 ON THE PAGE · COLOR MOVE: the GTA reference, the 8 in a 4 by 2 block, the old MOVE COLOR board under them, BAKE ALL"""
    fid = f['id']
    head = {'kind': 'step', 'n': 9, 'title': 'COLOR MOVE',
            'under': 'a global colour shift on all 8 at once, the old Pace Shift MOVE COLOR, no AI · + ADD SAMPLE: the OLD colour on any picture, the NEW colour on the GTA reference · its range, INSIDE and OUTSIDE · BAKE ALL'}
    slots = [x['n'] for x in con.execute("SELECT n FROM skin WHERE film = ? AND state = 'baked' ORDER BY n", (fid,)) if _move_src(conf, fid, x['n'])]
    if not slots:
        return [head, {'kind': 'note', 'title': '9 · waits for the bakes', 'text': 'bake the colour first'}]
    r = con.execute('SELECT * FROM colormove WHERE film = ?', (fid,)).fetchone()
    pics = []
    for n in slots:
        p = _move_src(conf, fid, n)
        pics.append(_src(conf, f"{fid}/{os.path.basename(os.path.dirname(p))}", os.path.basename(p)))
    ref = f"{conf['scratch_url']}/{os.path.relpath(os.path.join(conf['references'], COLOR_REF), SCRATCH)}"
    out = [head, {'kind': 'colormove', 'do': 'colormovesave', 'land': 'colormovebake', 'value': f'{fid}:0', 'pictures': pics, 'reference': ref, 'width': 720,
                  'settings': json.loads(r['settings'] or '{}') if r is not None else {}, 'title': '9 · COLOR MOVE · all 8, live'},
           {'kind': 'press', 'do': 'colormovebake', 'value': f'{fid}:0', 'label': 'BAKE ALL (the saved colour move on all 8, full size)'}]   # (the owner 2026-10-29: "now we need a bake all button")
    if r is not None and r['state'] == 'baked':
        out.append({'kind': 'note', 'title': '9 · baked', 'text': f"colormove/baked_N.png · {r['made_at']}"})
    return out


# ============ PART 10 · RESTORE DETAIL (the owner 2026-10-29: "its called restore detail / it has the GTA as bottom layer (step 9) / then it has color on top of that (step 8) /
# then it has original on top of that (step 7) / and the two top layers you can adjust a slider from 0 to 100 % / then a bake button to bake them all together"): three
# layers a slot, the page draws them live (each over the one below at its opacity) and BAKE lays them the same way (ffmpeg's overlay at that alpha), nothing else
RESTORE_LAYERS = (('colormove', 'GTA (step 9)'), ('color', 'COLOR (step 8)'), ('cleanup', 'ORIGINAL (step 7)'))


def _restore_layer(conf, fid, n, step):
    p = os.path.join(conf['films'], fid, step, f'baked_{n}.png')
    return p if os.path.exists(p) else ''


def restore_press(store, do, one, conf):
    """BAKE (one slot) or BAKE ALL: the three layers laid together, COLOR at its %, ORIGINAL at its % (restore/baked_N.png)"""
    con = _db(store)
    try:
        fid, _, rest = one('value').partition(':')
        n_, _, act = rest.partition(':')
        if not _film(con, fid):
            return f'RESTORE refused · no project {fid}'
        slots = [x['n'] for x in con.execute("SELECT n FROM skin WHERE film = ? AND state = 'baked' ORDER BY n", (fid,)) if all(_restore_layer(conf, fid, x['n'], st) for st, _l in RESTORE_LAYERS)]
        for m in slots:
            con.execute('INSERT OR IGNORE INTO restore (film, n, color, original, state, made_at) VALUES (?, ?, 0, 0, ?, ?)', (fid, m, 'new', _now()))
        try:
            n = int(n_)
        except ValueError:
            n = 0
        for k_ in ('color', 'original'):
            if one(k_) != '' and n:
                con.execute(f'UPDATE restore SET {k_} = ? WHERE film = ? AND n = ?', (round(max(0, min(100, float(one(k_)))), 1), fid, n))
        con.commit()
        home = os.path.join(conf['films'], fid, 'restore')
        os.makedirs(home, exist_ok=True)
        done = []
        for m in slots:
            if act == 'one' and m != n:
                continue
            r = con.execute('SELECT * FROM restore WHERE film = ? AND n = ?', (fid, m)).fetchone()
            a8, a7 = (r['color'] or 0) / 100.0, (r['original'] or 0) / 100.0
            base, c8, c7 = (_restore_layer(conf, fid, m, st) for st, _l in RESTORE_LAYERS)
            out = os.path.join(home, f'baked_{m}.png')
            _ff(['-i', base, '-i', c8, '-i', c7, '-filter_complex',
                 f'[1]format=rgba,colorchannelmixer=aa={a8:.3f}[c];[2]format=rgba,colorchannelmixer=aa={a7:.3f}[o];[0][c]overlay=format=auto[b];[b][o]overlay=format=auto,format=rgb24',
                 '-frames:v', '1', out], f'the restore of slot {m}')
            con.execute("UPDATE restore SET state = 'baked', why = ?, made_at = ? WHERE film = ? AND n = ?",
                        (f"GTA under, COLOR {round(a8 * 100)}%, ORIGINAL {round(a7 * 100)}%", _now(), fid, m))
            _keep(con, conf, fid, 'restore', m, f'restore/baked_{m}.png', 'restore', extra={'layers': {st: _sha(_restore_layer(conf, fid, m, st)) for st, _l in RESTORE_LAYERS}})
            con.commit()
            done.append(str(m))
        return f"{'BAKED' if act == 'one' else 'BAKED ALL'} · {fid} · restore detail on slots {', '.join(done) or 'none'}"
    finally:
        con.close()


def restore_parts(con, f, conf):
    """PART 10 ON THE PAGE · RESTORE DETAIL: each slot's three layers drawn live with its two sliders, BAKE; BAKE ALL"""
    fid = f['id']
    head = {'kind': 'step', 'n': 10, 'title': 'RESTORE DETAIL',
            'under': 'three layers a slot: the GTA move (step 9) at the bottom, the COLOR (step 8) over it, the ORIGINAL (step 7) on top · the top two 0 to 100% live · BAKE ALL lays them together'}
    slots = [x['n'] for x in con.execute("SELECT n FROM skin WHERE film = ? AND state = 'baked' ORDER BY n", (fid,)) if all(_restore_layer(conf, fid, x['n'], st) for st, _l in RESTORE_LAYERS)]
    if not slots:
        return [head, {'kind': 'note', 'title': '10 · waits for step 9', 'text': 'bake the colour move first'}]
    rr = {x['n']: x for x in con.execute('SELECT * FROM restore WHERE film = ?', (fid,))}
    rows = []
    for n in slots:
        r = rr.get(n)
        url = lambda st: _src(conf, f'{fid}/{st}', f'baked_{n}.png')   # noqa: E731
        baked = r is not None and r['state'] == 'baked' and os.path.exists(os.path.join(conf['films'], fid, 'restore', f'baked_{n}.png'))
        board = {'image': url('colormove'), 'do': 'restorebake', 'value': f'{fid}:{n}', 'kinds': [], 'full': False, 'marks': [], 'width': 1280, 'title': f'SLOT {n}',
                 'paint': {'view': True, 'strokes': [], 'result': _src(conf, f'{fid}/restore', f'baked_{n}.png') if baked else '', 'result_url': f"{conf['films_url']}/{fid}/restore/baked_{n}.png",
                           'tune': {'layers': [url('color'), url('cleanup')], 'by': 'color', 'amount': 'original', 'do': 'restorebake', 'made': True},
                           'bake': {'do': 'restorebake', 'sliders': [{'name': 'color', 'label': 'COLOR (step 8)', 'min': 0, 'max': 100, 'value': r['color'] if r is not None and r['color'] is not None else 0, 'unit': '%'},
                                                                     {'name': 'original', 'label': 'ORIGINAL (step 7)', 'min': 0, 'max': 100, 'value': r['original'] if r is not None and r['original'] is not None else 0, 'unit': '%'}]},
                           'show': 'result' if baked else 'tune'}}
        rows.append({'key': f'{fid}:{n}', 'wide': {'marker': board}, 'cells': [str(n), {'word': 'BAKED', 'text': r['why'] or ''} if baked else {'word': 'TUNE', 'text': 'set the two layers live, then BAKE'}]})
    out = [head, {'kind': 'table', 'title': '10 · RESTORE DETAIL · GTA under, COLOR, ORIGINAL on top', 'columns': ['Slot', 'Status'], 'rows': rows},
           {'kind': 'press', 'do': 'restorebake', 'value': f'{fid}:0:all', 'label': 'BAKE ALL (every slot at its own %)'}]
    row = con.execute('SELECT map FROM music WHERE film = ?', (fid,)).fetchone()
    if row:   # THE FINAL VIDEO (the owner 2026-10-29: "a new video version under this so we can see our final results"): step 3's player, each slot its final picture for its seconds
        mslots = json.loads(row['map'])['slots']
        types_ = _types(con, fid, mslots)
        insp = {x['n']: x for x in con.execute('SELECT n, tag FROM inspiration WHERE film = ?', (fid,))}
        slides, at = [], 0
        for x in mslots:
            t = insp[x['n']]['tag'] if x['n'] in insp and insp[x['n']]['tag'] else types_[x['n'] - 1]
            pic = next((st for st in ('restore', 'colormove', 'color', 'cleanup') if os.path.exists(os.path.join(conf['films'], fid, st, f"baked_{x['n']}.png"))), '')
            slides.append({'src': _src(conf, f'{fid}/{pic}', f"baked_{x['n']}.png") if pic else '', 'at': at, 'end': at + x['seconds'], 'label': f"{x['n']}·{t}", 'tone': TONE_OF[t]})
            at += x['seconds']
        # THE ORIGINAL ABOVE (the owner 2026-10-29: "we need to sync the original video above the new one with our song"; "make sure they sync on the music
        # not time"; "voice can match its the same voice"): the Riff Raff video's own minute, matched on the music (chroma + beats) and on the voice, both at
        # one point, video 96.48 s = our second 0, every window within 26 ms; its picture with our final song (original/minute_original.mp4)
        # THE FOUR FILMS, 2 x 2 (the owner 2026-10-29: "make the video size smaller so we have 4 videos all in a matrix together 2 x 2"; "and 1 play button
        # plays all together"; "keep the original 1 then quavo 2 then movement 3 and lips 4 then effects drop and we can do that later"): each cell its minute
        # on our song, a cell with no film yet saying where it comes from. QUAVO is the movement's source: Quavo's sections of A COLORS SHOW (Hotel Lobby),
        # retimed onto our beat and chosen slot by slot ("like we chop up the quavo video to match our segments")
        out.append({'kind': 'films', 'title': '10 · THE FOUR FILMS · ORIGINAL, QUAVO, MOVEMENT, LIPS · all on our final song',
                    'films': [{'title': '1 · ORIGINAL · synced to our song (video 1:36.48)', 'src': _src(conf, f'{fid}/original', 'minute_original.mp4'), 'empty': 'the original minute is not cut yet'},
                              {'title': '2 · QUAVO · the moves, retimed onto our beat', 'src': _src(conf, f'{fid}/quavo', 'minute_quavo.mp4'), 'empty': 'Quavo\'s sections come here (A COLORS SHOW, on our beat)'},
                              {'title': '3 · MOVEMENT', 'src': _src(conf, f'{fid}/movement', 'minute_movement.mp4'), 'empty': 'the movement video comes here (our pictures doing Quavo\'s moves)'},
                              {'title': '4 · LIPS MOVING', 'src': _src(conf, f'{fid}/lips', 'minute_lips.mp4'), 'empty': 'the lips video comes here (PF Lip-sync, after the movement)'}],
                    'segments': [{'n': x['n'], 'at': sl['at'], 'end': sl['end']} for x, sl in zip(mslots, slides)],
                    'under': 'one PLAY ALL 4 plays them together on the original\'s sound · click a number to jump that film to its slot'})
        out.append({'kind': 'slideshow', 'title': '10 · THE FINAL PICTURES · PLAY THEM WITH THE FINAL SONG · each slot its final picture for its seconds',
                    'audio': _src(conf, f'{fid}/music', 'minute_final.wav'), 'slides': slides, 'under': 'press play on the song: the picture changes on each slot · click a bar to jump to its slot',
                    'empty': 'the player appears when the final song is made (step 1)'})
    return out


# ============ PART 11 · MOVE TO THE BEAT (the owner 2026-10-29, after Wan 2.2 Animate lost him: "what about we just use kling 4 ... and animate each with a
# clear prompt to give it some movement"; "we use replicate for our kling api"; then "move a clip forward or back with a slider like our music slider ...
# and we can speed up or slow down to match the beat"; "the video player would be a slide show with multiple videos then you can adjust the slider and get
# perfect cuts for the transition"; "each video we could just double the length"; "we dont need a button send to lips we will make that a new tool after this"). Each slot's
# Kling 4.0 clip (kling_pack/long/slot_N.mp4, twice its seconds; else kling_pack/slot_N.mp4, its seconds) plays in one player on our song from its MOVE
# point at its SPEED; SAVE ALL keeps the sixteen numbers (movetime), BAKE ALL makes each slot's clip as set (movement/baked_N.mp4, its seconds at 30 fps)
# and the movement minute (cell 3); the lips are the next tool's (its scripts wait in tools/lips).
MOVE_SLOTS_OFF, MOVE_SPEED = (-1.5, 30.0), (0.1, 3.0)   # SPEED from almost still to fast (the owner 2026-10-29: "the speed has to have way more adjustment from almost no movement to fast movement")
_LENGTHS = {}


def _clip(conf, fid, n):
    """slot n's Kling clip: the double one when it is made, else the one of its own seconds -> (folder under the film, file name) or None"""
    for sub in ('kling_pack/long', 'kling_pack'):
        if os.path.exists(os.path.join(conf['films'], fid, sub, f'slot_{n}.mp4')):
            return sub, f'slot_{n}.mp4'
    return None


def _length(path):
    """a clip's seconds (ffprobe), kept while the file is the same"""
    key = (path, os.path.getmtime(path))
    if key not in _LENGTHS:
        out = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', path], capture_output=True, text=True, timeout=60).stdout
        _LENGTHS[key] = float(out.strip() or 0)
    return _LENGTHS[key]


# ============ EVERY GENERATION KEEPS WHAT MADE IT (the owner 2026-10-30: "make sure all controls and versions are saving data... if it was the last one generated that
# should be stored in the db"; "im saying this as a global issue"): each file the agent generates or bakes writes one row in versions at that moment, the exact settings
# and inputs it was made from (the sliders as they were, the source and its fingerprint, the prompt, the tool); the current sliders may move on, the version never does
def _sha(path, n=12):
    """a file's fingerprint (its first n hex of SHA-256), '' when there is no file"""
    import hashlib
    if not path or not os.path.exists(path):
        return ''
    h = hashlib.sha256()
    with open(path, 'rb') as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()[:n]


def _version(con, fid, step, n, settings, file):
    """the version of one generated file: its step, its slot (0 for the film), the settings it was made from, the file -> its id"""
    cur = con.execute('INSERT INTO versions (film, step, n, settings, file, made_at) VALUES (?, ?, ?, ?, ?, ?)', (fid, step, n, json.dumps(settings, sort_keys=True), file, _now()))
    con.commit()
    return cur.lastrowid


def _last_version(con, fid, step, n):
    """the newest version of a slot's step -> its settings (a dict) or None"""
    r = con.execute('SELECT settings FROM versions WHERE film = ? AND step = ? AND n = ? ORDER BY id DESC LIMIT 1', (fid, step, n)).fetchone()
    return json.loads(r['settings']) if r is not None else None


def _keep(con, conf, fid, step, n, file, table=None, per_film=False, also=(), files=(), extra=None):
    """THE VERSION OF ONE GENERATED FILE, AT THE MOMENT IT IS MADE (the owner 2026-10-30: "make sure all controls and versions are saving data"; "im saying this as a
    global issue"): its step's row exactly as the bake read it (every slider, stroke list and setting), the rows it also leaned on (also: (table, n) pairs, the
    master slot's, the poster's), any extra words (the tool, the prompt), the output's fingerprint, and the masks it was made from (files) copied into versions/<step>/
    under their own fingerprint, since a mask is painted over later -> the version's id"""
    home = os.path.join(conf['films'], fid)
    def row(t, k):
        r = con.execute(f'SELECT * FROM {t} WHERE film = ?' + ('' if k is None else ' AND n = ?'), (fid,) if k is None else (fid, k)).fetchone()
        return {c: r[c] for c in r.keys() if c != 'film'} if r is not None else None
    s = dict(extra or {})
    if table:
        s['row'] = row(table, None if per_film else n)
    for t, k in also:
        s[f'{t}_{k}'] = row(t, k)
    s['file_sha'] = _sha(os.path.join(home, file))
    kept = {}
    for f in files:
        src = f if os.path.isabs(f) else os.path.join(home, f)
        if os.path.exists(src):
            d = os.path.join(home, 'versions', step); os.makedirs(d, exist_ok=True)
            dst = os.path.join(d, f'{_sha(src)}_{os.path.basename(src)}')
            if not os.path.exists(dst):
                shutil.copyfile(src, dst)
            kept[os.path.relpath(src, home)] = os.path.relpath(dst, home)
    if kept:
        s['kept_files'] = kept
    return _version(con, fid, step, n, s, file)


def _strip(path, n=12):
    """A CLIP AS A STRIP OF ITS FRAMES (the owner 2026-10-29: "the move slider should look like our music slider so you see the entire clip and you see the
    duration"): n frames across its whole length in one row, made once beside it (strip_<name>.jpg) and again when the clip is made again -> its path"""
    out = os.path.join(os.path.dirname(path), 'strip_' + os.path.splitext(os.path.basename(path))[0] + '.jpg')
    if not os.path.exists(out) or os.path.getmtime(out) < os.path.getmtime(path):
        rate = n / max(0.5, _length(path))
        _ff(['-i', path, '-vf', f'fps={rate:.5f},scale=160:90,tile={n}x1', '-frames:v', '1', '-q:v', '4', out], 'the clip\'s strip')
    return out


def _minute_beats(conf, fid):
    """our minute's own beats and downbeats (the steady grid step 1 found in the song, from the minute's start) -> (beats, downbeats) in seconds"""
    a = _read(os.path.join(conf['films'], fid, 'music', 'analysis.json'), {}) or {}
    m = _read(os.path.join(conf['films'], fid, 'music', 'minute.json'), {}) or {}
    st = float(m.get('start') or 0)
    pick = lambda xs: [round(b - st, 3) for b in xs or () if st - 0.05 <= b < st + TOTAL]   # noqa: E731
    return pick(a.get('beats')), pick(a.get('downbeats'))


def _move_slots(con, fid):
    """the minute's slots in order -> [(n, start, seconds)]"""
    row = con.execute('SELECT map FROM music WHERE film = ?', (fid,)).fetchone()
    out, at = [], 0
    for x in (json.loads(row['map'])['slots'] if row else []):
        out.append((x['n'], at, x['seconds'])); at += x['seconds']
    return out


def _motion_rhythm(path, fps=24, w=48, h=27):
    """A CLIP'S OWN RHYTHM: how much the picture changes from frame to frame (small grey frames), its slow drift taken out, and the repeat in it that
    is strongest between 0.3 and 2.2 seconds -> (seconds, strength 0..1); (0, 0) when the clip says nothing"""
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', path, '-vf', f'fps={fps},scale={w}:{h},format=gray', '-f', 'rawvideo', '-'], capture_output=True, timeout=300).stdout
    n = w * h; frames = [raw[i:i + n] for i in range(0, len(raw) - n + 1, n)]
    if len(frames) < 3 * fps:
        return 0.0, 0.0
    e = [sum(abs(a - b) for a, b in zip(f1, f0)) / n for f0, f1 in zip(frames, frames[1:])]
    k = fps // 2                                                                       # the drift: a half-second running mean, taken out
    e = [x - sum(e[max(0, i - k):i + k + 1]) / len(e[max(0, i - k):i + k + 1]) for i, x in enumerate(e)]
    var = sum(x * x for x in e) or 1.0
    best = (0.0, 0.0)
    for lag in range(int(0.3 * fps), min(int(2.2 * fps), len(e) // 2) + 1):
        ac = sum(e[i] * e[i + lag] for i in range(len(e) - lag)) / var * len(e) / (len(e) - lag)
        if ac > best[1]:
            best = (lag / fps, ac)
    return best


def move_auto(con, conf, fid):
    """AUTO SPEED (the owner 2026-10-29: "can you add an auto button for speed to auto set it"): each slot's clip measured for its own rhythm and sped up
    or slowed so that rhythm lands on our beat, a half beat, two or four beats (whichever asks the least change, within the SPEED slider's reach); a clip
    with no clear rhythm keeps 1.00x. MOVE is left as set. -> the words for the press"""
    row = con.execute('SELECT tempo FROM music WHERE film = ?', (fid,)).fetchone()
    beat = 60.0 / float((row['tempo'] if row else 0) or 120)
    tm = {r['n']: r for r in con.execute('SELECT * FROM movetime WHERE film = ?', (fid,))}
    said = []
    for n, _at, _sec in _move_slots(con, fid):
        c = _clip(conf, fid, n)
        if not c:
            continue
        period, strength = _motion_rhythm(os.path.join(conf['films'], fid, *c))
        sp, how = 1.0, 'no clear rhythm'
        if period and strength >= 0.15:
            fits = [(abs(period / (beat * m) - 1), period / (beat * m), m) for m in (0.5, 1, 2, 4) if MOVE_SPEED[0] <= period / (beat * m) <= MOVE_SPEED[1]]
            if fits:
                _d, sp, m = min(fits)
                how = f'moves every {period:.2f} s -> {m:g} beat{"s" if m != 1 else ""}'
        off = float(tm[n]['offset']) if n in tm else 0.0
        con.execute('INSERT INTO movetime (film, n, offset, speed, made_at) VALUES (?, ?, ?, ?, ?) ON CONFLICT(film, n) DO UPDATE SET speed = excluded.speed, made_at = excluded.made_at',
                    (fid, n, off, round(sp, 2), _now()))
        said.append(f'{n} {sp:.2f}x ({how})')
    con.commit()
    return ' · '.join(said)


def move_bake(con, conf, fid):
    """BAKE ALL: each slot's clip from its MOVE point at its SPEED, its seconds at 30 fps, 1280x720 (a clip that runs out holds its last frame, a MOVE
    before its start holds its first) -> movement/baked_N.mp4, and the movement minute on our final song -> the words for the press"""
    home = os.path.join(conf['films'], fid, 'movement'); os.makedirs(home, exist_ok=True)
    tm = {r['n']: r for r in con.execute('SELECT * FROM movetime WHERE film = ?', (fid,))}
    parts, said = [], []
    for n, _at, sec in _move_slots(con, fid):
        c = _clip(conf, fid, n)
        if not c:
            raise ValueError(f'slot {n} has no Kling clip yet')
        r = tm.get(n)
        off, sp = (float(r['offset']), float(r['speed'])) if r is not None else (0.0, 1.0)
        pre = ['-ss', f'{off:.3f}'] if off > 0 else []
        rate = 'minterpolate=fps=30:mi_mode=blend' if sp < 0.7 else 'fps=30'   # slowed far: frames blended between, not held
        vf = f'setpts=(PTS-STARTPTS)/{sp:.4f},' + (f'tpad=start_mode=clone:start_duration={-off:.3f},' if off < 0 else '') + f'{rate},scale=1280:720,tpad=stop_mode=clone:stop_duration=5'
        out = os.path.join(home, f'baked_{n}.mp4')
        _ff(pre + ['-i', os.path.join(conf['films'], fid, *c), '-an', '-vf', vf, '-t', str(sec), '-c:v', 'libx264', '-crf', '14', '-pix_fmt', 'yuv420p', out], f'slot {n} baked')
        _version(con, fid, 'move', n, {'offset': off, 'speed': sp, 'seconds': sec, 'clip': '/'.join(c), 'clip_sha': _sha(os.path.join(conf['films'], fid, *c))}, os.path.relpath(out, os.path.join(conf['films'], fid)))
        parts.append(out); said.append(f'{n} {off:+.2f}s {sp:.2f}x')
    lst = os.path.join(home, 'baked.txt')
    with open(lst, 'w') as f:
        f.write(''.join(f"file '{p}'\n" for p in parts))
    _ff(['-f', 'concat', '-safe', '0', '-i', lst, '-i', os.path.join(conf['films'], fid, 'music', 'minute_final.wav'), '-map', '0:v', '-map', '1:a', '-t', str(TOTAL),
         '-c:v', 'libx264', '-crf', '18', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '256k', '-movflags', '+faststart', os.path.join(home, 'minute_movement.part.mp4')], 'the movement minute')
    os.replace(os.path.join(home, 'minute_movement.part.mp4'), os.path.join(home, 'minute_movement.mp4'))   # the players never see it half made
    _version(con, fid, 'move_minute', 0, {'slots': said, 'song_sha': _sha(os.path.join(conf['films'], fid, 'music', 'minute_final.wav'))}, 'movement/minute_movement.mp4')
    return ' · '.join(said)


def movetime_press(store, do, one, conf):
    """a slider let go of keeps every slot's MOVE and SPEED; AUTO SPEED sets each SPEED from its clip's rhythm; BAKE ALL makes them; RESET ALL undoes them"""
    con = _db(store)
    try:
        fid = one('value').partition(':')[0]
        if not _film(con, fid):
            return f'refused · no project {fid}'
        if do == 'movetime':
            kept = []
            for n, _at, _sec in _move_slots(con, fid):
                try:
                    off = max(MOVE_SLOTS_OFF[0], min(MOVE_SLOTS_OFF[1], float(one(f'offset_{n}'))))
                    sp = max(MOVE_SPEED[0], min(MOVE_SPEED[1], float(one(f'speed_{n}'))))
                except ValueError:
                    continue
                con.execute('INSERT INTO movetime (film, n, offset, speed, made_at) VALUES (?, ?, ?, ?, ?) ON CONFLICT(film, n) DO UPDATE SET '
                            'offset = excluded.offset, speed = excluded.speed, made_at = excluded.made_at', (fid, n, off, sp, _now()))
                kept.append(f'{n} {off:+.2f}s {sp:.2f}x')
            con.commit()
            return f"SAVED · {fid} · {' · '.join(kept) or 'nothing'}"
        if do == 'movereset':   # RESET ALL (the owner 2026-10-29: "it needs a reset too"): every slot back to MOVE 0 and SPEED 1x
            con.execute('DELETE FROM movetime WHERE film = ?', (fid,)); con.commit()
            return f'RESET · {fid} · every slot back to MOVE 0.00 s and SPEED 1.00x'
        if do == 'moveauto':
            return f'AUTO SPEED · {fid} · {move_auto(con, conf, fid)} · MOVE kept; watch it, any slider you move saves by itself'
        if do == 'movebake':   # IN THE BACKGROUND (the owner 2026-10-29: "when you bake it in the future it should run in the background not lock the page")
            st = os.path.join(conf['films'], fid, 'movement', 'bake.json')
            if (_read(st, {}) or {}).get('state') == 'baking':
                return 'BAKE refused · a bake is already going'
            if not all(_clip(conf, fid, n) for n, _a, _s in _move_slots(con, fid)):
                return 'BAKE refused · a slot has no Kling clip yet'
            os.makedirs(os.path.dirname(st), exist_ok=True); _write(st, {'state': 'baking', 'started': _now()})
            def work():
                c = _db(store)
                try:
                    _write(st, {'state': 'baked', 'said': move_bake(c, conf, fid), 'ended': _now()})
                except Exception as e:   # noqa: BLE001 - said on the page
                    _write(st, {'state': 'failed', 'said': str(e)[:300], 'ended': _now()})
                finally:
                    c.close()
            threading.Thread(target=work, daemon=True).start()
            return f'BAKING · {fid} · in the background, the page is free; it says BAKED here when the movement minute is made'
        return f'refused · not one of its presses: {do}'
    finally:
        con.close()


def movetime_parts(con, f, conf):
    """PART 11 ON THE PAGE · MOVE TO THE BEAT: the slots in one player, MOVE and SPEED for each (saved as they are let go of), AUTO SPEED, BAKE ALL"""
    fid = f['id']
    head = {'kind': 'step', 'n': 11, 'title': 'MOVE TO THE BEAT',
            'under': 'each slot its Kling 4.0 clip (made twice as long as its slot) in one player on our song · MOVE slides it, SPEED speeds it up or slows it to the beat (AUTO SPEED sets it from each clip\'s own rhythm) · a slider saves by itself when you let go · then BAKE ALL'}
    slots = _move_slots(con, fid)
    if not slots or not all(_clip(conf, fid, n) for n, _a, _s in slots):
        return [head, {'kind': 'note', 'title': '11 · waits for the Kling clips', 'text': 'each slot needs its Kling 4.0 clip (kling_pack)'}]
    tm = {r['n']: r for r in con.execute('SELECT * FROM movetime WHERE film = ?', (fid,))}
    row = con.execute('SELECT map, tempo FROM music WHERE film = ?', (fid,)).fetchone()
    types_ = _types(con, fid, json.loads(row['map'])['slots'])
    insp = {x['n']: x for x in con.execute('SELECT n, tag FROM inspiration WHERE film = ?', (fid,))}
    rows = []
    for n, at, sec in slots:
        sub, name = _clip(conf, fid, n)
        t = insp[n]['tag'] if n in insp and insp[n]['tag'] else types_[n - 1]
        r = tm.get(n)
        strip = _strip(os.path.join(conf['films'], fid, sub, name))
        lv = _last_version(con, fid, 'move', n)
        rows.append({'n': n, 'label': f'{n}·{t}', 'tone': TONE_OF[t], 'video': _src(conf, f'{fid}/{sub}', name), 'strip': _src(conf, f'{fid}/{sub}', os.path.basename(strip)), 'start': at, 'seconds': sec,
                     **({'last': {'offset': lv['offset'], 'speed': lv['speed']}} if lv else {}),
                     'length': _length(os.path.join(conf['films'], fid, sub, name)), 'offset': r['offset'] if r is not None else 0, 'speed': r['speed'] if r is not None else 1})
    beats, downbeats = _minute_beats(conf, fid)
    out = [head, {'kind': 'cliptime', 'title': '11 · THE KLING CLIPS ON OUR SONG · slide and speed each to the beat, watch the cuts', 'do': 'movetime', 'value': fid,
                  'audio': _src(conf, f'{fid}/music', 'minute_final.wav'), 'beats': beats, 'downbeats': downbeats, 'rows': rows,
                  'under': 'the dot under the picture lights on every beat (white on the first of the bar) · click a slot number to play from just before its cut · MOVE: the strip is the whole clip, the green window the part the slot plays (drag it) · a slider moved while paused shows that slot at its cut'},
           {'kind': 'press', 'do': 'moveauto', 'value': fid, 'label': 'AUTO SPEED (each clip\'s own rhythm onto our beat)'},
           {'kind': 'press', 'do': 'movebake', 'value': fid, 'label': 'BAKE ALL (make the movement minute as set)'},
           {'kind': 'press', 'do': 'movereset', 'value': fid, 'label': 'RESET ALL (every slot back to MOVE 0, SPEED 1x)', 'confirm': 'Put every slot back to MOVE 0 and SPEED 1x?'}]
    out += _bake_line(conf, fid, 'movement', 'the movement minute')
    return out


# ============ PART 12 · LIPS (the owner 2026-10-29: "we dont need a button send to lips we will make that a new tool after this"; "and next.. we have the
# lips in a brand new section"; "and in the UI have an on off for lips so we can control on or off"). Each slot's lips ON or OFF (a slot with no face, the
# mouth alone or the hand, starts OFF); MAKE LIPS sends the baked movement of the ON slots to the Exxact in the background (tools/lips/lips_send.py,
# detached): Rumpel cut onto green with a wide mouth box, PF Lip-sync to our vocals, only the new mouth laid back on the baked clip (the owner: "we had to
# cut the guy out with a green screen for better results and our mask box could not be too small"; "the green screen cut out is just to get the lips
# accurate then you put them directly on the original"); the lips minute (cell 4) is the lips where ON and made, the baked movement elsewhere.
LIPS_SEND = os.path.join(SCRATCH, 'tools', 'lips', 'lips_send.py')
LIPS_NO_FACE = {4, 6}   # F-0004: slot 4 is his mouth alone, slot 6 his hand: no face for the mouth tool


def _lips_on(con, fid):
    """each slot's switch -> {n: True/False} (a slot never switched: ON, but the slots with no face)"""
    got = {r['n']: bool(r['lips']) for r in con.execute('SELECT n, lips FROM lipsset WHERE film = ?', (fid,))}
    return {n: got.get(n, n not in LIPS_NO_FACE) for n, _a, _s in _move_slots(con, fid)}


def lips_press(store, do, one, conf):
    """a slot's ON/OFF; MAKE LIPS (in the background)"""
    con = _db(store)
    try:
        fid, _, rest = one('value').partition(':')
        if not _film(con, fid):
            return f'refused · no project {fid}'
        if do == 'lipsswitch':
            n_, _, to = rest.partition(':')
            try:
                n = int(n_)
            except ValueError:
                return 'refused · no slot'
            con.execute('INSERT INTO lipsset (film, n, lips, made_at) VALUES (?, ?, ?, ?) ON CONFLICT(film, n) DO UPDATE SET lips = excluded.lips, made_at = excluded.made_at',
                        (fid, n, 1 if to == 'on' else 0, _now()))
            con.commit()
            went = _comp_follow(store, con, conf, fid)   # the owner 2026-10-30: "changes in 12 dont move to 13": its composition is made again from the clip it has now
            return f"LIPS {'ON' if to == 'on' else 'OFF'} · {fid} slot {n}" + (f" · step 13 composing it again" if n in went else '')
        home = os.path.join(conf['films'], fid)
        if not all(os.path.exists(os.path.join(home, 'movement', f'baked_{n}.mp4')) for n, _a, _s in _move_slots(con, fid)):
            return 'MAKE LIPS refused · BAKE ALL in step 11 first'
        if not os.path.exists(os.path.join(home, 'music', 'minute_vocals.wav')):
            return 'MAKE LIPS refused · the minute has no vocals (step 1 makes them)'
        on = [n for n, v in _lips_on(con, fid).items() if v]
        if not on:
            return 'MAKE LIPS refused · every slot is OFF'
        if (_read(os.path.join(home, 'lips', 'status.json'), {}) or {}).get('state') in ('sending', 'running', 'bringing home'):
            return 'MAKE LIPS refused · a lips run is already going'
        os.makedirs(os.path.join(home, 'lips'), exist_ok=True)
        _write(os.path.join(home, 'lips', 'status.json'), {'state': 'sending', 'slots': {str(n): 'waiting its turn' for n in on}})   # the page that comes back follows it at once
        with open(os.path.join(home, 'lips', 'send.log'), 'ab') as log:
            subprocess.Popen(['python3', LIPS_SEND, conf['films'], fid, ','.join(map(str, on)), store.db_path if hasattr(store, 'db_path') else str(store)], stdout=log, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL, start_new_session=True)
        return f"MAKING LIPS · {fid} · slots {', '.join(map(str, on))} · on the Exxact in the background, about 10 minutes a slot; each slot's state shows here"
    finally:
        con.close()


def lips_parts(con, f, conf):
    """PART 12 ON THE PAGE · LIPS: each slot ON or OFF and how its lips go, MAKE LIPS, the lips minute"""
    fid = f['id']
    head = {'kind': 'step', 'n': 12, 'title': 'LIPS',
            'under': 'his mouth to our vocals on the baked movement · each slot ON or OFF · MAKE LIPS runs on the Exxact in the background (him cut onto green, a wide mouth box, only the new mouth laid back) · OFF keeps the slot as baked'}
    slots = _move_slots(con, fid)
    if not slots or not all(os.path.exists(os.path.join(conf['films'], fid, 'movement', f'baked_{n}.mp4')) for n, _a, _s in slots):
        return [head, {'kind': 'note', 'title': '12 · waits for step 11', 'text': 'BAKE ALL in step 11 first'}]
    on = _lips_on(con, fid)
    st = _read(os.path.join(conf['films'], fid, 'lips', 'status.json'), {}) or {}
    live = st.get('state') in ('sending', 'running', 'bringing home')
    rows = []
    for n, at, sec in slots:
        word = (st.get('slots') or {}).get(str(n), '')
        made = os.path.exists(os.path.join(conf['films'], fid, 'lips', f'lips_{n}.mp4'))
        cell = {'word': 'ON' if on[n] else 'OFF', 'text': (word or ('made' if made else 'not made yet')) if on[n] else ('no face for the mouth tool' if n in LIPS_NO_FACE else 'kept as baked')}
        if on[n]:
            cell['poll'] = str(n)   # its words follow the run in place, the page never reloads (the owner 2026-10-29: "the page keeps relaoding and not text status")
        rows.append({'key': f'{fid}:{n}', 'cells': [str(n), f'{_mmss(at)}-{_mmss(at + sec)} · {sec} s', cell],
                     'presses': [{'do': 'lipsswitch', 'value': f"{fid}:{n}:{'off' if on[n] else 'on'}", 'label': 'TURN OFF' if on[n] else 'TURN ON', 'cell': 2}]})
    # THE LIPS' OWN PLAYER (the owner 2026-10-29: "lips needs its own video player"): step 11's player with nothing to set, on our song: each slot its lips when
    # they are home, else its baked movement; a slot whose lips come home while the page is open takes them in place (the run followed on the page says so)
    prow = []
    for n, at, sec in slots:
        lp = os.path.join(conf['films'], fid, 'lips', f'lips_{n}.mp4')
        made = on[n] and os.path.exists(lp)
        path = lp if made else os.path.join(conf['films'], fid, 'movement', f'baked_{n}.mp4')
        prow.append({'n': n, 'label': f"{n} · {'LIPS' if made else ('LIPS ON' if on[n] else 'LIPS OFF')}", 'video': _src(conf, f'{fid}/lips' if made else f'{fid}/movement', os.path.basename(path)),
                     'start': at, 'seconds': sec, 'length': _length(path), 'offset': 0, 'speed': 1,
                     **({'swap': f"{conf['films_url']}/{fid}/lips/lips_{n}.mp4"} if on[n] and not made else {})})
    player = {'kind': 'cliptime', 'fixed': True, 'title': '12 · THE LIPS PLAYER · on our song', 'audio': _src(conf, f'{fid}/music', 'minute_final.wav'), 'rows': prow,   # no beat dot here (the owner 2026-10-30: "we dont need the green blinking dot for the lips")
                'under': 'each slot its lips when they are made, its baked movement until then (a slot made while you watch comes in by itself) · click a slot number to play from just before its cut'}   # on top of the panel (the owner 2026-10-30: "put the player on top of the lips panel not below")
    out = [head, player, {'kind': 'table', 'title': f"12 · LIPS · {sum(on.values())} of {len(slots)} ON" + (f" · {str(st.get('state', '')).upper()}" if st else ''),
                  'columns': ['Slot', 'In the minute', 'Lips'], 'rows': rows},
           {'kind': 'poll', 'src': _src(conf, f'{fid}/lips', 'status.json'), 'live': live, 'media': f'/{fid}/lips/minute_lips.mp4',
            'text': ('THE RUN · ' + str(st.get('state', '')).upper()) if st else 'no lips run yet'},
           {'kind': 'press', 'do': 'lipsmake', 'value': fid, 'label': 'MAKE LIPS (the ON slots, in the background)'}]
    if st.get('state') == 'failed':
        out.append({'kind': 'note', 'title': '12 · the lips run stopped', 'text': str(st.get('why', ''))[:400]})
    return out


# ============ PART 13 · COMPOSITION (the owner 2026-10-30: "next after we need a new section for Composition and we have that tool already in larry 5 and larry 6 a new
# one / we need to use the avatar and composition tools to adjust each clip / this is a brand new section"; "its a reference match tool"; "has the compostion built into
# it"; "all clips"; green behind, as LARRY 5; "just use the avatars we have christensen and corinne"; "basically same setup with all the adjustments the same"): LARRY 5's
# PF REFERENCE MATCH, a block a slot, on a frame of the slot's clip (its lips where made, else its baked movement): the ONE composition stage (THE SHOT, ORIENTATION, ON THE
# GRID, MOVE + RESIZE with TILT and SQUISH, SNAP, ROTATE, the TRAINING AREA), LARRY 5's own avatars (M Christensen, F Corinne) and golden-ratio grid; SAVE keeps the eleven
# values (composition); BAKE ALL lays each clip on the 16:9 frame by the stage's own maths (artApply: fit, x scale, x squish, moved, tilted about its middle), green
# #00B140 where nothing is, in the background -> composition/comp_N.mp4 and the composition minute.
COMP_VIEWS = ('front', '3_4_right', 'side_right', '3_4_back_right', 'back', '3_4_back_left', 'side_left', '3_4_left')
COMP_SIZES = ('WS', 'FS', 'MWS', 'MS', 'MCU', 'CU', 'ECU')
COMP_GREEN = '0x00B140'
COMP_W, COMP_H = 1280, 720


def _comp_src(con, conf, fid, n):
    """the clip a slot's composition is made from, by step 12's own rule (its player's): its lips where the slot is ON and they are made, else its baked movement
    (the owner 2026-10-30: "changes in 12 dont move to 13"; the lips minute's pieces in lips/fit are made once at a run's end and never knew a later ON or OFF)"""
    lp = os.path.join(conf['films'], fid, 'lips', f'lips_{n}.mp4')
    if _lips_on(con, fid).get(n) and os.path.exists(lp):
        return lp
    bp = os.path.join(conf['films'], fid, 'movement', f'baked_{n}.mp4')
    return bp if os.path.exists(bp) else ''


# TWO FILES A SLOT (the owner 2026-10-30: "but should it just have 2 files"; "1 lips on 1 lips off and it knows"; "instead of updating one file"): each slot set in step 13
# keeps its composition made from both its clips, composition/comp_N_lips.mp4 (from its lips) and comp_N_move.mp4 (from its baked movement), each with a note of what it
# was made from (comp_N_<which>.json: the clip, its time, the values); step 12's switch only picks which one lands, nothing is made again.
COMP_WHICH = ('lips', 'move')


def _comp_srcs(conf, fid, n):
    """a slot's two clips -> {'lips': its lips (when made), 'move': its baked movement}"""
    lp, bp = os.path.join(conf['films'], fid, 'lips', f'lips_{n}.mp4'), os.path.join(conf['films'], fid, 'movement', f'baked_{n}.mp4')
    return {k: p for k, p in (('lips', lp), ('move', bp)) if os.path.exists(p)}


def _comp_which(con, conf, fid, n):
    """which of the two lands now: 'lips' where the slot is ON and its lips are made, else 'move'"""
    return 'lips' if _lips_on(con, fid).get(n) and 'lips' in _comp_srcs(conf, fid, n) else 'move'


def _comp_file(conf, fid, n, which):
    return os.path.join(conf['films'], fid, 'composition', f'comp_{n}_{which}.mp4')


def _comp_saved(con, fid, n):
    """a slot's saved values (a slot never set: OFF; one saved before OFF was kept: its 6K) -> (values, set at all)"""
    r = con.execute('SELECT vals FROM composition WHERE film = ? AND n = ?', (fid, n)).fetchone()
    return ({'frame': '6k', **json.loads(r['vals'])}, True) if r is not None else (_comp_vals({'FRAME': 'off'}), False)


def _comp_fresh(con, conf, fid, n, which, v=None):
    """one of a slot's two files made from that clip as it is now and the values saved now -> True"""
    src, out = _comp_srcs(conf, fid, n).get(which), _comp_file(conf, fid, n, which)
    if not src or not os.path.exists(out):
        return False
    note = _read(out[:-4] + '.json', {}) or {}
    return (note.get('source') == os.path.relpath(src, os.path.join(conf['films'], fid)) and note.get('source_mtime') == os.path.getmtime(src)
            and note.get('vals') == (v if v is not None else _comp_saved(con, fid, n)[0]))


def _comp_made(con, conf, fid, n):
    """the slot's composed file that lands now, when it is up to date -> its path, or ''"""
    which = _comp_which(con, conf, fid, n)
    return _comp_file(conf, fid, n, which) if _comp_fresh(con, conf, fid, n, which) else ''


def _comp_stale(con, conf, fid, n, src=None):
    """a slot set in step 13 with one of its two files missing or out of date -> True"""
    if not _comp_saved(con, fid, n)[1]:
        return False
    return not all(_comp_fresh(con, conf, fid, n, w) for w in _comp_srcs(conf, fid, n))


def _comp_start(store, conf, fid, n, sec, v=None, seq=None):
    """ONE SLOT COMPOSED IN THE BACKGROUND, its state in composition/slot_N.json (the block follows it and the player above takes the clip in place); a compose
    overtaken by a newer one of the same slot is not laid down, and its 'made' is never written over the newer one's state"""
    st = os.path.join(conf['films'], fid, 'composition', f'slot_{n}.json'); seq = seq or _now()
    _write(st, {'state': 'composing', 'seq': seq, 'at': _now(), 't': time.time()})
    latest = lambda: (_read(st, {}) or {}).get('seq') == seq   # noqa: E731
    def work():
        c = _db(store)
        try:
            now = _comp_which(c, conf, fid, n)   # the one that lands first, so the player takes it at once; then the other, so the switch in 12 never waits
            for which in [now] + [w for w in COMP_WHICH if w != now and w in _comp_srcs(conf, fid, n)]:
                if which != now and _comp_fresh(c, conf, fid, n, which, v):
                    continue
                out_, _v = comp_one(c, conf, fid, n, sec, v, latest, which)
                if not out_ or not latest():
                    return
                _write(st, {'state': 'made', 'seq': seq, 'at': _now(), 'busy': which == now, 't': time.time()})
            _write(st, {'state': 'made', 'seq': seq, 'at': _now()})
        except Exception as e:   # noqa: BLE001 - said in the block
            if latest():
                _write(st, {'state': 'failed', 'seq': seq, 'why': str(e)[:200], 'at': _now()})
        finally:
            c.close()
    threading.Thread(target=work, daemon=True).start()


def _comp_follow(store, con, conf, fid):
    """STEP 12'S CHANGES REACH 13: each slot set in step 13 whose two files are not both made from its clips of now (new lips, a new bake, files from before the two)
    is composed again, with its saved values, in the background (once: not while it is composing, unless that compose is over ten minutes old); a switch in 12 needs
    nothing made -> the slots started"""
    home = os.path.join(conf['films'], fid, 'composition')
    went = []
    for n, _a, sec in _move_slots(con, fid):
        if not _comp_stale(con, conf, fid, n):
            continue
        st = _read(os.path.join(home, f'slot_{n}.json'), {}) or {}
        if (st.get('state') == 'composing' or st.get('busy')) and time.time() - float(st.get('t') or 0) < 600:
            continue
        _comp_start(store, conf, fid, n, sec)
        went.append(n)
    return went


def _comp_assets(conf):
    """LARRY 5's static references, copied from production (cdn sites 290c5204 and faf51f39): the golden-ratio grid and the avatar set, 8 views x M/F"""
    base = f"{conf['scratch_url']}/composition_assets"
    home = os.path.join(SCRATCH, 'composition_assets')
    av = {os.path.basename(x)[len('avatars_avatar_'):-4]: f'{base}/{os.path.basename(x)}' for x in sorted(os.listdir(home)) if x.startswith('avatars_avatar_')} if os.path.isdir(home) else {}
    return {'grid': f'{base}/DA-M_5829C2EB28A9_F7BF.png', 'avatar': f'{base}/DA-M_0F5B0EB02453_9845.png', 'avatars': av}


def _comp_vals(raw):
    """the eleven values, checked as LARRY 5's server checks them (_RM_FIELDS) -> the values, or raises ValueError"""
    f = lambda k, lo, hi, d: max(lo, min(hi, float(raw.get(k) if raw.get(k) not in (None, '') else d)))   # noqa: E731
    v = {'view': raw.get('VIEW') or 'front', 'bio': raw.get('BIO') or 'm', 'size': raw.get('SIZE') or 'FS', 'snap': raw.get('SNAP') or '', 'frame': raw.get('FRAME') or '6k',
         'scale': f('SCALE', 0.2, 3, 1), 'dx': f('DX', -5, 5, 0), 'dy': f('DY', -5, 5, 0), 'rot': f('ROT', -180, 180, 0), 'sx': f('SQX', 0.2, 5, 1), 'sy': f('SQY', 0.2, 5, 1)}
    if v['view'] not in COMP_VIEWS or v['bio'] not in ('m', 'f') or v['size'] not in COMP_SIZES or v['snap'] not in ('', 'h', 'v') or v['frame'] not in ('off', '6k', '4k'):
        raise ValueError('a value is not one of the stage\'s')
    return v


def _comp_place(v, iw, ih, fw=COMP_W, fh=COMP_H):
    """THE STAGE'S OWN MATHS (PFCompositionStage.artApply, LARRY 5): fit (cover; the height for SNAP TOP + BOTTOM; the width for SNAP SIDES), x scale, x squish, the
    middle moved by dx, dy of the frame -> (dw, dh, middle x, middle y)"""
    k = fh / ih if v['snap'] == 'v' else fw / iw if v['snap'] == 'h' else max(fw / iw, fh / ih)
    k *= v['scale']
    dw, dh = iw * k * v['sx'], ih * k * v['sy']
    return dw, dh, (fw - dw) / 2 + v['dx'] * fw + dw / 2, (fh - dh) / 2 + v['dy'] * fh + dh / 2


def comp_one(con, conf, fid, n, sec, v=None, latest=None, which=None):
    """ONE OF A SLOT'S TWO FILES COMPOSED: that clip (which: 'lips' or 'move'; the one that lands now when not said) laid on the frame as its stage says (green behind),
    its own seconds at 30 fps -> composition/comp_N_<which>.mp4, its note and its version"""
    home = os.path.join(conf['films'], fid, 'composition'); os.makedirs(home, exist_ok=True)
    which = which or _comp_which(con, conf, fid, n)
    src = _comp_srcs(conf, fid, n).get(which)
    if not src:
        raise ValueError(f'slot {n} has no {"lips" if which == "lips" else "clip"} yet (step 11 or 12)')
    if v is None:
        v = _comp_saved(con, fid, n)[0]
    saved_v = dict(v)
    def lay(part, out, settings):   # laid down with its note (what it was made from), unless a newer save of this slot came in while it was made
        if latest is not None and not latest():
            os.remove(part)
            return False
        os.replace(part, out)   # the player never sees it half made
        _write(out[:-4] + '.json', {'source': os.path.relpath(src, os.path.join(conf['films'], fid)), 'source_mtime': os.path.getmtime(src), 'vals': saved_v, 'made': _now()})
        _version(con, fid, 'composition', n, {**settings, 'which': which}, os.path.relpath(out, os.path.join(conf['films'], fid)))
        return True
    if v.get('frame') == 'off':   # OFF (the owner 2026-10-30: "should have an OFF first so it doent use the controls just the original version baked before this"): the clip as it came
        out = _comp_file(conf, fid, n, which); part = out[:-4] + f'.{os.getpid()}.{threading.get_ident()}.part.mp4'
        _ff(['-i', src, '-an', '-vf', f'fps=30,scale={COMP_W}:{COMP_H}:force_original_aspect_ratio=decrease,pad={COMP_W}:{COMP_H}:-1:-1,tpad=stop_mode=clone:stop_duration=2', '-t', str(sec),
             '-c:v', 'libx264', '-crf', '15', '-pix_fmt', 'yuv420p', part], f'slot {n} as it came')
        if not lay(part, out, {'frame': 'off', 'seconds': sec, 'source': os.path.relpath(src, os.path.join(conf['films'], fid)), 'source_sha': _sha(src)}):
            return None, v
        return out, {**v, 'size': 'OFF', 'view': 'as it came', 'scale': 1.0}
    p = subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=width,height', '-of', 'csv=p=0', src], capture_output=True, text=True)
    iw, ih = (int(x) for x in p.stdout.strip().split(',')[:2])
    # THE FRAME (the owner 2026-10-30: "a 4k button in each row ... to resize to the 4k canvas"; "when we tilt or move things the gaps need to swap to 4k"; "its really
    # just zooming in to show the 4k space in the 6k space"): the stage's artboard is the 6K frame; 4K is its middle 62.5% (3840 of 6144). For 4K the board is laid at
    # 2048x1152 and its middle 1280x720 cut out, so the window fills the frame unenlarged and the green the tilt or the move leaves at the 6K edge falls outside it
    k4 = v.get('frame') == '4k'
    bw, bh = (round(COMP_W / 0.625), round(COMP_H / 0.625)) if k4 else (COMP_W, COMP_H)
    dw, dh, cx, cy = _comp_place(v, iw, ih, bw, bh)
    a = v['rot'] * 3.141592653589793 / 180   # + turns clockwise, as the stage's CSS rotate and ffmpeg's rotate both do
    out = _comp_file(conf, fid, n, which)
    fg = f"[0:v]fps=30,scale={max(2, round(dw))}:{max(2, round(dh))},format=rgba,rotate={a:.6f}:ow=rotw({a:.6f}):oh=roth({a:.6f}):c=none[fg]"
    cut = f",crop={COMP_W}:{COMP_H}:{(bw - COMP_W) // 2}:{(bh - COMP_H) // 2}" if k4 else ''
    part = out[:-4] + f'.{os.getpid()}.{threading.get_ident()}.part.mp4'   # its own part: a SAVE's compose and a BAKE ALL never share one
    _ff(['-i', src, '-f', 'lavfi', '-i', f'color=c={COMP_GREEN}:s={bw}x{bh}:r=30:d={sec}', '-filter_complex',
         f"{fg};[1:v][fg]overlay=x={cx:.3f}-overlay_w/2:y={cy:.3f}-overlay_h/2:eof_action=repeat{cut},format=yuv420p[v]", '-map', '[v]', '-an', '-t', str(sec),
         '-c:v', 'libx264', '-crf', '15', part], f'slot {n} composed')
    if not lay(part, out, {**v, 'seconds': sec, 'source': os.path.relpath(src, os.path.join(conf['films'], fid)), 'source_sha': _sha(src), 'size_out': [COMP_W, COMP_H], 'board': [bw, bh], 'green': COMP_GREEN}):
        return None, v
    return out, v


def comp_bake(con, conf, fid):
    """BAKE ALL: each slot's clip laid on the frame as its stage says (green behind), its own seconds at 30 fps -> composition/comp_N.mp4 and the minute"""
    home = os.path.join(conf['films'], fid, 'composition'); os.makedirs(home, exist_ok=True)
    parts, said = [], []
    for n, _at, sec in _move_slots(con, fid):
        out, v = comp_one(con, conf, fid, n, sec)   # the one that lands now, then the other of the two
        for other in [w for w in COMP_WHICH if w != _comp_which(con, conf, fid, n) and w in _comp_srcs(conf, fid, n)]:
            comp_one(con, conf, fid, n, sec, which=other)
        parts.append(out); said.append(f"{n} {v['size']} {v['view']} x{v['scale']:.2f}")
    lst = os.path.join(home, 'comp.txt')
    with open(lst, 'w') as f:
        f.write(''.join(f"file '{p}'\n" for p in parts))
    _ff(['-f', 'concat', '-safe', '0', '-i', lst, '-i', os.path.join(conf['films'], fid, 'music', 'minute_final.wav'), '-map', '0:v', '-map', '1:a', '-t', str(TOTAL),
         '-c:v', 'libx264', '-crf', '18', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '256k', '-movflags', '+faststart', os.path.join(home, 'minute_composition.part.mp4')], 'the composition minute')
    os.replace(os.path.join(home, 'minute_composition.part.mp4'), os.path.join(home, 'minute_composition.mp4'))   # the players never see it half made
    _version(con, fid, 'composition_minute', 0, {'slots': said, 'song_sha': _sha(os.path.join(conf['films'], fid, 'music', 'minute_final.wav'))}, 'composition/minute_composition.mp4')
    return ' · '.join(said)


def comp_press(store, do, one, conf):
    """a slot's SAVE (the eleven values and its training area); BAKE ALL in the background"""
    con = _db(store)
    try:
        fid, _, n_ = one('value').partition(':')
        if not _film(con, fid):
            return f'refused · no project {fid}'
        home = os.path.join(conf['films'], fid, 'composition'); os.makedirs(home, exist_ok=True)
        if do == 'compsave':
            try:
                n = int(n_); v = _comp_vals({k: one(k) for k in ('VIEW', 'BIO', 'SIZE', 'SCALE', 'DX', 'DY', 'ROT', 'SNAP', 'SQX', 'SQY', 'FRAME')})
            except ValueError as e:
                return f'SAVE refused · {e}'
            r = con.execute('SELECT mask FROM composition WHERE film = ? AND n = ?', (fid, n)).fetchone()
            mask = r['mask'] if r is not None else ''
            m = one('MASK')
            if m.startswith('data:image/png;base64,'):   # THE TRAINING AREA, one PNG at the frame's own size (LARRY 5 kept it on DA-M; here beside the slot)
                import base64
                mask = f'mask_{n}.png'
                with open(os.path.join(home, mask), 'wb') as fh:
                    fh.write(base64.b64decode(m.split(',', 1)[1]))
            elif m == '':
                mask = ''
            con.execute('INSERT INTO composition (film, n, vals, mask, made_at) VALUES (?, ?, ?, ?, ?) ON CONFLICT(film, n) DO UPDATE SET vals = excluded.vals, mask = excluded.mask, made_at = excluded.made_at',
                        (fid, n, json.dumps(v), mask, _now()))
            con.commit()
            # THE SLOT COMPOSED AT ONCE (the owner 2026-10-30: "does the composition change the player above it? i pressed save and i dont see the video"): in the
            # background; its state in composition/slot_N.json, which the block reads until the player above takes the new clip
            # SAVED BY ITSELF (the owner 2026-10-30: "the composition should auto save"): the page sends each save its number (SEQ); a compose overtaken by a newer save
            # of the same slot is not laid down, and its 'made' is never written over the newer save's state
            sec = dict((k, c) for k, _a, c in _move_slots(con, fid)).get(n)
            if sec and _comp_src(con, conf, fid, n):
                _comp_start(store, conf, fid, n, sec, v, one('SEQ'))
            return f"SAVED · {fid} slot {n} · {v['size']} {v['view']} {v['bio'].upper()} · x{v['scale']:.2f} · tilt {v['rot']:+.1f} · composing it now"
        st = os.path.join(home, 'bake.json')
        if (_read(st, {}) or {}).get('state') == 'baking':
            return 'BAKE refused · a bake is already going'
        if not all(_comp_src(con, conf, fid, n) for n, _a, _s in _move_slots(con, fid)):
            return 'BAKE refused · a slot has no clip yet (step 11 or 12)'
        _write(st, {'state': 'baking', 'started': _now()})
        def work():
            c = _db(store)
            try:
                _write(st, {'state': 'baked', 'said': comp_bake(c, conf, fid), 'ended': _now()})
            except Exception as e:   # noqa: BLE001 - said on the page
                _write(st, {'state': 'failed', 'said': str(e)[:300], 'ended': _now()})
            finally:
                c.close()
        threading.Thread(target=work, daemon=True).start()
        return f'BAKING · {fid} · the composition in the background, the page is free; it says BAKED here when the minute is made'
    finally:
        con.close()


def _comp_poster(conf, fid, n, src):
    """a frame from the middle of the slot's clip, the picture its stage stands on (made again when the clip is) -> its file name in composition/"""
    home = os.path.join(conf['films'], fid, 'composition'); os.makedirs(home, exist_ok=True)
    out = os.path.join(home, f"frame_{n}_{os.path.basename(os.path.dirname(src))}.jpg")   # its lips' frame and its baked movement's apart: turning lips ON or OFF shows the right one
    if not os.path.exists(out) or os.path.getmtime(out) < os.path.getmtime(src):
        _ff(['-ss', f'{_length(src) / 2:.3f}', '-i', src, '-frames:v', '1', '-q:v', '2', out], f'slot {n} frame')
    return os.path.basename(out)


def comp_parts(con, f, conf):
    """PART 13 ON THE PAGE · COMPOSITION: the player on top, PF REFERENCE MATCH a slot, BAKE ALL and how it went"""
    fid = f['id']
    head = {'kind': 'step', 'n': 13, 'title': 'COMPOSITION',
            'under': 'PF REFERENCE MATCH from LARRY 5 for every slot: THE SHOT, ORIENTATION, ON THE GRID, MOVE + RESIZE (tilt, squish), SNAP, ROTATE, the TRAINING AREA, against LARRY 5\'s avatars (M Christensen, F Corinne) · SAVE each · BAKE ALL lays the clips (green behind)'}
    slots = _move_slots(con, fid)
    if not slots or not all(_comp_src(con, conf, fid, n) for n, _a, _s in slots):
        return [head, {'kind': 'note', 'title': '13 · waits for steps 11 and 12', 'text': 'BAKE ALL in step 11 first (the lips come in when made)'}]
    _comp_follow(con.execute('PRAGMA database_list').fetchone()[2], con, conf, fid)   # step 12's changes reach 13 by themselves
    saved = {r['n']: r for r in con.execute('SELECT * FROM composition WHERE film = ?', (fid,))}
    assets = _comp_assets(conf)
    home = os.path.join(conf['films'], fid, 'composition')
    prow, blocks = [], []
    for n, at, sec in slots:
        src = _comp_src(con, conf, fid, n)
        made = _comp_made(con, conf, fid, n)
        show = made or src   # the composed file of the clip that lands now (lips ON or OFF in 12), as it came until it is made
        prow.append({'n': n, 'label': f"{n} · {'COMPOSED' if show == made else 'AS IT CAME'}", 'video': _src(conf, os.path.relpath(os.path.dirname(show), conf['films']), os.path.basename(show)),
                     'start': at, 'seconds': sec, 'length': _length(show), 'offset': 0, 'speed': 1})
        r = saved.get(n)
        v = json.loads(r['vals']) if r is not None else {}
        frame = _comp_poster(conf, fid, n, src)
        blocks.append({'n': n, 'value': f'{fid}:{n}', 'label': f'SLOT {n} · {_mmss(at)}-{_mmss(at + sec)} · {sec} s',
                       'composing': (lambda j: j.get('seq') if j.get('state') == 'composing' else '')(_read(os.path.join(home, f'slot_{n}.json'), {}) or {}),
                       'status': f"{conf['films_url']}/{fid}/composition/slot_{n}.json", 'made': f"{conf['films_url']}/{fid}/composition/comp_{n}_{_comp_which(con, conf, fid, n)}.mp4",
                       'line': (('saved: OFF · the clip as it came' if v.get('frame') == 'off' else f"saved: {v.get('size')} · {str(v.get('view', '')).replace('_', ' ')} · {str(v.get('bio', '')).upper()} · x{float(v.get('scale', 1)):.2f} · {str(v.get('frame', '6k')).upper()}") if v else 'OFF · the clip as it came (not set yet)')
                       + f" · from {os.path.relpath(src, os.path.join(conf['films'], fid))}",
                       'src': _src(conf, f'{fid}/composition', frame), 'mask': _src(conf, f'{fid}/composition', r['mask']) if r is not None and r['mask'] else '',
                       'vals': {'view': v.get('view'), 'bio': v.get('bio'), 'size': v.get('size'), 'scale': v.get('scale'), 'dx': v.get('dx'), 'dy': v.get('dy'), 'rot': v.get('rot'),
                                'snap': v.get('snap'), 'sx': v.get('sx'), 'sy': v.get('sy'), 'frame': v.get('frame', '6k')} if v else {'frame': 'off'}, 'assets': assets,
                       **({'last': {k: lv.get(k, '6k' if k == 'frame' else None) for k in ('view', 'bio', 'size', 'scale', 'dx', 'dy', 'rot', 'snap', 'sx', 'sy', 'frame')}} if (lv := _last_version(con, fid, 'composition', n)) else {})})
    out = [head, {'kind': 'cliptime', 'fixed': True, 'player': 'composition', 'title': '13 · THE COMPOSITION PLAYER · on our song', 'audio': _src(conf, f'{fid}/music', 'minute_final.wav'), 'rows': prow,
                  'under': 'each slot as composed once BAKE ALL has made it, as it came until then · click a slot number to play from just before its cut'},
           {'kind': 'compstage', 'title': '13 · PF REFERENCE MATCH · a slot at a time', 'do': 'compsave', 'rows': blocks,
            'under': 'the frame is from the middle of the slot\'s clip · OFF keeps the slot as it came · 6K the whole board, 4K its middle window · SAVE keeps it and shows it on the player'},
           {'kind': 'press', 'do': 'compbake', 'value': fid, 'label': 'BAKE ALL (lay every clip as set, green behind)'}]
    out += _bake_line(conf, fid, 'composition', 'the composition minute')
    return out


# ============ EXPORT, THE LAST STEP (the owner 2026-10-30: "a new 14 section but dont call it 14 call it export and have it on the bottom"; "we have tools in larry 5 for
# this"; "you pick the ouput format"; "it has a table with all the sizes and usage"; "then it asks if you want a logo or not"; "then you can shift it left or right only";
# "for example we want to export 30 seconds for instagram reel size"; "it will bake it and make the export file and save it in the downloads"; "make sure to use the exact
# tools we have built before ... it has a french grid system to align it for export"). LARRY 5's RESIZE AND UPSCALE, carried over as it is (production backup,
# wid_tool_slots_positivefeedback_data.py _RZ_LAYOUTS / _RZ_LOGO_MAP / _rz_crop_rect and inc_widget_resize_upscale.html): the same layouts, the same 6K master
# canvas (6144x3456, cover, never gaps), the crop within the 4K zone, the horizontal shift clamped to 18.75% either way, the layout's own French grid and the horizontal
# grid on the stage, the layout-locked 6K logo (PRO or RETRO, its variants), now laid on our minute's frames and its seconds; the file goes to the Downloads.
EXPORT_ASSETS = os.path.join(SCRATCH, 'export_assets')   # LARRY 5's layouts/ (grids, logos, logos_6k) and its horizontal grid (DA-M_31026C97358E_406B.png as hgrid.png)
EXPORT_LAYOUTS = [
    # (layout, group, shape, w, h, use, overlay, renderable): LARRY 5's roster, verbatim
    ('1080x1080',  'VERTICAL',   'Square',          1080, 1080, 'Instagram Feed, Facebook Post, LinkedIn', '1080x1080.png', True),
    ('1080x1350',  'VERTICAL',   'Portrait 4:5',    1080, 1350, 'Instagram Portrait, Facebook Portrait',   '1080x1350.png', True),
    ('1080x1920',  'VERTICAL',   'Story 9:16',      1080, 1920, 'Instagram Story, TikTok, Snapchat, Reels', '1080x1920.png', True),
    ('2550x3300',  'VERTICAL',   'Print 8.5x11',    2550, 3300, 'US Letter Portrait, Brochure, Flyer',     '2550x3300.png', True),
    ('1080x566',   'HORIZONTAL', 'Banner 1.9:1',    1080, 566,  'Website Hero, Twitter/X Header',          '1080x566.png',  True),
    ('3300x2550',  'HORIZONTAL', 'Print 11x8.5',    3300, 2550, 'US Letter Landscape, Presentation',       '3300x2550.png', True),
    ('2560x1440',  'HORIZONTAL', '2K',              2560, 1440, 'Desktop Wallpaper, YouTube Thumbnail',    '16x9.png',      True),
    ('3840x2160',  'HORIZONTAL', '4K',              3840, 2160, 'TV, Desktop 4K, Digital Signage',         '16x9.png',      True),
    ('6144x3456',  'HORIZONTAL', '6K',              6144, 3456, 'Full Canvas (no crop)',                   '16x9.png',      True),
    ('7680x4320',  'HORIZONTAL', '8K',              7680, 4320, '8K Display, Large Format Digital',        '16x9.png',      False),
    ('12288x6480', 'HORIZONTAL', '12K',            12288, 6480, 'Billboard, Ultra-Wide Print',             '12k.png',       False),
]
EXPORT_LOGOS = {
    '1080x1080':  {'pro': ['pro_1080x1080.png'], 'retro': ['retro_1080x1080.png']},
    '1080x1350':  {'pro': ['pro_1080x1350.png'], 'retro': ['retro_1080x1350.png']},
    '1080x1920':  {'pro': ['pro_1080x1920.png'], 'retro': ['retro_1080x1920.png']},
    '1080x566':   {'pro': ['pro_1080x566.png'],  'retro': ['retro_1080x566.png']},
    '2550x3300':  {'pro': ['pro_2550x3300.png'], 'retro': ['retro_2550x3300.png']},
    '3300x2550':  {'pro': ['pro_3300x2550_a.png', 'pro_3300x2550_b.png', 'pro_3300x2550_c.png', 'pro_3300x2550_d.png', 'pro_3300x2550_e.png'], 'retro': ['retro_3300x2550.png']},
    '2560x1440':  {'pro': ['pro_16x9.png'], 'retro': ['retro_16x9.png']},
    '3840x2160':  {'pro': ['pro_16x9.png'], 'retro': ['retro_16x9.png']},
    '6144x3456':  {'pro': ['pro_16x9.png'], 'retro': ['retro_16x9.png']},
}
EXPORT_FILL = '0x101010'   # FILL GAPS (the owner 2026-10-30: "it will put a black color but not pure black over the green layer so you dont see the green screen flaws")
EXPORT_KEY = (0.18, 0.08)   # how near the composition's green (COMP_GREEN) a pixel must be to be filled, and the soft edge: the green gaps only, never his teal or the neon
EXPORT_MAX = 18.75   # LARRY 5's clamp: the shift, a share of the 6K canvas, either way


def _export_crop(out_w, out_h, offset_x_pct, frame='4k'):
    """THE crop math, verbatim from LARRY 5's layout system (_rz_crop_rect): layouts crop as aspect boxes within the 4K zone (3840x2160) centered in the 6K canvas
    (6144x3456); the horizontal offset is a percentage of the display container (1024px = 6144 native), clamped to the canvas. THE FRAME (the owner 2026-10-30: "we
    need a brand new setting for 4k 6k"; "if it is 4k it uses the inner frame and 6k the outer frame"; "its the canvas area"): 6K boxes within the whole canvas instead"""
    zone_w, zone_h = (6144, 3456) if frame == '6k' else (3840, 2160)
    zone_cx, zone_cy = 3072, 1728
    out_aspect = out_w / out_h
    zone_aspect = zone_w / zone_h
    if out_aspect <= zone_aspect:
        crop_h = zone_h
        crop_w = int(round(zone_h * out_aspect))
    else:
        crop_w = zone_w
        crop_h = int(round(zone_w / out_aspect))
    offset_px = (offset_x_pct / 100) * 6144
    cx = zone_cx - offset_px
    cy = zone_cy
    left = int(round(cx - crop_w / 2))
    top = int(round(cy - crop_h / 2))
    left = max(0, min(left, 6144 - crop_w))
    top = max(0, min(top, 3456 - crop_h))
    return left, top, left + crop_w, top + crop_h


def _export_room(out_w, out_h, frame='4k'):
    """how far the size can shift either way before its box meets the canvas edge, in % of the canvas: LARRY 5's 18.75% is exactly the 4K zone's room; in the 6K
    frame a box is bigger and has less (a 16:9 or a banner fills the canvas and has none)"""
    l, _t, r, _b = _export_crop(out_w, out_h, 0, frame)
    return min(EXPORT_MAX, round((6144 - (r - l)) / 2 / 6144 * 100, 2))


def _export_slots(con, conf, fid):
    """WHAT LANDS IN THE EXPORT, A SLOT AT A TIME (the owner 2026-10-30: "how do we know the latest clips have landed down there... for example if i turn off the lips for
    clip 7"): each slot's clip as step 13 has it now: its composed clip where that is made from the slot's clip of now, else the slot's clip of now itself (step 12's rule:
    its lips where ON and made, its baked movement elsewhere) -> [{n, at, sec, path, src, composed, composing, frame}]"""
    home = os.path.join(conf['films'], fid, 'composition')
    out = []
    for n, at, sec in _move_slots(con, fid):
        src = _comp_src(con, conf, fid, n)
        made = _comp_made(con, conf, fid, n)
        fresh = bool(made)
        st = _read(os.path.join(home, f'slot_{n}.json'), {}) or {}
        lv = _comp_saved(con, fid, n)[0]
        out.append({'n': n, 'at': at, 'sec': sec, 'path': made if fresh else src, 'src': src, 'composed': fresh, 'composing': st.get('state') == 'composing',
                    'frame': str(lv.get('frame', '')) if fresh else ''})
    return out


def _export_sig(slots, song):
    """the latest minute's fingerprint: every slot's clip (its file, its time) and the song"""
    import hashlib
    parts = [(x['n'], x['sec'], x['path'], os.path.getmtime(x['path']) if x['path'] and os.path.exists(x['path']) else 0) for x in slots]
    return hashlib.sha256(json.dumps([parts, song, os.path.getmtime(song) if os.path.exists(song) else 0]).encode()).hexdigest()[:16]


def export_latest(con, conf, fid):
    """THE LATEST MINUTE (export/minute_latest.mp4): every slot's clip of now, its own seconds at 30 fps on the 1280x720 frame, one after the other, our song under them;
    made again only when a slot's clip or the song changed -> its path"""
    home = os.path.join(conf['films'], fid, 'export'); os.makedirs(os.path.join(home, 'parts'), exist_ok=True)
    slots, song = _export_slots(con, conf, fid), os.path.join(conf['films'], fid, 'music', 'minute_final.wav')
    out, meta = os.path.join(home, 'minute_latest.mp4'), os.path.join(home, 'minute_latest.json')
    sig = _export_sig(slots, song)
    if os.path.exists(out) and (_read(meta, {}) or {}).get('sig') == sig:
        return out
    if not all(x['path'] for x in slots):
        raise ValueError('a slot has no clip yet (step 11)')
    import hashlib
    parts = []
    for x in slots:   # each slot's piece made once for each file it may come from and kept: a switch in 12 only joins kept pieces again (seconds)
        key = hashlib.sha256(json.dumps([x['path'], os.path.getmtime(x['path']), x['sec']]).encode()).hexdigest()[:12]
        pp = os.path.join(home, 'parts', f'slot_{x["n"]}_{key}.mp4')
        parts.append(pp)
        if os.path.exists(pp):
            continue
        _ff(['-i', x['path'], '-an', '-vf', 'fps=30,scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:-1:-1,setsar=1,tpad=stop_mode=clone:stop_duration=2', '-t', str(x['sec']),
             '-c:v', 'libx264', '-crf', '14', '-pix_fmt', 'yuv420p', '-r', '30', pp + '.part.mp4'], f"slot {x['n']} for the latest minute")
        os.replace(pp + '.part.mp4', pp)
    lst = os.path.join(home, 'parts', 'list.txt')
    with open(lst, 'w') as fh:
        fh.write(''.join(f"file '{p_}'\n" for p_ in parts))
    part = out + f'.{os.getpid()}.{threading.get_ident()}.part.mp4'
    _ff(['-f', 'concat', '-safe', '0', '-i', lst, '-i', song, '-map', '0:v', '-map', '1:a', '-t', str(TOTAL), '-c:v', 'copy',   # the pieces are made alike: joined as they are
         '-c:a', 'aac', '-b:a', '256k', '-movflags', '+faststart', part], 'the latest minute')
    os.replace(part, out)
    _write(meta, {'sig': sig, 'made': _now(), 'slots': [{k: (os.path.relpath(x[k], os.path.join(conf['films'], fid)) if k == 'path' and x[k] else x[k]) for k in ('n', 'sec', 'path', 'composed', 'frame')} for x in slots]})
    return out


def _export_latest_bg(store, conf, fid):
    """the latest minute brought up to date in the background, once (its state in export/minute.json) -> True when it is up to date already"""
    con = _db(store)
    try:
        slots, song = _export_slots(con, conf, fid), os.path.join(conf['films'], fid, 'music', 'minute_final.wav')
        home = os.path.join(conf['films'], fid, 'export')
        if os.path.exists(os.path.join(home, 'minute_latest.mp4')) and (_read(os.path.join(home, 'minute_latest.json'), {}) or {}).get('sig') == _export_sig(slots, song):
            return True
    finally:
        con.close()
    os.makedirs(home, exist_ok=True)
    st = os.path.join(home, 'minute.json')
    j = _read(st, {}) or {}
    if j.get('state') == 'building' and time.time() - float(j.get('t') or 0) < 600:
        return False
    _write(st, {'state': 'building', 't': time.time(), 'at': _now()})
    def work():
        c = _db(store)
        try:
            export_latest(c, conf, fid)
            _write(st, {'state': 'built', 'at': _now()})
        except Exception as e:   # noqa: BLE001 - said on the page
            _write(st, {'state': 'failed', 'why': str(e)[:300], 'at': _now()})
        finally:
            c.close()
    threading.Thread(target=work, daemon=True).start()
    return False


def _export_src(conf, fid):
    """the minute to export: the latest minute (every slot as step 13 has it now) once it is made, else the most finished one there is -> (path, its words)"""
    for folder, name, words in (('export', 'minute_latest.mp4', 'THE LATEST MINUTE (every slot as it is now)'), ('composition', 'minute_composition.mp4', 'THE COMPOSITION MINUTE (13)'), ('lips', 'minute_lips.mp4', 'THE LIPS MINUTE (12)'),
                                ('movement', 'minute_movement.mp4', 'THE MOVEMENT MINUTE (11)')):
        p = os.path.join(conf['films'], fid, folder, name)
        if os.path.exists(p):
            return p, words
    return '', ''


def _export_vals(con, fid):
    """the export's saved settings (a Reel, 30 s from the start, no logo, until set)"""
    r = con.execute('SELECT * FROM exportset WHERE film = ?', (fid,)).fetchone()
    v = {'layout': '1080x1920', 'frame': '4k', 'offset': 0.0, 'logo': 0, 'style': 'pro', 'variant': '', 'start': 0.0, 'seconds': 30.0, 'audio': 1, 'fill': 0}
    if r is not None:
        v.update({k: r[k] for k in v if r[k] is not None})
    return v


def _export_checked(one, src_len):
    """the settings as sent, checked -> the values, or raises ValueError"""
    row = next((l for l in EXPORT_LAYOUTS if l[0] == one('LAYOUT')), None)
    if not row or not row[7]:
        raise ValueError('that size is not available')
    f = lambda k, d: float(one(k) or d)   # noqa: E731
    start = max(0.0, min(f('START', 0), max(0.0, src_len - 1)))
    frame = '6k' if one('FRAME') == '6k' else '4k'; room = _export_room(row[3], row[4], frame)
    return {'layout': row[0], 'frame': frame, 'audio': 0 if one('AUDIO') in ('0', 'off', 'false') else 1, 'fill': 1 if one('FILL') in ('1', 'on', 'true') else 0, 'offset': max(-room, min(room, f('OFFSET', 0))) + 0.0, 'logo': 1 if one('LOGO') in ('1', 'on', 'true') else 0,
            'style': 'retro' if one('STYLE') == 'retro' else 'pro', 'variant': (one('VARIANT') or '')[:1].lower(),
            'start': round(start, 2), 'seconds': round(max(1.0, min(f('SECONDS', 30), src_len - start)), 2)}


def export_one(conf, fid, v, out):
    """THE EXPORT BAKED, LARRY 5's pipeline on every frame: the minute normalized onto the 6K master canvas (cover, never gaps), the layout's crop within the 4K zone with
    the shift, scaled to the layout's pixels, the layout-locked 6K logo laid center-fixed, our song under it, its seconds -> out"""
    src, _w = _export_src(conf, fid)
    lay = next(l for l in EXPORT_LAYOUTS if l[0] == v['layout'])
    W, H = lay[3], lay[4]
    p = subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=width,height', '-of', 'csv=p=0', src], capture_output=True, text=True)
    sw, sh = (int(x) for x in p.stdout.strip().split(',')[:2])
    KW, KH = 6144, 3456
    k = max(KW / sw, KH / sh)   # cover: the canvas always filled
    ox, oy = (KW - sw * k) / 2, (KH - sh * k) / 2
    l, t, r, b = _export_crop(W, H, v['offset'], v.get('frame', '4k'))
    cx, cy, cw, ch = (l - ox) / k, (t - oy) / k, (r - l) / k, (b - t) / k   # the same box on the minute's own frame
    vf = f"[0:v]crop={cw:.3f}:{ch:.3f}:{cx:.3f}:{cy:.3f},scale={W}:{H}:flags=lanczos,setsar=1,fps=30[v0]"
    if v.get('fill'):   # FILL GAPS: the composition's green keyed out over the near-black, under everything else (the logo stays on top)
        vf += (f";[v0]colorkey={COMP_GREEN}:{EXPORT_KEY[0]}:{EXPORT_KEY[1]}[vk];color=c={EXPORT_FILL}:s={W}x{H}:r=30:d={v['seconds']}[bg];"
               f"[bg][vk]overlay=shortest=1,format=yuv420p[vfill]")
    v0 = '[vfill]' if v.get('fill') else '[v0]'
    inputs = ['-ss', str(v['start']), '-t', str(v['seconds']), '-i', src]
    last = v0
    if v['logo']:
        files = EXPORT_LOGOS.get(v['layout'], {}).get(v['style'], [])
        lf = files[0] if files else ''
        if len(files) > 1 and v['variant'] and 0 <= 'abcde'.find(v['variant']) < len(files):
            lf = files['abcde'.find(v['variant'])]
        lp = os.path.join(EXPORT_ASSETS, 'layouts', 'logos_6k', lf) if lf else ''
        if lp and os.path.isfile(lp):   # the logo's own crop at no shift (center-fixed), as LARRY 5 lays it: layout-locked, the same place on the size in 4K and 6K
            L0, T0, R0, B0 = _export_crop(W, H, 0.0)
            inputs += ['-loop', '1', '-i', lp]
            vf += f";[1:v]crop={R0 - L0}:{B0 - T0}:{L0}:{T0},scale={W}:{H}:flags=lanczos,format=rgba[lg];{v0}[lg]overlay=0:0:shortest=1[v1]"
            last = '[v1]'
    vf += f";{last}format=yuv420p[vout]"
    part = out + f'.{os.getpid()}.{threading.get_ident()}.part.mp4'
    sound = ['-map', '0:a?', '-c:a', 'aac', '-b:a', '256k'] if v.get('audio', 1) else ['-an']   # AUDIO ON or OFF (the owner 2026-10-30: "there should be an option for audio or no audio")
    _ff([*inputs, '-filter_complex', vf, '-map', '[vout]', *sound, '-t', str(v['seconds']), '-c:v', 'libx264', '-crf', '16', '-preset', 'slow', '-pix_fmt', 'yuv420p',
         '-movflags', '+faststart', part], f"the export {lay[2]} {W}x{H}")
    os.replace(part, out)
    return out


def export_press(store, do, one, conf):
    """EXPORT: its settings saved by themselves (exportsave); EXPORT (exportmake) bakes the file in the background into the Downloads"""
    con = _db(store)
    try:
        fid = one('value').partition(':')[0]
        f = _film(con, fid)
        if not f:
            return f'refused · no project {fid}'
        src, words = _export_src(conf, fid)
        if not src and not all(x['path'] for x in _export_slots(con, conf, fid) or [{'path': ''}]):
            return 'EXPORT refused · a slot has no clip yet (step 11 bakes them)'
        words = words or 'THE LATEST MINUTE (every slot as it is now)'
        try:
            v = _export_checked(one, _length(src) if src else float(TOTAL))
        except ValueError as e:
            return f'EXPORT refused · {e}'
        con.execute('INSERT INTO exportset (film, layout, frame, audio, fill, offset, logo, style, variant, start, seconds, made_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) ON CONFLICT(film) DO UPDATE SET '
                    'layout = excluded.layout, frame = excluded.frame, audio = excluded.audio, fill = excluded.fill, offset = excluded.offset, logo = excluded.logo, style = excluded.style, variant = excluded.variant, start = excluded.start, '
                    'seconds = excluded.seconds, made_at = excluded.made_at', (fid, v['layout'], v['frame'], v['audio'], v['fill'], v['offset'], v['logo'], v['style'], v['variant'], v['start'], v['seconds'], _now()))
        con.commit()
        if do == 'exportsave':
            return f"SAVED · the export {v['layout']} · {v['frame'].upper()} · audio {'ON' if v['audio'] else 'OFF'} · fill gaps {'ON' if v['fill'] else 'OFF'} · shift {v['offset']:+.1f}% · logo {'ON ' + v['style'].upper() if v['logo'] else 'OFF'} · {v['seconds']:g} s from {v['start']:g} s"
        home = os.path.join(conf['films'], fid, 'export'); os.makedirs(home, exist_ok=True)
        st = os.path.join(home, 'status.json')
        if (_read(st, {}) or {}).get('state') == 'exporting':
            return 'EXPORT refused · an export is already going'
        lay = next(l for l in EXPORT_LAYOUTS if l[0] == v['layout'])
        name = re.sub(r'[^A-Za-z0-9._-]+', '_', f"{fid}_{f['title'] or ''}").strip('_')[:60]
        fname = f"{name}_{lay[2].split()[0]}_{lay[3]}x{lay[4]}_{v['frame'].upper()}_{v['seconds']:g}s{'' if v['audio'] else '_noaudio'}{'_filled' if v['fill'] else ''}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
        dl = conf.get('downloads') or os.path.expanduser('~/Downloads')
        _write(st, {'state': 'exporting', 'file': fname, 'started': _now()})
        def work():
            c = _db(store)
            try:
                # THE LATEST CLIPS, ALWAYS (the owner 2026-10-30: "how do we know the latest clips have landed down there"): a slot still being composed is waited for
                # (ten minutes at most), then the latest minute is brought up to date from every slot as it is now, and the export is cut from it
                for _ in range(300):
                    if not any(x['composing'] for x in _export_slots(c, conf, fid)):
                        break
                    _write(st, {'state': 'exporting', 'file': fname, 'started': _now(), 'said': 'waiting for step 13 to finish composing a slot'})
                    time.sleep(2)
                _write(st, {'state': 'exporting', 'file': fname, 'started': _now(), 'said': 'bringing the latest minute up to date'})
                export_latest(c, conf, fid)
                landed = _read(os.path.join(home, 'minute_latest.json'), {}) or {}
                _write(st, {'state': 'exporting', 'file': fname, 'started': _now(), 'said': 'cutting the export'})
                kept = export_one(conf, fid, v, os.path.join(home, fname))   # the agent's own copy (the page links it), then the Downloads
                shutil.copyfile(kept, os.path.join(dl, fname))
                src_ = _export_src(conf, fid)[0]
                _version(c, fid, 'export', 0, {**v, 'size': [lay[3], lay[4]], 'shape': lay[2], 'use': lay[5], 'source': os.path.relpath(src_, os.path.join(conf['films'], fid)),
                                                'source_sha': _sha(src_), 'slots': landed.get('slots'), 'downloads': os.path.join(dl, fname), 'sha': _sha(kept)}, os.path.relpath(kept, os.path.join(conf['films'], fid)))
                _write(st, {'state': 'exported', 'file': fname, 'downloads': os.path.join(dl, fname), 'ended': _now()})
            except Exception as e:   # noqa: BLE001 - said on the page
                _write(st, {'state': 'failed', 'file': fname, 'why': str(e)[:300], 'ended': _now()})
            finally:
                c.close()
        threading.Thread(target=work, daemon=True).start()
        return f"EXPORTING · {lay[2]} {lay[3]}x{lay[4]} · {v['frame'].upper()} · {v['seconds']:g} s from {v['start']:g} s of {words.lower()} · into the Downloads as {fname}"
    finally:
        con.close()


def export_parts(con, f, conf):
    """EXPORT ON THE PAGE, the very bottom: LARRY 5's layouts table and stage on our minute, the logo asked, the shift, the seconds, EXPORT, the files made"""
    fid = f['id']
    head = {'kind': 'step', 'n': 'EXPORT', 'title': 'EVERY SIZE FROM THE MINUTE',
            'under': "LARRY 5's RESIZE AND UPSCALE on our minute: pick the size, a logo or not, shift it left or right on the French grid, the seconds, EXPORT · the file goes to your Downloads"}
    slots = _export_slots(con, conf, fid)
    if not slots or not all(x['path'] for x in slots):
        return [head, {'kind': 'note', 'title': 'EXPORT · waits for step 11', 'text': 'BAKE ALL in step 11 makes the first clips'}]
    fresh = _export_latest_bg(con.execute('PRAGMA database_list').fetchone()[2], conf, fid)   # every change upstream reaches the export by itself
    src, words = _export_src(conf, fid)
    v = _export_vals(con, fid)
    base = f"{conf['scratch_url']}/export_assets"
    made = []
    for r in con.execute("SELECT settings, file, made_at FROM versions WHERE film = ? AND step = 'export' ORDER BY id DESC LIMIT 12", (fid,)):
        s_ = json.loads(r['settings']); p_ = os.path.join(conf['films'], fid, r['file'])
        made.append({'key': r['file'], 'cells': [r['made_at'].replace('T', ' ')[:16], f"{s_.get('shape', '')} {s_['size'][0]}x{s_['size'][1]} · {str(s_.get('frame', '4k')).upper()}", f"{s_['seconds']:g} s from {s_['start']:g} s" + ('' if s_.get('audio', 1) else ' · no audio') + (' · gaps filled' if s_.get('fill') else ''),
                                                 ('logo ' + s_['style'].upper() + (' ' + s_['variant'].upper() if s_.get('variant') else '')) if s_.get('logo') else 'no logo', f"shift {s_['offset']:+.1f}%",
                                                 {'links': [['⬇ ' + os.path.basename(p_), _src(conf, f'{fid}/export', os.path.basename(p_))]]} if os.path.exists(p_) else 'gone']})
    st = _read(os.path.join(conf['films'], fid, 'export', 'status.json'), {}) or {}
    stage = {'kind': 'exportstage', 'do': 'exportsave', 'make': 'exportmake', 'value': fid, 'title': f"EXPORT · from {words or 'THE LATEST MINUTE (being made)'}",
             'video': _src(conf, os.path.relpath(os.path.dirname(src), conf['films']), os.path.basename(src)) if src else '', 'length': round(_length(src), 2) if src else float(TOTAL),
             'vals': v, 'max': EXPORT_MAX, 'fill': {'key': COMP_GREEN, 'color': EXPORT_FILL, 'similarity': EXPORT_KEY[0], 'blend': EXPORT_KEY[1]}, 'slots': [[x['n'], x['at'], x['sec']] for x in slots],
             'hgrid': f'{base}/hgrid.png', 'layouts_url': f'{base}/layouts', 'layouts': [list(l) for l in EXPORT_LAYOUTS], 'logos': EXPORT_LOGOS, 'status': f"{conf['films_url']}/{fid}/export/status.json",
             'under': "the stage is the 6K master at 1/6 with the horizontal French grid and the size's own grid · 4K cuts the size from the inner 4K frame, 6K from the whole outer canvas · the shift moves the picture under the size, never past the canvas · saves by itself"}
    mj = _read(os.path.join(conf['films'], fid, 'export', 'minute.json'), {}) or {}
    rows = []
    for x in slots:
        kind = 'LIPS (12)' if x['src'] and os.sep + 'lips' + os.sep in x['src'] else 'MOVEMENT (11)'
        how = (f"COMPOSED {x['frame'].upper()}" if x['frame'] and x['frame'] != 'off' else 'COMPOSED · OFF, as it came') if x['composed'] else ('COMPOSING NOW…' if x['composing'] else 'NOT COMPOSED (as it came)')
        rows.append({'key': f"{fid}:{x['n']}", 'cells': [str(x['n']), f"{_mmss(x['at'])}-{_mmss(x['at'] + x['sec'])}", kind, how,
                                                      {'word': 'LANDED' if fresh else 'COMING IN', 'text': os.path.basename(x['path'])}]})
    out = [head, stage,
           {'kind': 'poll', 'src': _src(conf, f'{fid}/export', 'minute.json'), 'live': not fresh and mj.get('state') == 'building', 'reload': True,
            'text': 'THE LATEST MINUTE · UP TO DATE · every slot below is in it' if fresh else
                    ('THE LATEST MINUTE · BRINGING IT UP TO DATE · a slot changed upstream, the stage takes it when it is made' if mj.get('state') != 'failed' else f"THE LATEST MINUTE · NOT MADE · {mj.get('why', '')}")},
           {'kind': 'table', 'title': 'EXPORT · WHAT LANDS IN THE EXPORT · each slot as step 13 has it now', 'columns': ['Slot', 'In the minute', 'Its clip', 'Composition', 'Landed'], 'rows': rows}]
    if st:
        word = {'exporting': 'EXPORTING', 'exported': 'IN YOUR DOWNLOADS', 'failed': 'NOT EXPORTED'}.get(st.get('state'), str(st.get('state', '')).upper())
        out.append({'kind': 'poll', 'src': _src(conf, f'{fid}/export', 'status.json'), 'live': st.get('state') == 'exporting', 'reload': True,
                    'text': f"THE EXPORT · {word} · {st.get('file', '')}" + (f" · {st['why']}" if st.get('why') else '')})
    out.append({'kind': 'table', 'title': f'EXPORT · THE FILES MADE · {len(made)}', 'columns': ['Made', 'Size', 'Seconds', 'Logo', 'Shift', 'File'], 'rows': made,
                'empty': 'nothing exported yet'})
    return out


def _bake_line(conf, fid, folder, what):
    """A BAKE FOLLOWED IN PLACE (the owner 2026-10-29: "the page keeps relaoding and not text status its a little annoying"): its state line, read again by the page every
    few seconds while it bakes; the page draws itself once when it is baked, where he was, so the players show what was made"""
    bk = _read(os.path.join(conf['films'], fid, folder, 'bake.json'), {}) or {}
    if not bk:
        return []
    word = {'baking': 'BAKING', 'baked': 'BAKED', 'failed': 'NOT BAKED'}.get(bk.get('state'), str(bk.get('state', '')).upper())
    return [{'kind': 'poll', 'src': _src(conf, f'{fid}/{folder}', 'bake.json'), 'live': bk.get('state') == 'baking', 'reload': True,
             'text': f"THE BAKE · {word} · {what}" + (f" · {bk['said'][:240]}" if bk.get('said') else f" · started {bk.get('started', '')}")}]


def faceswap_parts(con, f, conf):
    """PART 3 ON THE PAGE: its big 3, the face it uses, SWAP FACES, then each poster's original beside its face swap"""
    fid = f['id']
    posts = {r['n']: r for r in con.execute("SELECT * FROM posters WHERE film = ? AND file IS NOT NULL AND file != ''", (fid,))}
    swaps = {r['n']: r for r in con.execute('SELECT * FROM faceswap WHERE film = ?', (fid,))}
    head = {'kind': 'step', 'n': 3, 'title': 'FACE SWAP', 'under': 'his real face onto Rumpel in every poster · everything else kept · the original beside the swap'}
    if not posts:
        return [head, {'kind': 'note', 'title': '3 · waits for step 2', 'text': 'make the posters first'}]
    measured = _read(os.path.join(conf['films'], fid, 'faceswap', 'angles.json'), {}) or {}
    refs = donors_of(f)
    face = {'kind': 'table', 'title': f'3 · THE FACES · {len(refs)} references · each poster uses the one turned most like its face', 'columns': ['His face', 'The picture', 'Its angle'],
            'rows': [{'key': f'{fid}|{name}', 'cells': [{'image': (f"{conf['scratch_url']}/{os.path.relpath(found, SCRATCH)}" if found else ''), 'width': 140, 'text': '' if found else 'not found'},
                                                       name, angle_word(measured[name]) if name in measured else 'measured at SWAP FACES'],
                      'presses': [{'do': 'donor', 'value': f'{fid}|-{name}', 'label': 'REMOVE', 'cell': 1}]} for name in refs for found in [find_file(name, conf)]]
            + [{'key': f'{fid}|add', 'cells': ['', 'add another', ''], 'presses': [{'do': 'donor', 'value': f'{fid}|+', 'label': 'ADD', 'text': True, 'placeholder': 'a file name in the CMO\'s folders', 'cell': 1}]}]}
    go = {'kind': 'press', 'do': 'swap', 'value': fid, 'label': f"SWAP FACES · {(f['swap_state'] or 'not done yet').upper()}"}
    rows = []
    for n in sorted(posts):
        w_ = swaps.get(n)
        mk = {'image': _src(conf, f'{fid}/posters', posts[n]['file']), 'do': 'mark', 'value': f'{fid}:{n}', 'kinds': ['swap'], 'width': 420, 'full': True,
              'marks': [[w_['face_x'], w_['face_y'], 'swap']] if w_ is not None and w_['face_x'] is not None else []}
        board_ = os.path.join(conf['films'], fid, 'faceswap', 'refboard.png')
        hd_ = os.path.join(conf['films'], fid, 'faceswap', 'refboard_hd.png')   # the 6 HD pictures of him a Kling 4 swap was made from (the owner 2026-10-29: "update the references on the left ... we replaced these blurry ones")
        used = hd_ if (w_ is not None and (w_['why'] or '').startswith('made by Kling') and os.path.exists(hd_)) else board_ if (w_ is not None and w_['file'] and os.path.exists(os.path.join(conf['films'], fid, 'faceswap', f'head_{n}.png')) and os.path.exists(board_)) else (find_file(w_['donor'], conf) if w_ is not None and w_['donor'] else '')
        ref = {'image': f"{conf['scratch_url']}/{os.path.relpath(used, SCRATCH)}", 'width': 420, 'text': 'his 6 HD pictures from the 1080p film' if used.endswith('refboard_hd.png') else 'his front and side' if used.endswith('refboard.png') else w_['donor'], 'full': True} if used else 'none'   # all three big (the owner 2026-10-28: "all 3 need to be big")   # each one its reference (the owner 2026-10-28: "then each one has a ref")
        rows.append({'key': f'{fid}:{n}', 'cells': [str(n), ref, {'marker': mk},   # the reference 1, the original 2, the swap 3, in one row (the owner 2026-10-28: "ref 1, orig 2, swapped 3 / all three in 1 row")
                                                   ({'image': _src(conf, f'{fid}/faceswap', w_['file']), 'width': 420, 'full': True} if w_ and w_['file'] else ((w_['state'].upper() + ' · ' + (w_['why'] or '')) if w_ else 'not swapped yet')),
                                                   (w_['why'] if w_ and w_['file'] else '')],
                     'presses': [{'do': 'face', 'label': 'SET', 'text': True, 'placeholder': 'face 2 · none · a reference file name · empty = automatic', 'cell': 4}]})
    table = {'kind': 'table', 'title': '3 · THE POSTERS · the reference · the original · the face swap', 'columns': ['Slot', 'Reference', 'Original (click to mark)', 'Face swap', 'Which face'], 'rows': rows}
    parts = [head, go, table]   # no faces table (the owner 2026-10-28: "we dont need this table anymore")
    row = con.execute('SELECT map FROM music WHERE film = ?', (fid,)).fetchone()
    if row:   # THE SWAPS ON TIME, the same player as step 2's (the owner 2026-10-29: "under it ... a new video player slide show like the one above ... with music and with the clip colored below same player but with the new images")
        slots = json.loads(row['map'])['slots']
        types = _types(con, fid, slots)
        insp = {r['n']: r for r in con.execute('SELECT n, tag FROM inspiration WHERE film = ?', (fid,))}
        slides, at = [], 0
        for x in slots:
            t = insp[x['n']]['tag'] if x['n'] in insp and insp[x['n']]['tag'] else types[x['n'] - 1]
            w_ = swaps.get(x['n'])
            shown = (_src(conf, f'{fid}/faceswap', w_['file']) if w_ is not None and w_['file'] and w_['state'] == 'done' else
                     _src(conf, f'{fid}/posters', posts[x['n']]['file']) if x['n'] in posts else '')   # the face swap, else its poster
            slides.append({'src': shown, 'at': at, 'end': at + x['seconds'], 'label': f"{x['n']}·{t}", 'tone': TONE_OF[t]})
            at += x['seconds']
        parts.append({'kind': 'slideshow', 'title': '3 · THE FACE SWAPS · PLAY THEM WITH THE FINAL SONG · each slot its swap for its seconds', 'audio': _src(conf, f'{fid}/music', 'minute_final.wav'),
                      'slides': slides, 'under': 'press play on the song: the picture changes on each slot · click a bar to jump to its slot', 'empty': 'the player appears when the final song is made (step 1)'})
    return parts


def posters_parts(con, f, conf):
    """PART 2 ON THE PAGE, ITS FIRST PART: the types (the options when more than one), the sources with their codes, each slot's inspiration line,
    tag and frame; words and addresses only"""
    fid = f['id']
    row = con.execute('SELECT map FROM music WHERE film = ?', (fid,)).fetchone()
    head = {'kind': 'step', 'n': 2, 'title': 'THE POSTERS', 'under': 'first the INSPIRATION: composition and idea only (not the people, not the color) · then MAKE POSTERS'}
    if not row:
        return [head, {'kind': 'note', 'title': '2 · waits for step 1', 'text': 'the music must be ready first: its map gives the slots'}]
    slots = json.loads(row['map'])['slots']
    opts = type_options(slots)
    types = _types(con, fid, slots)
    srcs = inspiration_sources(conf)
    insp = {r['n']: r for r in con.execute('SELECT * FROM inspiration WHERE film = ?', (fid,))}
    posts = {r['n']: r for r in con.execute('SELECT * FROM posters WHERE film = ?', (fid,))}
    tag_of = lambda x: (insp[x['n']]['tag'] if x['n'] in insp and insp[x['n']]['tag'] else types[x['n'] - 1])   # noqa: E731
    final = [tag_of(x) for x in slots]
    clash = {i + 1 for i in range(len(final) - 1) if final[i] == final[i + 1]} | {i + 2 for i in range(len(final) - 1) if final[i] == final[i + 1]}
    sources = {'kind': 'table', 'title': f"2 · THE SOURCES · {len(srcs)} · put videos and pictures in {conf['source']}", 'columns': ['Code', 'Source', 'Length'],
               'rows': [{'key': x['code'], 'cells': [x['code'], x['name'], _mmss(_seconds_of(x['path'])) if x['kind'] == 'video' else 'picture']} for x in srcs],
               'empty': f"no source yet: put the original video (and any pictures) in {conf['source']}"}
    the_map = json.loads(row['map'])
    rows_ = []
    for vibe, order, sl in sequences(conf):   # ONE TABLE (the owner 2026-10-28: "1 fucking table / name of the sequence 1 under it 2 / and then seeconds for each 1 to 8 / under it I, II, or III / nothing else and you just pick")
        fake = [{'n': i, 'insert': 'INSERT' in g} for i, (g, _x) in enumerate(sl, 1)]
        t = types if (vibe, order) == (the_map['sequence'], the_map['order']) else (type_options(fake) or [['I'] * len(sl)])[0]
        using = (vibe, order) == (the_map['sequence'], the_map['order'])
        rows_.append({'key': f'{vibe} {order}', 'cells': [f"{vibe.upper()} {order.split()[-1]}{' ✓' if using else ''}"] + [{'chips': [[f'{x}s {y}', TONE_OF[y]]]} for (_g, x), y in zip(sl, t)],
                      'presses': [] if using else [{'do': 'sequence', 'value': f'{fid}|{vibe} {order}', 'label': 'SELECT', 'cell': 0}]})   # one slim row: its name, then each slot's seconds and type (the owner 2026-10-28: "combine into 1 row and have sec then type after"; "the human can pick with a button select")
    seqs = {'kind': 'table', 'title': '2 · THE SEQUENCES', 'columns': ['Sequence'] + [str(i) for i in range(1, len(slots) + 1)], 'rows': rows_}
    inserts = [x['n'] for x in slots if x['insert']]

    rows = []
    for x in slots:
        r = insp.get(x['n'])
        flag = ' · TWO ' + final[x['n'] - 1] + ' SIDE BY SIDE' if x['n'] in clash else ''
        rows.append({'key': f"{fid}:{x['n']}", 'cells': [
            str(x['n']), {'chips': [[f"TYPE {final[x['n'] - 1]}{' INSERT' if final[x['n'] - 1] == 'III' else ''}", TONE_OF[final[x['n'] - 1]]]], 'text': flag}, f"{x['seconds']} s · {_mmss(x['at'])}-{_mmss(x['at'] + x['seconds'])}",
            (r['line'] if r else '(none yet)'),
            {'image': _src(conf, f'{fid}/inspiration', r['frame']) if r else '', 'width': 240, 'text': '' if r else 'no frame'},
            {'images': samples(conf).get(x['group'], []), 'thumb': 72, 'text': x['group'].title()},
            ({'image': _src(conf, f'{fid}/posters', posts[x['n']]['file']), 'width': 240} if x['n'] in posts and posts[x['n']]['file'] else (posts[x['n']]['why'] if x['n'] in posts else ''))],   # its shot group's samples beside its frame (the owner 2026-10-28: "the sample shots need to be next to the inspiration so we can match them up")
            'presses': [{'do': 'inspire', 'label': 'SET', 'text': True, 'placeholder': 'V1 1:41 II · or a file name', 'cell': 3}], 'below': 'THE WORDS · ' + (x['words'] or '(no words)'), 'tone': TONE_OF[final[x['n'] - 1]]})
    slot_table = {'kind': 'table', 'title': f'2 · INSPIRATION · a slot a line: the source code, its second, its type (V1 1:41 II · P2 III), or any file name in the CMO\'s folders (2026-03-15_18-00-36_UTC_4.jpg III) · {len(insp)} of {len(slots)} set',
                  'columns': ['Slot', 'Type', 'Length', 'Inspiration', 'Frame', 'Samples of its shot group', 'Poster'], 'rows': rows}
    find = {'kind': 'press', 'do': 'find', 'value': fid, 'label': 'FIND INSPIRATION (first guesses)'}
    make = {'kind': 'press', 'do': 'posters', 'value': fid, 'label': f"MAKE POSTERS · {(f['posters_state'] or 'not made yet').upper()}"}
    slides, at = [], 0
    for x in slots:   # THE PICTURES ON TIME (the owner 2026-10-28: "it doesnt need to play a movie it can just show the image for that duration")
        r = insp.get(x['n'])
        pr = posts.get(x['n'])
        # ONLY UP TO ITS OWN STEP (the owner 2026-10-29: "all the video players should not play video content below them. just to that point"): the poster, else its inspiration
        shown = _src(conf, f'{fid}/posters', pr['file']) if pr and pr['file'] else (_src(conf, f'{fid}/inspiration', r['frame']) if r else '')
        slides.append({'src': shown, 'at': at, 'end': at + x['seconds'], 'label': f"{x['n']}·{final[x['n'] - 1]}",
                       'tone': TONE_OF[final[x['n'] - 1]]})
        at += x['seconds']
    player = {'kind': 'slideshow', 'title': '2 · INSPIRATION · PLAY IT WITH THE FINAL SONG · each slot its picture for its seconds', 'audio': _src(conf, f'{fid}/music', 'minute_final.wav'),
              'slides': slides, 'under': 'press play on the song: the picture changes on each slot · click a bar to jump to its slot', 'empty': 'the player appears when the final song is made (step 1)'}
    return [head, sources, seqs, find, player, slot_table, make]


def samples(conf):
    """the shot list's samples by shot group -> {group: [[address, preset name], ...]}"""
    m = _read(os.path.join(conf['shot_samples'], 'shot_samples.json'), {}) or {}
    out = {}
    for name, v in m.items():
        out.setdefault(v['group'], []).append([f"{conf['scratch_url']}/shot_samples/{v['file']}", name.split(' - ', 1)[-1].replace(' (CLIP 1 OR CLIP 8)', '')])
    return out


def music_parts(con, f, conf):
    """PART 1 ON THE PAGE: its state, the slider over the whole song (the minute he wants), the minute as a multitrack (MIX, VOCALS, INSTRUMENTAL,
    BEATS, SECTIONS, LYRICS, SEQUENCE) and the map, slot by slot; words and numbers only, read from the CMO's own database"""
    fid = f['id']
    row = con.execute('SELECT * FROM music WHERE film = ?', (fid,)).fetchone()
    state = (f['music_state'] or 'asked').upper()
    head = {'kind': 'note', 'title': f"{fid} · {f['title']} · 1 · THE MUSIC · {state}",
            'text': (f"{f['song']} · its project folder: {os.path.join(conf['films'], fid)} · " + (f['music_why'] or ('ready: pick the minute, press SET MINUTE, then RUN AGENT' if row else 'press RUN AGENT: it splits the vocals, finds the beats, sections, words and the map')))}
    if not row:
        return [head]
    an, lyrics, peaks, the_map = json.loads(row['analysis']), json.loads(row['lyrics']), json.loads(row['peaks']), json.loads(row['map'])
    start = float(the_map['start'])
    asked = float(f['song_start']) if f['song_start'] is not None else start   # the minute he set (the map catches up when its recut is done)
    url = lambda name: _src(conf, f'{fid}/music', name)   # noqa: E731
    shrink = lambda vals, n=900: [max(vals[i:i + max(1, len(vals) // n)] or [0]) for i in range(0, len(vals), max(1, len(vals) // n))]   # noqa: E731
    q = lambda vals: vals[int(start * 4):int((start + TOTAL) * 4)]   # noqa: E731  (peaks are a quarter second each)
    slider = {'kind': 'slider', 'title': '1 · THE MUSIC · SLIDE TO THE MINUTE YOU WANT', 'do': 'minute', 'value': fid, 'name': 'start', 'label': 'SET MINUTE',
              'total': an['seconds'], 'window': TOTAL, 'min': 0, 'max': max(0.0, an['seconds'] - TOTAL), 'start': asked, 'snaps': an['downbeats'],
              'audio': url('song.wav'), 'peaks': shrink(peaks.get('mix') or []),
              'under': f"the whole song, {_mmss(an['seconds'])} · the hook it found starts at {_mmss(an['hook'])} · the window snaps to the downbeats · {an['tempo']} BPM ({an.get('beats_by', '')})"}
    rel = lambda t: round(t - start, 3)   # noqa: E731
    lanes = [{'name': 'FINAL (smooth in and out)', 'peaks': q(peaks.get('mix') or []), 'audio': url('minute_final.wav')},
             {'name': 'MIX', 'peaks': q(peaks.get('mix') or []), 'audio': url('minute_mix.wav')},
             {'name': 'VOCALS', 'peaks': q(peaks.get('vocals') or []), 'audio': url('minute_vocals.wav')},
             {'name': 'INSTRUMENTAL', 'peaks': q(peaks.get('instrumental') or []), 'audio': url('minute_instrumental.wav')},
             {'name': 'BEATS', 'marks': [{'t': rel(b), 'strong': b in set(an['downbeats'])} for b in an['beats'] if start <= b < start + TOTAL]},
             {'name': 'SECTIONS', 'blocks': [{'start': rel(x['start']), 'end': rel(x['end']), 'label': x['name'], 'strong': x['name'].startswith('HIGH')} for x in an['sections'] if x['end'] > start and x['start'] < start + TOTAL]},
             {'name': 'LYRICS', 'blocks': [{'start': rel(w['start']), 'end': rel(w['end']), 'label': w['word']} for w in lyrics.get('words') or () if start <= w['start'] < start + TOTAL]},
             {'name': 'SEQUENCE', 'blocks': [{'start': x['at'], 'end': x['at'] + x['seconds'], 'label': f"{x['n']} · {x['seconds']}s", 'strong': True} for x in the_map['slots']]}]
    tracks = {'kind': 'tracks', 'title': f"1 · THE MINUTE, LAYER BY LAYER · {_mmss(start)}-{_mmss(start + TOTAL)} · {the_map['sequence']} ({the_map['order']})",
              'seconds': TOTAL, 'lanes': lanes, 'under': 'press ▶ on a layer to hear it alone · click anywhere on the lanes to jump there'}
    off = sum(x['off'] for x in the_map['slots'])
    table = {'kind': 'table', 'title': f"1 · THE MAP · {the_map['sequence']} ({the_map['order']}) · its 7 slot changes sit {off:.2f} s from the beats in all ({1000 * off / 7:.0f} ms each on average)",
             'under': 'others that fit: ' + ' · '.join(f"{o['sequence']} ({o['order']}) {o['score']:.2f}" for o in the_map['others'][1:5]),
             'columns': ['Slot', 'Shot group', 'Seconds', 'In the song', 'Beats', 'Its end to the beat', 'Section'],
             'rows': [{'key': f'{fid}:{x["n"]}', 'cells': [str(x['n']), x['group'] + (' (insert)' if x['insert'] else ''), f"{x['seconds']} s", f"{_mmss(x['start'])}-{_mmss(x['end'])}",
                                                         f"{len(x['beats'])} ({len(x['downbeats'])} downbeats)", f"{x['off']:.2f} s" if x['n'] < CLIPS else 'the end', x['section']],
             'tone': 'insert' if x['insert'] else '', 'below': 'THE WORDS · ' + (x['words'] or '(no words)')}
                      for x in the_map['slots']]
             + [{'key': fid, 'cells': ['', '', '', '', '', '', ''], 'presses': [{'do': 'sequence', 'label': 'USE THIS SEQUENCE', 'text': True, 'placeholder': 'a sequence: Lens, or Lens minute 2 (empty: the best fit)', 'cell': 1}]}]}
    return [head, slider, tracks, table]


def _split(fields):
    """the form's one box name carries three lists: 'layers:logo', 'music:<track>', a bare reference"""
    refs, layers, music, sources, picked = [], [], [], [], []
    for v in fields:
        k, _, rest = v.partition(':')
        (layers if k == 'layers' else music if k == 'music' else sources if k == 'source' else picked if k == 'song' else refs).append(rest if k in ('layers', 'music', 'source', 'song') else v)
    return refs, layers, music, sources, picked

