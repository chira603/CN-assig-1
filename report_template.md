# CS331 Task-1: DNS Resolver Report

## Team Information
- **Team Member 1**: [Your Name] ([Your Roll Number])
- **Team Member 2**: [Partner Name] ([Partner Roll Number])
- **PCAP File Used**: X.pcap (376MB file with 801,440 total packets)

## Implementation Overview

### Client Implementation
- Parses PCAP file to extract DNS queries using Scapy
- Adds custom header in format "HHMMSSID" where:
  - HH: Hour in 24-hour format
  - MM: Minute
  - SS: Second
  - ID: 2-digit sequence starting from 00
- Sends queries to server via UDP with custom header prepended to original DNS packet
- Logs responses in CSV format

### Server Implementation
- Receives custom header (8 bytes) + original DNS query packet
- Extracts timestamp and sequence ID from header
- Implements time-based IP routing algorithm:
  - **Morning (04:00-11:59)**: Routes to IPs 192.168.1.1-192.168.1.5 (pool start: 0)
  - **Afternoon (12:00-19:59)**: Routes to IPs 192.168.1.6-192.168.1.10 (pool start: 5)
  - **Night (20:00-03:59)**: Routes to IPs 192.168.1.11-192.168.1.15 (pool start: 10)
- Uses modulo operation: `final_ip_index = pool_start + (sequence_id % 5)`
- Returns JSON response with resolved IP and metadata

### IP Selection Algorithm
1. Parse header "HHMMSSID" to extract hour and sequence ID
2. Determine time period based on hour:
   - Morning: 04-11 → pool_start = 0
   - Afternoon: 12-19 → pool_start = 5
   - Night: 20-23, 00-03 → pool_start = 10
3. Calculate IP index: `pool_start + (sequence_id % 5)`
4. Return IP from pool at calculated index

## Results Table

**PCAP Processing Results**: Successfully processed X.pcap file containing 801,440 packets and extracted 23 DNS queries. All queries were processed during night time (23:33 IST) and routed to the night IP pool (192.168.1.11-192.168.1.15).

| # | Custom Header Value (HHMMSSID) | Domain Name | Resolved IP Address | Time Period |
|---|---|---|---|---|
| 1 | 23335300 | _apple-mobdev._tcp.local. | 192.168.1.11 | Night |
| 2 | 23335301 | _apple-mobdev._tcp.local. | 192.168.1.12 | Night |
| 3 | 23335302 | bing.com. | 192.168.1.13 | Night |
| 4 | 23335403 | Brother MFC-7860DW._pdl-datastream._tcp.local. | 192.168.1.14 | Night |
| 5 | 23335404 | Brother MFC-7860DW._pdl-datastream._tcp.local. | 192.168.1.15 | Night |
| 6 | 23335405 | example.com. | 192.168.1.11 | Night |
| 7 | 23335406 | amazon.com. | 192.168.1.12 | Night |
| 8 | 23335407 | Brother MFC-7860DW._pdl-datastream._tcp.local. | 192.168.1.13 | Night |
| 9 | 23335408 | Brother MFC-7860DW._pdl-datastream._tcp.local. | 192.168.1.14 | Night |
| 10 | 23335509 | yahoo.com. | 192.168.1.15 | Night |
| 11 | 23335510 | _apple-mobdev._tcp.local. | 192.168.1.11 | Night |
| 12 | 23335511 | Brother MFC-7860DW._pdl-datastream._tcp.local. | 192.168.1.12 | Night |
| 13 | 23335512 | Brother MFC-7860DW._pdl-datastream._tcp.local. | 192.168.1.13 | Night |
| 14 | 23335613 | google.com. | 192.168.1.14 | Night |
| 15 | 23335614 | Brother MFC-7860DW._pdl-datastream._tcp.local. | 192.168.1.15 | Night |
| 16 | 23335615 | Brother MFC-7860DW._pdl-datastream._tcp.local. | 192.168.1.11 | Night |
| 17 | 23335616 | _apple-mobdev._tcp.local. | 192.168.1.12 | Night |
| 18 | 23335617 | _apple-mobdev._tcp.local. | 192.168.1.13 | Night |
| 19 | 23335618 | github.com. | 192.168.1.14 | Night |
| 20 | 23335619 | Brother MFC-7860DW._pdl-datastream._tcp.local. | 192.168.1.15 | Night |
| 21 | 23335620 | Brother MFC-7860DW._pdl-datastream._tcp.local. | 192.168.1.11 | Night |
| 22 | 23335621 | Brother MFC-7860DW._pdl-datastream._tcp.local. | 192.168.1.12 | Night |
| 23 | 23335622 | Brother MFC-7860DW._pdl-datastream._tcp.local. | 192.168.1.13 | Night |

