import sqlite3

class DatabaseManager:
    def __init__(self, db_path='telegram.db'):
        self.connection = sqlite3.connect(db_path, check_same_thread=False)
        self.cursor = self.connection.cursor()
        self.initialize_tables()

    def initialize_tables(self):
        # Create credentials table
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS credentials (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                api_id INTEGER NOT NULL,
                api_hash TEXT NOT NULL,
                session_data TEXT NOT NULL,
                user_id TEXT NOT NULL, 
                username TEXT NOT NULL
            )
        """)
        # Create groups table
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS groups (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                type TEXT NOT NULL
            )
        """)
        # Create users table
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                username TEXT NOT NULL,
                full_name TEXT NOT NULL,
                group_id INTEGER,
                table_name TEXT,
                FOREIGN KEY (group_id) REFERENCES groups(id)
            )
        """)
        self.connection.commit()

    def get_all_credentials(self):
        self.cursor.execute("SELECT id, api_id, api_hash, session_data, user_id, username FROM credentials")
        return self.cursor.fetchall()


    def get_credentials_by_id(self, cred_id):
        self.cursor.execute("SELECT api_id, api_hash, session_data FROM credentials WHERE id = ?", (cred_id,))
        return self.cursor.fetchone()

    def add_credentials(self, api_id, api_hash, session_data, user_id, username):
        self.cursor.execute("""
        INSERT INTO credentials (api_id, api_hash, session_data, user_id, username)
        VALUES (?, ?, ?, ?, ?)
        """, (api_id, api_hash, session_data, user_id, username))
        self.connection.commit()

    def add_group(self, group_id, group_name, group_type):
        self.cursor.execute("""
            INSERT OR IGNORE INTO groups (id, name, type)
            VALUES (?, ?, ?)
        """, (group_id, group_name, group_type))
        self.connection.commit()

    def add_user(self, user_id, username, full_name, group_id, save_table):
        # Validate table name to prevent SQL injection
        if not save_table.isidentifier():
            raise ValueError("Invalid table name. Use only letters, numbers, and underscores.")

        # Create table if it doesn't exist
        self.cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS "{save_table}" (
                id INTEGER PRIMARY KEY,
                username TEXT NOT NULL,
                full_name TEXT NOT NULL
            )
        """)
        self.connection.commit()

        # Insert user into the specified table
        self.cursor.execute(f"""
            INSERT OR IGNORE INTO "{save_table}" (id, username, full_name)
            VALUES (?, ?, ?)
        """, (user_id, username, full_name))
        self.connection.commit()
    
    def get_table_names(self):
        """
        Retrieve all table names excluding 'credentials', 'groups', 'users', and internal SQLite tables.

        Returns:
            List[str]: A list of table names.
        """
        self.cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' 
        AND name NOT LIKE 'sqlite_%' 
        AND name NOT IN ('credentials', 'groups', 'users');
        """)
        tables = [row[0] for row in self.cursor.fetchall()]
        return tables


    def close(self):
        self.connection.close()

    def get_users_from_table(self, table_name):
        """
        Retrieve all users from the specified table.

        Args:
            table_name (str): The name of the table to fetch users from.

        Returns:
            List[Tuple]: A list of tuples, each representing a user.
                        Each tuple contains (id, username, full_name).
        """
        # Validate table name to prevent SQL injection
        if not table_name.isidentifier():
            raise ValueError("Invalid table name. Use only letters, numbers, and underscores.")

        # Prepare the SQL query
        query = f"""
            SELECT id, username, full_name 
            FROM "{table_name}"
        """

        try:
            self.cursor.execute(query)
            users = self.cursor.fetchall()
            return users
        except sqlite3.OperationalError as e:
            print(f"Database error: {e}")
            raise  # Re-raise the exception to be handled by the caller
        
    def delete_user_from_table(self, table_name, username):
        """
        Delete a user from a specified table by username.

        Args:
            table_name (str): The name of the table.
            username (str): The username of the user to delete.
        """
        # Validate table name to prevent SQL injection
        if not table_name.isidentifier():
            raise ValueError("Invalid table name. Use only letters, numbers, and underscores.")

        try:
            self.cursor.execute(f'DELETE FROM "{table_name}" WHERE username = ?', (username,))
            self.connection.commit()
            print(f"DEBUG: Deleted user '{username}' from table '{table_name}'.")
        except sqlite3.OperationalError as e:
            print(f"Database error when deleting user: {e}")
            raise  # Re-raise the exception to be handled by the caller
