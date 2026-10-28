"""Ejecución de la araña CuspideSpider en un proceso propio.

Scrapy usa el reactor de Twisted, que solo puede iniciarse una vez por
proceso; por eso el sistema ejecuta la araña con este módulo en un proceso
nuevo cada vez que se pide el scraping:

    python -m book_manager.scraper.ejecutar libros.json resultados.jsonl

El primer archivo tiene los libros a buscar y en el segundo quedan los
resultados (un JSON por línea).
"""
import sys
from typing import List

from scrapy.crawler import CrawlerProcess
from scrapy.settings import Settings

from book_manager.scraper.cuspide.spiders.cuspide_spider import CuspideSpider

MODULO_CONFIGURACION: str = "book_manager.scraper.cuspide.settings"


def ejecutar_arana(archivo_libros: str, archivo_salida: str) -> None:
    """Ejecuta CuspideSpider y espera a que termine.

    Args:
        archivo_libros (str): Archivo JSON con los libros a buscar.
        archivo_salida (str): Archivo JSON Lines donde se escriben los
            resultados.
    """
    configuracion = Settings()
    configuracion.setmodule(MODULO_CONFIGURACION, priority="project")
    configuracion.set("ARCHIVO_SALIDA", archivo_salida, priority="cmdline")
    proceso = CrawlerProcess(configuracion)
    proceso.crawl(CuspideSpider, archivo_libros=archivo_libros)
    proceso.start()


def principal(argumentos: List[str]) -> int:
    """Lee los argumentos de la línea de comandos y ejecuta la araña.

    Args:
        argumentos (List[str]): Argumentos (sin el nombre del programa).

    Returns:
        int: Código de salida (0 si terminó bien, 2 si faltan argumentos).
    """
    if len(argumentos) != 2:
        print("Uso: python -m book_manager.scraper.ejecutar "
              "libros.json resultados.jsonl", file=sys.stderr)
        return 2
    ejecutar_arana(argumentos[0], argumentos[1])
    return 0


if __name__ == "__main__":
    sys.exit(principal(sys.argv[1:]))
