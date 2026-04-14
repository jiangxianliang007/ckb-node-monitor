# CKB Node Monitor (Prometheus Exporter)

Per-node CKB Prometheus exporter. Deploy one exporter per CKB node, then scrape each exporter from Prometheus.

```
CKB Node (local RPC) -> CKB Exporter (/metrics) -> Prometheus -> Grafana
```

## Architecture

- This project is a **per-node exporter**, not a centralized monitor.
- Each instance runs alongside one CKB node and scrapes that local node (default `http://127.0.0.1:8114`).
- Grafana chain/node selection is done via metric labels (`chain`, `node_name`, `node_location`, `node_ip`).
- Exporter endpoints:
  - `GET /metrics`
  - `GET /health`

## Quick Start

### A) Direct Python

```bash
pip install -r requirements.txt
cp .env.example .env
# edit .env: CKB_NODE_RPC_URL, CHAIN, NODE_NAME
python run.py
```

### B) Docker

```bash
docker build -t ckb-node-monitor .
docker run -d \
  -e CKB_NODE_RPC_URL=http://host.docker.internal:8114 \
  -e CHAIN=mainnet \
  -e NODE_NAME=mainnet-node-1 \
  -p 8090:8090 \
  ckb-node-monitor
```

### C) Docker Compose

```bash
docker compose up -d --build
```

`docker-compose.yml` includes an optional Prometheus service example.

## Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `CKB_NODE_RPC_URL` | Yes | - | Local CKB RPC endpoint |
| `CHAIN` | Yes | - | Chain label (`mainnet` / `testnet` / `preview`) |
| `NODE_NAME` | Yes | - | Unique node name label |
| `NODE_IP` | No | host from `CKB_NODE_RPC_URL` | Node IP/hostname label |
| `NODE_LOCATION` | No | `unknown` | Node location label |
| `EXPORTER_PORT` | No | `8090` | Exporter listening port |
| `EXPORTER_HOST` | No | `0.0.0.0` | Exporter listening host |
| `LOG_LEVEL` | No | `INFO` | Logging level |
| `RPC_TIMEOUT` | No | `10` | RPC timeout in seconds |
| `BOOTNODES` | No | empty | Comma-separated bootnode IP list for maintainer ban tracking |

> `BOOTNODES` is optional. If unset/empty, `node_ban_bootnode` reports `0`.

## Prometheus Scrape Example

Use `prometheus/prometheus.yml`:

```yaml
scrape_configs:
  - job_name: 'ckb-mainnet'
    static_configs:
      - targets: ['mainnet-node-1:8090', 'mainnet-node-2:8090']
  - job_name: 'ckb-testnet'
    static_configs:
      - targets: ['testnet-node-1:8090']
```

## Grafana Tips

- Create template variables from labels:
  - `chain`: `label_values(node_status, chain)`
  - `node_name`: `label_values(node_status{chain="$chain"}, node_name)`
  - `node_location`: `label_values(node_status{chain="$chain"}, node_location)`
- Filter dashboards by label selectors instead of exporter query parameters.

## Metrics and RPC Compatibility

All existing RPC methods and all existing gauge families were preserved and refactored into:

- `app/rpc.py`: RPC methods and timeout/error handling
- `app/metrics.py`: Gauge definitions and collection
- `app/main.py`: Flask endpoints
- `app/config.py`: `.env` + environment config
