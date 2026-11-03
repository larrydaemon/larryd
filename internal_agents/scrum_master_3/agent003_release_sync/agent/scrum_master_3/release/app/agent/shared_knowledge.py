"""THE KNOWLEDGE STORE, READ (the owner 2026-10-22): the Scrum Master's one reader of knowledge.db, in its own home
(settings knowledge.db, never inside this package). Read only: the database opened file:...?mode=ro, never written, and
the knowledge package never imported (it runs only as its own process: the 3 way switch before a hire, the night step).

    db()                    the read-only connection, or None when the knowledge store is not there
    routes(since, until)    the 3 way switch's routes in a span
    nights(since)           the night step's runs since a moment
    waiting()               the proposals waiting on the owner, each with whether its entry is locked
    entry_ids(ids)          which of these entry ids the knowledge store holds
"""
import json
import os
import sqlite3

from agent import shared_where as where

CONF = where.SETTINGS['knowledge']


def path(name):
    return os.path.abspath(os.path.expanduser(str(CONF[name]))) if CONF.get(name) else ''


def db_file():
    """The knowledge store's file (a check's own under its scratch home)."""
    return os.environ.get('SCRUM_MASTER_KNOWLEDGE_DB') or path('db')


def db(file=None):
    """The knowledge store, read only (None when it is not there: before the one move)."""
    f = file or db_file()
    if not f or not os.path.exists(f):
        return None
    con = sqlite3.connect(f'file:{f}?mode=ro', uri=True, timeout=5)
    con.row_factory = sqlite3.Row
    return con


def _rows(con, sql, args=()):
    try:
        return [dict(r) for r in con.execute(sql, args)]
    except sqlite3.Error:
        return []


def routes(con, since, until='9999'):
    out = _rows(con, 'SELECT * FROM routes WHERE at >= ? AND at < ? ORDER BY id', (since, until))
    for r in out:
        try:
            r['delivered'] = json.loads(r.get('delivered') or '[]')
        except ValueError:
            r['delivered'] = []
    return out


def nights(con, since):
    out = _rows(con, 'SELECT * FROM nights WHERE at >= ? ORDER BY at', (since,))
    for r in out:
        try:
            r['report'] = json.loads(r.get('report') or '{}')
        except ValueError:
            r['report'] = {}
    return out


def waiting(con):
    return _rows(con, "SELECT p.id, p.entry_id, p.by, p.at, e.key, e.locked FROM proposals p JOIN entries e ON e.id = p.entry_id WHERE p.state = 'waiting' ORDER BY p.at")


def entry_ids(con, ids):
    ids = [int(i) for i in ids if str(i).lstrip('-').isdigit()]
    if not ids:
        return set()
    return {r['id'] for r in _rows(con, f'SELECT id FROM entries WHERE id IN ({",".join("?" for _ in ids)})', ids)}


def door_writes(con, since):
    """The keys the knowledge door took in since a moment (the inbox): what a memory file may be changed for."""
    return {r['key'] for r in _rows(con, 'SELECT key FROM inbox WHERE at >= ?', (since,))}
