import logging
import sys


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
        stream=sys.stderr,
    )
    logger = logging.getLogger(__name__)

    try:
        from app.config import load_config
        from app.main import create_app

        logger.info("Loading configuration...")
        config = load_config()
        logger.info(
            "Configuration loaded: chain=%s node=%s rpc=%s port=%s",
            config.chain,
            config.node_name,
            config.ckb_node_rpc_url,
            config.exporter_port,
        )

        logger.info("Creating Flask app...")
        app = create_app(config)

        logger.info("CKB exporter starting on %s:%s (threaded=True)", config.exporter_host, config.exporter_port)
        app.run(host=config.exporter_host, port=config.exporter_port, threaded=True)
    except Exception:
        logger.exception("Failed to start CKB exporter")
        sys.exit(1)


if __name__ == "__main__":
    main()
