from __future__ import annotations

from news_aggregator.config.settings import Settings
from news_aggregator.utils.helpers import setup_logging
from news_aggregator.scheduler.scheduler import run_daily_pipeline
from news_aggregator.models.database import init_db


def main() -> int:
    settings = Settings.load()
    logger = setup_logging(settings)

    init_db(settings)

    logger.info("Starting News Aggregator Pipeline...")
    run_daily_pipeline()
    logger.info("Pipeline finished.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())