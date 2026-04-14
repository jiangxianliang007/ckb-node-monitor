import logging

from app.config import load_config
from app.main import create_app

logger = logging.getLogger(__name__)

config = load_config()
app = create_app(config)

if __name__ == "__main__":
    logger.info("CKB exporter starting on %s:%s", config.exporter_host, config.exporter_port)
    app.run(host=config.exporter_host, port=config.exporter_port)
