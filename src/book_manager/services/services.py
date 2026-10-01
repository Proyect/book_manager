"""Servicios con la lógica de negocio aplicada a cada operación del sistema.

Los servicios validan las reglas del negocio (unicidad, integridad
referencial, stock suficiente, conversión de monedas) y delegan la
persistencia en los repositorios.
"""

import copy
import datetime
import re
import unicodedata
from dataclasses import dataclass
from typing import Any, Dict, Generic, List, Optional, TypeVar

import requests
from bs4 import BeautifulSoup

from book_manager.entities.entities import (
    CotizacionDolar, Editorial, EntidadBase, Genero, Libro, Moneda, Precio,
    Stock, TipoCotizacion)
from book_manager.repositories.repositories import (
    RepositorioCotizacionDolar, RepositorioCSV, RepositorioEditorial,
    RepositorioGenero, RepositorioLibro, RepositorioMoneda,
    RepositorioPrecio, RepositorioStock, RepositorioTipoCotizacion)

T = TypeVar('T', bound=EntidadBase)

URL_DOLAR_API = "https://dolarapi.com/v1/dolares"
URL_CUSPIDE = "https://cuspide.com/"
TIMEOUT_SEGUNDOS = 10
ENCABEZADOS_HTTP = {"User-Agent": "Mozilla/5.0 (BookManager UGR)"}

# Relación entre el campo "casa" de dolarapi.com y el nombre del tipo.
CASAS_DOLAR_API = {"oficial": "Oficial", "blue": "Blue", "bolsa": "MEP",
                   "contadoconliqui": "CCL", "mayorista": "Mayorista",
                   "cripto": "Cripto", "tarjeta": "Tarjeta"}


class ServicioCRUD(Generic[T]):
    """Lógica común de alta, lectura, modificación y baja de entidades."""

    def __init__(self, repositorio: RepositorioCSV[T]) -> None:
        """Recibe el repositorio de la entidad."""
        self._repo = repositorio

    def listar(self) -> List[T]:
        """Devuelve todas las entidades."""
        return self._repo.leer_todos()

    def obtener(self, id: int) -> T:
        """Devuelve la entidad o lanza ValueError si no existe."""
        entidad = self._repo.leer_por_id(id)
        if entidad is None:
            raise ValueError(f"No existe un registro con ID {id}.")
        return entidad

    def crear(self, entidad: T) -> T:
        """Valida y da de alta una entidad."""
        self._validar_alta(entidad)
        return self._repo.crear(entidad)

    def modificar(self, id: int, cambios: Dict[str, Any]) -> T:
        """Aplica los cambios sobre una copia y, si son válidos, los guarda."""
        entidad = copy.copy(self.obtener(id))
        for campo, valor in cambios.items():
            setattr(entidad, campo, valor)
        self._validar_modificacion(entidad)
        return self._repo.actualizar(entidad)

    def eliminar(self, id: int) -> bool:
        """Da de baja la entidad si no tiene registros dependientes."""
        self._validar_baja(self.obtener(id))
        return self._repo.eliminar(id)

    def _validar_alta(self, entidad: T) -> None:
        """Reglas adicionales para el alta (a redefinir)."""

    def _validar_modificacion(self, entidad: T) -> None:
        """Reglas adicionales para la modificación (a redefinir)."""

    def _validar_baja(self, entidad: T) -> None:
        """Reglas adicionales para la baja (a redefinir)."""


class ServicioGenero(ServicioCRUD[Genero]):
    """Lógica de géneros: nombre único y no borrar si tiene libros."""

    def __init__(self, repo: RepositorioGenero,
                 repo_libro: RepositorioLibro) -> None:
        """Recibe los repositorios de géneros y de libros."""
        super().__init__(repo)
        self._repo_libro = repo_libro

    def _validar_alta(self, entidad: Genero) -> None:
        """Impide géneros con nombre repetido."""
        self._validar_modificacion(entidad)

    def _validar_modificacion(self, entidad: Genero) -> None:
        """Impide géneros con nombre repetido."""
        for genero in self.listar():
            if (genero.nombre.lower() == entidad.nombre.lower()
                    and genero.id != entidad.id):
                raise ValueError("Ya existe un género con ese nombre.")

    def _validar_baja(self, entidad: Genero) -> None:
        """Impide borrar un género asignado a libros."""
        if any(libro.genero.id == entidad.id
               for libro in self._repo_libro.leer_todos()):
            raise ValueError("El género tiene libros asociados.")


