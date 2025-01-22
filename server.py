from mcp.server.fastmcp import FastMCP, Context
import sqlite3
from typing import List, Dict, Any, Optional
import pandas as pd
from dataclasses import dataclass
import json
import os
import sys

DEFAULT_DB_PATH = f"{os.getenv('HOMEPATH')}\\mcpDefaultSqlite.db"

if sys.platform == "darwin":
    DEFAULT_DB_PATH = f"~/mcpDefaultSqlite.db"

class DatabaseManager:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._test_connection()
    
    def _test_connection(self):
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("SELECT 1")
        except sqlite3.Error as e:
            raise ValueError(f"Could not connect to database: {str(e)}")
    
    def get_connection(self):
        return sqlite3.connect(self.db_path)

    def get_tables(self) -> List[str]:
        with self.get_connection() as conn:
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
            return [row[0] for row in cursor.fetchall()]

    def get_schema(self, table_name: str) -> str:
        with self.get_connection() as conn:
            cursor = conn.execute(
                "SELECT sql FROM sqlite_master WHERE type='table' AND name=?",
                (table_name,)
            )
            result = cursor.fetchone()
            if not result:
                raise ValueError(f"Table {table_name} not found")
            return result[0]

    def get_table_info(self, table_name: str) -> List[Dict[str, str]]:
        with self.get_connection() as conn:
            cursor = conn.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            return [
                {
                    "name": col[1],
                    "type": col[2],
                    "notnull": bool(col[3]),
                    "pk": bool(col[4])
                }
                for col in columns
            ]

class SQLiteMCP:
    def __init__(self, db_path: str):
        if db_path is None:
            # db_path = ":memory:"
            db_path = DEFAULT_DB_PATH
        self.db = DatabaseManager(db_path)
        self.mcp = FastMCP("SQLite Explorer")
        self._setup_resources()
        self._setup_tools()
    
    def _setup_resources(self):
        @self.mcp.resource("schema://tables")
        def list_tables() -> str:
            """Get a list of all tables in the database"""
            tables = self.db.get_tables()
            return "Available tables:\n" + "\n".join(f"- {table}" for table in tables)

        @self.mcp.resource("schema://{table}")
        def get_table_schema(table: str) -> str:
            """Get the schema for a specific table"""
            try:
                schema = self.db.get_schema(table)
                columns = self.db.get_table_info(table)
                
                # Format detailed schema information
                details = [
                    f"Table: {table}",
                    "\nCreate Statement:",
                    schema,
                    "\nColumns:",
                ]
                
                for col in columns:
                    details.append(
                        f"- {col['name']} ({col['type']})"
                        f"{' NOT NULL' if col['notnull'] else ''}"
                        f"{' PRIMARY KEY' if col['pk'] else ''}"
                    )
                
                return "\n".join(details)
            except Exception as e:
                return f"Error retrieving schema: {str(e)}"

    def _setup_tools(self):
        @self.mcp.tool()
        def query(sql: str) -> str:
            """
            Execute a SQL query and return the results
            
            Args:
                sql: SQL query to execute
            """
            try:
                with self.db.get_connection() as conn:
                    df = pd.read_sql_query(sql, conn)
                    return df.to_string()
            except Exception as e:
                return f"Error executing query: {str(e)}"

        @self.mcp.tool()
        def update_data(table: str, sql: str) -> str:
            """
            Execute an UPDATE or INSERT SQL statement
            
            Args:
                table: Table to modify
                sql: SQL statement to execute
            """
            if not any(keyword in sql.upper() for keyword in ["UPDATE", "INSERT", "DELETE"]):
                return "Error: Only UPDATE, INSERT, and DELETE statements are allowed"
                
            try:
                with self.db.get_connection() as conn:
                    cursor = conn.execute(sql)
                    conn.commit()
                    return f"Successfully modified {cursor.rowcount} rows"
            except Exception as e:
                return f"Error updating data: {str(e)}"

        @self.mcp.tool()
        def get_database_path() -> str:
            """
            Get the path to the database
            """
            return DEFAULT_DB_PATH


        @self.mcp.tool()
        def analyze_table(table: str, analysis_type: str = "basic") -> str:
            """
            Perform statistical analysis on a table
            
            Args:
                table: Table to analyze
                analysis_type: Type of analysis ('basic' or 'detailed')
            """
            try:
                with self.db.get_connection() as conn:
                    df = pd.read_sql_query(f"SELECT * FROM {table}", conn)
                    
                    if analysis_type == "basic":
                        stats = {
                            "row_count": len(df),
                            "column_count": len(df.columns),
                            "null_counts": df.isnull().sum().to_dict(),
                            "numeric_columns": {
                                col: {
                                    "mean": df[col].mean(),
                                    "std": df[col].std(),
                                    "min": df[col].min(),
                                    "max": df[col].max()
                                }
                                for col in df.select_dtypes(include=['number']).columns
                            }
                        }
                    else:  # detailed
                        stats = {
                            "row_count": len(df),
                            "column_count": len(df.columns),
                            "null_counts": df.isnull().sum().to_dict(),
                            "numeric_columns": {
                                col: df[col].describe().to_dict()
                                for col in df.select_dtypes(include=['number']).columns
                            },
                            "categorical_columns": {
                                col: df[col].value_counts().to_dict()
                                for col in df.select_dtypes(include=['object']).columns
                            }
                        }
                    
                    return json.dumps(stats, indent=2)
            except Exception as e:
                return f"Error analyzing table: {str(e)}"

    def run(self):
        """Run the MCP server"""
        self.mcp.run()

if __name__ == "__main__":
    # import argparse
    
    # parser = argparse.ArgumentParser(description="SQLite MCP Server")
    # # parser.add_argument("database", help="Path to SQLite database file")
    # parser.add_argument("DB_PATH", help="Path to SQLite database file")

    # args = parser.parse_args()
    server = SQLiteMCP(DEFAULT_DB_PATH)
    if os.getenv("DB_PATH") != None:
        if os.path.exists(os.getenv("DB_PATH")):
            server = SQLiteMCP(os.getenv("DB_PATH"))
            DEFAULT_DB_PATH = os.getenv("DB_PATH")

    server.run()
