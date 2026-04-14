from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from urllib.parse import urlparse

from dotenv import load_dotenv


@dataclass(frozen=True)
class Config:
    ckb_node_rpc_url: str
    chain: str
    node_name: str
    node_type: str
    node_ip: str
    node_location: str
    exporter_port: int
    exporter_host: str
    log_level: str
    rpc_timeout: int
    bootnodes: list[str]


def load_config() -> Config:
    load_dotenv()

    ckb_node_rpc_url = os.getenv("CKB_NODE_RPC_URL", "").strip()
    chain = os.getenv("CHAIN", "").strip()
    node_name = os.getenv("NODE_NAME", "").strip()
    node_type = os.getenv("NODE_TYPE", "public").strip()

    if not ckb_node_rpc_url:
        raise ValueError("CKB_NODE_RPC_URL is required")
    if not chain:
        raise ValueError("CHAIN is required")
    if not node_name:
        raise ValueError("NODE_NAME is required")

    parsed_url = urlparse(ckb_node_rpc_url)
    node_ip = os.getenv("NODE_IP", parsed_url.hostname or "unknown")
    node_location = os.getenv("NODE_LOCATION", "unknown")
    # Container-internal Flask port is fixed to match Docker EXPOSE/compose target.
    exporter_port = 8090
    exporter_host = os.getenv("EXPORTER_HOST", "0.0.0.0")
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    rpc_timeout = int(os.getenv("RPC_TIMEOUT", "10"))

    bootnodes_raw = os.getenv("BOOTNODES", "")
    bootnodes = [value.strip() for value in bootnodes_raw.split(",") if value.strip()]

    logging.getLogger().setLevel(getattr(logging, log_level, logging.INFO))

    return Config(
        ckb_node_rpc_url=ckb_node_rpc_url,
        chain=chain,
        node_name=node_name,
        node_type=node_type,
        node_ip=node_ip,
        node_location=node_location,
        exporter_port=exporter_port,
        exporter_host=exporter_host,
        log_level=log_level,
        rpc_timeout=rpc_timeout,
        bootnodes=bootnodes,
    )
