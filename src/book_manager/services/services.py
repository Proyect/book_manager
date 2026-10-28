#@title Escritura de services.py (parte 1)
"""Servicios con la lógica de negocio aplicada a cada operación del sistema.

Los servicios validan las reglas del negocio (unicidad, integridad
referencial, stock suficiente, conversión de monedas) y delegan la
persistencia en los repositorios. Las operaciones que modifican varias
tablas se ejecutan en una única transacción de la base de datos. La URL de
la API de cotizaciones se lee del archivo .env con python-dotenv. El
scraping de precios de la competencia se ejecuta con la araña de Scrapy del
paquete scraper.
"""

import copy
import csv
import datetime
import json
import os
import re
import subprocess
import sys
import tempfile
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Generic, List, Optional, TypeVar

import requests
from bs4 import BeautifulSoup
from dotenv import dotenv_values

from book_manager.database.connection import ConexionDB
from book_manager.entities.entities import (
    CotizacionDolar, Editorial, EntidadBase, Genero, Libro, Moneda, Precio,
    PrecioWeb, Stock, TipoCotizacion)
from book_manager.repositories.repositories import (
    RepositorioCotizacionDolar, RepositorioEditorial, RepositorioGenero,
    RepositorioLibro, RepositorioMoneda, RepositorioPrecio,
    RepositorioPrecioWeb, RepositorioSQL, RepositorioStock,
    RepositorioTipoCotizacion)

T = TypeVar('T', bound=EntidadBase)

RUTA_ENV: Path = Path(__file__).resolve().parents[3] / ".env"
RUTA_EXPORTACION: Path = (
    Path(__file__).resolve().parent.parent / "data" / "exports"
    / "precios.csv"
)
URL_CUSPIDE = "https://cuspide.com/"
TIMEOUT_SEGUNDOS = 10
DIRECTORIO_SRC: Path = Path(__file__).resolve().parents[2]
MODULO_ARANA: str = "book_manager.scraper.ejecutar"
TIMEOUT_SCRAPING_SEGUNDOS = 900
ENCABEZADOS_HTTP = {"User-Agent": "Mozilla/5.0 (BookManager UGR)"}

# Relación entre el campo "casa" de dolarapi.com y el nombre del tipo.
CASAS_DOLAR_API = {"oficial": "Oficial", "blue": "Blue", "bolsa": "MEP",
                   "contadoconliqui": "CCL", "mayorista": "Mayorista",
                   "cripto": "Cripto", "tarjeta": "Tarjeta"}


def cargar_url_api(ruta_env: Path = RUTA_ENV) -> str:
    """Lee la URL de la API de cotizaciones del archivo .env.

    Args:
        ruta_env (Path): Ruta del archivo .env (por defecto, el de la raíz
            del repositorio).

    Returns:
        str: Valor de la variable API_URL.

    Raises:
        ValueError: Si el archivo no existe o no define API_URL.
    """
    if not ruta_env.is_file():
        raise ValueError(f"No se encontró el archivo de configuración "
                         f"{ruta_env}.")
    url: Optional[str] = dotenv_values(ruta_env).get("API_URL")
    if not url or not url.strip():
        raise ValueError(f"El archivo {ruta_env.name} no define API_URL.")
    return url.strip()


