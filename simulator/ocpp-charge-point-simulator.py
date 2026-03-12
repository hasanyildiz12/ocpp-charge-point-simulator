#!/usr/bin/env python3
"""
ocpp-charge-point-simulator — OCPP 1.6J Charge Point Simulator
========================================================
Lightweight, interactive OCPP 1.6 JSON charge-point simulator.
Optimised for low-resource environments (tested on Raspberry Pi Zero 2 W
with 512 MB RAM) but runs on any Python 3.9+ system.

Dependency : pip install websockets
Usage      : python simulator/OCPP-Simulator-yldz.py [CSMS_URL] [CHARGE_BOX_ID]
"""

import asyncio
import json
import signal
import sys
import time
from datetime import datetime, timezone

try:
    import websockets
except ImportError:
    print("[ERROR] 'websockets' package is missing. Install it with:  pip install websockets")
    sys.exit(1)

# ─── Import configuration ────────────────────────────────────────────────────

sys.path.insert(0, ".")
from config.config import (
    CSMS_URL       as _CFG_CSMS_URL,
    CHARGE_BOX_ID  as _CFG_CHARGE_BOX_ID,
    DEFAULT_ID_TAG,
    VENDOR,
    MODEL,
    SERIAL,
    FIRMWARE,
    HEARTBEAT_INTERVAL,
    METER_INCREMENT_WH,
    DEFAULT_VOLTAGE,
    DEFAULT_CURRENT,
    SUBPROTOCOL,
    PING_INTERVAL,
)

# ─── Runtime State ────────────────────────────────────────────────────────────

CSMS_URL       = _CFG_CSMS_URL,
CHARGE_BOX_ID  = _CFG_CHARGE_BOX_ID,

msg_id         = 1
transaction_id = None
meter_wh       = 0
hb_interval    = HEARTBEAT_INTERVAL
hb_task        = None

# ─── Colour Helpers (ANSI) ────────────────────────────────────────────────────

RESET  = "\033[0m"
BOLD   = "\033[1m"
CYAN   = "\033[36m"
GREEN  = "\033[32m"
YELLOW = "\033[33m"
RED    = "\033[31m"
DIM    = "\033[2m"


def _ts() -> str:
    """Short timestamp for log lines."""
    return datetime.now().strftime("%H:%M:%S.%f")[:-3]


def log(direction: str, msg: str):
    colors = {"SEND": CYAN, "RECV": GREEN, "INFO": DIM, "WARN": YELLOW, "ERR": RED}
    c = colors.get(direction, RESET)
    print(f"{DIM}{_ts()}{RESET}  {c}{BOLD}{direction:<4}{RESET}  {msg}")


# ─── Helpers ──────────────────────────────────────────────────────────────────

def next_id() -> str:
    global msg_id
    i = msg_id
    msg_id += 1
    return str(i)


def iso_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


# ─── Low-level Send ──────────────────────────────────────────────────────────

async def send(ws, action: str, payload: dict) -> str:
    mid = next_id()
    msg = json.dumps([2, mid, action, payload])
    await ws.send(msg)
    log("SEND", f"[{action}] {payload}")
    return mid


async def send_result(ws, mid: str, payload: dict):
    msg = json.dumps([3, mid, payload])
    await ws.send(msg)
    log("SEND", f"[Response/{mid}] {payload}")


# ─── OCPP 1.6 Messages (Charge Point → CSMS) ────────────────────────────────

async def boot_notification(ws):
    await send(ws, "BootNotification", {
        "chargePointVendor":       VENDOR,
        "chargePointModel":        MODEL,
        "chargePointSerialNumber": SERIAL,
        "firmwareVersion":         FIRMWARE,
    })


async def heartbeat(ws):
    await send(ws, "Heartbeat", {})


async def status_notification(ws, connector_id: int, status: str, error_code: str = "NoError"):
    await send(ws, "StatusNotification", {
        "connectorId": connector_id,
        "status":      status,
        "errorCode":   error_code,
        "timestamp":   iso_now(),
    })


