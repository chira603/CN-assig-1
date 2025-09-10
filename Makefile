.PHONY: run-server run-client test format install clean

# Install dependencies
install:
	pip install -r requirements.txt

# Run server
run-server:
	python server.py --port 53535 --rules rules.json

# Run client (set PCAP via env, e.g., make run-client PCAP=X.pcap)
run-client:
	@if [ -z "$(PCAP)" ]; then echo "Usage: make run-client PCAP=path/to/X.pcap [LIMIT=N]"; exit 2; fi
	python client.py --pcap $(PCAP) --server-ip 127.0.0.1 --server-port 53535 $(if $(LIMIT),--limit $(LIMIT))

# Run test client to verify server functionality
test:
	python test_client.py

# Format code (if black is installed)
format:
	black *.py || true

# Clean log files
clean:
	rm -f client_log.csv server_log.csv

# Show help
help:
	@echo "Available targets:"
	@echo "  install     - Install Python dependencies"
	@echo "  run-server  - Start the DNS resolver server"
	@echo "  run-client  - Run client with PCAP file (requires PCAP=filename)"
	@echo "  test        - Run test client to verify server"
	@echo "  format      - Format Python code with black"
	@echo "  clean       - Remove log files"
	@echo ""
	@echo "Examples:"
	@echo "  make install"
	@echo "  make run-server"
	@echo "  make run-client PCAP=X.pcap LIMIT=10"
	@echo "  make test"