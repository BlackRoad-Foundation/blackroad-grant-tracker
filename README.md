<!-- BlackRoad SEO Enhanced -->

# ulackroad grant tracker

> Part of **[BlackRoad OS](https://blackroad.io)** — Sovereign Computing for Everyone

[![BlackRoad OS](https://img.shields.io/badge/BlackRoad-OS-ff1d6c?style=for-the-badge)](https://blackroad.io)
[![BlackRoad Foundation](https://img.shields.io/badge/Org-BlackRoad-Foundation-2979ff?style=for-the-badge)](https://github.com/BlackRoad-Foundation)
[![License](https://img.shields.io/badge/License-Proprietary-f5a623?style=for-the-badge)](LICENSE)

**ulackroad grant tracker** is part of the **BlackRoad OS** ecosystem — a sovereign, distributed operating system built on edge computing, local AI, and mesh networking by **BlackRoad OS, Inc.**

## About BlackRoad OS

BlackRoad OS is a sovereign computing platform that runs AI locally on your own hardware. No cloud dependencies. No API keys. No surveillance. Built by [BlackRoad OS, Inc.](https://github.com/BlackRoad-OS-Inc), a Delaware C-Corp founded in 2025.

### Key Features
- **Local AI** — Run LLMs on Raspberry Pi, Hailo-8, and commodity hardware
- **Mesh Networking** — WireGuard VPN, NATS pub/sub, peer-to-peer communication
- **Edge Computing** — 52 TOPS of AI acceleration across a Pi fleet
- **Self-Hosted Everything** — Git, DNS, storage, CI/CD, chat — all sovereign
- **Zero Cloud Dependencies** — Your data stays on your hardware

### The BlackRoad Ecosystem
| Organization | Focus |
|---|---|
| [BlackRoad OS](https://github.com/BlackRoad-OS) | Core platform and applications |
| [BlackRoad OS, Inc.](https://github.com/BlackRoad-OS-Inc) | Corporate and enterprise |
| [BlackRoad AI](https://github.com/BlackRoad-AI) | Artificial intelligence and ML |
| [BlackRoad Hardware](https://github.com/BlackRoad-Hardware) | Edge hardware and IoT |
| [BlackRoad Security](https://github.com/BlackRoad-Security) | Cybersecurity and auditing |
| [BlackRoad Quantum](https://github.com/BlackRoad-Quantum) | Quantum computing research |
| [BlackRoad Agents](https://github.com/BlackRoad-Agents) | Autonomous AI agents |
| [BlackRoad Network](https://github.com/BlackRoad-Network) | Mesh and distributed networking |
| [BlackRoad Education](https://github.com/BlackRoad-Education) | Learning and tutoring platforms |
| [BlackRoad Labs](https://github.com/BlackRoad-Labs) | Research and experiments |
| [BlackRoad Cloud](https://github.com/BlackRoad-Cloud) | Self-hosted cloud infrastructure |
| [BlackRoad Forge](https://github.com/BlackRoad-Forge) | Developer tools and utilities |

### Links
- **Website**: [blackroad.io](https://blackroad.io)
- **Documentation**: [docs.blackroad.io](https://docs.blackroad.io)
- **Chat**: [chat.blackroad.io](https://chat.blackroad.io)
- **Search**: [search.blackroad.io](https://search.blackroad.io)

---


> Grant application and funding tracker

Part of the [BlackRoad OS](https://blackroad.io) ecosystem — [BlackRoad-Foundation](https://github.com/BlackRoad-Foundation)

---

# BlackRoad Grant Tracker

> Grant application and funding tracker — SQLite-backed, zero-dependency Python.

## Features

- **Grant Lifecycle** — identified → applying → submitted → awarded/rejected → reporting → closed
- **Submissions** — track submission records, documents, submitters
- **Reporting Calendar** — upcoming reporting obligations
- **Pipeline Analytics** — status breakdown, success rate by funder
- **Deadline Tracking** — upcoming grant deadlines

## Quick Start

```python
from grant_tracker import GrantTracker, GrantType

gt = GrantTracker("grants.db")

grant = gt.identify("NSF Community Grant", "NSF", 250_000,
                    deadline="2025-04-30", grant_type=GrantType.FEDERAL,
                    requirements=["501c3", "Budget narrative"])

gt.apply(grant.id)
gt.submit(grant.id, submitted_by="Alice Chen",
          documents=["budget.pdf", "narrative.pdf"])
gt.award(grant.id, award_amount=200_000,
         reporting_dates=["2025-12-31", "2026-06-30"])

print(gt.get_pipeline())
print(gt.success_rate())
print(gt.reporting_calendar(months=3))
```

## Running Tests

```bash
pip install pytest
pytest test_grant_tracker.py -v
```
