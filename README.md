<p align="center">
  <img src="https://img.shields.io/badge/OCPP-1.6J-blue?style=for-the-badge" alt="OCPP 1.6J">
  <img src="https://img.shields.io/badge/Python-3.9+-green?style=for-the-badge&logo=python&logoColor=white" alt="Python 3.9+">
  <img src="https://img.shields.io/badge/WebSocket-RFC%206455-orange?style=for-the-badge" alt="WebSocket">
  <img src="https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge" alt="MIT License">
  <img src="https://img.shields.io/badge/Raspberry%20Pi-Compatible-c51a4a?style=for-the-badge&logo=raspberrypi&logoColor=white" alt="Raspberry Pi">
</p>

# ⚡ ocpp-charge-point-simulator

> Minimal **OCPP 1.6J charge point simulator** written in Python.  
> Simulate an EV charger to test any CSMS backend — no hardware required.

---

## 🎯 Overview

This project provides a lightweight, interactive charge point simulator that communicates over **WebSocket** using the **OCPP 1.6 JSON** protocol. It is designed to validate and test **Central System Management System (CSMS)** backends such as:

- [SteVe](https://github.com/steve-community/steve) — Open-source OCPP server
- Custom OCPP backends
- Charging network platforms

Whether you're building a CSMS from scratch or integrating with an existing platform, this simulator lets you trigger every standard OCPP message from your terminal.

### 🍓 Raspberry Pi Ready

This simulator is fully compatible with **Raspberry Pi** boards. It was originally developed and tested on a **Raspberry Pi 3 B+** (512 MB RAM). Thanks to its minimal footprint and zero heavy dependencies, it runs smoothly on resource-constrained embedded environments — making it ideal for field testing, demo setups, and IoT charging prototypes.

---

## ✨ Features

| Feature               | Description                                              |
|-----------------------|----------------------------------------------------------|
| `BootNotification`    | Register the charge point with the CSMS                  |
| `Heartbeat`           | Periodic keep-alive with configurable interval           |
| `StatusNotification`  | Report connector status (Available, Charging, etc.)      |
| `Authorize`           | Validate an RFID tag / token                             |
| `StartTransaction`    | Begin a charging session                                 |
| `MeterValues`         | Send simulated energy readings (Wh, V, A)                |
| `StopTransaction`     | End the active charging session                          |
| Interactive Console   | Menu-driven CLI to trigger any message on demand         |
| Remote Commands       | Auto-responds to CSMS-initiated requests                 |

---

## 📦 Project Structure

```
ocpp-charge-point-simulator/
│
├── simulator/
│   └── ocpp-charge-point-simulator.py   # Main simulator entry point
│
├── config/
│   └── config.py                 # All tuneable parameters
│
├── docs/
│   └── ocpp-flow.md              # OCPP message flow reference
│
├── requirements.txt
├── README.md
├── .gitignore
└── LICENSE
```

---

## 🚀 Quick Start

### Prerequisites

- **Python 3.9+**
- A running CSMS backend (e.g., [SteVe](https://github.com/steve-community/steve))

### Installation

```bash
# Clone the repository
git clone https://github.com/hasanyildiz12/ocpp-charge-point-simulator.git
cd ocpp-charge-point-simulator

# Create a virtual environment (recommended)
python -m venv venv
source venv/bin/activate        # Linux / macOS
venv\Scripts\activate           # Windows

# Install dependencies
pip install -r requirements.txt
```

### Configuration

Before running, edit `config/config.py` with your own values:

```python
CSMS_URL       = "ws://<YOUR_CSMS_HOST>:<PORT>/steve/websocket/CentralSystemService/<CHARGE_BOX_ID>"
CHARGE_BOX_ID  = "YOUR_CHARGE_BOX_ID"
DEFAULT_ID_TAG = "YOUR_ID_TAG"
```

### Run

```bash
python simulator/ocpp-charge-point-simulator
```

---

## 🔌 Specify a CSMS URL

You can also override the CSMS URL directly from the command line without editing the config file:

```bash
# Custom CSMS endpoint
python simulator/ocpp-charge-point-simulator.py ws://10.0.0.5:8180/steve/websocket/CentralSystemService/CP2

# Custom endpoint + charge-box ID
python simulator/ocpp-charge-point-simulator.py ws://10.0.0.5:8180/steve/websocket/CentralSystemService/MyCharger MyCharger
```

---

## 🖥️ Interactive Console

Once connected, an interactive menu appears:

```
┌─────────────────────────────────────────┐
│  ocpp-charge-point-simulator  ·  OCPP 1.6J     │
└─────────────────────────────────────────┘
  1  BootNotification
  2  Heartbeat (manual)
  3  StatusNotification → Available
  4  StatusNotification → Charging
  5  Authorize
  6  StartTransaction
  7  MeterValues
  8  StopTransaction
  q  Quit
```

Type a number and press **Enter** to send the corresponding OCPP message.

---

## 🧪 Example CSMS

This simulator is tested and compatible with:

| CSMS                                                              | Protocol  | Status |
|-------------------------------------------------------------------|-----------|--------|
| [SteVe](https://github.com/steve-community/steve)                | OCPP 1.6J | ✅ Verified |
| Any standards-compliant OCPP 1.6 JSON backend                    | OCPP 1.6J | ✅ Compatible |

---

## 🏗️ Architecture

```
┌────────────────────────────────────────────┐
│   ocpp-charge-point-simulator           │
│   (Charge Point Simulator)                  │
│                                             │
│   simulator/                                │
│     ocpp-charge-point-simulator.py                  │
│   config/                                   │
│     config.py                               │
└─────────────────────┬──────────────────────┘
                │
                │  OCPP 1.6 JSON
                │  (WebSocket)
                │
                ▼
┌──────────────────────────────────┐
│   CSMS Backend                    │
│   (SteVe / custom backend)       │
└──────────────────────────────────┘
```

The simulator opens a persistent **WebSocket** connection to the CSMS and exchanges JSON frames using the OCPP 1.6 wire format:

```
CALL        →  [2, "<messageId>", "<action>", {payload}]
CALLRESULT  →  [3, "<messageId>", {payload}]
CALLERROR   →  [4, "<messageId>", "<errorCode>", "<errorDescription>", {details}]
```

---

## ⚙️ Configuration

All tuneable parameters live in [`config/config.py`](config/config.py):

| Parameter            | Default                         | Description                                 |
|----------------------|---------------------------------|---------------------------------------------|
| `CSMS_URL`           | `ws://<YOUR_CSMS_HOST>:…`      | WebSocket URL of the CSMS                   |
| `CHARGE_BOX_ID`      | `YOUR_CHARGE_BOX_ID`            | Unique identity of the simulated charger    |
| `DEFAULT_ID_TAG`     | `YOUR_ID_TAG`                    | RFID tag used for authorization             |
| `VENDOR`             | `TestVendor`                    | Charge point vendor string                  |
| `MODEL`              | `TestModel`                     | Charge point model string                   |
| `SERIAL`             | `SN-001`                        | Serial number                               |
| `FIRMWARE`           | `1.0.0`                         | Firmware version                            |
| `HEARTBEAT_INTERVAL` | `30`                            | Seconds between heartbeats                  |
| `METER_INCREMENT_WH` | `500`                           | Wh added per MeterValues call               |

---

## 📄 License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

---

## 🤝 Contributing

Contributions, issues, and feature requests are welcome!  
Feel free to open an issue or submit a pull request.

---

<p align="center">
  <sub>Built for EV charging · OCPP protocol · WebSocket · Embedded simulation</sub>
</p>
