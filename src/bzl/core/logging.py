import logging

# Future file-logging hook: add a RotatingFileHandler here (e.g. logs/bzl.log)
# once the app needs persistent logs across runs.


def configure_logging(level: int = logging.INFO) -> None:
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        handlers=[logging.StreamHandler()],
    )
