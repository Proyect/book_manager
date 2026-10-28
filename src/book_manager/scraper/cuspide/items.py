"""Items del proyecto Scrapy: datos obtenidos de cada producto."""
import scrapy


class LibroWebItem(scrapy.Item):
    """Resultado de la búsqueda de un libro del catálogo en Cúspide.

    Los campos libro_* identifican el libro del catálogo que se buscó; el
    resto son los datos del producto publicado en la web.
    """

    libro_id = scrapy.Field()
    libro_titulo = scrapy.Field()
    posicion = scrapy.Field()
    titulo = scrapy.Field()
    autor = scrapy.Field()
    isbn = scrapy.Field()
    precio = scrapy.Field()
    precio_usd = scrapy.Field()
    url = scrapy.Field()
    url_imagen = scrapy.Field()
    formas_pago = scrapy.Field()
    descripcion = scrapy.Field()
    fecha_extraccion = scrapy.Field()
