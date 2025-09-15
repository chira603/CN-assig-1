#!/usr/bin/env python3
"""
CS331 Task-1: DNS Resolver - Server
Listens on UDP and handles custom messages of the form:
  [8-byte ASCII header "HHMMSSID"] + [raw DNS message (as captured from pcap)]
Extracts the header, parses the DNS query, resolves per rules.json (or system DNS),
and replies to the client with:
  [same 8-byte header] + [UTF-8 JSON payload]
where the JSON includes qname, qtype, answers, and the decision source.
"""
import argparse
import json
import socket
import sys
import time
import re
import os

try:
    from scapy.all import DNS
except Exception as e:
    print("[-] Failed to import scapy. Install dependencies with: pip install -r requirements.txt", file=sys.stderr)
    raise

def load_rules(path: str):
    try:
        with open(path, "r", encoding="utf-8") as f:
            cfg = json.load(f)
        # Ensure required fields exist
        if "rules" not in cfg:
            cfg["rules"] = []
        if "ip_pool" not in cfg:
            cfg["ip_pool"] = [
                "192.168.1.1", "192.168.1.2", "192.168.1.3", "192.168.1.4", "192.168.1.5",
                "192.168.1.6", "192.168.1.7", "192.168.1.8", "192.168.1.9", "192.168.1.10",
                "192.168.1.11", "192.168.1.12", "192.168.1.13", "192.168.1.14", "192.168.1.15"
            ]
        return cfg
    except Exception as e:
        print(f"[-] Could not load rules from {path}: {e}", file=sys.stderr)
        return {
            "rules": [],
            "fallback": "custom_header_routing",
            "ip_pool": [
                "192.168.1.1", "192.168.1.2", "192.168.1.3", "192.168.1.4", "192.168.1.5",
                "192.168.1.6", "192.168.1.7", "192.168.1.8", "192.168.1.9", "192.168.1.10",
                "192.168.1.11", "192.168.1.12", "192.168.1.13", "192.168.1.14", "192.168.1.15"
            ]
        }

def resolve_with_custom_header(header_txt: str, cfg: dict):
    """
    Implement the custom header-based IP resolution algorithm:
    1. Extract timestamp from custom header: "HHMMSSID"
    2. Parse hour to determine time period (morning/afternoon/night)
    3. Use ID with modulo 5 to select IP from appropriate pool segment
    """
    if len(header_txt) != 8:
        return [], "invalid_header"

    try:
        # Parse HHMMSSID format
        hour = int(header_txt[:2])
        minute = int(header_txt[2:4])
        second = int(header_txt[4:6])
        seq_id = int(header_txt[6:8])
    except ValueError:
        return [], "invalid_header_format"

    ip_pool = cfg.get("ip_pool", [])
    if len(ip_pool) != 15:
        return [], "invalid_ip_pool"

    # Determine time period and IP pool segment
    if 4 <= hour <= 11:  # Morning: 04:00-11:59
        ip_pool_start = 0
        period = "morning"
    elif 12 <= hour <= 19:  # Afternoon: 12:00-19:59
        ip_pool_start = 5
        period = "afternoon"
    else:  # Night: 20:00-03:59 (covers 20-23 and 0-3)
        ip_pool_start = 10
        period = "night"

    # Apply modulo 5 to sequence ID and select IP
    ip_index = ip_pool_start + (seq_id % 5)
    selected_ip = ip_pool[ip_index]

    return [selected_ip], f"custom_header_{period}"

def match_rules(qname: str, header_txt: str, cfg: dict):
    qname_norm = qname.lower()
    for rule in cfg.get("rules", []):
        # Optional header filter
        hpat = (rule.get("header_pattern") or "")
        if hpat:
            try:
                if not re.search(hpat, header_txt):
                    continue
            except Exception:
                # treat as literal substring if regex invalid
                if hpat not in header_txt:
                    continue
        mtype = (rule.get("match") or "").lower()
        pat = (rule.get("pattern") or "").lower()
        answers = rule.get("answers") or []
        if not pat:
            continue
        if mtype == "exact" and qname_norm == pat:
            return answers, "rules"
        if mtype == "suffix" and qname_norm.endswith(pat):
            return answers, "rules"
        if mtype == "prefix" and qname_norm.startswith(pat):
            return answers, "rules"
        if mtype == "contains" and pat in qname_norm:
            return answers, "rules"

    # Check fallback behavior
    fb = (cfg.get("fallback") or "system").lower()
    if fb == "deny":
        return [], "deny"
    elif fb == "custom_header_routing":
        return resolve_with_custom_header(header_txt, cfg)
    return [], "system"

