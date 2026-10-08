"""Root application entrypoint for WSGI servers (Gunicorn) on Render."""

from src.app import app

__all__ = ["app"]

if __name__ == "__main__":
    from src import config
    app.run(host=config.HOST, port=config.PORT, debug=config.DEBUG)