async def authorize(ws, id_tag: str = DEFAULT_ID_TAG):
    await send(ws, "Authorize", {"idTag": id_tag})


async def start_transaction(ws, id_tag: str = DEFAULT_ID_TAG):
    global meter_wh
    await send(ws, "StartTransaction", {
        "connectorId": 1,
        "idTag":       id_tag,
        "meterStart":  meter_wh,
        "timestamp":   iso_now(),
    })


async def stop_transaction(ws):
    global transaction_id, meter_wh
    if transaction_id is None:
        log("WARN", "No active transaction!")
        return
    await send(ws, "StopTransaction", {
        "transactionId": transaction_id,
        "idTag":         DEFAULT_ID_TAG,
        "meterStop":     meter_wh,
        "timestamp":     iso_now(),
        "reason":        "Local",
    })


async def meter_values(ws):
    global meter_wh, transaction_id
    meter_wh += METER_INCREMENT_WH
    payload = {
        "connectorId": 1,
        "meterValue": [{
            "timestamp": iso_now(),
            "sampledValue": [
                {"value": str(meter_wh), "measurand": "Energy.Active.Import.Register", "unit": "Wh"},
                {"value": str(DEFAULT_VOLTAGE), "measurand": "Voltage", "unit": "V"},
                {"value": str(DEFAULT_CURRENT), "measurand": "Current.Import", "unit": "A"},
            ]
        }]
    }
    if transaction_id:
        payload["transactionId"] = transaction_id
    await send(ws, "MeterValues", payload)


# ─── Heartbeat Scheduler ─────────────────────────────────────────────────────

async def heartbeat_loop(ws, interval: int):
    log("INFO", f"Heartbeat started — every {interval}s")
    while True:
        await asyncio.sleep(interval)
        try:
            await heartbeat(ws)
        except Exception:
            break


# ─── Incoming Message Handler ─────────────────────────────────────────────────

async def handle_message(ws, raw: str):
    global transaction_id, hb_interval, hb_task

    try:
        msg = json.loads(raw)
    except json.JSONDecodeError:
        log("ERR", f"JSON parse error: {raw}")
        return

    msg_type = msg[0]
    mid      = msg[1]

    # ── CALLRESULT (3) — response to our request ─────────────────────────────
    if msg_type == 3:
        payload = msg[2]
        log("RECV", f"[Response/{mid}] {payload}")

        # BootNotification response → update heartbeat interval
        if "interval" in payload and "status" in payload:
            status   = payload["status"]
            interval = payload.get("interval", hb_interval)
            log("INFO", f"BootNotification: status={status}, interval={interval}s")
            if status == "Accepted":
                hb_interval = interval
                if hb_task:
                    hb_task.cancel()
                hb_task = asyncio.create_task(heartbeat_loop(ws, hb_interval))

        # StartTransaction response → store transactionId
        if "transactionId" in payload:
            transaction_id = payload["transactionId"]
            log("INFO", f"Transaction started: ID={transaction_id}")

    # ── CALL (2) — request from CSMS ─────────────────────────────────────────
    elif msg_type == 2:
        action  = msg[2]
        payload = msg[3] if len(msg) > 3 else {}
        log("RECV", f"[{action}] ← Server: {payload}")

        responses = {
            "GetConfiguration":       {"configurationKey": [], "unknownKey": []},
            "ChangeConfiguration":    {"status": "Accepted"},
            "Reset":                  {"status": "Accepted"},
            "RemoteStartTransaction": {"status": "Accepted"},
            "RemoteStopTransaction":  {"status": "Accepted"},
            "TriggerMessage":         {"status": "Accepted"},
            "UnlockConnector":        {"status": "Unlocked"},
            "ClearCache":             {"status": "Accepted"},
        }
        response = responses.get(action, {})
        await send_result(ws, mid, response)

    # ── CALLERROR (4) ─────────────────────────────────────────────────────────
    elif msg_type == 4:
        log("ERR", f"CALLERROR [{mid}]: {msg[2]} — {msg[3]}")


