#!/usr/bin/env python3
"""
CS331 Task-1: DNS Resolver - Client
Reads a PCAP, filters DNS queries, prepends an 8-byte custom header "HHMMSSID",
sends to the server over UDP, and logs responses.
"""
import argparse
import csv
import socket
import sys
import time
from datetime import datetime, timezone, timedelta
import os, json

try:
    from scapy.all import rdpcap, DNS, DNSQR
except Exception as e:
    print("[-] Failed to import scapy. Install dependencies with: pip install -r requirements.txt", file=sys.stderr)
    raise

IST = timezone(timedelta(hours=5, minutes=30), name="IST")

def current_header(seq:int) -> bytes:
    now = datetime.now(IST)
    hhmmss = now.strftime("%H%M%S")
    sid = f"{seq:02d}"
    return (hhmmss + sid).encode("ascii")

def extract_dns_queries(pcap_path: str, limit: int = 0):
    print(f"[+] Loading PCAP file: {pcap_path}")
    try:
        packets = rdpcap(pcap_path)
        print(f"[+] Loaded {len(packets)} packets from PCAP")
    except Exception as e:
        print(f"[-] Error loading PCAP: {e}")
        return

    dns_count = 0
    for i, pkt in enumerate(packets):
        if limit and dns_count >= limit:
            break

        if i % 10000 == 0 and i > 0:
            print(f"[+] Processed {i} packets, found {dns_count} DNS queries")

        if DNS in pkt and DNSQR in pkt:
            dns = pkt[DNS]
            try:
                if int(dns.qr) != 0:  # Skip DNS responses
                    continue
            except Exception:
                continue
            qname = None
            if dns.qd is not None:
                qname = dns.qd.qname
                if isinstance(qname, bytes):
                    qname = qname.decode("utf-8", "ignore")
            dns_count += 1
            yield qname, bytes(dns)

    print(f"[+] Finished processing PCAP. Found {dns_count} DNS queries total.")

def main():
    ap = argparse.ArgumentParser(description="CS331 Task-1 DNS Resolver Client")
    ap.add_argument("--pcap", required=True, help="Path to PCAP file (X.pcap)")
    ap.add_argument("--server-ip", default="127.0.0.1", help="DNS resolver server IP (default: 127.0.0.1)")
    ap.add_argument("--server-port", type=int, default=53535, help="Server UDP port (default: 53535)")
    ap.add_argument("--limit", type=int, default=0, help="Limit number of queries (0 = no limit)")
    ap.add_argument("--log", default="client_log.csv", help="CSV log path")
    ap.add_argument("--timeout", type=float, default=3.0, help="Receive timeout seconds")
    args = ap.parse_args()

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(args.timeout)

    if not os.path.exists(args.log):
        with open(args.log, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["ts_iso", "custom_header", "qname", "answers", "source", "ok"])

    count = 0
    for qname, dns_bytes in extract_dns_queries(args.pcap, args.limit):
        header = current_header(count)
        payload = header + dns_bytes
        sock.sendto(payload, (args.server_ip, args.server_port))

        try:
            resp, _ = sock.recvfrom(65535)
        except socket.timeout:
            ts = datetime.now(IST).isoformat(timespec="seconds")
            with open(args.log, "a", newline="", encoding="utf-8") as f:
                csv.writer(f).writerow([ts, header.decode("ascii"), qname, "", "timeout", False])
            print(f"[timeout] {qname} (header={header.decode('ascii')})")
            count += 1
            continue

        if len(resp) < 8:
            print(f"[-] Short response for {qname}")
            count += 1
            continue
        rjson = resp[8:]
        try:
            meta = json.loads(rjson.decode("utf-8"))
        except Exception:
            meta = {"ok": False, "error": "bad-json", "answers": []}

        ts = datetime.now(IST).isoformat(timespec="seconds")
        answers = ";".join(meta.get("answers") or [])
        source = meta.get("source", "unknown")
        ok = bool(meta.get("ok", False))
        with open(args.log, "a", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow([ts, header.decode("ascii"), qname, answers, source, ok])

        print(f"[{source:6}] {qname} -> {answers}  (header={header.decode('ascii')})")
        count += 1

    print(f"[+] Done. Processed {count} DNS queries from {args.pcap}")

if __name__ == "__main__":
    main()
