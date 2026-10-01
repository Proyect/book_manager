"""Repositorios responsables de la persistencia de datos (CRUD por entidad).

Cada repositorio mantiene sus registros en memoria y los persiste en un
archivo CSV propio dentro de la carpeta ``data`` del paquete. Las relaciones
entre entidades se guardan por ID y se resuelven al leer el archivo usando
los repositorios de las entidades relacionadas.
"""

import abc
import csv
import datetime
from pathlib import Path
from typing import Any, Dict, Generic, List, Optional, Tuple, TypeVar

from book_manager.entities.entities import (
    CotizacionDolar, Editorial, EntidadBase, Genero, Libro, Moneda, Precio,
    Stock, TipoCotizacion)

T = TypeVar('T', bound=EntidadBase)

DIRECTORIO_DATOS = Path(__file__).resolve().parent.parent / "data"


class IRepositorio(abc.ABC, Generic[T]):
    """Interfaz para repositorios de entidades con operaciones CRUD básicas."""

    @abc.abstractmethod
    def crear(self, entidad: T) -> T:
        """Crea una nueva entidad en el repositorio.

        Args:
            entidad (T): La entidad a crear.

        Returns:
            T: La entidad creada.

        Raises:
            ValueError: Si ya existe una entidad con el mismo ID.
        """

    @abc.abstractmethod
    def leer_por_id(self, id: int) -> Optional[T]:
        """Lee una entidad del repositorio por su ID.

        Args:
            id (int): El ID de la entidad a leer.

        Returns:
            Optional[T]: La entidad si se encuentra, None en caso contrario.
        """

    @abc.abstractmethod
    def leer_todos(self) -> List[T]:
        """Lee todas las entidades del repositorio.

        Returns:
            List[T]: Una lista de todas las entidades.
        """

    @abc.abstractmethod
    def actualizar(self, entidad: T) -> T:
        """Actualiza una entidad existente en el repositorio.

        Args:
            entidad (T): La entidad a actualizar (debe tener un ID existente).

        Returns:
            T: La entidad actualizada.

        Raises:
            ValueError: Si no se encuentra la entidad para actualizar.
        """

    @abc.abstractmethod
    def eliminar(self, id: int) -> bool:
        """Elimina una entidad del repositorio por su ID.

        Args:
            id (int): El ID de la entidad a eliminar.

        Returns:
            bool: True si la entidad fue eliminada, False si no se encontró.
        """


class IRepositorioStock(abc.ABC):
    """Interfaz para repositorios del tipo Stock."""

    @abc.abstractmethod
    def crear(self, stock: Stock) -> Stock:
        """Crea un nuevo registro de stock.

        Args:
            stock (Stock): El objeto Stock a crear.

        Returns:
            Stock: El objeto Stock creado.

        Raises:
            ValueError: Si ya existe un registro de stock para el mismo libro.
        """

    @abc.abstractmethod
    def leer_por_libro(self, libro_id: int) -> Optional['Stock']:
        """Lee un registro de stock por ID de libro.

        Args:
            libro_id (int): El ID del libro asociado al stock.

        Returns:
            Optional[Stock]: El objeto Stock si se encuentra, None en caso
            contrario.
        """

    @abc.abstractmethod
    def actualizar(self, stock: 'Stock') -> 'Stock':
        """Actualiza un registro de stock existente.

        Args:
            stock (Stock): El objeto Stock a actualizar.

        Returns:
            Stock: El objeto Stock actualizado.

        Raises:
            ValueError: Si no se encuentra el stock para actualizar.
        """

    @abc.abstractmethod
    def eliminar(self, libro_id: int) -> bool:
        """Elimina un registro de stock por ID de libro.

        Args:
            libro_id (int): El ID del libro asociado al stock a eliminar.

        Returns:
            bool: True si el stock fue eliminado, False si no se encontró.
        """