# ─── Interactive Console ──────────────────────────────────────────────────────

def print_menu():
    print(f"""
{BOLD}{CYAN}┌─────────────────────────────────────────┐{RESET}
{BOLD}{CYAN}│ ocpp-charge-point-simulator · OCPP 1.6J  │{RESET}
{BOLD}{CYAN}└─────────────────────────────────────────┘{RESET}
  {BOLD}1{RESET}  BootNotification
  {BOLD}2{RESET}  Heartbeat (manual)
  {BOLD}3{RESET}  StatusNotification → Available
  {BOLD}4{RESET}  StatusNotification → Charging
  {BOLD}5{RESET}  Authorize ({DEFAULT_ID_TAG})
  {BOLD}6{RESET}  StartTransaction
  {BOLD}7{RESET}  MeterValues
  {BOLD}8{RESET}  StopTransaction
  {BOLD}q{RESET}  Quit
""")


async def console_input(ws):
    """Async console input — runs as a separate task."""
    loop = asyncio.get_event_loop()
    print_menu()
    while True:
        try:
            choice = await loop.run_in_executor(None, input, f"\n{BOLD}>{RESET} ")
            choice = choice.strip().lower()

            actions = {
                "1": lambda: boot_notification(ws),
                "2": lambda: heartbeat(ws),
                "3": lambda: status_notification(ws, 1, "Available"),
                "4": lambda: status_notification(ws, 1, "Charging"),
                "5": lambda: authorize(ws),
                "6": lambda: start_transaction(ws),
                "7": lambda: meter_values(ws),
                "8": lambda: stop_transaction(ws),
            }

            if choice in actions:
                await actions[choice]()
            elif choice in ("q", "quit", "exit"):
                log("INFO", "Shutting down...")
                sys.exit(0)
            elif choice == "m":
                print_menu()
            else:
                log("WARN", f"Unknown command: '{choice}' — press 'm' for menu")

        except (EOFError, KeyboardInterrupt):
            break


# ─── Receive Loop ─────────────────────────────────────────────────────────────

async def recv_loop(ws):
    """Continuously listen for incoming WebSocket messages."""
    try:
        async for message in ws:
            await handle_message(ws, message)
    except websockets.exceptions.ConnectionClosed as e:
        log("WARN", f"Connection closed: code={e.code}")


# ─── Main ─────────────────────────────────────────────────────────────────────

async def main():
    global hb_task

    print(f"\n{BOLD}ocpp-charge-point-simulator · OCPP 1.6J Charge Point Simulator{RESET}")
    print(f"{DIM}Connecting to: {CSMS_URL}{RESET}\n")

    # Graceful shutdown
    def handle_sigint(*_):
        log("INFO", "Ctrl+C — disconnecting...")
        sys.exit(0)
    signal.signal(signal.SIGINT, handle_sigint)

    try:
        async with websockets.connect(
            CSMS_URL,
            subprotocols=[SUBPROTOCOL],
            ping_interval=PING_INTERVAL,
        ) as ws:
            log("INFO", f"Connected ✓  ({CSMS_URL})")

            # Auto-send BootNotification on connect
            await boot_notification(ws)

            # Run receiver + interactive console in parallel
            recv_task  = asyncio.create_task(recv_loop(ws))
            input_task = asyncio.create_task(console_input(ws))

            await asyncio.gather(recv_task, input_task)

    except OSError as e:
        log("ERR", f"Connection failed: {e}")
        log("INFO", "Is your CSMS running? Is the URL correct?")
    except Exception as e:
        log("ERR", f"Unexpected error: {e}")


# ─── Entry Point ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    if len(sys.argv) >= 2:
        CSMS_URL = sys.argv[1]
    if len(sys.argv) >= 3:
        CHARGE_BOX_ID = sys.argv[2]
        parts = CSMS_URL.rsplit("/", 1)
        CSMS_URL = parts[0] + "/" + CHARGE_BOX_ID

    asyncio.run(main())
