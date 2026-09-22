#!/usr/bin/env python3
# ==============================================================================
# kiw-excel - Automatic Department Accounts & Team Seeding
# Ensures all configured department accounts are registered as members of the team
# ==============================================================================
import os
import sys
import time
import sqlite3
import datetime

# Try loading .env if not already loaded into os.environ
def load_env_file(env_path):
    if os.path.isfile(env_path):
        with open(env_path, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    k = k.strip()
                    v = v.strip().strip("'\"")
                    if k not in os.environ:
                        os.environ[k] = v

for candidate in [".env", "../.env", "/persist/.env", "/data/.env"]:
    load_env_file(candidate)

# Auto-detect data directory:
DATA_DIR = os.environ.get("DATA_DIR")
if not DATA_DIR:
    if os.path.exists("/persist/home.sqlite3") or os.path.exists("/persist"):
        DATA_DIR = "/persist"
    elif os.path.exists("/data/home.sqlite3") or os.path.exists("/data"):
        DATA_DIR = "/data"
    elif os.path.exists("./grist-data/home.sqlite3") or os.path.exists("./grist-data"):
        DATA_DIR = "./grist-data"
    else:
        DATA_DIR = "/data"

DB_PATH = os.path.join(DATA_DIR, "home.sqlite3")
TEAM_NAME = os.environ.get("TEAM", "citiplumb")

# Map of department email prefixes to friendly display names
FRIENDLY_NAMES = {
    "admin": "Admin Citiplumb",
    "gudang.lokal": "Gudang Lokal",
    "gudang.impor": "Gudang Impor",
    "kepala.gudang": "Kepala Gudang",
    "ppic": "PPIC",
    "plating": "Plating",
    "injeksi": "Injeksi",
    "spray": "Spray",
    "assembly": "Assembly",
    "purchase": "Admin Purchase",
    "purchasing": "Admin Purchase",
}

# Collect all accounts from environment
accounts = []

def add_acc(prefix, role="editor"):
    email_var = f"EMAIL{prefix}" if prefix else "EMAIL"
    email = os.environ.get(email_var)
    if email:
        clean_email = email.strip()
        username = clean_email.split("@")[0].lower()
        friendly_name = FRIENDLY_NAMES.get(username, username.replace(".", " ").title())
        accounts.append({
            "email": clean_email,
            "name": friendly_name,
            "role": role
        })

add_acc("", role="owner")
for i in range(2, 20):
    add_acc(str(i), role="editor")

if not accounts:
    print("[Init Users] No accounts configured in environment.")
    sys.exit(0)

# Waiting / retry loop (up to 30 seconds) for Grist to initialize database & team
MAX_WAIT = int(os.environ.get("INIT_USERS_WAIT_TIMEOUT", "30"))
start_time = time.time()

print(f"[Init Users] Checking database at {DB_PATH} for team '{TEAM_NAME}' (timeout {MAX_WAIT}s)...")

con = None
org_id = None
owner_gid = None
editor_gid = None

while time.time() - start_time < MAX_WAIT:
    if os.path.exists(DB_PATH):
        try:
            test_con = sqlite3.connect(DB_PATH, timeout=5)
            test_cur = test_con.cursor()
            org_row = test_cur.execute(
                "SELECT id, name FROM orgs WHERE domain = ? OR name = ?;", 
                (TEAM_NAME, TEAM_NAME)
            ).fetchone()
            if org_row:
                org_id = org_row[0]
                groups = {}
                for gid, perm, gname in test_cur.execute("""
                    SELECT ar.group_id, ar.permissions, g.name
                    FROM acl_rules ar
                    JOIN groups g ON ar.group_id = g.id
                    WHERE ar.org_id = ?;
                """, (org_id,)).fetchall():
                    groups[gname] = gid
                
                if "owners" in groups and "editors" in groups:
                    owner_gid = groups["owners"]
                    editor_gid = groups["editors"]
                    con = test_con
                    break
            test_con.close()
        except Exception:
            pass
    time.sleep(2)

if not con or not org_id or not editor_gid or not owner_gid:
    print(f"[Init Users] Organization '{TEAM_NAME}' not found or not ready yet. Skipping sync.")
    sys.exit(0)

try:
    cur = con.cursor()
    now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

    added_count = 0
    updated_count = 0

    for acc in accounts:
        email = acc["email"]
        name = acc["name"]
        target_role = acc["role"]
        target_gid = owner_gid if target_role == "owner" else editor_gid

        # Check if user already exists
        user_row = cur.execute("""
            SELECT u.id, u.name FROM users u
            JOIN logins l ON l.user_id = u.id
            WHERE lower(l.email) = lower(?);
        """, (email,)).fetchone()

        if not user_row:
            # Create user
            cur.execute("""
                INSERT INTO users (name, ref, type, created_at)
                VALUES (?, ?, 'login', ?);
            """, (name, email, now))
            user_id = cur.lastrowid

            # Create login entry
            cur.execute("""
                INSERT INTO logins (user_id, email, display_email)
                VALUES (?, ?, ?);
            """, (user_id, email, email))
            print(f"[Init Users] Created user {email} (id={user_id}, name='{name}').")
        else:
            user_id = user_row[0]
            existing_name = user_row[1]
            # Update display name to friendly name if different
            if existing_name != name:
                cur.execute("UPDATE users SET name = ? WHERE id = ?;", (name, user_id))
                updated_count += 1

        # Check if user is in target group of the team org
        membership = cur.execute("""
            SELECT 1 FROM group_users WHERE group_id = ? AND user_id = ?;
        """, (target_gid, user_id)).fetchone()

        if not membership:
            cur.execute("""
                INSERT OR IGNORE INTO group_users (group_id, user_id)
                VALUES (?, ?);
            """, (target_gid, user_id))
            added_count += 1
            print(f"[Init Users] Added {email} to team '{TEAM_NAME}' as {target_role} (group_id={target_gid}).")

    con.commit()
    con.close()
    print(f"[Init Users] Synchronization complete: {added_count} membership(s) added, {updated_count} name(s) updated.")

except Exception as e:
    print(f"[Init Users] Error during synchronization: {e}")
