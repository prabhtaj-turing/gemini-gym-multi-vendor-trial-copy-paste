"""
duckdb_manager.py  – persistent version
"""

from __future__ import annotations
from common_utils.print_log import print_log

import json
import os
import re
import os
import signal
from typing import Dict, List, Optional, Tuple, Union, Any

import duckdb
from sqlglot import parse_one, transpile, Dialect
from sqlglot.expressions import (
    Create,
    Drop,
    Use,
    Attach,
    Alias,
    Literal,
    Identifier,
    Command as SqlglotCommand,
)

# ──────────────────────────────────────────────────────────────────────────────
# Helpers                                                                      



QueryResult = Dict[str, Optional[Union[List[Tuple[Any, ...]], int, str, bool]]]


# ──────────────────────────────────────────────────────────────────────────────
# Manager                                                                      

class DuckDBManager:
    """
    Minimal MySQL-ish façade over DuckDB **with persistent simulator state**.

    Parameters
    ----------
    main_url           Path/filename for the main database (or ':memory:').
    database_directory Directory that holds all other *.duckdb files.
    simulation_state_path
                       JSON file used to persist/restore attachments and
                       current database between runs.
    """

    # ─────────── init ───────────
    def __init__(
        self,
        main_url: str = ":memory:",
        *,
        database_directory: str | None = None,
        simulation_state_path: str | None = None,
    ):
        # config paths
        self._database_directory = (
            os.path.abspath(database_directory) if database_directory else os.getcwd()
        )
        os.makedirs(self._database_directory, exist_ok=True)

        self._state_path = (
            os.path.abspath(simulation_state_path) if simulation_state_path else None
        )
        self._attached_aliases: Dict[str, str] = {}
        self._main_db_url = main_url  
        self._is_main_memory = main_url == ":memory:"
        self._main_db_alias = "memory" if self._is_main_memory else "main"
        self._current_db_alias = self._main_db_alias

        self._try_unlock_duckdb(self._resolve_path(self._main_db_url, for_creation=True))

        # open / create main db
        self._main_connection = duckdb.connect(
            database=self._resolve_path(main_url, for_creation=True), read_only=False
        )
        row = self._main_connection.execute(
            "select database_name from duckdb_databases() "
            "where database_name not in ('system','temp')"
        ).fetchone()
        self._primary_internal_name = row[0] if row else self._main_db_alias

        # restore state or discover existing *.duckdb
        if not self._load_state_from_json():
            self._auto_discover_duckdb_files()

    def _try_unlock_duckdb(self, db_path):
        try:
            con = duckdb.connect(db_path)
            con.close()
        except duckdb.IOException as e:
            match = re.search(r'PID (\d+)', str(e))
            if match:
                pid = int(match.group(1))
                try:
                    print_log(f"Attempting to kill PID {pid} to release DuckDB lock.")
                    os.kill(pid, signal.SIGTERM)
                except ProcessLookupError:
                    print_log(f"Process {pid} not found.")
                except PermissionError:
                    print_log(f"No permission to kill process {pid}.")
            else:
                raise

    # ─────────── public API ───────────
    def execute_query(self, query: str) -> QueryResult:
        q = query.strip()
        u = q.upper()
        conn = self._conn()
        result: QueryResult = {
            "data": None,
            "affected_rows": 0,
            "is_ddl": False,
            "command": None,
        }

        # fast-path regex ATTACH / DETACH
        m = re.match(r"ATTACH\s+DATABASE\s+'([^']+)'\s+AS\s+([^\s;]+)", q, re.I)
        if m:
            path, alias = m.groups()
            self._attach(alias, self._resolve_path(path, for_creation=True))
            result.update({"is_ddl": True, "command": "attachdatabase"})
            self._save_state()
            return result

        m = re.match(r"DETACH\s+DATABASE\s+([^\s;]+)", q, re.I)
        if m:
            alias = m.group(1).strip('`"')
            if alias.lower() == self._main_db_alias:
                raise ValueError(
                    f"cannot detach the main database ('{self._main_db_alias}') via manager"
                )
            self._detach(alias)
            result.update({"is_ddl": True, "command": "detachdatabase"})
            self._save_state()
            return result

        # sqlglot parse for manager commands
        parsed, dialect = None, None
        try:
            parsed = parse_one(q, read="mysql" if not u.startswith(("ATTACH", "DETACH")) else "duckdb")
            dialect = "mysql" if not u.startswith(("ATTACH", "DETACH")) else "duckdb"
        except Exception:
            parsed = None

        # CREATE DATABASE
        if isinstance(parsed, Create) and parsed.kind == "DATABASE":
            result["command"] = "createdatabase"
            ident: Identifier = parsed.this
            user_db = ident.name.strip("`")
            if not self._is_mysql_valid_db_name(user_db):
                raise ValueError(
                    f"invalid database name '{user_db}' according to mysql rules"
                )

            sane = self._sanitize(user_db)
            db_fp = self._resolve_path(sane, for_creation=True)
            if_exists = parsed.args.get("exists", False)
            exists = (
                user_db in self._attached_aliases
                or sane in self._attached_aliases.values()
                or os.path.exists(db_fp)
            )
            if exists and not if_exists:
                raise duckdb.CatalogException(
                    f"can't create database '{user_db}'; database exists"
                )
            if not exists:
                duckdb.connect(db_fp).close()
                self._attach(user_db, db_fp)
                result["affected_rows"] = 1
            result["is_ddl"] = True
            self._save_state()
            return result

                # DROP DATABASE
        if isinstance(parsed, Drop) and parsed.kind == "DATABASE":
            result["command"] = "dropdatabase"
            ident: Identifier = parsed.this
            user_db = ident.name.strip("`")
            if_exists = parsed.args.get("exists", False)

            # figure out file path for potential deletion
            try:
                sane_alias = (
                    self._attached_aliases.get(user_db)
                    or self._sanitize(user_db)
                )
            except ValueError:
                sane_alias = None
            db_file_path = (
                self._resolve_path(sane_alias, for_creation=False)
                if sane_alias
                else None
            )

            is_attached = user_db in self._attached_aliases
            file_exists = os.path.exists(db_file_path) if db_file_path else False

            if not is_attached and not file_exists and not if_exists:
                raise duckdb.CatalogException(
                    f"can't drop database '{user_db}'; database doesn't exist"
                )

            # detach if necessary
            if is_attached:
                self._detach(user_db)

            # delete the .duckdb file if it is present
            if file_exists:
                try:
                    os.remove(db_file_path)
                except OSError:
                    # Ignore deletion errors (file locked, permissions, etc.)
                    pass

            result["is_ddl"] = True
            self._save_state()
            return result

        # USE database
        if isinstance(parsed, Use):
            result["command"] = "usedatabase"
            ident: Identifier = parsed.this
            user_db = ident.name.strip("`")
            if user_db.lower() == self._main_db_alias:
                target = self._main_db_alias
            else:
                target = self._attached_aliases.get(user_db)
            if not target:
                raise duckdb.CatalogException(f"unknown database '{user_db}'")
            target = f'{target}' if target not in ("main","memory") else target
            conn.execute(f'USE {target}')
            self._current_db_alias = target
            self._save_state()
            return result

        # plain SQL
        sql_to_run = self._convert_mysql_to_duckdb(q) if dialect == "mysql" else q
        rel = conn.execute(sql_to_run)
        if rel and rel.description:
            data = rel.fetchall()
            if "duckdb_databases" in q.lower():
                patched = []
                for (name,) in data:
                    if name == self._primary_internal_name:
                        patched.append((self._main_db_alias,))
                    else:
                        patched.append((name,))
                data = patched
            result["data"] = data
            result["affected_rows"] = len(data)
        else:
            result["affected_rows"] = rel.rowcount if hasattr(rel, "rowcount") else 0
        return result
    
    def get_db_names(self):
        return list(self._attached_aliases.keys()) + [self._main_db_alias]

    # ─────────── clean-up ───────────
    def close_main_connection(self):
        """
        Persist simulator-state **without** detaching individual databases.
        Detaching on shutdown made persistence pointless: the JSON snapshot
        ended up empty.  Instead we just write the current mapping and close
        the DuckDB connection.  On next start-up, `_load_state_from_json`
        will faithfully re-attach every entry.
        """
        # always save first
        self._save_state()
        if self._main_connection:
            try:
                self._main_connection.close()
            except Exception:  # pragma: no cover – very unlikely
                pass
        # keep aliases dict intact (needed for coverage checks, and harmless
        # once connection is gone).  Mark connection closed.
        self._main_connection = None
        self._current_db_alias = "memory"

    # ─────────── internal helpers ───────────

    def _is_mysql_valid_db_name(self, name: str) -> bool:
        if not name:
            return False
        nm = name.strip("`")
        return bool(re.fullmatch(r"[A-Za-z0-9_\-]+", nm)) and nm not in {".", ".."}

    def _convert_mysql_to_duckdb(self,mysql_sql: str) -> str: # pragma: no cover
        try:
            # Ensure 'mysql' dialect is explicitly used if needed, though sqlglot often infers well.
            mysql_dialect = Dialect.get_or_raise("mysql")
            transpiled_sqls = transpile(mysql_sql, read='mysql', write='duckdb')
            return transpiled_sqls[0] if transpiled_sqls else ""
        except Exception as e: # pragma: no cover
            raise ValueError(f"Error converting MySQL SQL to DuckDB: {e}")
    
    def _conn(self):
        return self._main_connection

    def _resolve_path(self, filename: str, *, for_creation: bool = False) -> str:
        if filename == ":memory:":
            return ":memory:"
        if not (os.sep in filename or filename.endswith((".duckdb", ".db"))):
            filename += ".duckdb"
        path = (
            os.path.join(self._database_directory, filename)
            if not os.path.isabs(filename)
            else filename
        )
        if for_creation:
            os.makedirs(os.path.dirname(os.path.normpath(path)), exist_ok=True)
        return path

    # compatibility for older tests/helpers
    def _sanitize_for_duckdb_alias_and_filename(self, n: str) -> str:
        return self._sanitize(n)

    def _sanitize(self, user_name: str) -> str:
        s = re.sub(r"[^\w.]", "_", user_name.strip("`\"'")).strip("._")
        if s and not re.match(r"[A-Za-z_]", s[0]):
            s = f"_{s}"
        if (
            not s
            or s == "_"
            or s.lower() in {"main", "memory", "temp", "system", ".", ".."}
        ):
            raise ValueError(
                f"name '{user_name}' results in reserved/invalid sanitized duckdb alias '{s}'"
            )
        return s

    def _attach(self, user_alias: str, db_path: str, *, read_only: bool = False):
        conn = self._conn()
        sane = self._sanitize(user_alias)
        conn.execute(f'DETACH DATABASE IF EXISTS "{sane}"')
        self._attached_aliases = {k: v for k, v in self._attached_aliases.items() if v != sane}

        if not os.path.exists(db_path) and not read_only:
            duckdb.connect(db_path).close()

        conn.execute(
            f"ATTACH '{db_path}' AS \"{sane}\"" + (" (READ_ONLY)" if read_only else "")
        )
        self._attached_aliases[user_alias] = sane

    def _detach(self, user_alias: str):
        conn = self._conn()
        sane = self._attached_aliases.get(user_alias, user_alias)

        if sane.lower() == self._main_db_alias:
            raise ValueError(
                f"cannot detach the main database ('{self._main_db_alias}') via manager"
            )

        if self._current_db_alias == sane:
            target = (
                self._primary_internal_name
                if self._primary_internal_name not in {"main", "memory"}
                else self._main_db_alias
            )
            target = f'{target}' if target not in ("main","memory") else target
            conn.execute(f'USE {target}')
            self._current_db_alias = self._main_db_alias

        conn.execute(f'DETACH DATABASE IF EXISTS "{sane}"')
        self._attached_aliases = {k: v for k, v in self._attached_aliases.items() if v != sane}


    # ─────────── persistence helpers ───────────
        # ─────────── persistence helpers ───────────
    def _save_state(self):
        """
        Write the current attachment map and active database to the JSON
        snapshot on disk.

        If `self._state_path` is `None`, persistence is disabled and the
        method returns immediately.
        """
        if not self._state_path:   # nothing to do
            return

        # Build "attached" mapping, including the main DB file when it is
        # not in-memory.
        attached: Dict[str, Dict[str, str]] = {}

        if not self._is_main_memory:
            main_base = os.path.splitext(os.path.basename(self._main_db_url))[0]
            attached[main_base] = {
                "sanitized": main_base,
                "path": os.path.relpath(
                    self._resolve_path(self._main_db_url),
                    start=self._database_directory,
                ),
            }

        for user_alias, sane in self._attached_aliases.items():
            attached[user_alias] = {
                "sanitized": sane,
                "path": os.path.relpath(
                    self._resolve_path(sane + ".duckdb"),
                    start=self._database_directory,
                ),
            }

        state = {
            "attached": attached,
            "current": self._current_db_alias,
            "primary_internal_name": self._primary_internal_name,
        }

        os.makedirs(os.path.dirname(self._state_path), exist_ok=True)
        with open(self._state_path, "w", encoding="utf-8") as fh:
            json.dump(state, fh, indent=2)

    def _load_state_from_json(self) -> bool:
        if not self._state_path or not os.path.exists(self._state_path):
            return False
        try:
            with open(self._state_path, "r", encoding="utf-8") as fh:
                state = json.load(fh)
            for user_alias, info in state.get("attached", {}).items():
                db_rel_path = info.get("path")
                if not db_rel_path:
                    continue
                abs_path = os.path.join(self._database_directory, db_rel_path)
                if not self._is_main_memory and abs_path == self._resolve_path(self._main_db_url):
                    continue
                self._attach(user_alias, abs_path, read_only=False)
            saved_current = state.get("current")
            if saved_current and (
                saved_current == self._main_db_alias
                or saved_current in self._attached_aliases.values()
            ):
                self.execute_query(f"USE {saved_current}")
            self._primary_internal_name = state.get(
                "primary_internal_name", self._primary_internal_name
            )
            return True
        except Exception:
            # any problem -> start fresh
            return False

    def _auto_discover_duckdb_files(self):
        for fname in os.listdir(self._database_directory):
            if not fname.endswith(".duckdb"):
                continue
            base = os.path.splitext(fname)[0]
            if (
                base == os.path.splitext(os.path.basename(self._primary_internal_name))[0]
                or base in {"system", "temp", "main"}
            ):
                continue
            if not self._is_mysql_valid_db_name(base):
                continue
            path = os.path.join(self._database_directory, fname)
            try:
                self._attach(base, path, read_only=False)
            except Exception:
                pass
        self._save_state()