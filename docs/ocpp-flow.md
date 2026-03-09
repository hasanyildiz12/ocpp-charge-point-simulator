# OCPP 1.6J — Message Flow Reference

This document describes the OCPP 1.6 JSON message flow implemented by the simulator.

---

## Connection Lifecycle

```
Charge Point                         CSMS (SteVe)
     │                                    │
     │──── WebSocket CONNECT ────────────▶│
     │     subprotocol: ocpp1.6           │
     │                                    │
     │──── BootNotification ─────────────▶│
     │◀─── BootNotification.conf ─────────│
     │     (status, heartbeat interval)   │
     │                                    │
     │──── StatusNotification ───────────▶│
     │     (Available / Charging / …)     │
     │                                    │
     │──── Heartbeat ────────────────────▶│  ← repeats every N seconds
     │◀─── Heartbeat.conf ───────────────│
     │                                    │
```

## Charging Session

```
Charge Point                         CSMS (SteVe)
     │                                    │
     │──── Authorize ────────────────────▶│
     │◀─── Authorize.conf ───────────────│
     │                                    │
     │──── StartTransaction ─────────────▶│
     │◀─── StartTransaction.conf ────────│
     │     (transactionId)                │
     │                                    │
     │──── StatusNotification ───────────▶│
     │     (Charging)                     │
     │                                    │
     │──── MeterValues ──────────────────▶│  ← periodic energy readings
     │     (Wh, V, A)                     │
     │                                    │
     │──── StopTransaction ──────────────▶│
     │◀─── StopTransaction.conf ─────────│
     │                                    │
     │──── StatusNotification ───────────▶│
     │     (Available)                    │
```

## Remote Operations (CSMS → Charge Point)

The simulator automatically accepts these server-initiated requests:

| Action                  | Response          |
|-------------------------|-------------------|
| `GetConfiguration`      | Empty config list |
| `ChangeConfiguration`   | `Accepted`        |
| `Reset`                 | `Accepted`        |
| `RemoteStartTransaction`| `Accepted`        |
| `RemoteStopTransaction` | `Accepted`        |
| `TriggerMessage`        | `Accepted`        |
| `UnlockConnector`       | `Unlocked`        |
| `ClearCache`            | `Accepted`        |

## OCPP 1.6 Frame Format

```
CALL        →  [2, "<messageId>", "<action>", {payload}]
CALLRESULT  →  [3, "<messageId>", {payload}]
CALLERROR   →  [4, "<messageId>", "<errorCode>", "<errorDescription>", {details}]
```
