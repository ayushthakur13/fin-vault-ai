import logging


def setup_logging(log_level: str) -> None:
	level = logging.getLevelName(log_level.upper())
	logging.basicConfig(
		level=level,
		format="%(asctime)s %(levelname)s %(name)s - %(message)s",
	)


def get_logger(name: str) -> logging.Logger:
	return logging.getLogger(name)
