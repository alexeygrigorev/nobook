"""Jupyter server extension that registers the NobookContentsManager."""


def _jupyter_server_extension_points():
    return [{"module": "nobook.jupyter.serverextension"}]


def _load_jupyter_server_extension(server_app):
    """Register NobookContentsManager with the server."""
    from .contentsmanager import NobookContentsManager

    server_app.contents_manager_class = NobookContentsManager
    server_app.log.info("nobook: ContentsManager registered")