class ServicioEditorial(ServicioCRUD[Editorial]):
    """Lógica de editoriales: CUIT único y no borrar si tiene libros."""

    def __init__(self, repo: RepositorioEditorial,
                 repo_libro: RepositorioLibro) -> None:
        """Recibe los repositorios de editoriales y de libros."""
        super().__init__(repo)
        self._repo_libro = repo_libro

    def _validar_alta(self, entidad: Editorial) -> None:
        """Impide editoriales con CUIT repetido."""
        self._validar_modificacion(entidad)

    def _validar_modificacion(self, entidad: Editorial) -> None:
        """Impide editoriales con CUIT repetido."""
        for editorial in self.listar():
            if editorial.cuit == entidad.cuit and editorial.id != entidad.id:
                raise ValueError("Ya existe una editorial con ese CUIT.")

    def _validar_baja(self, entidad: Editorial) -> None:
        """Impide borrar una editorial con libros."""
        if any(libro.editorial.id == entidad.id
               for libro in self._repo_libro.leer_todos()):
            raise ValueError("La editorial tiene libros asociados.")


class ServicioMoneda(ServicioCRUD[Moneda]):
    """Lógica de monedas: código único y no borrar si tiene precios."""

    def __init__(self, repo: RepositorioMoneda,
                 repo_precio: RepositorioPrecio) -> None:
        """Recibe los repositorios de monedas y de precios."""
        super().__init__(repo)
        self._repo_precio = repo_precio

    def _validar_alta(self, entidad: Moneda) -> None:
        """Impide monedas con código repetido."""
        self._validar_modificacion(entidad)

    def _validar_modificacion(self, entidad: Moneda) -> None:
        """Impide monedas con código repetido."""
        for moneda in self.listar():
            if moneda.codigo == entidad.codigo and moneda.id != entidad.id:
                raise ValueError("Ya existe una moneda con ese código.")

    def _validar_baja(self, entidad: Moneda) -> None:
        """Impide borrar una moneda usada en precios."""
        if any(p.moneda.id == entidad.id
               for p in self._repo_precio.leer_todos()):
            raise ValueError("La moneda está usada en precios.")


class ServicioTipoCotizacion(ServicioCRUD[TipoCotizacion]):
    """Lógica de tipos de cotización: nombre único, baja sin histórico."""

    def __init__(self, repo: RepositorioTipoCotizacion,
                 repo_cotizacion: RepositorioCotizacionDolar) -> None:
        """Recibe los repositorios de tipos y de cotizaciones."""
        super().__init__(repo)
        self._repo_cotizacion = repo_cotizacion

    def _validar_alta(self, entidad: TipoCotizacion) -> None:
        """Impide tipos con nombre repetido."""
        self._validar_modificacion(entidad)

    def _validar_modificacion(self, entidad: TipoCotizacion) -> None:
        """Impide tipos con nombre repetido."""
        for tipo in self.listar():
            if (tipo.nombre.lower() == entidad.nombre.lower()
                    and tipo.id != entidad.id):
                raise ValueError("Ya existe un tipo con ese nombre.")

    def _validar_baja(self, entidad: TipoCotizacion) -> None:
        """Impide borrar un tipo con cotizaciones registradas."""
        if self._repo_cotizacion.leer_historico_por_tipo(entidad.id):
            raise ValueError("El tipo tiene cotizaciones registradas.")


class ServicioLibro(ServicioCRUD[Libro]):
    """Lógica de libros: ISBN único y baja en cascada de precios y stock."""

    def __init__(self, repo: RepositorioLibro, repo_precio: RepositorioPrecio,
                 repo_stock: RepositorioStock) -> None:
        """Recibe los repositorios de libros, precios y stock."""
        super().__init__(repo)
        self._repo_precio = repo_precio
        self._repo_stock = repo_stock

    def crear(self, entidad: Libro) -> Libro:
        """Da de alta el libro y le crea el stock en cero."""
        libro = super().crear(entidad)
        self._repo_stock.crear(Stock(libro))
        return libro

    def _validar_alta(self, entidad: Libro) -> None:
        """Impide libros con ISBN repetido."""
        self._validar_modificacion(entidad)

    def _validar_modificacion(self, entidad: Libro) -> None:
        """Impide libros con ISBN repetido."""
        for libro in self.listar():
            if libro.isbn == entidad.isbn and libro.id != entidad.id:
                raise ValueError("Ya existe un libro con ese ISBN.")

    def eliminar(self, id: int) -> bool:
        """Borra el libro junto con sus precios y su stock."""
        self.obtener(id)
        for precio in self._repo_precio.leer_por_libro(id):
            self._repo_precio.eliminar(precio.id)
        self._repo_stock.eliminar(id)
        return self._repo.eliminar(id)

    def buscar(self, texto: str) -> List[Libro]:
        """Busca libros por título, autor o ISBN."""
        texto = texto.lower()
        return [libro for libro in self.listar()
                if texto in libro.titulo.lower()
                or texto in libro.autor.lower()
                or texto in libro.isbn.lower()]


