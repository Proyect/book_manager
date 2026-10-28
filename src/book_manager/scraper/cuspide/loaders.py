"""Loaders del proyecto Scrapy: limpieza de los datos de cada producto.

LibroWebLoader aplica a cada campo los procesadores de entrada (limpiar
textos, convertir importes) y de salida (tomar el primer valor o unir
varios) antes de armar el LibroWebItem.
"""
import re
from typing import Optional

from itemloaders.processors import Join, MapCompose, TakeFirst
from scrapy.loader import ItemLoader

from book_manager.scraper.cuspide.items import LibroWebItem


def limpiar_texto(texto: str) -> Optional[str]:
    """Quita espacios repetidos y en los extremos; None si queda vacío.

    Args:
        texto (str): Texto extraído del HTML.

    Returns:
        Optional[str]: Texto limpio, o None para descartarlo.
    """
    limpio: str = " ".join(str(texto).split())
    return limpio or None


def importe_a_numero(texto: str) -> Optional[float]:
    """Convierte un importe con formato argentino a número.

    Args:
        texto (str): Importe como '$ 48.500,00' o '31,09'.

    Returns:
        Optional[float]: El importe (48500.0, 31.09), o None si el texto
        no tiene un número válido.
    """
    digitos: str = re.sub(r"[^\d,]", "", str(texto)).replace(",", ".")
    try:
        return float(digitos)
    except ValueError:
        return None


def solo_isbn(texto: str) -> Optional[str]:
    """Deja solo los dígitos (y la X final) de un ISBN.

    Args:
        texto (str): ISBN extraído del HTML.

    Returns:
        Optional[str]: ISBN limpio, o None si queda vacío.
    """
    limpio: str = re.sub(r"[^\dXx]", "", str(texto)).upper()
    return limpio or None


def quitar_vineta(texto: str) -> Optional[str]:
    """Quita la viñeta '>' con que el sitio lista las formas de pago.

    Args:
        texto (str): Línea de la lista de formas de pago.

    Returns:
        Optional[str]: La forma de pago sin la viñeta, o None si está vacía.
    """
    return limpiar_texto(str(texto).lstrip(">  "))


class LibroWebLoader(ItemLoader):
    """Loader de LibroWebItem: un valor por campo, salvo los textos largos.

    Las formas de pago se unen con ' | ' y los párrafos de la descripción
    con un espacio.
    """

    default_item_class = LibroWebItem
    default_input_processor = MapCompose(limpiar_texto)
    default_output_processor = TakeFirst()

    precio_in = MapCompose(importe_a_numero)
    precio_usd_in = MapCompose(importe_a_numero)
    isbn_in = MapCompose(solo_isbn)
    posicion_in = MapCompose(int)
    libro_id_in = MapCompose(int)
    formas_pago_in = MapCompose(quitar_vineta)
    formas_pago_out = Join(" | ")
    descripcion_out = Join(" ")
