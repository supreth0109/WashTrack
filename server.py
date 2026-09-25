#!/usr/bin/env python3
"""WashTrack prototype API — stdlib only. Serves the frontend and JSON REST API."""

from __future__ import annotations

import json
import random
import threading
from datetime import datetime
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import os

ROOT = Path(__file__).resolve().parent
DATA_FILE = ROOT / "data.json"
HOST = "0.0.0.0"
PORT = int(os.environ.get("PORT", 5000))
STATUS_STEPS = ["Submitted", "In Wash", "Ready for Pickup", "Delivered"]
LOCK = threading.Lock()

SEED_STAFF = [
    {"email": "staff01@laundry.edu", "password": "password123", "uid": "STAFF01", "name": "Counter Staff 01"},
    {"email": "staff02@laundry.edu", "password": "password123", "uid": "STAFF02", "name": "Counter Staff 02"},
]

SEED_STUDENTS = [
    {
        "regNo": "21BCE0001",
        "name": "Alex Smith",
        "hostel": "Block A (Men's)",
        "room": "302",
        "phone": "+91 9876543210",
    },
    {
        "regNo": "21BCE0002",
        "name": "Rachel Green",
        "hostel": "Block C (Ladies')",
        "room": "108",
        "phone": "+91 9123456789",
    },
]

SEED_ORDERS = [
    {
        "orderId": "1",
        "studentRegNo": "21BCE0001",
        "studentName": "Alex Smith",
        "hostelBlock": "Block A (Men's)",
        "roomNo": "302",
        "studentPhone": "+91 9876543210",
        "staffUid": "STAFF01",
        "clothesDetails": "Shirt: 2, Pant: 1, Shorts: 1",
        "totalQuantity": 4,
        "submissionDateTime": "17-09-2026 10:30",
        "status": "Ready for Pickup",
        "token": "TK-21BCE0001-101",
        "handoverOtp": "482910",
        "ironingRequested": True,
    },
    {
        "orderId": "2",
        "studentRegNo": "21BCE0001",
        "studentName": "Alex Smith",
        "hostelBlock": "Block A (Men's)",
        "roomNo": "302",
        "studentPhone": "+91 9876543210",
        "staffUid": "STAFF01",
        "clothesDetails": "T-Shirt: 2, Shorts: 1",
        "totalQuantity": 3,
        "submissionDateTime": "16-09-2026 18:10",
        "status": "Delivered",
        "token": "TK-21BCE0001-100",
        "handoverOtp": "918234",
        "ironingRequested": False,
    },
    {
        "orderId": "3",
        "studentRegNo": "21BCE0002",
        "studentName": "Rachel Green",
        "hostelBlock": "Block C (Ladies')",
        "roomNo": "108",
        "studentPhone": "+91 9123456789",
        "staffUid": "STAFF02",
        "clothesDetails": "Jeans: 1, Jacket: 1",
        "totalQuantity": 2,
        "submissionDateTime": "17-09-2026 14:15",
        "status": "In Wash",
        "token": "TK-21BCE0002-102",
        "handoverOtp": "635142",
        "ironingRequested": True,
    },
]

SEED_COMPLAINTS = [
    {
        "complaintId": "C-101",
        "studentRegNo": "21BCE0001",
        "token": "TK-21BCE0001-101",
        "staffUid": "STAFF01",
        "category": "Missing Clothing Item",
        "description": "One formal shirt is missing from my intake bag TK-21BCE0001-101.",
        "timestamp": "17-09-2026 11:15",
        "photoUrl": None,
        "status": "Pending",
    }
]


def now_stamp() -> str:
    return datetime.now().strftime("%d-%m-%Y %H:%M")


def generate_otp() -> str:
    return f"{random.randint(100000, 999999)}"


def seed_db() -> dict:
    return {
        "tokenCounter": 103,
        "staff": SEED_STAFF,
        "students": SEED_STUDENTS,
        "orders": SEED_ORDERS,
        "complaints": SEED_COMPLAINTS,
    }


def load_db() -> dict:
    if not DATA_FILE.exists():
        data = seed_db()
        save_db(data)
        return data
    with DATA_FILE.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_db(data: dict) -> None:
    DATA_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def public_order(order: dict, include_otp: bool) -> dict:
    item = dict(order)
    if not include_otp:
        item.pop("handoverOtp", None)
    return item


def find_order(db: dict, token: str) -> dict | None:
    token = (token or "").strip()
    for order in db["orders"]:
        if order["token"] == token:
            return order
    return None