class IRepositorioCotizacionDolar(abc.ABC):
    """Interfaz para repositorios del tipo RepositorioCotizacionDolar."""

    @abc.abstractmethod
    def crear(self, cotizacion: 'CotizacionDolar') -> 'CotizacionDolar':
        """Crea una nueva cotización de dólar.

        Args:
            cotizacion (CotizacionDolar): El objeto CotizacionDolar a crear.

        Returns:
            CotizacionDolar: El objeto CotizacionDolar creado.

        Raises:
            ValueError: Si ya existe una cotización para el mismo tipo y fecha.
        """

    @abc.abstractmethod
    def leer_por_tipo_y_fecha(self, tipo_id: int, fecha: datetime.date
                              ) -> Optional['CotizacionDolar']:
        """Lee una cotización de dólar por tipo y fecha.

        Args:
            tipo_id (int): El ID del tipo de cotización.
            fecha (datetime.date): La fecha de la cotización.

        Returns:
            Optional[CotizacionDolar]: La cotización si se encuentra, None en
            caso contrario.
        """

    @abc.abstractmethod
    def leer_historico_por_tipo(self, tipo_id: int
                                ) -> List['CotizacionDolar']:
        """Lee el histórico de cotizaciones para un tipo específico.

        Args:
            tipo_id (int): El ID del tipo de cotización.

        Returns:
            List[CotizacionDolar]: Cotizaciones históricas del tipo dado.
        """

    @abc.abstractmethod
    def actualizar(self, cotizacion: 'CotizacionDolar'
                   ) -> 'CotizacionDolar':
        """Actualiza una cotización de dólar existente.

        Args:
            cotizacion (CotizacionDolar): El objeto CotizacionDolar a
                actualizar.

        Returns:
            CotizacionDolar: El objeto CotizacionDolar actualizado.
        """

    @abc.abstractmethod
    def eliminar(self, tipo_id: int, fecha: datetime.date) -> bool:
        """Elimina una cotización de dólar por tipo y fecha.

        Args:
            tipo_id (int): El ID del tipo de cotización.
            fecha (datetime.date): La fecha de la cotización a eliminar.

        Returns:
            bool: True si la cotización fue eliminada, False si no se
            encontró.
        """


class ArchivoCSV:
    """Lectura y escritura de un archivo CSV con encabezado."""

    def __init__(self, nombre: str, campos: List[str],
                 directorio: Path = DIRECTORIO_DATOS) -> None:
        """Define el archivo y sus columnas."""
        self._ruta = directorio / nombre
        self._campos = campos

    @property
    def ruta(self) -> Path:
        """Ruta completa del archivo."""
        return self._ruta

    def leer(self) -> List[Dict[str, str]]:
        """Devuelve las filas del archivo (lista vacía si no existe)."""
        if not self._ruta.exists():
            return []
        with open(self._ruta, newline="", encoding="utf-8") as archivo:
            return list(csv.DictReader(archivo))

    def escribir(self, filas: List[Dict[str, Any]]) -> None:
        """Sobrescribe el archivo con las filas indicadas."""
        self._ruta.parent.mkdir(parents=True, exist_ok=True)
        with open(self._ruta, "w", newline="", encoding="utf-8") as archivo:
            escritor = csv.DictWriter(archivo, fieldnames=self._campos)
            escritor.writeheader()
            escritor.writerows(filas)


