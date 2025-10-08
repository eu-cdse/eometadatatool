import logging.config
from typing import Literal

from rich.console import Console


def configure_logging(log_level: Literal['DEBUG', 'INFO', 'WARNING']) -> None:
    logging.config.dictConfig({
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'default': {
                'format': '[dark_red]%(name)s[/] %(message)s',
                'datefmt': '%Y-%m-%d %H:%M:%S',
            },
        },
        'handlers': {
            'default': {
                'formatter': 'default',
                'class': 'rich.logging.RichHandler',
                'console': Console(stderr=True),
                'omit_repeated_times': False,
                'markup': True,
            },
        },
        'loggers': {
            'root': {'handlers': ['default'], 'level': log_level},
            **{
                # reduce logging verbosity of some modules
                module: {'handlers': [], 'level': 'INFO'}
                for module in (
                    'botocore',
                    'hpack',
                    'httpx',
                    'httpcore',
                )
            },
        },
    })
