# CKB Node Monitor (Prometheus Exporter)

Per-node CKB Prometheus exporter. Deploy one exporter per CKB node, then scrape each exporter from Prometheus.

```
CKB Node (local RPC) -> CKB Exporter (/metrics) -> Prometheus -> Grafana
```

## Architecture

- This project is a **per-node exporter**, not a centralized monitor.
- Each instance runs alongside one CKB node and scrapes that local node (default `http://127.0.0.1:8114`).
- Grafana chain/node selection is done via metric labels (`chain`, `node_type`, `node_name`, `node_location`, `node_ip`).
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

### B) Docker (pre-built image)

Pre-built multi-arch images (amd64/arm64) are available on GHCR:

```bash
docker pull ghcr.io/jiangxianliang007/ckb-node-monitor:latest

# Container always listens on 8090 internally.
# Replace <your-ckb-node-rpc-host> with your CKB node RPC host.
docker run -d \
  -e CKB_NODE_RPC_URL=http://<your-ckb-node-rpc-host>:8114 \
  -e CHAIN=mainnet \
  -e NODE_NAME=mainnet-node-1 \
  -p 8090:8090 \
  --restart=unless-stopped \
  ghcr.io/jiangxianliang007/ckb-node-monitor:latest
```

Supports both x86_64 and ARM64 (e.g. Apple Silicon, AWS Graviton).

### C) Docker (local build)

```bash
docker build -t ckb-node-monitor .
docker run -d \
  -e CKB_NODE_RPC_URL=http://<your-ckb-node-rpc-host>:8114 \
  -e CHAIN=mainnet \
  -e NODE_NAME=mainnet-node-1 \
  -p 8090:8090 \
  ckb-node-monitor
```

Use `-p <host_port>:8090` to expose the exporter on any host port.

### D) Docker Compose

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
| `NODE_TYPE` | No | `public` | Node type label (`bootnode` / `public`) for Grafana filtering |
| `NODE_IP` | No | host from `CKB_NODE_RPC_URL` | Node IP/hostname label |
| `NODE_LOCATION` | No | `unknown` | Node location label |
| `EXPORTER_PORT` | No | `8090` | Host port mapping to container port `8090` (Docker only; ignored by `python run.py`) |
| `EXPORTER_HOST` | No | `0.0.0.0` | Exporter listening host (mainly for direct `python run.py`) |
| `LOG_LEVEL` | No | `INFO` | Logging level |
| `RPC_TIMEOUT` | No | `10` | RPC timeout in seconds |
| `BOOTNODES` | No | empty | Comma-separated bootnode IP list to check whether known bootnodes are currently banned by this node |

> `BOOTNODES` is optional. If unset/empty, `ckb_banned_bootnodes_count` reports `0`.

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
  - `chain`: `label_values(ckb_node_status, chain)`
  - `node_type`: `label_values(ckb_node_status{chain="$chain"}, node_type)`
  - `node_name`: `label_values(ckb_node_status{chain="$chain", node_type="$node_type"}, node_name)`
  - `node_location`: `label_values(ckb_node_status{chain="$chain"}, node_location)`
- Filter dashboards by label selectors instead of exporter query parameters.

## Grafana Dashboard

Import the pre-built dashboard:

1. Open Grafana → Dashboards → Import
2. Upload `grafana/ckb-node-monitor.json`
3. Select your Prometheus datasource
4. Click Import

Dashboard features:
- **Variable selectors**: Filter by chain, node type, and individual nodes
- **Node overview**: Total/online/offline node counts with status table
- **Version distribution**: Pie charts showing CKB node version and miner version proportions
- **Block performance**: Block height, interval, size, difficulty, and network hashrate trends
- **Peer network**: Inbound/outbound peers, light clients, banned addresses
- **Transaction pool**: Pending/proposed txs, pool size, oldest pending age
- **Fee economics**: Fee rate mean/median/estimated, block transaction counts, epoch info
- **Chain economics**: DAO deposit, DAO depositors count

## Metrics and RPC Compatibility

The exporter uses `ckb_*` metric names aligned with CKB RPC semantics:

| Metric | Source RPC / meaning |
|---|---|
| `ckb_node_status` | Node connectivity status from `local_node_info` |
| `ckb_node_info` | Node info labels from `local_node_info` |
| `ckb_peers_outbound_count` | Outbound peers from `get_peers` |
| `ckb_peers_inbound_count` | Inbound peers from `get_peers` |
| `ckb_peers_light_client_count` | Light client peers from `get_peers` |
| `ckb_tip_header_info` | Tip header info labels (`block_hash`, `block_number`, `block_timestamp`) |
| `ckb_tip_block_number` | Tip block number from `get_tip_header` |
| `ckb_block_commit_transactions` | Tip block committed tx count from `get_block` |
| `ckb_block_proposal_transactions` | Tip block proposal tx count from `get_block` |
| `ckb_block_uncles_count` | Tip block uncle count from `get_block` |
| `ckb_block_interval_seconds` | Interval between tip and previous block (seconds) |
| `ckb_block_time_since_last_seconds` | Time since tip block timestamp (seconds) |
| `ckb_miner_client_version` | Miner client version marker from cellbase witness |
| `ckb_tx_pool_total_tx_size` | Total tx pool size from `tx_pool_info` |
| `ckb_tx_pool_total_tx_cycles` | Total tx pool cycles from `tx_pool_info` |
| `ckb_tx_pool_orphan` | Orphan tx count from `tx_pool_info` |
| `ckb_tx_pool_pending` | Pending tx count from `tx_pool_info` |
| `ckb_tx_pool_proposed` | Proposed tx count from `tx_pool_info` |
| `ckb_tx_pool_verify_queue_size` | Verify queue size from `tx_pool_info` |
| `ckb_epoch_number` | Epoch number from `get_current_epoch` |
| `ckb_epoch_start_number` | Epoch start number from `get_current_epoch` |
| `ckb_epoch_length` | Epoch length from `get_current_epoch` |
| `ckb_banned_addresses_total` | Total banned addresses from `get_banned_addresses` |
| `ckb_banned_bootnodes_count` | Banned bootnode count from `get_banned_addresses` |
| `ckb_tx_pool_oldest_pending_seconds` | Oldest pending tx age from `get_raw_tx_pool` |
| `ckb_tx_pool_pending_count` | Pending tx count from `get_raw_tx_pool` |
| `ckb_tx_pool_max_ancestors_count` | Max pending tx ancestors from `get_raw_tx_pool` |
| `ckb_fee_rate_mean` | Fee rate mean from `get_fee_rate_statistics` |
| `ckb_fee_rate_median` | Fee rate median from `get_fee_rate_statistics` |
| `ckb_block_size_bytes` | Serialized block size |
| `ckb_estimate_fee_rate` | Estimated fee rate from `estimate_fee_rate` |
| `ckb_blockchain_difficulty` | Chain difficulty from `get_blockchain_info` |
| `ckb_dao_deposit` | Nervos DAO total deposit in CKB from rich-indexer RPC `get_cells_capacity` (DAO type script) |
| `ckb_dao_depositors_count` | Nervos DAO unique depositor addresses count from rich-indexer RPC `get_cells` (unique lock scripts) |
| `ckb_network_hashrate` | Estimated network hashrate in H/s from difficulty and epoch average block time |

> DAO metrics (`ckb_dao_deposit`, `ckb_dao_depositors_count`) require rich-indexer RPC support on the node. If unavailable, exporter reports `-1` and continues running.