class ServicioPrecio(ServicioCRUD[Precio]):
    """Lógica de precios."""

    def __init__(self, repo: RepositorioPrecio) -> None:
        """Recibe el repositorio de precios."""
        super().__init__(repo)

    def _validar_alta(self, entidad: Precio) -> None:
        """Impide dos precios del mismo libro, moneda y fecha."""
        self._validar_modificacion(entidad)

    def _validar_modificacion(self, entidad: Precio) -> None:
        """Impide dos precios del mismo libro, moneda y fecha."""
        for precio in self._repo.leer_por_libro(entidad.libro.id):
            if (precio.moneda.id == entidad.moneda.id
                    and precio.fecha == entidad.fecha
                    and precio.id != entidad.id):
                raise ValueError("El libro ya tiene precio en esa moneda "
                                 "y fecha.")

    def precio_vigente(self, libro_id: int) -> Optional[Precio]:
        """Devuelve el precio más reciente del libro."""
        precios = self._repo.leer_por_libro(libro_id)
        return precios[0] if precios else None


class ServicioStock:
    """Lógica de stock: altas, ingresos y egresos de unidades."""

    def __init__(self, repo: RepositorioStock,
                 repo_libro: RepositorioLibro) -> None:
        """Recibe los repositorios de stock y de libros."""
        self._repo = repo
        self._repo_libro = repo_libro

    def listar(self) -> List[Stock]:
        """Devuelve el stock de todos los libros."""
        return self._repo.leer_todos()

    def obtener(self, libro_id: int) -> Stock:
        """Devuelve el stock del libro o lanza ValueError."""
        stock = self._repo.leer_por_libro(libro_id)
        if stock is None:
            raise ValueError(f"No hay stock registrado para el libro "
                             f"{libro_id}.")
        return stock

    def crear(self, stock: Stock) -> Stock:
        """Registra el stock de un libro existente."""
        if self._repo_libro.leer_por_id(stock.libro_id) is None:
            raise ValueError("El libro no existe.")
        return self._repo.crear(stock)

    def modificar(self, libro_id: int, cantidad: int,
                  stock_minimo: int) -> Stock:
        """Fija cantidad y stock mínimo de un libro."""
        stock = copy.copy(self.obtener(libro_id))
        stock.cantidad = cantidad
        stock.stock_minimo = stock_minimo
        return self._repo.actualizar(stock)

    def ingresar(self, libro_id: int, unidades: int) -> Stock:
        """Suma unidades recibidas del proveedor."""
        stock = copy.copy(self.obtener(libro_id))
        stock.agregar(unidades)
        return self._repo.actualizar(stock)

    def vender(self, libro_id: int, unidades: int) -> Stock:
        """Descuenta unidades vendidas (valida stock suficiente)."""
        stock = copy.copy(self.obtener(libro_id))
        stock.retirar(unidades)
        return self._repo.actualizar(stock)

    def eliminar(self, libro_id: int) -> bool:
        """Borra el registro de stock del libro."""
        return self._repo.eliminar(libro_id)

    def para_reponer(self) -> List[Stock]:
        """Libros cuya cantidad está por debajo del stock mínimo."""
        return [s for s in self.listar() if s.requiere_reposicion]


