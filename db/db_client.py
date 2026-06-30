import sqlite3
import subprocess
import json


class DBClient:
    CONTAINER_NAME = "open-webui"
    DB_PATH = "/app/backend/data/webui.db"

    def execute(self, query, params=None):
        """
        Execute SQL directly inside the Docker container.

        Returns:
            list: Query results as a list of lists.
        """

        params = params or ()

        script = f"""
import sqlite3
import json

conn = sqlite3.connect('{self.DB_PATH}')
cursor = conn.cursor()

cursor.execute({query!r}, {params!r})

rows = cursor.fetchall()

print(json.dumps(rows))

conn.close()
"""

        result = subprocess.run(
            [
                "docker",
                "exec",
                self.CONTAINER_NAME,
                "python",
                "-c",
                script
            ],
            capture_output=True,
            text=True,
            check=True
        )

        return json.loads(result.stdout.strip())

    def execute_non_query(self, query, params=None):
        """
        Execute INSERT/UPDATE/DELETE statements.
        """

        params = params or ()

        script = f"""
import sqlite3

conn = sqlite3.connect('{self.DB_PATH}')
cursor = conn.cursor()

cursor.execute({query!r}, {params!r})

conn.commit()

conn.close()
"""

        subprocess.run(
            [
                "docker",
                "exec",
                self.CONTAINER_NAME,
                "python",
                "-c",
                script
            ],
            check=True
        )