def system_resolve(qname: str, qtype: int):
    results = set()
    family = 0
    if qtype == 1:
        family = socket.AF_INET
    elif qtype == 28:
        family = socket.AF_INET6
    try:
        for res in socket.getaddrinfo(qname.rstrip("."), None, family, socket.SOCK_STREAM):
            sockaddr = res[4]
            ip = sockaddr[0]
            results.add(ip)
    except Exception:
        pass
    if not results:
        try:
            import dns.resolver
            rrtype = "A" if qtype == 1 else ("AAAA" if qtype == 28 else "A")
            ans = dns.resolver.resolve(qname.rstrip("."), rrtype, lifetime=2.0)
            for r in ans:
                results.add(r.to_text())
        except Exception:
            pass
    return sorted(results)

def parse_dns_query(dns_bytes: bytes):
    try:
        dns = DNS(dns_bytes)
        if dns.qdcount >= 1 and dns.qd is not None:
            qname = dns.qd.qname
            if isinstance(qname, bytes):
                qname = qname.decode("utf-8", "ignore")
            qtype = int(dns.qd.qtype)
            return qname, qtype
    except Exception:
        pass
    return None, None

def main():
    ap = argparse.ArgumentParser(description="CS331 Task-1 DNS Resolver Server")
    ap.add_argument("--port", type=int, default=53535, help="UDP port to listen on (default: 53535)")
    ap.add_argument("--bind", default="0.0.0.0", help="Bind address (default: 0.0.0.0)")
    ap.add_argument("--rules", default="rules.json", help="Path to rules.json")
    ap.add_argument("--log", default="server_log.csv", help="CSV log file path")
    args = ap.parse_args()

    cfg = load_rules(args.rules)

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((args.bind, args.port))
    sock.settimeout(0.5)
    print(f"[+] Server listening on {args.bind}:{args.port} with rules '{args.rules}'")

    if not os.path.exists(args.log):
        with open(args.log, "w", encoding="utf-8") as f:
            f.write("Custom header value (HHMMSSID),Domain name,Resolved IP address\n")

    while True:
        try:
            data, addr = sock.recvfrom(65535)
        except socket.timeout:
            continue
        except KeyboardInterrupt:
            print("\n[+] Server stopping.")
            break

        if len(data) < 8:
            print(f"[-] Dropping short packet from {addr}")
            continue

        header = data[:8]
        payload = data[8:]
        try:
            header_txt = header.decode("ascii", "ignore")
        except Exception:
            header_txt = "????????"

        qname, qtype = parse_dns_query(payload)
        if qname is None:
            resp = {"ok": False, "error": "Could not parse DNS query", "header": header_txt}
            sock.sendto(header + json.dumps(resp).encode("utf-8"), addr)
            print(f"[!] Bad DNS from {addr}, header={header_txt}")
            continue

        answers, source = match_rules(qname, header_txt, cfg)
        if source == "system":
            answers = system_resolve(qname, qtype) or []

        resp = {"ok": True, "header": header_txt, "qname": qname, "qtype": qtype, "answers": answers, "source": source}
        sock.sendto(header + json.dumps(resp).encode("utf-8"), addr)

        # Log in the required format: Custom header value (HHMMSSID), Domain name, Resolved IP address
        qname_clean = (qname or "").rstrip(".")
        resolved_ip = answers[0] if answers else ""
        with open(args.log, "a", encoding="utf-8") as f:
            f.write(f"{header_txt},{qname_clean},{resolved_ip}\n")

if __name__ == "__main__":
    main()
