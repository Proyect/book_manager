"""Araña CuspideSpider: precios y datos de los libros del catálogo.

Por cada libro del catálogo busca su título en el sitio de Cúspide, toma los
10 primeros resultados de la búsqueda y, de la página de cada producto,
obtiene el precio, la URL de la imagen, las formas de pago con su precio y
la descripción detallada. Solo se buscan los libros del catálogo, que
recibe en un archivo JSON.
"""
import datetime
import json
from pathlib import Path
from typing import Any, AsyncIterator, Dict, Iterator, List
from urllib.parse import urlencode

import scrapy
from scrapy.http import Response

from book_manager.scraper.cuspide.loaders import LibroWebLoader

URL_BUSQUEDA: str = "https://cuspide.com/"
MAX_RESULTADOS: int = 10

# Selectores de la página de búsqueda y de la página de cada producto.
SEL_RESULTADOS: str = ".products .type-product .product-title a::attr(href)"
SEL_PAGINA_PRODUCTO: str = ".product-info h1.product_title"
SEL_TITULO: str = ".product-info h1.product_title::text"
SEL_AUTOR: str = ".product-info > span a::text"
SEL_ISBN: str = ".product_meta .sku::text"
SEL_PRECIOS: str = ".product-info p.price bdi"
XPATH_PRECIO_USD: str = (
    "//div[contains(@class, 'product-info')]"
    "/span[contains(text(), 'U$s')]/span/text()")
SEL_IMAGEN: str = ".product-gallery img.wp-post-image"
XPATH_FORMAS_PAGO: str = (
    "//div[@id='contentPaymentsPopUpArg']//li"
    " | //div[contains(@class, 'pum-content')]"
    "[.//*[contains(text(), 'Medios de pago')]]"
    "//p[starts-with(normalize-space(.), '>')]")
LARGO_MAXIMO_DETALLE_PAGO: int = 60
SEL_DESCRIPCION: str = "p.livriz-text-synopsis ::text"
SEL_DESCRIPCION_ALTERNATIVA: str = "#tab-description ::text"