def find_student(db: dict, reg_no: str) -> dict | None:
    key = (reg_no or "").strip().upper()
    for student in db["students"]:
        if student["regNo"].upper() == key:
            return student
    return None


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PATCH, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(204)
        self.end_headers()

    def log_message(self, format, *args):
        print("[%s] %s" % (self.log_date_time_string(), format % args))

    def send_json(self, payload, status=200):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def read_json(self):
        length = int(self.headers.get("Content-Length") or 0)
        if length <= 0:
            return {}
        raw = self.rfile.read(length)
        if not raw:
            return {}
        return json.loads(raw.decode("utf-8"))

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        query = parse_qs(parsed.query)

        if path == "/api/health":
            return self.send_json({"ok": True, "service": "washtrack"})

        if path == "/api/state":
            role = (query.get("role") or ["staff"])[0]
            reg_no = (query.get("regNo") or [""])[0].strip().upper()
            include_otp = role == "student"
            with LOCK:
                db = load_db()
                orders = db["orders"]
                if role == "student" and reg_no:
                    orders = [o for o in orders if o["studentRegNo"].upper() == reg_no]
                return self.send_json({
                    "orders": [public_order(o, include_otp) for o in orders],
                    "complaints": db["complaints"] if role == "staff" else [
                        c for c in db["complaints"] if not reg_no or c["studentRegNo"].upper() == reg_no
                    ],
                    "tokenCounter": db["tokenCounter"],
                })

        if path == "/api/meta/next-token":
            reg_no = (query.get("regNo") or ["21BCE0001"])[0].strip().upper() or "21BCE0001"
            with LOCK:
                db = load_db()
                return self.send_json({
                    "token": f"TK-{reg_no}-{db['tokenCounter']}",
                    "tokenCounter": db["tokenCounter"],
                })

        return super().do_GET()

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")
        try:
            body = self.read_json()
        except json.JSONDecodeError:
            return self.send_json({"error": "Invalid JSON body"}, 400)

        if path == "/api/auth/student":
            return self._auth_student(body)
        if path == "/api/auth/staff":
            return self._auth_staff(body)
        if path == "/api/orders":
            return self._create_order(body)
        if path == "/api/complaints":
            return self._create_complaint(body)

        parts = path.split("/")
        # /api/orders/{token}/check-otp | deliver | rewash | status
        if len(parts) >= 5 and parts[1] == "api" and parts[2] == "orders":
            token = parts[3]
            action = parts[4]
            if action == "check-otp":
                return self._check_otp(token, body)
            if action == "deliver":
                return self._deliver(token, body)
            if action == "rewash":
                return self._rewash(token)
            if action == "status":
                return self._advance_status(token, body)

        if len(parts) >= 5 and parts[1] == "api" and parts[2] == "complaints" and parts[4] == "resolve":
            return self._resolve_complaint(parts[3])

        return self.send_json({"error": "Not found"}, 404)

    def do_PATCH(self):
        self.do_POST()

    def _auth_student(self, body: dict):
        reg_no = (body.get("regNo") or "").strip().upper()
        if not reg_no:
            return self.send_json({"error": "Registration number is required"}, 400)
        student = {
            "regNo": reg_no,
            "name": (body.get("name") or "Student").strip() or "Student",
            "hostel": body.get("hostel") or "Block A (Men's)",
            "room": (body.get("room") or "302").strip() or "302",
            "phone": (body.get("phone") or "+91 9876543210").strip() or "+91 9876543210",
        }
        with LOCK:
            db = load_db()
            existing = find_student(db, reg_no)
            if existing:
                existing.update(student)
            else:
                db["students"].append(student)
            save_db(db)
        return self.send_json({"student": student})

    def _auth_staff(self, body: dict):
        email = (body.get("email") or "").strip().lower()
        password = (body.get("password") or "").strip()
        if not email or not password:
            return self.send_json({"error": "Email and password are required"}, 400)
        with LOCK:
            db = load_db()
            for staff in db["staff"]:
                if staff["email"].lower() == email and staff["password"] == password:
                    return self.send_json({
                        "staff": {
                            "email": staff["email"],
                            "uid": staff["uid"],
                            "name": staff.get("name") or staff["uid"],
                        }
                    })
        return self.send_json({"error": "Invalid staff credentials"}, 401)

    def _create_order(self, body: dict):
        reg = (body.get("studentRegNo") or "").strip().upper()
        clothes = (body.get("clothesDetails") or "").strip()
        qty = int(body.get("totalQuantity") or 0)
        if not reg:
            return self.send_json({"error": "Student registration number is required"}, 400)
        if qty <= 0 or not clothes:
            return self.send_json({"error": "Select at least one clothing item"}, 400)

        with LOCK:
            db = load_db()
            student = find_student(db, reg)
            token = f"TK-{reg}-{db['tokenCounter']}"
            order = {
                "orderId": str(len(db["orders"]) + 1),
                "studentRegNo": reg,
                "studentName": body.get("studentName") or (student["name"] if student else "Student"),
                "hostelBlock": body.get("hostelBlock") or (student["hostel"] if student else "Block A (Men's)"),
                "roomNo": body.get("roomNo") or (student["room"] if student else "302"),
                "studentPhone": body.get("studentPhone") or (student["phone"] if student else "+91 9876543210"),
                "staffUid": body.get("staffUid") or "STAFF01",
                "clothesDetails": clothes,
                "totalQuantity": qty,
                "submissionDateTime": now_stamp(),
                "status": "Submitted",
                "token": token,
                "handoverOtp": generate_otp(),
                "ironingRequested": bool(body.get("ironingRequested")),
            }
            db["orders"].insert(0, order)
            db["tokenCounter"] += 1
            save_db(db)
        return self.send_json({"order": public_order(order, include_otp=False), "tokenCounter": db["tokenCounter"]})

    def _advance_status(self, token: str, body: dict):
        target = body.get("status")
        if target not in STATUS_STEPS or target == "Delivered":
            return self.send_json({"error": "Use OTP handover to mark Delivered"}, 400)
        with LOCK:
            db = load_db()
            order = find_order(db, token)
            if not order:
                return self.send_json({"error": "Order not found"}, 404)
            current = "Delivered" if order["status"] == "Completed" else order["status"]
            try:
                cur_i = STATUS_STEPS.index(current)
                tgt_i = STATUS_STEPS.index(target)
            except ValueError:
                return self.send_json({"error": "Unknown status"}, 400)
            if tgt_i != cur_i + 1:
                return self.send_json({"error": f"Cannot move from {current} to {target}"}, 400)
            order["status"] = target
            if target == "Ready for Pickup" and not order.get("handoverOtp"):
                order["handoverOtp"] = generate_otp()
            save_db(db)
            return self.send_json({"order": public_order(order, include_otp=False)})

    def _check_otp(self, token: str, body: dict):
        otp = str(body.get("otp") or "").strip()
        with LOCK:
            db = load_db()
            order = find_order(db, token)
            if not order:
                return self.send_json({"error": "Order not found"}, 404)
            return self.send_json({"match": otp == str(order.get("handoverOtp") or "") and len(otp) == 6})

    def _deliver(self, token: str, body: dict):
        otp = str(body.get("otp") or "").strip()
        with LOCK:
            db = load_db()
            order = find_order(db, token)
            if not order:
                return self.send_json({"error": "Order not found"}, 404)
            status = "Delivered" if order["status"] == "Completed" else order["status"]
            if status != "Ready for Pickup":
                return self.send_json({"error": "Order is not ready for pickup"}, 400)
            if otp != str(order.get("handoverOtp") or ""):
                return self.send_json({"error": "Invalid OTP code"}, 401)
            order["status"] = "Delivered"
            save_db(db)
            return self.send_json({"order": public_order(order, include_otp=False)})

    def _create_complaint(self, body: dict):
        token = (body.get("token") or "").strip()
        desc = (body.get("description") or "").strip()
        if not token or not desc:
            return self.send_json({"error": "Token and description are required"}, 400)
        with LOCK:
            db = load_db()
            order = find_order(db, token)
            complaint = {
                "complaintId": f"C-{int(datetime.now().timestamp() * 1000)}",
                "studentRegNo": body.get("studentRegNo") or (order["studentRegNo"] if order else "UNKNOWN"),
                "token": token,
                "staffUid": body.get("staffUid") or (order.get("staffUid") if order else "STAFF01"),
                "category": body.get("category") or "Other",
                "description": desc,
                "timestamp": now_stamp(),
                "photoUrl": body.get("photoUrl"),
                "status": "Pending",
            }
            db["complaints"].insert(0, complaint)
            save_db(db)
        return self.send_json({"complaint": complaint})

    def _resolve_complaint(self, complaint_id: str):
        with LOCK:
            db = load_db()
            for complaint in db["complaints"]:
                if complaint["complaintId"] == complaint_id:
                    complaint["status"] = "Resolved"
                    save_db(db)
                    return self.send_json({"complaint": complaint})
        return self.send_json({"error": "Complaint not found"}, 404)

    def _rewash(self, token: str):
        with LOCK:
            db = load_db()
            order = find_order(db, token)
            if not order:
                return self.send_json({"error": "Order not found"}, 404)
            complaint = {
                "complaintId": f"C-{int(datetime.now().timestamp() * 1000)}",
                "studentRegNo": order["studentRegNo"],
                "token": token,
                "staffUid": order.get("staffUid") or "STAFF01",
                "category": "Re-Wash Request",
                "description": f"Student requested a re-wash for delivered order token {token}",
                "timestamp": now_stamp(),
                "photoUrl": None,
                "status": "Pending",
            }
            db["complaints"].insert(0, complaint)
            save_db(db)
        return self.send_json({"complaint": complaint})


def main():
    with LOCK:
        load_db()
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"WashTrack backend running at http://{HOST}:{PORT}")
    print("Open the portal at that URL. Staff demo: staff01@laundry.edu / password123")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping server")
        server.server_close()


if __name__ == "__main__":
    main()
