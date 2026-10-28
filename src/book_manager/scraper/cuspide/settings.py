"""Configuración del proyecto Scrapy cuspide.

Se identifica el bot, se respeta el robots.txt del sitio y se limita la
velocidad de las consultas para no sobrecargarlo.
"""
from typing import Dict

BOT_NAME: str = "cuspide"

SPIDER_MODULES = ["book_manager.scraper.cuspide.spiders"]
NEWSPIDER_MODULE: str = "book_manager.scraper.cuspide.spiders"

USER_AGENT: str = ("Mozilla/5.0 (compatible; BookManagerUGR/3.0; "
                   "Trabajo practico academico)")
ROBOTSTXT_OBEY: bool = True

# Consultas moderadas: pocas en paralelo y con una pausa entre ellas.
CONCURRENT_REQUESTS: int = 8
CONCURRENT_REQUESTS_PER_DOMAIN: int = 8
DOWNLOAD_DELAY: float = 0.25
AUTOTHROTTLE_ENABLED: bool = True
AUTOTHROTTLE_START_DELAY: float = 0.25
AUTOTHROTTLE_TARGET_CONCURRENCY: float = 4.0
AUTOTHROTTLE_MAX_DELAY: float = 5.0
DOWNLOAD_TIMEOUT: int = 30
RETRY_TIMES: int = 2

DEFAULT_REQUEST_HEADERS: Dict[str, str] = {
    "Accept": "text/html,application/xhtml+xml",
    "Accept-Language": "es-AR,es;q=0.9",
}

# Orden de los pipelines: primero se valida, después se descartan los
# repetidos y al final se exporta cada resultado al archivo de salida.
ITEM_PIPELINES: Dict[str, int] = {
    "book_manager.scraper.cuspide.pipelines.ValidacionPipeline": 100,
    "book_manager.scraper.cuspide.pipelines.DuplicadosPipeline": 200,
    "book_manager.scraper.cuspide.pipelines.ExportacionPipeline": 300,
}

# Archivo JSON Lines donde ExportacionPipeline deja los resultados (lo
# define el proceso que ejecuta la araña).
ARCHIVO_SALIDA: str = ""

LOG_LEVEL: str = "INFO"
FEED_EXPORT_ENCODING: str = "utf-8"
REQUEST_FINGERPRINTER_IMPLEMENTATION: str = "2.7"