class CuspideSpider(scrapy.Spider):
    """Busca en Cúspide los libros del catálogo y obtiene sus datos."""

    name = "cuspide"
    allowed_domains = ["cuspide.com"]

    def __init__(self, archivo_libros: str = "", *args: Any,
                 **kwargs: Any) -> None:
        """Lee los libros a buscar.

        Args:
            archivo_libros (str): Archivo JSON con una lista de libros, cada
                uno con 'id' y 'titulo'.

        Raises:
            ValueError: Si no se indica el archivo o no tiene libros.
        """
        super().__init__(*args, **kwargs)
        if not archivo_libros:
            raise ValueError("Falta el archivo con los libros a buscar.")
        with open(Path(archivo_libros), encoding="utf-8") as archivo:
            self.libros: List[Dict[str, Any]] = json.load(archivo)
        if not self.libros:
            raise ValueError("No hay libros para buscar.")
        self.fecha_extraccion: str = datetime.datetime.now().isoformat(
            sep=" ", timespec="seconds")

    @staticmethod
    def url_busqueda(titulo: str) -> str:
        """URL de la búsqueda de un título en el sitio.

        Args:
            titulo (str): Título del libro.

        Returns:
            str: URL de la búsqueda de productos.
        """
        parametros: str = urlencode({"s": titulo, "post_type": "product"})
        return f"{URL_BUSQUEDA}?{parametros}"

    def start_requests(self) -> Iterator[scrapy.Request]:
        """Una búsqueda por cada libro del catálogo."""
        for libro in self.libros:
            yield scrapy.Request(self.url_busqueda(libro["titulo"]),
                                 callback=self.parse_busqueda,
                                 cb_kwargs={"libro": libro})

    async def start(self) -> AsyncIterator[scrapy.Request]:
        """Punto de inicio de Scrapy 2.13+ (usa start_requests)."""
        for pedido in self.start_requests():
            yield pedido

    def parse_busqueda(self, response: Response,
                       libro: Dict[str, Any]) -> Iterator[Any]:
        """Sigue los 10 primeros resultados de la búsqueda de un libro.

        Si la búsqueda tiene un único resultado, el sitio muestra
        directamente la página del producto.

        Args:
            response (Response): Página de resultados de la búsqueda.
            libro (Dict[str, Any]): Libro del catálogo que se buscó.

        Yields:
            Any: Un pedido por producto, o el item si ya es la página del
            producto.
        """
        if response.css(SEL_PAGINA_PRODUCTO):
            yield self.parse_producto(response, libro, 1)
            return
        enlaces: List[str] = response.css(SEL_RESULTADOS).getall()
        if not enlaces:
            self.logger.info("Sin resultados para '%s'", libro["titulo"])
        for posicion, enlace in enumerate(enlaces[:MAX_RESULTADOS], start=1):
            yield response.follow(
                enlace, callback=self.parse_producto,
                cb_kwargs={"libro": libro, "posicion": posicion})

    @staticmethod
    def forma_de_pago(texto: str, precio_texto: str) -> str:
        """Arma el texto de una forma de pago con su precio.

        Del texto del sitio se toma el nombre del medio de pago (lo que está
        antes de los dos puntos) y, si es breve, su detalle (por ejemplo,
        las tarjetas aceptadas).

        Args:
            texto (str): Línea de la lista de medios de pago del sitio.
            precio_texto (str): Precio del producto tal como lo muestra.

        Returns:
            str: Por ejemplo 'Tarjetas de créditos (Visa, Mastercard y
            American Express): $ 48.500,00'.
        """
        nombre, _, detalle = " ".join(texto.split()).lstrip("> ").partition(
            ":")
        detalle = detalle.strip().rstrip(".")
        if detalle and len(detalle) <= LARGO_MAXIMO_DETALLE_PAGO:
            nombre = f"{nombre} ({detalle})"
        return f"{nombre}: {' '.join(precio_texto.split())}"

    def parse_producto(self, response: Response, libro: Dict[str, Any],
                       posicion: int) -> Any:
        """Obtiene los datos de la página de un producto.

        Args:
            response (Response): Página del producto.
            libro (Dict[str, Any]): Libro del catálogo que se buscó.
            posicion (int): Posición del producto en la búsqueda.

        Returns:
            Any: LibroWebItem con los datos del producto.
        """
        cargador = LibroWebLoader(response=response)
        cargador.add_value("libro_id", libro["id"])
        cargador.add_value("libro_titulo", libro["titulo"])
        cargador.add_value("posicion", posicion)
        cargador.add_value("url", response.url)
        cargador.add_value("fecha_extraccion", self.fecha_extraccion)
        cargador.add_css("titulo", SEL_TITULO)
        cargador.add_css("autor", SEL_AUTOR)
        cargador.add_css("isbn", SEL_ISBN)
        cargador.add_xpath("precio_usd", XPATH_PRECIO_USD)

        # Si el producto está en oferta hay dos precios: el último es el
        # precio con descuento, que es el que se paga.
        precios: List[str] = [
            nodo.xpath("string()").get()
            for nodo in response.css(SEL_PRECIOS)]
        precio_texto: str = precios[-1] if precios else ""
        cargador.add_value("precio", precio_texto)

        imagen = response.css(SEL_IMAGEN)
        url_imagen: str = (imagen.attrib.get("data-large_image")
                           or imagen.attrib.get("src", "")) if imagen else ""
        if url_imagen:
            cargador.add_value("url_imagen", response.urljoin(url_imagen))

        for forma in response.xpath(XPATH_FORMAS_PAGO):
            cargador.add_value("formas_pago", self.forma_de_pago(
                forma.xpath("string()").get(), precio_texto))

        descripcion: List[str] = (response.css(SEL_DESCRIPCION).getall()
                                  or response.css(
                                      SEL_DESCRIPCION_ALTERNATIVA).getall())
        cargador.add_value("descripcion", descripcion)
        return cargador.load_item()