class RepositorioCSV(IRepositorio[T]):
    """Repositorio genérico con IDs autoincrementales persistido en CSV."""

    NOMBRE_ARCHIVO: str = ""
    CAMPOS: List[str] = []

    def __init__(self, directorio: Path = DIRECTORIO_DATOS) -> None:
        """Carga en memoria los registros guardados en el archivo."""
        self._archivo = ArchivoCSV(self.NOMBRE_ARCHIVO, self.CAMPOS,
                                   directorio)
        self._entidades: Dict[int, T] = {}
        for fila in self._archivo.leer():
            entidad = self._desde_fila(fila)
            self._entidades[entidad.id] = entidad

    @abc.abstractmethod
    def _desde_fila(self, fila: Dict[str, str]) -> T:
        """Construye la entidad a partir de una fila del CSV."""

    def _guardar(self) -> None:
        """Persiste todas las entidades en el archivo."""
        self._archivo.escribir([e.to_dict() for e in self.leer_todos()])

    def _proximo_id(self) -> int:
        """Devuelve el siguiente ID libre."""
        return max(self._entidades, default=0) + 1

    def crear(self, entidad: T) -> T:
        """Agrega la entidad asignándole un ID si no lo tiene."""
        if entidad.id is None:
            entidad.id = self._proximo_id()
        elif entidad.id in self._entidades:
            raise ValueError(f"Ya existe una entidad con ID {entidad.id}.")
        self._entidades[entidad.id] = entidad
        self._guardar()
        return entidad

    def leer_por_id(self, id: int) -> Optional[T]:
        """Busca una entidad por su ID."""
        return self._entidades.get(id)

    def leer_todos(self) -> List[T]:
        """Devuelve todas las entidades ordenadas por ID."""
        return [self._entidades[i] for i in sorted(self._entidades)]

    def actualizar(self, entidad: T) -> T:
        """Reemplaza la entidad con el mismo ID."""
        if entidad.id not in self._entidades:
            raise ValueError(f"No existe una entidad con ID {entidad.id}.")
        self._entidades[entidad.id] = entidad
        self._guardar()
        return entidad

    def eliminar(self, id: int) -> bool:
        """Borra la entidad con el ID indicado."""
        if self._entidades.pop(id, None) is None:
            return False
        self._guardar()
        return True

    def vaciar(self) -> None:
        """Elimina todos los registros (usado por la carga inicial)."""
        self._entidades.clear()
        self._guardar()


class RepositorioGenero(RepositorioCSV[Genero]):
    """Persistencia de géneros literarios."""

    NOMBRE_ARCHIVO = "generos.csv"
    CAMPOS = ["id", "nombre", "descripcion"]

    def _desde_fila(self, fila: Dict[str, str]) -> Genero:
        """Construye un Genero desde una fila."""
        return Genero(fila["nombre"], fila["descripcion"], int(fila["id"]))


class RepositorioEditorial(RepositorioCSV[Editorial]):
    """Persistencia de editoriales."""

    NOMBRE_ARCHIVO = "editoriales.csv"
    CAMPOS = ["id", "nombre", "cuit", "condicion_iva", "direccion", "email",
              "telefono"]

    def _desde_fila(self, fila: Dict[str, str]) -> Editorial:
        """Construye una Editorial desde una fila."""
        return Editorial(fila["nombre"], fila["cuit"], fila["condicion_iva"],
                         fila["direccion"], fila["email"], fila["telefono"],
                         int(fila["id"]))


class RepositorioMoneda(RepositorioCSV[Moneda]):
    """Persistencia de monedas."""

    NOMBRE_ARCHIVO = "monedas.csv"
    CAMPOS = ["id", "codigo", "nombre", "simbolo"]

    def _desde_fila(self, fila: Dict[str, str]) -> Moneda:
        """Construye una Moneda desde una fila."""
        return Moneda(fila["codigo"], fila["nombre"], fila["simbolo"],
                      int(fila["id"]))

    def leer_por_codigo(self, codigo: str) -> Optional[Moneda]:
        """Busca una moneda por su código ISO (ARS, USD, ...)."""
        for moneda in self.leer_todos():
            if moneda.codigo == codigo.upper():
                return moneda
        return None


class RepositorioTipoCotizacion(RepositorioCSV[TipoCotizacion]):
    """Persistencia de tipos de cotización del dólar."""

    NOMBRE_ARCHIVO = "tipos_cotizacion.csv"
    CAMPOS = ["id", "nombre", "descripcion"]

    def _desde_fila(self, fila: Dict[str, str]) -> TipoCotizacion:
        """Construye un TipoCotizacion desde una fila."""
        return TipoCotizacion(fila["nombre"], fila["descripcion"],
                              int(fila["id"]))

    def leer_por_nombre(self, nombre: str) -> Optional[TipoCotizacion]:
        """Busca un tipo de cotización por nombre (ignora mayúsculas)."""
        for tipo in self.leer_todos():
            if tipo.nombre.lower() == nombre.lower():
                return tipo
        return None


