import argparse
import json
import secrets
import sqlite3
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_DB = BASE_DIR / "data" / "license_server.sqlite3"


def now_iso():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def parse_time(value):
    value = str(value or "").strip()
    if not value:
        return None
    if value.endswith("Z"):
        value = value[:-1] + "+00:00"
    try:
        result = datetime.fromisoformat(value)
    except ValueError:
        result = datetime.fromisoformat(value + "T23:59:59+00:00")
    if result.tzinfo is None:
        result = result.replace(tzinfo=timezone.utc)
    return result


def is_expired(expires_at):
    expires = parse_time(expires_at)
    return bool(expires and datetime.now(timezone.utc) > expires)


def connect(db_path):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path):
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    with connect(db_path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS license_cards (
                card_key TEXT PRIMARY KEY,
                expires_at TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'active',
                machine_id TEXT NOT NULL DEFAULT '',
                machine_name TEXT NOT NULL DEFAULT '',
                bind_at TEXT NOT NULL DEFAULT '',
                token TEXT NOT NULL DEFAULT '',
                unbind_count INTEGER NOT NULL DEFAULT 0,
                max_unbinds INTEGER NOT NULL DEFAULT 3,
                created_at TEXT NOT NULL
            )
            """
        )


def create_card(db_path, card_key, expires_at, max_unbinds=3):
    init_db(db_path)
    with connect(db_path) as conn:
        conn.execute(
            """
            INSERT INTO license_cards(card_key, expires_at, max_unbinds, created_at)
            VALUES(?, ?, ?, ?)
            ON CONFLICT(card_key) DO UPDATE SET
                expires_at=excluded.expires_at,
                max_unbinds=excluded.max_unbinds,
                status='active'
            """,
            (card_key, expires_at, int(max_unbinds), now_iso()),
        )


def row_to_public(row, message="操作成功"):
    remaining = max(0, int(row["max_unbinds"]) - int(row["unbind_count"]))
    return {
        "ok": True,
        "message": message,
        "card_key": row["card_key"],
        "expires_at": row["expires_at"],
        "remaining_unbinds": remaining,
        "bound": bool(row["machine_id"]),
        "machine_name": row["machine_name"],
    }


class LicenseHandler(BaseHTTPRequestHandler):
    server_version = "GrokVideoLicense/1.0"

    def read_payload(self):
        length = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(length).decode("utf-8") if length else "{}"
        return json.loads(raw or "{}")

    def write_json(self, status, data):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def fail(self, status, message):
        self.write_json(status, {"ok": False, "message": message})

    def load_card(self, conn, card_key):
        row = conn.execute("SELECT * FROM license_cards WHERE card_key=?", (card_key,)).fetchone()
        if not row:
            raise ValueError("卡密不存在")
        if row["status"] != "active":
            raise ValueError("卡密已停用")
        if is_expired(row["expires_at"]):
            raise ValueError("卡密已到期")
        return row

    def do_POST(self):
        try:
            payload = self.read_payload()
            card_key = str(payload.get("card_key") or "").strip()
            machine_id = str(payload.get("machine_id") or "").strip()
            machine_name = str(payload.get("machine_name") or "").strip()
            token = str(payload.get("token") or "").strip()
            if not card_key:
                self.fail(400, "缺少卡密")
                return
            if not machine_id:
                self.fail(400, "缺少机器码")
                return
            if self.path == "/api/license/activate":
                self.handle_activate(card_key, machine_id, machine_name)
            elif self.path == "/api/license/query":
                self.handle_query(card_key, machine_id)
            elif self.path == "/api/license/unbind":
                self.handle_unbind(card_key, machine_id, token)
            else:
                self.fail(404, "接口不存在")
        except json.JSONDecodeError:
            self.fail(400, "请求 JSON 无效")
        except ValueError as exc:
            self.fail(400, str(exc))
        except Exception as exc:
            self.fail(500, f"服务器错误：{exc}")

    def handle_activate(self, card_key, machine_id, machine_name):
        with connect(self.server.db_path) as conn:
            row = self.load_card(conn, card_key)
            if row["machine_id"] and row["machine_id"] != machine_id:
                self.fail(403, "卡密已绑定其他电脑，请先在原电脑解绑")
                return
            token = row["token"] or secrets.token_urlsafe(32)
            if not row["machine_id"]:
                conn.execute(
                    "UPDATE license_cards SET machine_id=?, machine_name=?, bind_at=?, token=? WHERE card_key=?",
                    (machine_id, machine_name, now_iso(), token, card_key),
                )
            else:
                conn.execute(
                    "UPDATE license_cards SET machine_name=?, token=? WHERE card_key=?",
                    (machine_name, token, card_key),
                )
            row = conn.execute("SELECT * FROM license_cards WHERE card_key=?", (card_key,)).fetchone()
            data = row_to_public(row, "验证成功")
            data["token"] = token
            self.write_json(200, data)

    def handle_query(self, card_key, machine_id):
        with connect(self.server.db_path) as conn:
            row = self.load_card(conn, card_key)
            data = row_to_public(row, "查询成功")
            data["bound_to_this_machine"] = row["machine_id"] == machine_id
            self.write_json(200, data)

    def handle_unbind(self, card_key, machine_id, token):
        with connect(self.server.db_path) as conn:
            row = self.load_card(conn, card_key)
            if not row["machine_id"]:
                self.fail(400, "卡密当前未绑定电脑")
                return
            if row["machine_id"] != machine_id:
                self.fail(403, "只能在当前绑定电脑上解绑")
                return
            if row["token"] and token != row["token"]:
                self.fail(403, "解绑令牌无效，请先验证卡密")
                return
            if int(row["unbind_count"]) >= int(row["max_unbinds"]):
                self.fail(403, "解绑次数已用完")
                return
            conn.execute(
                """
                UPDATE license_cards
                SET machine_id='', machine_name='', bind_at='', token='', unbind_count=unbind_count+1
                WHERE card_key=?
                """,
                (card_key,),
            )
            row = conn.execute("SELECT * FROM license_cards WHERE card_key=?", (card_key,)).fetchone()
            self.write_json(200, row_to_public(row, "解绑成功"))

    def log_message(self, fmt, *args):
        print(f"[{now_iso()}] {self.address_string()} {fmt % args}")


def serve(db_path, host, port):
    init_db(db_path)
    server = ThreadingHTTPServer((host, port), LicenseHandler)
    server.db_path = db_path
    print(f"License server listening on http://{host}:{port}")
    print(f"Database: {db_path}")
    server.serve_forever()


def main():
    parser = argparse.ArgumentParser(description="Grok Video Studio license server")
    parser.add_argument("--db", default=str(DEFAULT_DB))
    sub = parser.add_subparsers(dest="cmd", required=True)

    serve_cmd = sub.add_parser("serve", help="start HTTP license server")
    serve_cmd.add_argument("--host", default="0.0.0.0")
    serve_cmd.add_argument("--port", type=int, default=8765)

    create_cmd = sub.add_parser("create-card", help="create or update a license card")
    create_cmd.add_argument("card_key")
    create_cmd.add_argument("expires_at", help="YYYY-MM-DD or ISO datetime")
    create_cmd.add_argument("--max-unbinds", type=int, default=3)

    args = parser.parse_args()
    db_path = Path(args.db)
    if args.cmd == "serve":
        serve(db_path, args.host, args.port)
    elif args.cmd == "create-card":
        create_card(db_path, args.card_key, args.expires_at, args.max_unbinds)
        print(f"created card {args.card_key}, expires_at={args.expires_at}, max_unbinds={args.max_unbinds}")


if __name__ == "__main__":
    main()
