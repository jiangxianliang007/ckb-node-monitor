from __future__ import annotations

import logging

from flask import Flask, Response, jsonify
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from .config import Config, load_config
from .metrics import MetricsCollector
from .rpc import RpcGet

logger = logging.getLogger(__name__)


def create_app(config: Config | None = None) -> Flask:
    cfg = config or load_config()

    app = Flask(__name__)
    rpc_client = RpcGet(cfg.ckb_node_rpc_url, cfg.rpc_timeout, cfg.bootnodes)
    labels = {
        "chain": cfg.chain,
        "node_name": cfg.node_name,
        "node_ip": cfg.node_ip,
        "node_location": cfg.node_location,
    }
    collector = MetricsCollector(rpc_client, labels)

    @app.get("/metrics")
    def metrics() -> Response:
        collector.collect()
        return Response(generate_latest(collector.registry), mimetype=CONTENT_TYPE_LATEST)

    @app.get("/health")
    def health() -> Response:
        node_info = rpc_client.get_node_info()
        node_status = int(node_info.get("node_status", 0))
        payload = {
            "status": "up" if node_status == 1 else "down",
            "node_status": node_status,
            "chain": cfg.chain,
            "node_name": cfg.node_name,
            "rpc_url": cfg.ckb_node_rpc_url,
        }
        http_code = 200 if node_status == 1 else 503
        return jsonify(payload), http_code

    logger.info("CKB exporter configured for chain=%s node_name=%s rpc=%s", cfg.chain, cfg.node_name, cfg.ckb_node_rpc_url)
    return app