class RepositorioLibro(RepositorioCSV[Libro]):
    """Persistencia de libros (relacionados con Editorial y Genero)."""

    NOMBRE_ARCHIVO = "libros.csv"
    CAMPOS = ["id", "isbn", "titulo", "autor", "editorial_id", "genero_id",
              "fecha_impresion", "numero_impresion"]

    def __init__(self, repo_editorial: RepositorioEditorial,
                 repo_genero: RepositorioGenero,
                 directorio: Path = DIRECTORIO_DATOS) -> None:
        """Recibe los repositorios necesarios para resolver relaciones."""
        self._repo_editorial = repo_editorial
        self._repo_genero = repo_genero
        super().__init__(directorio)

    def _desde_fila(self, fila: Dict[str, str]) -> Libro:
        """Construye un Libro resolviendo su editorial y su género."""
        editorial = self._repo_editorial.leer_por_id(int(fila["editorial_id"]))
        genero = self._repo_genero.leer_por_id(int(fila["genero_id"]))
        return Libro(fila["isbn"], fila["titulo"], fila["autor"], editorial,
                     genero,
                     datetime.date.fromisoformat(fila["fecha_impresion"]),
                     int(fila["numero_impresion"]), int(fila["id"]))

    def leer_por_isbn(self, isbn: str) -> Optional[Libro]:
        """Busca un libro por ISBN."""
        isbn = isbn.replace("-", "").replace(" ", "").upper()
        for libro in self.leer_todos():
            if libro.isbn == isbn:
                return libro
        return None


class RepositorioPrecio(RepositorioCSV[Precio]):
    """Persistencia de precios (relacionados con Libro y Moneda)."""

    NOMBRE_ARCHIVO = "precios.csv"
    CAMPOS = ["id", "libro_id", "moneda_id", "valor", "fecha"]

    def __init__(self, repo_libro: RepositorioLibro,
                 repo_moneda: RepositorioMoneda,
                 directorio: Path = DIRECTORIO_DATOS) -> None:
        """Recibe los repositorios necesarios para resolver relaciones."""
        self._repo_libro = repo_libro
        self._repo_moneda = repo_moneda
        super().__init__(directorio)

    def _desde_fila(self, fila: Dict[str, str]) -> Precio:
        """Construye un Precio resolviendo su libro y su moneda."""
        return Precio(self._repo_libro.leer_por_id(int(fila["libro_id"])),
                      self._repo_moneda.leer_por_id(int(fila["moneda_id"])),
                      float(fila["valor"]),
                      datetime.date.fromisoformat(fila["fecha"]),
                      int(fila["id"]))

    def leer_por_libro(self, libro_id: int) -> List[Precio]:
        """Devuelve los precios de un libro, del más reciente al más viejo."""
        precios = [p for p in self.leer_todos() if p.libro.id == libro_id]
        return sorted(precios, key=lambda p: p.fecha, reverse=True)


class RepositorioStock(IRepositorioStock):
    """Persistencia del stock, identificado por el ID del libro."""

    CAMPOS = ["libro_id", "cantidad", "stock_minimo"]

    def __init__(self, repo_libro: RepositorioLibro,
                 directorio: Path = DIRECTORIO_DATOS) -> None:
        """Carga el stock guardado resolviendo cada libro."""
        self._archivo = ArchivoCSV("stock.csv", self.CAMPOS, directorio)
        self._stocks: Dict[int, Stock] = {}
        for fila in self._archivo.leer():
            libro = repo_libro.leer_por_id(int(fila["libro_id"]))
            self._stocks[libro.id] = Stock(libro, int(fila["cantidad"]),
                                           int(fila["stock_minimo"]))

    def _guardar(self) -> None:
        """Persiste el stock en el archivo."""
        self._archivo.escribir([s.to_dict() for s in self.leer_todos()])

    def crear(self, stock: Stock) -> Stock:
        """Crea el registro de stock de un libro."""
        if stock.libro_id in self._stocks:
            raise ValueError("Ya existe stock para ese libro.")
        self._stocks[stock.libro_id] = stock
        self._guardar()
        return stock

    def leer_por_libro(self, libro_id: int) -> Optional[Stock]:
        """Busca el stock de un libro."""
        return self._stocks.get(libro_id)

    def leer_todos(self) -> List[Stock]:
        """Devuelve todos los registros de stock ordenados por libro."""
        return [self._stocks[i] for i in sorted(self._stocks)]

    def actualizar(self, stock: Stock) -> Stock:
        """Reemplaza el stock del libro."""
        if stock.libro_id not in self._stocks:
            raise ValueError("No existe stock para ese libro.")
        self._stocks[stock.libro_id] = stock
        self._guardar()
        return stock

    def eliminar(self, libro_id: int) -> bool:
        """Borra el stock del libro."""
        if self._stocks.pop(libro_id, None) is None:
            return False
        self._guardar()
        return True

    def vaciar(self) -> None:
        """Elimina todos los registros."""
        self._stocks.clear()
        self._guardar()


