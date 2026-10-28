"""Pipelines del proyecto Scrapy: validación, duplicados y exportación.

Cada LibroWebItem que arma la araña pasa, en orden, por:

1. ValidacionPipeline: descarta los resultados sin título, URL o precio.
2. DuplicadosPipeline: descarta el mismo producto repetido para un libro.
3. ExportacionPipeline: escribe el resultado en el archivo JSON Lines que
   luego lee el sistema para guardarlo en la base.
"""
from pathlib import Path
from typing import Any, BinaryIO, Optional, Set, Tuple

from itemadapter import ItemAdapter
from scrapy import Spider
from scrapy.crawler import Crawler
from scrapy.exceptions import DropItem, NotConfigured
from scrapy.exporters import JsonLinesItemExporter

CAMPOS_OBLIGATORIOS: Tuple[str, ...] = ("libro_id", "posicion", "titulo",
                                        "url", "precio")


class ValidacionPipeline:
    """Descarta los resultados a los que les falta un dato obligatorio."""

    def process_item(self, item: Any, spider: Spider) -> Any:
        """Valida los campos obligatorios y el precio del resultado.

        Args:
            item (Any): LibroWebItem armado por la araña.
            spider (Spider): Araña que lo generó.

        Returns:
            Any: El mismo item, si es válido.

        Raises:
            DropItem: Si falta un campo obligatorio o el precio es negativo.
        """
        adaptador = ItemAdapter(item)
        faltantes = [campo for campo in CAMPOS_OBLIGATORIOS
                     if adaptador.get(campo) in (None, "")]
        if faltantes:
            raise DropItem(
                f"Faltan datos {faltantes} en {adaptador.get('url')}")
        if adaptador["precio"] < 0:
            raise DropItem(f"Precio inválido en {adaptador['url']}")
        return item


class DuplicadosPipeline:
    """Descarta un producto ya obtenido para el mismo libro del catálogo."""

    def __init__(self) -> None:
        """Inicia el registro de productos vistos (libro, url)."""
        self.__vistos: Set[Tuple[int, str]] = set()

    def process_item(self, item: Any, spider: Spider) -> Any:
        """Deja pasar el resultado solo la primera vez que aparece.

        Args:
            item (Any): LibroWebItem validado.
            spider (Spider): Araña que lo generó.

        Returns:
            Any: El mismo item, si no estaba repetido.

        Raises:
            DropItem: Si el producto ya se obtuvo para ese libro.
        """
        adaptador = ItemAdapter(item)
        clave: Tuple[int, str] = (adaptador["libro_id"], adaptador["url"])
        if clave in self.__vistos:
            raise DropItem(f"Producto repetido: {adaptador['url']}")
        self.__vistos.add(clave)
        return item


class ExportacionPipeline:
    """Escribe cada resultado en un archivo JSON Lines (uno por línea)."""

    def __init__(self, archivo_salida: str) -> None:
        """Recibe la ruta del archivo de salida.

        Args:
            archivo_salida (str): Ruta del archivo JSON Lines.
        """
        self.__ruta: Path = Path(archivo_salida)
        self.__archivo: Optional[BinaryIO] = None
        self.__exportador: Optional[JsonLinesItemExporter] = None

    @classmethod
    def from_crawler(cls, crawler: Crawler) -> "ExportacionPipeline":
        """Crea el pipeline con el ARCHIVO_SALIDA de la configuración.

        Args:
            crawler (Crawler): Crawler que ejecuta la araña.

        Returns:
            ExportacionPipeline: Pipeline configurado.

        Raises:
            NotConfigured: Si la configuración no define ARCHIVO_SALIDA.
        """
        archivo: str = crawler.settings.get("ARCHIVO_SALIDA", "")
        if not archivo:
            raise NotConfigured("Falta ARCHIVO_SALIDA en la configuración.")
        return cls(archivo)

    def open_spider(self, spider: Spider) -> None:
        """Abre el archivo de salida al iniciar la araña."""
        self.__ruta.parent.mkdir(parents=True, exist_ok=True)
        self.__archivo = open(self.__ruta, "wb")
        self.__exportador = JsonLinesItemExporter(self.__archivo,
                                                  encoding="utf-8")
        self.__exportador.start_exporting()

    def close_spider(self, spider: Spider) -> None:
        """Cierra el archivo de salida al terminar la araña."""
        if self.__exportador is not None:
            self.__exportador.finish_exporting()
        if self.__archivo is not None:
            self.__archivo.close()

    def process_item(self, item: Any, spider: Spider) -> Any:
        """Exporta el resultado al archivo.

        Args:
            item (Any): LibroWebItem validado y sin repetir.
            spider (Spider): Araña que lo generó.

        Returns:
            Any: El mismo item.
        """
        self.__exportador.export_item(item)
        return item
