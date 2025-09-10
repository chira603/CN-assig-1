
# CS331 - Task-1: DNS Resolver (Client-Server)

This repository contains a reference implementation for Task-1 (80 marks): a custom DNS pipeline to parse DNS queries from a PCAP, add an 8-byte custom header, send to a server, and log the resolved addresses returned by the server.

Custom header format: `HHMMSSID` (8 ASCII bytes)
- HH: hour (24-hour)
- MM: minute
- SS: second
- ID: 2-digit sequence starting from 00

The client prepends this header to the raw DNS message from the PCAP:

```
+------------------+------------------------------+
| Custom Header(8) |  Original DNS message bytes  |
+------------------+------------------------------+
```

The server extracts the header, parses the DNS query, resolves per predefined rules, or falls back to the system resolver, and replies with:

```
+------------------+-------------------------+
| Custom Header(8) |  JSON (qname, answers)  |
+------------------+-------------------------+
```

## Quick Start

Requirements: Python 3.9+

```bash
# 1) Create venv and install deps
python -m venv .venv && . .venv/bin/activate                # Linux/Mac
# Windows: py -m venv .venv && .venv\Scripts\activate
pip install -r requirements.txt

# 2) Start the server (terminal A)
python server.py --port 53535 --rules rules.json

# 3) Run the client (terminal B)
#    Replace X.pcap with your chosen PCAP per assignment rule.
python client.py --pcap X.pcap --server-ip 127.0.0.1 --server-port 53535
```

Logs:
- Client writes CSV: `client_log.csv` with columns (timestamp, header, qname, answers, source, ok).
- Server writes CSV: `server_log.csv` with (timestamp, client, header, qname, qtype, answers, source).

Limit processing during tests:
```
python client.py --pcap X.pcap --limit 10
```

## Rules (server-side)

Put your mappings in `rules.json`. A rule has:
```json
{
  "match": "exact | suffix | prefix | contains",
  "pattern": "www.example.com.",
  "answers": ["93.184.216.34"]
}
```
Order matters: the first matching rule wins.

Fallback behavior (if no rule matches):
```json
{ "fallback": "system" }  // system = use local DNS
{ "fallback": "deny" }    // deny = respond with empty answers
```

Note: We could not access the Google Drive "rules" doc in this environment; please copy the official rules into `rules.json` before evaluation.

## PCAP selection

Per the assignment: choose `X.pcap` where
```
X = (sum of the last 3 digits of both team members' roll numbers) % 10
```

## Report generation

The table required by the assignment can be produced from `client_log.csv`.

| # | Query (QNAME) | Custom Header | Resolved IPs | Source |
|---|---|---|---|---|

Use `report_template.md` as a starting point and export to PDF (VS Code extension or pandoc).

## Makefile

```Makefile
# Run server
run-server:
	python server.py --port 53535 --rules rules.json

# Run client (set PCAP via env, e.g., make run-client PCAP=pcaps/3.pcap)
run-client:
	python client.py --pcap $(PCAP) --server-ip 127.0.0.1 --server-port 53535

# Format (if black installed)
format:
	black *.py
```
