import logging

from bzl.config.paths import resolve_log_file


def configure_logging(level: int = logging.INFO) -> None:
    # A StreamHandler would write straight to stderr, corrupting the Textual
    # TUI's raw-mode terminal rendering while the app is running.
    log_file = resolve_log_file()
    log_file.parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        handlers=[logging.FileHandler(log_file)],
    )
