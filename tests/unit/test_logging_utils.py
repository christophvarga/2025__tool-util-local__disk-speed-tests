import logging

from diskbench.utils.logging import get_logger, setup_logging


def test_setup_logging_configures_root_logger():
    root = logging.getLogger()
    original_level = root.level
    original_handlers = list(root.handlers)

    for handler in list(root.handlers):
        root.removeHandler(handler)

    try:
        setup_logging(logging.INFO)
        assert root.level == logging.INFO
        assert any(isinstance(h, logging.StreamHandler) for h in root.handlers)

        # Reconfigure with different level to ensure override works
        setup_logging(logging.ERROR)
        assert root.level == logging.ERROR
    finally:
        for handler in list(root.handlers):
            root.removeHandler(handler)
        for handler in original_handlers:
            root.addHandler(handler)
        root.setLevel(original_level)


def test_get_logger_returns_named_logger():
    logger = get_logger('diskbench.test')
    assert logger.name == 'diskbench.test'