class ServicioCotizacion:
    """Lógica de cotizaciones del dólar (manuales y en línea)."""

    def __init__(self, repo: RepositorioCotizacionDolar,
                 repo_tipo: RepositorioTipoCotizacion) -> None:
        """Recibe los repositorios de cotizaciones y de tipos."""
        self._repo = repo
        self._repo_tipo = repo_tipo

    def listar(self) -> List[CotizacionDolar]:
        """Devuelve todas las cotizaciones registradas."""
        return self._repo.leer_todos()

    def historico(self, tipo_id: int) -> List[CotizacionDolar]:
        """Devuelve el histórico de un tipo ordenado por fecha."""
        return self._repo.leer_historico_por_tipo(tipo_id)

    def obtener(self, tipo_id: int, fecha: datetime.date) -> CotizacionDolar:
        """Devuelve la cotización o lanza ValueError."""
        cotizacion = self._repo.leer_por_tipo_y_fecha(tipo_id, fecha)
        if cotizacion is None:
            raise ValueError("No existe una cotización para ese tipo y fecha.")
        return cotizacion

    def crear(self, cotizacion: CotizacionDolar) -> CotizacionDolar:
        """Registra una cotización manual."""
        return self._repo.crear(cotizacion)

    def modificar(self, tipo_id: int, fecha: datetime.date, compra: float,
                  venta: float) -> CotizacionDolar:
        """Cambia los valores de compra y venta."""
        actual = self.obtener(tipo_id, fecha)
        nueva = CotizacionDolar(actual.tipo, fecha, compra, venta)
        return self._repo.actualizar(nueva)

    def eliminar(self, tipo_id: int, fecha: datetime.date) -> bool:
        """Borra una cotización."""
        return self._repo.eliminar(tipo_id, fecha)

    def ultima(self, tipo_id: int) -> Optional[CotizacionDolar]:
        """Devuelve la cotización más reciente de un tipo."""
        historico = self.historico(tipo_id)
        return historico[-1] if historico else None

    def registrar(self, cotizacion: CotizacionDolar) -> CotizacionDolar:
        """Crea la cotización o la actualiza si ya existe para esa fecha."""
        if self._repo.leer_por_tipo_y_fecha(cotizacion.tipo_id,
                                            cotizacion.fecha):
            return self._repo.actualizar(cotizacion)
        return self._repo.crear(cotizacion)

    def actualizar_desde_api(self) -> List[CotizacionDolar]:
        """Consulta dolarapi.com y registra las cotizaciones del día.

        Raises:
            ConnectionError: Si no se pudo obtener la información.
        """
        try:
            respuesta = requests.get(URL_DOLAR_API, timeout=TIMEOUT_SEGUNDOS,
                                     headers=ENCABEZADOS_HTTP)
            respuesta.raise_for_status()
            datos = respuesta.json()
        except (requests.RequestException, ValueError) as error:
            raise ConnectionError(
                f"No se pudo consultar la cotización: {error}") from error
        registradas = []
        hoy = datetime.date.today()
        for item in datos:
            nombre = CASAS_DOLAR_API.get(item.get("casa", ""))
            tipo = self._repo_tipo.leer_por_nombre(nombre) if nombre else None
            if tipo is None or not item.get("venta"):
                continue
            compra = item.get("compra") or item["venta"]
            registradas.append(self.registrar(
                CotizacionDolar(tipo, hoy, compra, item["venta"])))
        return registradas


@dataclass
class LineaInventario:
    """Fila del reporte de inventario valorizado."""

    libro: Libro
    precio: Optional[Precio]
    precio_ars: Optional[float]
    cantidad: int

    @property
    def subtotal_ars(self) -> float:
        """Valor en pesos de las unidades en stock."""
        return (self.precio_ars or 0.0) * self.cantidad


@dataclass
class ComparacionPrecio:
    """Fila del reporte de comparación con la competencia."""

    libro: Libro
    precio_propio_ars: Optional[float]
    precio_competencia_ars: Optional[float]

    @property
    def diferencia_porcentual(self) -> Optional[float]:
        """Diferencia del precio propio respecto de la competencia (%)."""
        if not self.precio_propio_ars or not self.precio_competencia_ars:
            return None
        return round((self.precio_propio_ars / self.precio_competencia_ars
                      - 1) * 100, 2)