class RepositorioCotizacionDolar(IRepositorioCotizacionDolar):
    """Persistencia del histórico de cotizaciones (clave: tipo y fecha)."""

    CAMPOS = ["tipo_id", "fecha", "compra", "venta"]

    def __init__(self, repo_tipo: RepositorioTipoCotizacion,
                 directorio: Path = DIRECTORIO_DATOS) -> None:
        """Carga las cotizaciones guardadas resolviendo cada tipo."""
        self._archivo = ArchivoCSV("cotizaciones_dolar.csv", self.CAMPOS,
                                   directorio)
        self._cotizaciones: Dict[Tuple[int, datetime.date],
                                 CotizacionDolar] = {}
        for fila in self._archivo.leer():
            cotizacion = CotizacionDolar(
                repo_tipo.leer_por_id(int(fila["tipo_id"])),
                datetime.date.fromisoformat(fila["fecha"]),
                float(fila["compra"]), float(fila["venta"]))
            self._cotizaciones[self._clave(cotizacion)] = cotizacion

    @staticmethod
    def _clave(cotizacion: CotizacionDolar) -> Tuple[int, datetime.date]:
        """Clave única de una cotización."""
        return cotizacion.tipo_id, cotizacion.fecha

    def _guardar(self) -> None:
        """Persiste las cotizaciones en el archivo."""
        self._archivo.escribir([c.to_dict() for c in self.leer_todos()])

    def crear(self, cotizacion: CotizacionDolar) -> CotizacionDolar:
        """Registra una nueva cotización."""
        if self._clave(cotizacion) in self._cotizaciones:
            raise ValueError("Ya existe una cotización para ese tipo y fecha.")
        self._cotizaciones[self._clave(cotizacion)] = cotizacion
        self._guardar()
        return cotizacion

    def leer_por_tipo_y_fecha(self, tipo_id: int, fecha: datetime.date
                              ) -> Optional[CotizacionDolar]:
        """Busca la cotización de un tipo en una fecha."""
        return self._cotizaciones.get((tipo_id, fecha))

    def leer_historico_por_tipo(self, tipo_id: int) -> List[CotizacionDolar]:
        """Devuelve las cotizaciones de un tipo ordenadas por fecha."""
        return sorted((c for c in self._cotizaciones.values()
                       if c.tipo_id == tipo_id), key=lambda c: c.fecha)

    def leer_todos(self) -> List[CotizacionDolar]:
        """Devuelve todas las cotizaciones ordenadas por tipo y fecha."""
        return [self._cotizaciones[k] for k in sorted(self._cotizaciones)]

    def actualizar(self, cotizacion: CotizacionDolar) -> CotizacionDolar:
        """Reemplaza la cotización del mismo tipo y fecha."""
        if self._clave(cotizacion) not in self._cotizaciones:
            raise ValueError("No existe la cotización a actualizar.")
        self._cotizaciones[self._clave(cotizacion)] = cotizacion
        self._guardar()
        return cotizacion

    def eliminar(self, tipo_id: int, fecha: datetime.date) -> bool:
        """Borra la cotización de un tipo en una fecha."""
        if self._cotizaciones.pop((tipo_id, fecha), None) is None:
            return False
        self._guardar()
        return True

    def vaciar(self) -> None:
        """Elimina todos los registros."""
        self._cotizaciones.clear()
        self._guardar()
