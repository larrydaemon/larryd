"""THE DOOR'S GUARD AND THE FROST SECURITY LOCK (owner 2026-10-04: "the original required a very specific way for any
database connection to be created in the code and it could never be a direct connection"; "we did this security for 1
year and its proven to be a secure way and i still want it in the code"): the same text in every office that opens a
database. Two lines of defence, one under the other:

THE LOCK (the original's FROST SECURITY LOCK, lock_frost_fact.py): every data statement an office runs is written as
    # =============================================================================
    # FROST SECURITY LOCK "ON" - PARAMETERIZED DATABASE QUERY
    # =============================================================================
    # Secure count query
    secure_count_query, secure_count_params = st.secure_query(
        'SELECT * FROM "table" WHERE column = ?',
        params=(value,)
    )
    rows = con.execute(secure_count_query, secure_count_params).fetchall()
    # =============================================================================
    # FROST SECURITY LOCK
    # =============================================================================
secure_query is the door's (store.secure_query, this function): the SQL is one string with every value a ? parameter
(a name may stand in the text in double quotes; a value never), the parameters a tuple; it hands back the query MARKED
(Secured). The door's connection (Locked) refuses a data statement that was not marked: a SELECT, INSERT, UPDATE,
DELETE, REPLACE or WITH written any other way raises FrostLockError, fail closed. DDL, PRAGMA, a transaction word and a
read of sqlite_master are the machine's own and pass, as the original's scanner exempted them. FROST's monitor reads the
block (rules 1, 20, 22, 27) and the Judge requires it.

THE GUARD (the second line, under the lock): every connection the door hands out reaches only the database its door
opened (no ATTACH, no DETACH) and one account's tables (the first account table it touches makes it that account's; a
table named for any other account is refused: sqlite3.DatabaseError, not authorized). Tables that carry no account key
are the office's own and open to its connections."""
import re
import sqlite3

ACCOUNT_IN_NAME = re.compile(r'ACCT_[0-9A-F]{12}_[0-9A-F]{4}')   # every account table carries its account key in its name
REFUSED = (sqlite3.SQLITE_ATTACH, sqlite3.SQLITE_DETACH)          # a door's connection never reaches another database
DATA = re.compile(r'^\s*(?:SELECT|INSERT|UPDATE|DELETE|REPLACE|WITH)\b', re.I)   # a data statement: through the lock, always
MACHINE = re.compile(r'\bsqlite_master\b', re.I)                                 # the schema's own catalog: a read of it is no data
VALUE_IN_TEXT = re.compile(r"'")                                                 # a value written into the SQL text (names are double-quoted)


class FrostLockError(sqlite3.DatabaseError):
    """A data statement that did not come through the lock (secure_query), or a query with a value in its text."""


class Secured(str):
    """The SQL text secure_query marked: the only text the door's connection runs a data statement from."""


def secure_query(query, params=None):
    """THE LOCK'S ONE FUNCTION: the SQL checked and marked -> (Secured query, params tuple). The SQL is one string; every
    value is a ? parameter (a single quote in the text is a value glued in: refused); params a tuple (a list becomes one).
    Nothing is rewritten: the door's connection and its guard do the rest at execute time."""
    if not isinstance(query, str) or isinstance(query, Secured):
        raise FrostLockError('secure_query takes the SQL as one plain string')
    if VALUE_IN_TEXT.search(query):
        raise FrostLockError('a value is written into the SQL text: pass it as a ? parameter (only a "name" may stand in the text)')
    if params is None:
        params = ()
    elif isinstance(params, list):
        params = tuple(params)
    elif not isinstance(params, tuple):
        raise FrostLockError('params is a tuple: params=(value,)')
    return Secured(query), params


def locked(sql):
    """Does this statement need the lock? A data statement, not a read of sqlite_master."""
    return bool(DATA.match(sql or '')) and not MACHINE.search(sql or '')


class Locked(sqlite3.Connection):
    """THE DOOR'S CONNECTION KIND: a data statement runs only from a Secured query (the lock's mark)."""
    def execute(self, sql, parameters=()):
        if locked(sql) and not isinstance(sql, Secured):
            raise FrostLockError('a data statement outside the FROST SECURITY LOCK: write it through secure_query')
        return super().execute(sql, parameters)

    def executemany(self, sql, seq_of_parameters):
        if locked(sql) and not isinstance(sql, Secured):
            raise FrostLockError('a data statement outside the FROST SECURITY LOCK: write it through secure_query')
        return super().executemany(sql, seq_of_parameters)


def guard():
    """A fresh guard for one connection (it remembers the one account that connection is for)."""
    mine = []

    def check(action, arg1, arg2, _db, _trigger):
        if action in REFUSED:
            return sqlite3.SQLITE_DENY
        for name in (arg1, arg2):
            found = ACCOUNT_IN_NAME.search(name or '')
            if found:
                if not mine:
                    mine.append(found.group(0))
                elif found.group(0) != mine[0]:
                    return sqlite3.SQLITE_DENY
        return sqlite3.SQLITE_OK
    return check


def wear(con):
    """The connection, wearing its guard: the door's last step before it hands a connection out."""
    con.set_authorizer(guard())
    return con