class ServicioCompetencia:
    """Consulta de precios en la web de la competencia (Cúspide)."""

    @staticmethod
    def _a_numero(texto: str) -> Optional[float]:
        """Convierte un importe como '$ 25.999,00' a 25999.0."""
        limpio = re.sub(r"[^\d,]", "", texto).replace(",", ".")
        try:
            return float(limpio)
        except ValueError:
            return None

    @staticmethod
    def _normalizar(texto: str) -> str:
        """Pasa a mayúsculas y quita acentos para comparar títulos."""
        sin_acentos = unicodedata.normalize("NFKD", texto)
        return "".join(c for c in sin_acentos
                       if not unicodedata.combining(c)).upper().strip()

    def _importe(self, contenedor: Any) -> Optional[float]:
        """Precio de un producto (si está en oferta, el precio rebajado)."""
        precio = contenedor.select_one(".price")
        if precio is None:
            return None
        importe = (precio.select_one("ins .woocommerce-Price-amount")
                   or precio.select_one(".woocommerce-Price-amount"))
        return self._a_numero(importe.get_text()) if importe else None

    def _buscar(self, termino: str) -> Optional[BeautifulSoup]:
        """Ejecuta la búsqueda en el sitio y devuelve el HTML parseado."""
        try:
            respuesta = requests.get(
                URL_CUSPIDE, params={"s": termino, "post_type": "product"},
                headers=ENCABEZADOS_HTTP, timeout=TIMEOUT_SEGUNDOS)
            respuesta.raise_for_status()
        except requests.RequestException:
            return None
        return BeautifulSoup(respuesta.text, "html.parser")

    def buscar_precio(self, libro: Libro) -> Optional[float]:
        """Devuelve el menor precio en pesos del libro en Cúspide (o None).

        Primero busca por ISBN; si no hay resultados, busca por título y
        toma los productos cuyo título contiene el del libro.
        """
        sopa = self._buscar(libro.isbn)
        if sopa is None:
            return None
        resumen = sopa.select_one(".product .summary")
        if resumen is not None:
            return self._importe(resumen)
        productos = sopa.select(".type-product")
        if productos:
            return self._importe(productos[0])
        sopa = self._buscar(libro.titulo)
        if sopa is None:
            return None
        buscado = self._normalizar(libro.titulo)
        precios = []
        for producto in sopa.select(".type-product"):
            titulo = producto.select_one(".woocommerce-loop-product__title")
            if titulo and buscado in self._normalizar(titulo.get_text()):
                importe = self._importe(producto)
                if importe:
                    precios.append(importe)
        return min(precios) if precios else None


class ServicioReportes:
    """Reportes: inventario, reposición, cotizaciones y competencia."""

    def __init__(self, servicio_libro: ServicioLibro,
                 servicio_precio: ServicioPrecio,
                 servicio_stock: ServicioStock,
                 servicio_cotizacion: ServicioCotizacion,
                 servicio_competencia: ServicioCompetencia) -> None:
        """Recibe los servicios que se combinan en los reportes."""
        self._libros = servicio_libro
        self._precios = servicio_precio
        self._stock = servicio_stock
        self._cotizaciones = servicio_cotizacion
        self._competencia = servicio_competencia

    def convertir_a_pesos(self, precio: Precio,
                          tipo: TipoCotizacion) -> Optional[float]:
        """Expresa un precio en pesos según la última cotización del tipo."""
        if precio.moneda.codigo == "ARS":
            return precio.valor
        if precio.moneda.codigo != "USD":
            return None
        cotizacion = self._cotizaciones.ultima(tipo.id)
        if cotizacion is None:
            return None
        return cotizacion.convertir_a_pesos(precio.valor)

    def precio_en_pesos(self, libro: Libro,
                        tipo: TipoCotizacion) -> Optional[float]:
        """Precio vigente del libro convertido a pesos."""
        precio = self._precios.precio_vigente(libro.id)
        return self.convertir_a_pesos(precio, tipo) if precio else None

    def inventario_valorizado(self, tipo: TipoCotizacion
                              ) -> List[LineaInventario]:
        """Stock de cada libro valorizado en pesos."""
        cantidades = {s.libro_id: s.cantidad for s in self._stock.listar()}
        lineas = []
        for libro in self._libros.listar():
            cantidad = cantidades.get(libro.id, 0)
            precio = self._precios.precio_vigente(libro.id)
            lineas.append(LineaInventario(
                libro, precio, self.precio_en_pesos(libro, tipo), cantidad))
        return lineas

    def libros_para_reponer(self) -> List[Stock]:
        """Libros con stock por debajo del mínimo."""
        return self._stock.para_reponer()

    def comparar_con_competencia(self, tipo: TipoCotizacion
                                 ) -> List[ComparacionPrecio]:
        """Compara el precio propio en pesos con el de Cúspide."""
        return [ComparacionPrecio(libro, self.precio_en_pesos(libro, tipo),
                                  self._competencia.buscar_precio(libro))
                for libro in self._libros.listar()]
