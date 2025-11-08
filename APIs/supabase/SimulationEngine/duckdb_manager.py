"""
DuckDB Manager for Supabase PostgreSQL simulation.

This module provides a PostgreSQL-compatible query execution layer using DuckDB
for the Supabase API simulation. It handles:
- Multiple projects with isolated IN-MEMORY databases
- PostgreSQL schema support (public, analytics, etc.)
- Table creation from JSON definitions
- Query execution with proper result formatting
- PostgreSQL-specific type mapping and response formats

IMPORTANT: All databases are IN-MEMORY only. No data is persisted to disk.
Each session starts fresh, and all data is lost when the session ends.
This is intentional for the simulation environment.
"""

from __future__ import annotations
from common_utils.print_log import print_log

import re
from typing import Dict,Optional,  Any
from datetime import datetime
from decimal import Decimal

import duckdb
from sqlglot import parse_one, transpile
from sqlglot.expressions import Select, Insert, Update, Delete, Create, Drop, Alter

from .db import DB
from . import custom_errors


class SupabaseDuckDBManager:
    """
    Manages DuckDB connections for Supabase project SQL simulation.
    
    Each Supabase project gets its own DuckDB database file to ensure
    complete isolation. Supports PostgreSQL schemas and query execution.
    """
    
    # PostgreSQL to DuckDB type mapping
    PG_TO_DUCK_TYPE_MAP = {
        'uuid': 'VARCHAR',
        'text': 'VARCHAR',
        'varchar': 'VARCHAR',
        'character varying': 'VARCHAR',
        'integer': 'INTEGER',
        'int': 'INTEGER',
        'bigint': 'BIGINT',
        'smallint': 'SMALLINT',
        'numeric': 'DECIMAL',
        'decimal': 'DECIMAL',
        'real': 'REAL',
        'double precision': 'DOUBLE',
        'float': 'DOUBLE',
        'boolean': 'BOOLEAN',
        'bool': 'BOOLEAN',
        'date': 'DATE',
        'time': 'TIME',
        'timestamp': 'TIMESTAMP',
        'timestamp with time zone': 'TIMESTAMP WITH TIME ZONE',
        'timestamp without time zone': 'TIMESTAMP',
        'timestamptz': 'TIMESTAMP WITH TIME ZONE',
        'json': 'JSON',
        'jsonb': 'JSON',
        'bytea': 'BLOB',
        'serial': 'INTEGER',
        'bigserial': 'BIGINT'
    }
    
    # PostgreSQL type OIDs (subset of common types)
    PG_TYPE_OIDS = {
        'VARCHAR': 1043,
        'TEXT': 25,
        'INTEGER': 23,
        'BIGINT': 20,
        'SMALLINT': 21,
        'DECIMAL': 1700,
        'NUMERIC': 1700,
        'REAL': 700,
        'DOUBLE': 701,
        'BOOLEAN': 16,
        'DATE': 1082,
        'TIME': 1083,
        'TIMESTAMP': 1114,
        'TIMESTAMP WITH TIME ZONE': 1184,
        'JSON': 114,
        'BLOB': 17,
        'UUID': 2950
    }
    
    def __init__(self, temp_dir: Optional[str] = None):
        """
        Initialize the DuckDB manager.
        
        Args:
            temp_dir: Optional directory for storing DuckDB files. 
                     If None, uses system temp directory.
                     NOT USED in this implementation - kept for API compatibility.
        """
        # Store connections in memory only - no persistence
        self._connections: Dict[str, duckdb.DuckDBPyConnection] = {}
        self._initialized_projects: set = set()
        
    def _get_connection(self, project_id: str) -> duckdb.DuckDBPyConnection:
        """
        Get or create an IN-MEMORY DuckDB connection for a project.
        
        Each project gets its own in-memory database that exists only
        for the duration of the session. No data is persisted to disk.
        
        Args:
            project_id: The Supabase project ID
            
        Returns:
            In-memory DuckDB connection for the project
        """
        if project_id not in self._connections:
            # Use ":memory:" for in-memory database - no files created
            self._connections[project_id] = duckdb.connect(":memory:")
            
        return self._connections[project_id]
    
    def _convert_pg_type_to_duckdb(self, pg_type: str) -> str:
        """Convert PostgreSQL type to DuckDB equivalent."""
        pg_type_lower = pg_type.lower()
        
        # Handle array types
        if pg_type_lower.endswith('[]'):
            base_type = pg_type_lower[:-2]
            duck_base = self.PG_TO_DUCK_TYPE_MAP.get(base_type, 'VARCHAR')
            return f"{duck_base}[]"
            
        # Handle types with parameters like VARCHAR(255)
        match = re.match(r'(\w+)(\(.+\))', pg_type_lower)
        if match:
            base_type = match.group(1)
            params = match.group(2)
            duck_base = self.PG_TO_DUCK_TYPE_MAP.get(base_type, base_type.upper())
            return f"{duck_base}{params}"
            
        return self.PG_TO_DUCK_TYPE_MAP.get(pg_type_lower, pg_type.upper())
    
    def _get_type_oid(self, duck_type: str) -> int:
        """Get PostgreSQL type OID for a DuckDB type."""
        # Normalize type name
        type_upper = duck_type.upper().split('(')[0].strip()
        return self.PG_TYPE_OIDS.get(type_upper, 705)  # 705 is 'unknown' type OID
    
    def _initialize_project_if_needed(self, project_id: str) -> None:
        """
        Initialize a project's database with tables from the DB state.
        
        Args:
            project_id: The project ID to initialize
        """
        if project_id in self._initialized_projects:
            return
            
        conn = self._get_connection(project_id)
        tables = DB.get("tables", {}).get(project_id, [])
        
        # Group tables by schema
        schemas = set()
        for table in tables:
            schema = table.get("schema", "public")
            schemas.add(schema)
        
        # Create schemas
        for schema in schemas:
            try:
                conn.execute(f"CREATE SCHEMA IF NOT EXISTS {schema}")
            except Exception:
                # Schema might already exist
                pass
        
        # Create tables
        for table in tables:
            schema = table.get("schema", "public")
            table_name = table["name"]
            columns = table.get("columns", [])
            primary_keys = table.get("primary_keys", [])
            
            # Build column definitions
            col_defs = []
            for col in columns:
                col_name = col["name"]
                col_type = self._convert_pg_type_to_duckdb(col["data_type"])
                nullable = "" if col.get("is_nullable", True) else " NOT NULL"
                default = ""
                if col.get("default_value"):
                    # Handle PostgreSQL function defaults
                    default_val = col["default_value"]
                    if default_val.lower() in ["now()", "current_timestamp"]:
                        default = " DEFAULT CURRENT_TIMESTAMP"
                    elif default_val.lower() == "uuid_generate_v4()":
                        # DuckDB doesn't have uuid_generate_v4, use a placeholder
                        default = " DEFAULT gen_random_uuid()"
                    else:
                        default = f" DEFAULT {default_val}"
                
                col_defs.append(f"{col_name} {col_type}{nullable}{default}")
            
            # Add primary key constraint
            if primary_keys:
                pk_names = [pk["name"] for pk in primary_keys]
                col_defs.append(f"PRIMARY KEY ({', '.join(pk_names)})")
            
            # Create the table
            create_sql = f"CREATE TABLE IF NOT EXISTS {schema}.{table_name} ({', '.join(col_defs)})"
            try:
                conn.execute(create_sql)
            except Exception as e:
                # Log but don't fail - some features might not be supported
                print_log(f"Warning: Could not create table {schema}.{table_name}: {e}")
        
        # TODO: Add foreign key constraints based on relationships
        
        self._initialized_projects.add(project_id)
    
    def _parse_query_type(self, sql: str) -> str:
        """
        Parse the query type from SQL string.
        
        Returns: 'select', 'insert', 'update', 'delete', 'ddl', or 'other'
        """
        try:
            parsed = parse_one(sql, dialect="postgres")
            if isinstance(parsed, Select):
                return "select"
            elif isinstance(parsed, Insert):
                return "insert"
            elif isinstance(parsed, Update):
                return "update"
            elif isinstance(parsed, Delete):
                return "delete"
            elif isinstance(parsed, (Create, Drop, Alter)):
                return "ddl"
        except Exception:
            # Fallback to simple keyword matching
            sql_upper = sql.strip().upper()
            if sql_upper.startswith("SELECT"):
                return "select"
            elif sql_upper.startswith("INSERT"):
                return "insert"
            elif sql_upper.startswith("UPDATE"):
                return "update"
            elif sql_upper.startswith("DELETE"):
                return "delete"
            elif any(sql_upper.startswith(kw) for kw in ["CREATE", "ALTER", "DROP", "TRUNCATE"]):
                return "ddl"
        
        return "other"
    
    def _preprocess_postgresql_sql(self, sql: str) -> str:
        """
        Preprocess PostgreSQL SQL to make it compatible with DuckDB.
        
        Args:
            sql: Raw PostgreSQL SQL query
            
        Returns:
            DuckDB-compatible SQL query
        """
        # Convert PostgreSQL SERIAL types to DuckDB equivalents
        # Since DuckDB doesn't have auto-increment, we'll just convert to the base type
        # and rely on users to handle ID generation manually (common in testing scenarios)
        
        # Handle SERIAL columns - convert to INTEGER but keep constraints
        serial_pattern = r'\b(\w+)\s+SERIAL\b([^,\)]*)'
        def replace_serial(match):
            col_name = match.group(1)
            constraints = match.group(2)
            return f"{col_name} INTEGER{constraints}"
        
        sql = re.sub(serial_pattern, replace_serial, sql, flags=re.IGNORECASE)
        
        # Handle BIGSERIAL columns - convert to BIGINT but keep constraints  
        bigserial_pattern = r'\b(\w+)\s+BIGSERIAL\b([^,\)]*)'
        def replace_bigserial(match):
            col_name = match.group(1)
            constraints = match.group(2)
            return f"{col_name} BIGINT{constraints}"
        
        sql = re.sub(bigserial_pattern, replace_bigserial, sql, flags=re.IGNORECASE)
        
        # Handle other PostgreSQL-specific constructs
        # Convert uuid_generate_v4() to gen_random_uuid()
        sql = re.sub(r'\buuid_generate_v4\(\)', 'gen_random_uuid()', sql, flags=re.IGNORECASE)
        
        # Convert now() to CURRENT_TIMESTAMP for consistency
        sql = re.sub(r'\bnow\(\)', 'CURRENT_TIMESTAMP', sql, flags=re.IGNORECASE)
        
        return sql

    def execute_query(self, project_id: str, query: str) -> Dict[str, Any]:
        """
        Execute a SQL query for a project.
        
        Args:
            project_id: The project ID
            query: The SQL query to execute
            
        Returns:
            Query result formatted according to PostgreSQL conventions:
            - For SELECT: {"rows": [...], "columns": [...], "row_count": n}
            - For DML: {"row_count": n, "status_message": "..."}
            
        Raises:
            DatabaseConnectionError: If connection fails
            SQLError: If query execution fails
        """
        try:
            self._initialize_project_if_needed(project_id)
            conn = self._get_connection(project_id)
        except Exception as e:
            raise custom_errors.DatabaseConnectionError(
                f"Failed to connect to project database: {str(e)}"
            )
        
        # Preprocess PostgreSQL SQL to make it DuckDB-compatible
        preprocessed_query = self._preprocess_postgresql_sql(query)
        query_type = self._parse_query_type(preprocessed_query)
        
        # For DML operations, modify query to use RETURNING clause to get accurate row count
        modified_query = preprocessed_query
        if query_type in ["insert", "update", "delete"]:
            # Add RETURNING clause if not already present to get accurate row count
            if "RETURNING" not in preprocessed_query.upper():
                # Add a minimal RETURNING clause to count affected rows
                modified_query = f"{preprocessed_query.rstrip(';')} RETURNING 1"
        
        try:
            # Try to transpile PostgreSQL to DuckDB SQL
            try:
                transpiled = transpile(modified_query, read="postgres", write="duckdb")
                if transpiled:
                    modified_query = transpiled[0]
            except Exception:
                # If transpilation fails, try executing as-is
                pass
            
            # Execute the query
            result = conn.execute(modified_query)
            
            if query_type == "select":
                # Format SELECT results
                rows = result.fetchall()
                columns = []
                
                if result.description:
                    for col_info in result.description:
                        col_name = col_info[0]
                        # DuckDB provides type info, but we need to map to PG OIDs
                        col_type = str(col_info[1]) if col_info[1] else "VARCHAR"
                        type_oid = self._get_type_oid(col_type)
                        
                        columns.append({
                            "name": col_name,
                            "type_oid": type_oid
                        })
                
                # Convert rows to list of dicts
                row_dicts = []
                for row in rows:
                    row_dict = {}
                    for i, col in enumerate(columns):
                        value = row[i]
                        # Handle special types
                        if isinstance(value, datetime):
                            value = value.isoformat()
                        elif value is None:
                            value = None
                        elif isinstance(value, (int, float, bool, Decimal)):
                            # Keep numeric and boolean types as-is (convert Decimal to float for JSON compatibility)
                            value = float(value) if isinstance(value, Decimal) else value
                        else:
                            # Convert everything else to string (text, varchar, etc.)
                            value = str(value)
                        row_dict[col["name"]] = value
                    row_dicts.append(row_dict)
                
                return {
                    "rows": row_dicts,
                    "columns": columns,
                    "row_count": len(rows)
                }
                
            elif query_type in ["insert", "update", "delete"]:
                # Format DML results
                # Use RETURNING clause results to get accurate row count
                try:
                    # If we added RETURNING clause, get the actual affected rows
                    if "RETURNING" in modified_query.upper():
                        rows = result.fetchall()
                        affected_rows = len(rows)
                    else:
                        # Fallback - this shouldn't happen with our modification above
                        affected_rows = 1
                except Exception:
                    # Final fallback
                    affected_rows = 1
                
                # Generate PostgreSQL-style status message
                if query_type == "insert":
                    # PostgreSQL format: INSERT 0 <count>
                    status_message = f"INSERT 0 {affected_rows}"
                elif query_type == "update":
                    # PostgreSQL format: UPDATE <count>
                    status_message = f"UPDATE {affected_rows}"
                elif query_type == "delete":
                    # PostgreSQL format: DELETE <count>
                    status_message = f"DELETE {affected_rows}"
                
                return {
                    "row_count": affected_rows,
                    "status_message": status_message
                }
                
            else:
                # DDL and other queries
                return {
                    "row_count": 0,
                    "status_message": "OK"
                }
                
        except duckdb.CatalogException as e:
            # Table/schema not found errors
            error_msg = str(e)
            if "Table" in error_msg and "not found" in error_msg:
                raise custom_errors.SQLError(f"relation does not exist: {error_msg}")
            elif "Schema" in error_msg and "not found" in error_msg:
                raise custom_errors.SQLError(f"schema does not exist: {error_msg}")
            else:
                raise custom_errors.SQLError(f"Catalog error: {error_msg}")
                
        except duckdb.ParserException as e:
            # SQL syntax errors
            raise custom_errors.SQLError(f"syntax error: {str(e)}")
            
        except duckdb.ConversionException as e:
            # Type conversion errors
            raise custom_errors.SQLError(f"type error: {str(e)}")
            
        except Exception as e:
            # Generic execution errors
            raise custom_errors.SQLError(f"Query execution failed: {str(e)}")
    
    def reset_project_schema(self, project_id: str):
        """
        Resets the database for a given project by closing its connection
        and removing it from the initialized set.
        
        Args:
            project_id: The project ID to reset.
        """
            
        if project_id in self._initialized_projects:
            self._initialized_projects.remove(project_id)
            
        # Re-create a fresh connection and default schemas
        conn = self._get_connection(project_id)
        conn.execute("CREATE SCHEMA IF NOT EXISTS public")
    

    def close_all_connections(self):
        """Close all open DuckDB connections."""
        for conn in self._connections.values():
            try:
                conn.close()
            except Exception:
                pass
        self._connections.clear()
        self._initialized_projects.clear()


# Global instance for reuse
_duckdb_manager: Optional[SupabaseDuckDBManager] = None


def get_duckdb_manager() -> SupabaseDuckDBManager:
    """Get or create the global DuckDB manager instance."""
    global _duckdb_manager
    if _duckdb_manager is None:
        _duckdb_manager = SupabaseDuckDBManager()
    return _duckdb_manager