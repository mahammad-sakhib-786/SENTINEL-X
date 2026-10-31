
import json
import os

import mysql.connector
from dotenv import load_dotenv

load_dotenv()

MAX_REPORTS = 30


def get_connection():
    return mysql.connector.connect(
        host=os.getenv("MYSQL_HOST", "localhost"),
        port=int(os.getenv("MYSQL_PORT", "3306")),
        user=os.getenv("MYSQL_USER"),
        password=os.getenv("MYSQL_PASSWORD"),
        database=os.getenv("MYSQL_DATABASE", "sentinel_x"),
    )


def initialize_database():
    connection = get_connection()
    cursor = connection.cursor()

    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS investigations (
                id INT AUTO_INCREMENT PRIMARY KEY,
                url TEXT NOT NULL,
                risk_score INT,
                risk_level VARCHAR(30),
                findings JSON,
                ai_report TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Add new columns without deleting existing records.
        new_columns = [
            ("threat_intelligence", "JSON"),
            ("ai_assessment", "JSON"),
            ("agent_review", "JSON"),
            ("ai_recommendations", "JSON"),
        ]

        cursor.execute("SHOW COLUMNS FROM investigations")
        existing_columns = {row[0] for row in cursor.fetchall()}

        for column_name, column_type in new_columns:
            if column_name not in existing_columns:
                cursor.execute(
                    f"ALTER TABLE investigations "
                    f"ADD COLUMN {column_name} {column_type} NULL"
                )

        connection.commit()

    except Exception:
        connection.rollback()
        raise

    finally:
        cursor.close()
        connection.close()


def save_investigation(result):
    connection = get_connection()
    cursor = connection.cursor()

    try:
        cursor.execute(
            """
            INSERT INTO investigations (
                url,
                risk_score,
                risk_level,
                findings,
                ai_report,
                threat_intelligence,
                ai_assessment,
                agent_review,
                ai_recommendations
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                result["url"],
                result["risk_score"],
                result["risk_level"],
                json.dumps(result.get("findings") or []),
                result.get("ai_report", ""),
                json.dumps(result.get("threat_intelligence")),
                json.dumps(result.get("ai_assessment")),
                json.dumps(result.get("agent_review")),
                json.dumps(result.get("ai_recommendations")),
            ),
        )

        report_id = cursor.lastrowid

        # Keep only the newest 30 reports.
        cursor.execute(
            """
            SELECT id
            FROM investigations
            ORDER BY id DESC
            LIMIT 18446744073709551615 OFFSET %s
            """,
            (MAX_REPORTS,),
        )

        old_ids = [row[0] for row in cursor.fetchall()]

        if old_ids:
            placeholders = ", ".join(["%s"] * len(old_ids))
            cursor.execute(
                f"DELETE FROM investigations WHERE id IN ({placeholders})",
                tuple(old_ids),
            )

        connection.commit()
        return report_id

    except Exception:
        connection.rollback()
        raise

    finally:
        cursor.close()
        connection.close()


def get_investigations():
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT
                id,
                url,
                risk_score,
                risk_level,
                findings,
                ai_report,
                threat_intelligence,
                ai_assessment,
                agent_review,
                ai_recommendations,
                created_at
            FROM investigations
            ORDER BY id DESC
        """)

        records = cursor.fetchall()

        json_fields = [
            "findings",
            "threat_intelligence",
            "ai_assessment",
            "agent_review",
            "ai_recommendations",
        ]

        for record in records:
            for field in json_fields:
                value = record.get(field)

                if isinstance(value, str):
                    try:
                        record[field] = json.loads(value)
                    except json.JSONDecodeError:
                        record[field] = None

            record["findings"] = record.get("findings") or []

        return records

    finally:
        cursor.close()
        connection.close()


def delete_investigation(report_id):
    connection = get_connection()
    cursor = connection.cursor()

    try:
        cursor.execute(
            "DELETE FROM investigations WHERE id = %s",
            (report_id,),
        )
        connection.commit()
        return cursor.rowcount

    except Exception:
        connection.rollback()
        raise

    finally:
        cursor.close()
        connection.close()


def delete_all_investigations():
    connection = get_connection()
    cursor = connection.cursor()

    try:
        cursor.execute("DELETE FROM investigations")
        deleted_count = cursor.rowcount
        connection.commit()
        return deleted_count

    except Exception:
        connection.rollback()
        raise

    finally:
        cursor.close()
        connection.close()
