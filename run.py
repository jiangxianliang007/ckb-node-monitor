from app.config import load_config
from app.main import create_app

config = load_config()
app = create_app(config)

if __name__ == "__main__":
    app.run(host=config.exporter_host, port=config.exporter_port)
