from __future__ import annotations
import os
import sqlite3
from typing import Optional

from app.models.models import ManualPostalAddress


class AddressResolver:
    """
    Resolves employer postal addresses using two SQLite databases.

    Databases:
    1)Manual DB
       -Stores addresses entered manually by the user.
       -Lookup is performed by company name.

    2)OpenRegister DB
       -Provides registered addresses from a public company register.
       -Lookup is also performed by company name.

    Workflow:
    -First the manual database is checked.
    -If no entry is found, OpenRegister is queried.
    -If still missing, the user can enter an address interactively,
    which is then stored permanently in the manual database.
    """

    def __init__(self, manual_db_path: str, openregister_db_path: str):
        """
        Initialize the AddressResolver and connect to both databases.

        Task:
        -Opens SQLite connections.
        -Ensures the manual database schema exists.
        """
        if not manual_db_path or not manual_db_path.strip():
            raise ValueError("MANUAL_ADDR_DB is missing")
        manual_db_path = manual_db_path.strip()

        if not openregister_db_path or not openregister_db_path.strip():
            raise ValueError("OPENREGISTER_DB is missing")
        openregister_db_path = openregister_db_path.strip()

        if not os.path.exists(openregister_db_path):
            raise FileNotFoundError("OpenRegister DB file not found: " + openregister_db_path)

        self.manual_conn = sqlite3.connect(manual_db_path)
        self.manual_conn.row_factory = sqlite3.Row

        self.openregister_conn = sqlite3.connect(openregister_db_path)
        self.openregister_conn.row_factory = sqlite3.Row

        self.ensure_manual_schema()

    def close(self) -> None:
        self.manual_conn.close()
        self.openregister_conn.close()

    def ensure_manual_schema(self) -> None:
        """
        Ensure the manual DB has the required table and unique index.

        Table: manual_addresses
        -id (autoincrement primary key)
        -company_name (TEXT, required)
        -street (TEXT, required)
        -postal_code (TEXT, required)
        -city (TEXT, required)
        -created_at (default CURRENT_TIMESTAMP)

        Index:
        -Unique, case-insensitive on company_name:
        ux_manual_company_name_nocase ON company_name COLLATE NOCASE
        """
        self.manual_conn.execute(
            """
            CREATE TABLE IF NOT EXISTS manual_addresses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                company_name TEXT NOT NULL,
                street TEXT NOT NULL,
                postal_code TEXT NOT NULL,
                city TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        self.manual_conn.execute(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS ux_manual_company_name_nocase
            ON manual_addresses(company_name COLLATE NOCASE)
            """
        )
        self.manual_conn.commit()

    def find_manual(self, company_name: str) -> Optional[ManualPostalAddress]:
        """
        Look up an address in the manual DB by company name.

        Input:
        -company_name: raw company name from your merged entry

        Behavior:
        -Strips whitespace; if empty -> returns None
        -SELECT street, postal_code, city FROM manual_addresses
        WHERE company_name = ? COLLATE NOCASE
        LIMIT 1

        Output:
        -ManualPostalAddress(...) if found
        -None if not found

        Example:
        DB contains: "ABC GmbH" -> "Main St 1, 12345 Berlin"

        find_manual("Abc GmbH")  -> returns ManualPostalAddress(...)
        find_manual("  ")        -> None
        find_manual("Other Co")  -> None
        """
        name = company_name.strip()
        if not name:
            return None

        row = self.manual_conn.execute(
            """
            SELECT street, postal_code, city
            FROM manual_addresses
            WHERE company_name = ? COLLATE NOCASE
            LIMIT 1
            """,
            (name,),
        ).fetchone()

        if not row:
            return None

        return ManualPostalAddress(
            street=row["street"],
            postal_code=row["postal_code"],
            city=row["city"],
        )

    def save_manual(self, company_name: str, street: str, postal_code: str, city: str) -> None:
        """
        Insert or update an address in the manual DB.

        Inputs:
        -company_name, street, postal_code, city are required.
        If any is empty -> function returns without doing anything.

        Behavior:
        1)Try UPDATE:
        UPDATE manual_addresses SET ... WHERE company_name = ? COLLATE NOCASE
        2)If nothing updated -> INSERT a new row
        3)Commit changes

        Example:
        save_manual("Abc GmbH", "Main St 1", "12345", "Berlin")
        -If "ABC GmbH" exists -> updated
        -If not -> inserted
        """
        name = company_name.strip()
        street = street.strip()
        postal_code = postal_code.strip()
        city = city.strip()

        if not name or not street or not postal_code or not city:
            return

        cur = self.manual_conn.execute(
            """
            UPDATE manual_addresses
            SET street      = ?,
                postal_code = ?,
                city        = ?
            WHERE company_name = ? COLLATE NOCASE
            """,
            (street, postal_code, city, name),
        )

        if cur.rowcount == 0:
            self.manual_conn.execute(
                """
                INSERT INTO manual_addresses (company_name, street, postal_code, city)
                VALUES (?, ?, ?, ?)
                """,
                (name, street, postal_code, city),
            )

        self.manual_conn.commit()

    def find_openregister(self, company_name: str) -> Optional[str]:
        """
        Look up a registered address in the OpenRegister DB by company name.

        Preconditions:
        -OpenRegister DB connection must exist.

        Behavior:
        -Strips whitespace, if empty -> None
        -Queries table "company":
        SELECT registered_address
        FROM company
        WHERE name = ? COLLATE NOCASE
        AND registered_address IS NOT NULL
        AND TRIM(registered_address) != ''
        LIMIT 1

        Output:
        -The raw registered_address string as stored in the OpenRegister DB
        -None if not found
        """
        name = company_name.strip()
        if not name:
            return None

        row = self.openregister_conn.execute(
            """
            SELECT registered_address
            FROM company
            WHERE name = ? COLLATE NOCASE
              AND registered_address IS NOT NULL
              AND TRIM(registered_address) != ''
            LIMIT 1
            """,
            (name,),
        ).fetchone()

        return row["registered_address"] if row else None

    def prompt_and_save(self, company_name: str) -> Optional[str]:
        """
        Interactive fallback:
        Ask the user for an address and store it into the manual DB.

        When used:
        -Only when no address could be resolved automatically.

        -> returns one line formatted address string
        """
        name = company_name.strip()
        if not name:
            return None

        print()
        print("Address not found for: " + name)
        print("Please enter the address (leave empty to skip).")

        street = input("Street: ").strip()
        if not street:
            return None

        postal_code = input("Postal code: ").strip()
        if not postal_code:
            return None

        city = input("City: ").strip()
        if not city:
            return None

        self.save_manual(name, street, postal_code, city)
        return street + ", " + postal_code + " " + city

def load_address_resolver() -> AddressResolver:
    manual_db = os.getenv("MANUAL_ADDR_DB")
    openregister_db = os.getenv("OPENREGISTER_DB")

    return AddressResolver(
        manual_db_path=manual_db or "",
        openregister_db_path=openregister_db or "",
    )