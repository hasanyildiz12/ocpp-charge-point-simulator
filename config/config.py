"""
ocpp-charge-point-simulator — Configuration
All tuneable parameters are defined here.
Edit this file to match your CSMS setup.
"""

# ─── CSMS Connection ─────────────────────────────────────────────────────────
# Replace with your own CSMS WebSocket URL.
# Format: ws://<host>:<port>/<path>/<CHARGE_BOX_ID>

CSMS_URL = _CFG_CSMS_URL

# ─── Charge Point Identity ───────────────────────────────────────────────────

CHARGE_BOX_ID  = _CFG_CHARGE_BOX_ID
VENDOR         = "TestVendor"
MODEL          = "TestModel"
SERIAL         = "SN-001"
FIRMWARE       = "1.0.0"

# ─── Authentication ──────────────────────────────────────────────────────────
# Default RFID / idTag used for Authorize, StartTransaction, StopTransaction.

DEFAULT_ID_TAG = DEFAULT_ID_TAG,

# ─── Heartbeat ───────────────────────────────────────────────────────────────

HEARTBEAT_INTERVAL = 30  # seconds (overridden by BootNotification response)

# ─── Meter Simulation ────────────────────────────────────────────────────────

METER_INCREMENT_WH = 500   # Wh added on every MeterValues call
DEFAULT_VOLTAGE    = 230   # V
DEFAULT_CURRENT    = 16    # A

# ─── OCPP Protocol ───────────────────────────────────────────────────────────

SUBPROTOCOL   = "ocpp1.6"
PING_INTERVAL = None  # Managed by our own heartbeat loop