class ServicioCRUD(Generic[T]):
    """Lógica común de alta, lectura, modificación y baja de entidades."""

    def __init__(self, repositorio: RepositorioSQL[T]) -> None:
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
    """Lógica de libros: ISBN único y baja en cascada de precios y stock.

    El alta (libro y stock) y la baja (precios, stock y libro) se ejecutan
    en una única transacción: o se completan enteras o no se hace nada.
    """

    def __init__(self, repo: RepositorioLibro, repo_precio: RepositorioPrecio,
                 repo_stock: RepositorioStock,
                 conexion_db: ConexionDB) -> None:
        """Recibe los repositorios de libros, precios y stock y la conexión.

        Args:
            repo (RepositorioLibro): Repositorio de libros.
            repo_precio (RepositorioPrecio): Repositorio de precios.
            repo_stock (RepositorioStock): Repositorio de stock.
            conexion_db (ConexionDB): Conexión con la que se abren las
                transacciones que abarcan varias tablas.
        """
        super().__init__(repo)
        self._repo_precio = repo_precio
        self._repo_stock = repo_stock
        self._conexion_db = conexion_db

    def crear(self, entidad: Libro) -> Libro:
        """Da de alta el libro y le crea el stock en cero (atómico)."""
        with self._conexion_db.transaccion():
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
        """Borra el libro junto con sus precios y su stock (atómico)."""
        self.obtener(id)
        with self._conexion_db.transaccion():
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

    def precio_vigente_en(self, libro_id: int,
                          moneda_id: int) -> Optional[Precio]:
        """Devuelve el precio más reciente del libro en una moneda.

        Args:
            libro_id (int): Id del libro.
            moneda_id (int): Id de la moneda.

        Returns:
            Optional[Precio]: El precio más reciente en esa moneda, o None
            si el libro no tiene precio registrado en ella.
        """
        for precio in self._repo.leer_por_libro(libro_id):
            if precio.moneda.id == moneda_id:
                return precio
        return None
#@title Escritura de services.py (parte 2)


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


class ServicioCotizacionDolar:
    """Lógica de cotizaciones del dólar (manuales y obtenidas por API)."""

    def __init__(self, repo: RepositorioCotizacionDolar,
                 repo_tipo: RepositorioTipoCotizacion,
                 conexion_db: ConexionDB, url_api: str) -> None:
        """Recibe los repositorios, la conexión y la URL de la API.

        Args:
            repo (RepositorioCotizacionDolar): Repositorio de cotizaciones.
            repo_tipo (RepositorioTipoCotizacion): Repositorio de tipos.
            conexion_db (ConexionDB): Conexión para registrar todas las
                cotizaciones descargadas en una sola transacción.
            url_api (str): URL de la API de cotizaciones (leída del .env).

        Raises:
            ValueError: Si la URL no es un texto http(s) válido.
        """
        if not isinstance(url_api, str) or not url_api.startswith(
                ("http://", "https://")):
            raise ValueError("La URL de la API debe empezar con http:// o "
                             "https://.")
        self._repo = repo
        self._repo_tipo = repo_tipo
        self._conexion_db = conexion_db
        self._url_api = url_api

    @property
    def url_api(self) -> str:
        """URL de la API de cotizaciones (solo lectura)."""
        return self._url_api

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

    def obtener_cotizaciones(self) -> List[CotizacionDolar]:
        """Busca, descarga y registra en la base las cotizaciones de la API.

        Returns:
            List[CotizacionDolar]: Cotizaciones registradas (creadas o
            actualizadas).

        Raises:
            ConnectionError: Si no se pudo consultar la API o la respuesta
                no tiene el formato esperado.
            ValueError: Si alguna cotización recibida es inválida (en ese
                caso no se registra ninguna).
        """
        return self._registrar_datos(self._descargar())

    def _descargar(self) -> List[Dict[str, Any]]:
        """Descarga las cotizaciones de la API.

        Returns:
            List[Dict[str, Any]]: Elementos de la respuesta JSON.

        Raises:
            ConnectionError: Si falla la consulta o el formato no es una
                lista JSON.
        """
        try:
            respuesta = requests.get(self._url_api, timeout=TIMEOUT_SEGUNDOS,
                                     headers=ENCABEZADOS_HTTP)
            respuesta.raise_for_status()
            datos = respuesta.json()
        except (requests.RequestException, ValueError) as error:
            raise ConnectionError(
                f"No se pudo consultar la API de cotizaciones: {error}"
            ) from error
        if not isinstance(datos, list):
            raise ConnectionError(
                "La API de cotizaciones devolvió un formato inesperado."
            )
        return datos

    @staticmethod
    def _fecha_de(item: Dict[str, Any]) -> datetime.date:
        """Fecha de una cotización según su campo fechaActualizacion.

        Args:
            item (Dict[str, Any]): Elemento de la respuesta de la API.

        Returns:
            datetime.date: La fecha informada por la API, o la fecha del
            día si el campo falta o no es válido.
        """
        texto: Any = item.get("fechaActualizacion")
        if isinstance(texto, str) and len(texto) >= 10:
            try:
                return datetime.date.fromisoformat(texto[:10])
            except ValueError:
                pass
        return datetime.date.today()

    def _registrar_datos(self, datos: List[Dict[str, Any]]
                         ) -> List[CotizacionDolar]:
        """Convierte los datos de la API en cotizaciones y las registra.

        Las casas sin tipo de cotización asociado se ignoran. Primero se
        construyen todas las cotizaciones y después se registran en una
        sola transacción.

        Args:
            datos (List[Dict[str, Any]]): Elementos descargados de la API.

        Returns:
            List[CotizacionDolar]: Cotizaciones registradas.

        Raises:
            ValueError: Si alguna cotización no pasa las validaciones.
        """
        cotizaciones: List[CotizacionDolar] = []
        for item in datos:
            if not isinstance(item, dict):
                continue
            nombre: Optional[str] = CASAS_DOLAR_API.get(item.get("casa", ""))
            tipo = self._repo_tipo.leer_por_nombre(nombre) if nombre else None
            if tipo is None or item.get("venta") is None:
                continue
            compra: Any = (item["compra"] if item.get("compra") is not None
                           else item["venta"])
            try:
                cotizaciones.append(CotizacionDolar(
                    tipo, self._fecha_de(item), compra, item["venta"]))
            except (TypeError, ValueError) as error:
                raise ValueError(
                    f"Cotización inválida recibida para '{nombre}': {error}"
                ) from error
        with self._conexion_db.transaccion():
            return [self.registrar(cotizacion) for cotizacion in cotizaciones]


