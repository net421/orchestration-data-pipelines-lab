import logging


def get_logger(name="analytics_pipeline"):
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    return logging.getLogger(name)


def log_event(logger, event_name: str, **fields) -> None:
    ordered_fields = " ".join(f"{key}={value}" for key, value in sorted(fields.items()))
    logger.info("%s %s", event_name, ordered_fields)
