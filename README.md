# SQLite MCP Server

A Model Context Protocol (MCP) server that provides comprehensive SQLite database management and analysis capabilities. This server allows LLMs to explore database schemas, query data, perform updates, and conduct statistical analysis.

## Features

- **Schema Exploration**
  - List all tables in the database
  - View detailed schema information for specific tables
  - Examine column types and constraints

- **Data Management**
  - Execute read-only SQL queries
  - Perform data modifications (UPDATE, INSERT, DELETE)
  - Safe execution with error handling

- **Data Analysis**
  - Basic statistical analysis (row counts, null counts, numeric stats)
  - Detailed analysis including categorical data distributions
  - Automatic type detection and appropriate statistical measures

## Prerequisites

- Python 3.8 or higher
- SQLite database file
- [Claude Desktop](https://claude.ai/download) (optional, for desktop integration)

## Installation

1. First, ensure you have the required Python packages:

```bash
pip install mcp pandas
```

2. Download the SQLite MCP server script:

```bash
# Clone this repository or download sqlite_mcp.py directly
curl -O https://raw.githubusercontent.com/yourusername/sqlite-mcp/main/sqlite_mcp.py
```

3. For Claude Desktop integration:

```bash
# Install using MCP CLI
mcp install sqlite_mcp.py --name "SQLite Explorer" --env DB_PATH=/path/to/your/database.sqlite
```

## Usage

- Locate the claude_desktop_config.json file and add below to the mcpServers section
- change the paths to the correct ones for your system.
- Set database location in DB_PATH variable in the .env file.

```json
"sqlite_mcp": {
    "command": "C:\\path\\to\\python.exe",
    "args": [
    "C:\\path\\to\\sqlite-mcp\\server.py"
    ]
}
```

## Available Resources

The server exposes the following MCP resources:

- `schema://tables`
  - Lists all available tables in the database
  - Example response:
    ```
    Available tables:
    - users
    - products
    - orders
    ```

- `schema://{table}`
  - Returns detailed schema information for a specific table
  - Example response:
    ```
    Table: users
    
    Create Statement:
    CREATE TABLE users (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        email TEXT UNIQUE
    )
    
    Columns:
    - id (INTEGER) NOT NULL PRIMARY KEY
    - name (TEXT) NOT NULL
    - email (TEXT)
    ```

## Available Tools

### query

Execute read-only SQL queries:

```sql
SELECT * FROM users LIMIT 5
```

### update_data

Perform data modifications:

```sql
INSERT INTO users (name, email) VALUES ('John Doe', 'john@example.com')
```

```sql
UPDATE users SET email = 'new@example.com' WHERE id = 1
```

### analyze_table

Perform statistical analysis on table data:

Parameters:
- `table`: Name of the table to analyze
- `analysis_type`: Either 'basic' or 'detailed'

Example response:
```json
{
  "row_count": 1000,
  "column_count": 5,
  "null_counts": {
    "id": 0,
    "name": 0,
    "email": 15
  },
  "numeric_columns": {
    "id": {
      "mean": 500.5,
      "std": 288.819,
      "min": 1,
      "max": 1000
    }
  }
}
```

## Security Considerations

The server implements several security measures:

1. Input validation for all SQL operations
2. Read-only queries are separated from data modifications
3. Database connection error handling
4. SQL injection protection through parameterized queries

## Error Handling

The server provides clear error messages for common issues:

- Database connection failures
- Invalid SQL syntax
- Table not found errors
- Permission issues
- Type mismatches

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