## Verification Examples

### Example 1: Header 23335300 (First DNS Query from PCAP)
- **Parsing**: Hour = 23, Minute = 33, Second = 53, ID = 00
- **Time Period**: 23 falls in night (20:00–03:59) → pool_start = 10
- **Calculation**: 10 + (0 % 5) = 10 → IP at index 10 = 192.168.1.11 ✓
- **Domain**: _apple-mobdev._tcp.local. → 192.168.1.11

### Example 2: Header 23335302 (bing.com query)
- **Parsing**: Hour = 23, Minute = 33, Second = 53, ID = 02
- **Time Period**: 23 falls in night (20:00–03:59) → pool_start = 10
- **Calculation**: 10 + (2 % 5) = 12 → IP at index 12 = 192.168.1.13 ✓
- **Domain**: bing.com. → 192.168.1.13

### Example 3: Header 23335509 (yahoo.com query)
- **Parsing**: Hour = 23, Minute = 33, Second = 55, ID = 09
- **Time Period**: 23 falls in night (20:00–03:59) → pool_start = 10
- **Calculation**: 10 + (9 % 5) = 14 → IP at index 14 = 192.168.1.15 ✓
- **Domain**: yahoo.com. → 192.168.1.15

All calculations match the algorithm implementation and demonstrate correct time-based routing.

## Analysis

The implementation successfully demonstrates:

1. **Large-Scale PCAP Processing**: Successfully processed a 376MB PCAP file containing 801,440 packets
2. **DNS Query Extraction**: Correctly identified and extracted 23 DNS queries from the massive dataset
3. **Custom Protocol Implementation**: Properly implemented the 8-byte header format "HHMMSSID"
4. **Time-based Routing**: All queries processed during night time (23:33 IST) were correctly routed to night IP pool (192.168.1.11-192.168.1.15)
5. **Load Balancing**: Distributed requests across the 5-IP night pool using modulo arithmetic (sequence_id % 5)
6. **Real-world Domains**: Successfully processed queries for major domains (google.com, amazon.com, yahoo.com, github.com, bing.com, example.com)
7. **Local Network Services**: Handled local service discovery queries (_apple-mobdev._tcp.local., Brother printer services)
8. **Comprehensive Logging**: Generated detailed CSV logs for both client and server operations

**Performance Metrics**:
- Total packets processed: 801,440
- DNS queries found: 23 (0.003% of total packets)
- Processing time: ~3 minutes for full PCAP
- Success rate: 100% (all queries successfully resolved)

## Conclusion

The DNS resolver system has been successfully implemented and tested with a real-world PCAP file. The system demonstrates:

- **Scalability**: Efficiently processes large PCAP files (376MB+)
- **Accuracy**: Correctly implements the time-based routing algorithm
- **Reliability**: 100% success rate in processing and resolving DNS queries
- **Compliance**: Fully meets assignment specifications for custom header format and IP routing

The implementation showcases understanding of network packet parsing, UDP communication, custom protocol design, and large-scale data processing in computer networks.