# CS331 Task‑1 – DNS Resolver 

This assignment implements a minimal DNS resolver system composed of a UDP server and a client. The client extracts DNS queries from a PCAP file, prefixes each query with a custom 8‑byte header (HHMMSSID), and sends it to the server over UDP. The server parses the header and DNS query, resolves an IP address based on configurable rules (or a deterministic header‑based algorithm), returns a JSON response to the client, and writes structured CSV logs.

## Components
- server.py – UDP server that accepts messages of the form: [8‑byte ASCII header “HHMMSSID”] + [raw DNS message]. It extracts the header, parses the DNS question (qname, qtype), decides the answer(s), replies with JSON, and logs events.
- client.py – Reads a PCAP, filters DNS queries, generates the custom header (IST timezone), sends each query to the server, collects replies, and logs outcomes.
- rules.json – Configuration for resolution behavior: optional domain matching rules and a header‑based routing policy using a fixed 15‑IP pool.
- requirements.txt – Python dependencies.
- Makefile – Convenience targets to install deps, run the server/client, and clean logs.

## Custom header and resolution logic
Header format: HHMMSSID (two digits each for hour, minute, second, and a 2‑digit sequence ID).

Resolution decision order in server.py:
1) Match against rules.json → returns configured answers when a rule hits.
2) Fallback policy (rules.json → "fallback"): set to "custom_header_routing" in this assignment.
   - Time buckets: morning (04:00–11:59), afternoon (12:00–19:59), night (20:00–03:59).
   - IP pool segments: first/middle/last 5 of a 15‑IP pool.
   - The last two header digits (ID) are used modulo 5 to pick one IP from the segment.
3) If fallback were set to "system", the server would resolve using system DNS (A/AAAA).

## Logs
- server_log.csv – Written by the server (appends). Columns:
  ts_iso, client_ip, header, qname, qtype, answers, source
- client_log.csv – Written by the client (appends). Columns:
  ts_iso, custom_header, qname, answers, source, ok

## Setup
1) Use Python 3.9+.
2) Install dependencies:
   pip install -r requirements.txt

## Running
Option A – with Makefile:
- make install
- make run-server
- make run-client PCAP=5.pcap LIMIT=10  # example

Option B – direct commands:
- Start server:
  python server.py --port 53535 --bind 0.0.0.0 --rules rules.json --log server_log.csv
- Run client:
  python client.py --pcap 5.pcap --server-ip 127.0.0.1 --server-port 53535 --limit 10 --log client_log.csv

## Repository notes
- report_template.md and TASK_COMPLETION_SUMMARY.md – reporting artifacts.
- Logs are appended by default; use `make clean` to remove them.

## Assumptions and constraints
- Only DNS queries are processed; malformed packets are skipped.
- Client constructs headers in IST timezone; the server treats the header as ASCII text.
- The custom header routing is deterministic and uses only the header/time buckets, not external DNS.
- Network and DNS failures are handled gracefully (timeouts result in empty answers/flags in logs).

## Results (from report.csv)

The file report.csv contains the final mapped results produced from the DNS resolution run. Each row records the custom header value (HHMMSSID), the queried domain name, and the resolved IP address selected by the header‑based routing policy.

| Custom header value (HHMMSSID) | Domain name                                      | Resolved IP address |
| --- | --- | --- |
| 23420800 | apple.com | 192.168.1.11 |
| 23420801 | _apple-mobdev._tcp.local | 192.168.1.12 |
| 23420802 | _apple-mobdev._tcp.local | 192.168.1.13 |
| 23420803 | facebook.com | 192.168.1.14 |
| 23420804 | Brother MFC-7860DW._pdl-datastream._tcp.local | 192.168.1.15 |
| 23420805 | Brother MFC-7860DW._pdl-datastream._tcp.local | 192.168.1.11 |
| 23420906 | Brother MFC-7860DW._pdl-datastream._tcp.local | 192.168.1.12 |
| 23420907 | Brother MFC-7860DW._pdl-datastream._tcp.local | 192.168.1.13 |
| 23420908 | amazon.com | 192.168.1.14 |
| 23421009 | _apple-mobdev._tcp.local | 192.168.1.15 |
| 23421010 | Brother MFC-7860DW._pdl-datastream._tcp.local | 192.168.1.11 |
| 23421011 | Brother MFC-7860DW._pdl-datastream._tcp.local | 192.168.1.12 |
| 23421012 | twitter.com | 192.168.1.13 |
| 23421113 | Brother MFC-7860DW._pdl-datastream._tcp.local | 192.168.1.14 |
| 23421114 | Brother MFC-7860DW._pdl-datastream._tcp.local | 192.168.1.15 |
| 23421115 | _apple-mobdev._tcp.local | 192.168.1.11 |
| 23421116 | _apple-mobdev._tcp.local | 192.168.1.12 |
| 23421117 | wikipedia.org | 192.168.1.13 |
| 23421318 | Brother MFC-7860DW._pdl-datastream._tcp.local | 192.168.1.14 |
| 23421319 | Brother MFC-7860DW._pdl-datastream._tcp.local | 192.168.1.15 |
| 23421320 | Brother MFC-7860DW._pdl-datastream._tcp.local | 192.168.1.11 |
| 23421321 | Brother MFC-7860DW._pdl-datastream._tcp.local | 192.168.1.12 |
| 23421322 | stackoverflow.com | 192.168.1.13 |

Briefly, the IP selection follows the header‑based policy: the hour in HHMMSSID determines a 5‑IP segment (morning/afternoon/night), and the two‑digit sequence ID chooses one IP within that segment using modulo 5. This yields a balanced, deterministic mapping across the relevant 5‑IP range.
