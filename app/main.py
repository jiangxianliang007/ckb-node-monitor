from __future__ import annotations

import logging
import time

from flask import Flask, Response, g, jsonify, request
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
        "node_type": cfg.node_type,
        "node_ip": cfg.node_ip,
        "node_location": cfg.node_location,
    }
    collector = MetricsCollector(rpc_client, labels)

    @app.before_request
    def log_request_start() -> None:
        g.start_time = time.time()
        logger.info("--> %s %s from %s", request.method, request.path, request.remote_addr)

    @app.after_request
    def log_request_end(response: Response) -> Response:
        duration_ms = (time.time() - getattr(g, "start_time", time.time())) * 1000
        logger.info(
            "<-- %s %s %s (%.1fms)",
            request.method,
            request.path,
            response.status_code,
            duration_ms,
        )
        return response

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

    logger.info(
        "CKB exporter configured: chain=%s node=%s rpc=%s listen=%s:%s",
        cfg.chain,
        cfg.node_name,
        cfg.ckb_node_rpc_url,
        cfg.exporter_host,
        cfg.exporter_port,
    )
    return app