class ServicioScraping:
    """Scraping de precios de la competencia y consulta de los resultados.

    Ejecuta la araña CuspideSpider (Scrapy) en un proceso propio, porque el
    motor de Scrapy solo puede iniciarse una vez por proceso, y guarda los
    resultados en la tabla precios_web en una sola transacción.
    """

    def __init__(self, servicio_libro: ServicioLibro,
                 repo: RepositorioPrecioWeb, conexion_db: ConexionDB,
                 timeout_segundos: int = TIMEOUT_SCRAPING_SEGUNDOS) -> None:
        """Recibe el servicio de libros, el repositorio y la conexión.

        Args:
            servicio_libro (ServicioLibro): Para obtener el catálogo.
            repo (RepositorioPrecioWeb): Repositorio de precios web.
            conexion_db (ConexionDB): Conexión para guardar los resultados
                de una ejecución en una sola transacción.
            timeout_segundos (int): Tiempo máximo de una ejecución.
        """
        self._libros = servicio_libro
        self._repo = repo
        self._conexion_db = conexion_db
        self._timeout = timeout_segundos

    def ejecutar_scraping(self, libros: Optional[List[Libro]] = None
                          ) -> List[PrecioWeb]:
        """Busca los libros en la web y guarda los resultados en la base.

        Args:
            libros (Optional[List[Libro]]): Libros a buscar; si es None,
                todo el catálogo.

        Returns:
            List[PrecioWeb]: Resultados guardados.

        Raises:
            ValueError: Si no hay libros para buscar.
            ConnectionError: Si la araña no pudo ejecutarse.
        """
        libros = self._libros.listar() if libros is None else libros
        if not libros:
            raise ValueError("No hay libros en el catálogo para buscar.")
        with tempfile.TemporaryDirectory() as carpeta:
            entrada: Path = Path(carpeta) / "libros.json"
            salida: Path = Path(carpeta) / "resultados.jsonl"
            with open(entrada, "w", encoding="utf-8") as archivo:
                json.dump([{"id": libro.id, "titulo": libro.titulo}
                           for libro in libros], archivo, ensure_ascii=False)
            self._ejecutar_arana(entrada, salida)
            datos: List[Dict[str, Any]] = self._leer_resultados(salida)
        por_id: Dict[int, Libro] = {libro.id: libro for libro in libros}
        ahora: datetime.datetime = datetime.datetime.now()
        resultados: List[PrecioWeb] = [
            self._a_precio_web(dato, por_id[dato["libro_id"]], ahora)
            for dato in datos if dato.get("libro_id") in por_id]
        with self._conexion_db.transaccion():
            return [self._repo.crear(resultado) for resultado in resultados]

    def _ejecutar_arana(self, entrada: Path, salida: Path) -> None:
        """Ejecuta la araña en un proceso nuevo y espera a que termine.

        Args:
            entrada (Path): Archivo JSON con los libros a buscar.
            salida (Path): Archivo JSON Lines para los resultados.

        Raises:
            ConnectionError: Si el proceso termina con error o demora más
                que el tiempo máximo.
        """
        entorno: Dict[str, str] = dict(os.environ)
        entorno["PYTHONPATH"] = os.pathsep.join(
            [str(DIRECTORIO_SRC), entorno.get("PYTHONPATH", "")]).strip(
                os.pathsep)
        try:
            proceso = subprocess.run(
                [sys.executable, "-m", MODULO_ARANA, str(entrada),
                 str(salida)],
                env=entorno, capture_output=True, text=True,
                timeout=self._timeout, check=False)
        except subprocess.TimeoutExpired as error:
            raise ConnectionError(
                "El scraping superó el tiempo máximo de ejecución."
            ) from error
        if proceso.returncode != 0 or not salida.exists():
            detalle: str = "\n".join(proceso.stderr.strip().splitlines()[-5:])
            raise ConnectionError(f"No se pudo ejecutar el scraper: {detalle}")

    @staticmethod
    def _leer_resultados(salida: Path) -> List[Dict[str, Any]]:
        """Lee el archivo JSON Lines que dejó la araña.

        Args:
            salida (Path): Archivo de resultados.

        Returns:
            List[Dict[str, Any]]: Un diccionario por resultado.
        """
        with open(salida, encoding="utf-8") as archivo:
            return [json.loads(linea) for linea in archivo if linea.strip()]

    @staticmethod
    def _a_precio_web(dato: Dict[str, Any], libro: Libro,
                      ahora: datetime.datetime) -> PrecioWeb:
        """Convierte un resultado de la araña en un PrecioWeb.

        Args:
            dato (Dict[str, Any]): Resultado leído del archivo.
            libro (Libro): Libro del catálogo que se buscó.
            ahora (datetime.datetime): Fecha a usar si el resultado no trae
                la fecha de extracción.

        Returns:
            PrecioWeb: El resultado como entidad (sin guardar).
        """
        fecha: datetime.datetime = (
            datetime.datetime.fromisoformat(dato["fecha_extraccion"])
            if dato.get("fecha_extraccion") else ahora)
        return PrecioWeb(
            libro, dato["posicion"], dato["titulo"], dato["precio"],
            dato["url"], fecha, dato.get("autor", ""), dato.get("isbn", ""),
            dato.get("precio_usd"), dato.get("url_imagen", ""),
            dato.get("formas_pago", ""), dato.get("descripcion", ""))

    def ultimos_resultados(self) -> List[PrecioWeb]:
        """Resultados de la extracción más reciente de cada libro."""
        return self._repo.leer_ultima_extraccion()

    def resultados_de(self, libro_id: int) -> List[PrecioWeb]:
        """Todos los resultados obtenidos para un libro."""
        return self._repo.leer_por_libro(libro_id)

    @staticmethod
    def mejor_coincidencia(resultados: List[PrecioWeb]
                           ) -> Optional[PrecioWeb]:
        """Elige, entre los resultados de un libro, el que le corresponde.

        Primero el que tiene el mismo ISBN; si no hay, el primero con el
        mismo título.

        Args:
            resultados (List[PrecioWeb]): Resultados de un mismo libro.

        Returns:
            Optional[PrecioWeb]: El resultado elegido, o None si ninguno
            corresponde al libro.
        """
        for resultado in resultados:
            if resultado.isbn and resultado.isbn == resultado.libro.isbn:
                return resultado
        return next((r for r in resultados if r.es_mismo_libro), None)


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
class LineaBimonetaria:
    """Fila de la lista de precios en pesos y en otra moneda."""

    libro: Libro
    moneda: Moneda
    precio_ars: Optional[float]
    precio_moneda: Optional[float]


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
    """Reportes: inventario, reposición, precios por moneda y competencia."""

    def __init__(self, servicio_libro: ServicioLibro,
                 servicio_precio: ServicioPrecio,
                 servicio_stock: ServicioStock,
                 servicio_cotizacion: ServicioCotizacionDolar,
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

    def precio_en_moneda(self, libro: Libro, moneda: Moneda,
                         tipo: TipoCotizacion) -> Optional[float]:
        """Precio del libro expresado en una moneda.

        Si el libro tiene precio registrado en esa moneda, se usa ese. Si
        la moneda es USD, se convierte el precio en pesos con la venta de la
        última cotización del tipo. En otro caso no hay dato, porque el
        sistema solo tiene cotizaciones del dólar.

        Args:
            libro (Libro): Libro a cotizar.
            moneda (Moneda): Moneda en la que se quiere el precio.
            tipo (TipoCotizacion): Tipo de cotización para convertir USD.

        Returns:
            Optional[float]: El precio en la moneda, o None si no se puede
            calcular.
        """
        if moneda.codigo == "ARS":
            return self.precio_en_pesos(libro, tipo)
        registrado = self._precios.precio_vigente_en(libro.id, moneda.id)
        if registrado is not None:
            return registrado.valor
        if moneda.codigo != "USD":
            return None
        pesos = self.precio_en_pesos(libro, tipo)
        cotizacion = self._cotizaciones.ultima(tipo.id)
        if pesos is None or cotizacion is None:
            return None
        return round(pesos / cotizacion.venta, 2)

    def lista_bimonetaria(self, moneda: Moneda, tipo: TipoCotizacion
                          ) -> List[LineaBimonetaria]:
        """Precio de cada libro en pesos y en la moneda seleccionada.

        Args:
            moneda (Moneda): Segunda moneda de la lista.
            tipo (TipoCotizacion): Tipo de cotización para convertir USD.

        Returns:
            List[LineaBimonetaria]: Una línea por libro.
        """
        return [LineaBimonetaria(libro, moneda,
                                 self.precio_en_pesos(libro, tipo),
                                 self.precio_en_moneda(libro, moneda, tipo))
                for libro in self._libros.listar()]

    def exportar_precios_csv(self, ruta: Path, monedas: List[Moneda],
                             tipo: TipoCotizacion) -> int:
        """Exporta los precios de todos los libros en todas las monedas.

        Escribe una fila por libro con su ISBN, su título y una columna por
        moneda. Las celdas sin dato quedan vacías.

        Args:
            ruta (Path): Archivo CSV de destino (se crea la carpeta).
            monedas (List[Moneda]): Monedas a exportar, una por columna.
            tipo (TipoCotizacion): Tipo de cotización para convertir USD.

        Returns:
            int: Cantidad de libros exportados.

        Raises:
            ValueError: Si no se indica ninguna moneda.
        """
        if not monedas:
            raise ValueError("No hay monedas para exportar.")
        ruta = Path(ruta)
        ruta.parent.mkdir(parents=True, exist_ok=True)
        libros: List[Libro] = self._libros.listar()
        with open(ruta, "w", newline="", encoding="utf-8") as archivo:
            escritor = csv.writer(archivo)
            escritor.writerow(["isbn", "titulo"]
                              + [f"precio_{m.codigo}" for m in monedas])
            for libro in libros:
                valores = [self.precio_en_moneda(libro, moneda, tipo)
                           for moneda in monedas]
                escritor.writerow(
                    [libro.isbn, libro.titulo]
                    + ["" if valor is None else f"{valor:.2f}"
                       for valor in valores])
        return len(libros)

    def libros_para_reponer(self) -> List[Stock]:
        """Libros con stock por debajo del mínimo."""
        return self._stock.para_reponer()

    def comparar_con_competencia(self, tipo: TipoCotizacion
                                 ) -> List[ComparacionPrecio]:
        """Compara el precio propio en pesos con el de Cúspide."""
        return [ComparacionPrecio(libro, self.precio_en_pesos(libro, tipo),
                                  self._competencia.buscar_precio(libro))
                for libro in self._libros.listar()]
