"""Repositorios responsables de la persistencia de datos (CRUD por entidad).

Cada repositorio guarda y lee sus entidades en la base de datos relacional
mediante SQLAlchemy. Las entidades del dominio se convierten a modelos ORM
para escribir y los modelos se convierten a entidades al leer, de modo que
el resto del sistema (servicios e interfaz) no depende de la base usada.
Cada operación se ejecuta dentro de una transacción.
"""

import abc
import datetime
from typing import Any, Generic, List, Optional, Type, TypeVar

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from book_manager.database.connection import ConexionDB
from book_manager.entities.entities import (
    CotizacionDolar, Editorial, EntidadBase, Genero, Libro, Moneda, Precio,
    Stock, TipoCotizacion)
from book_manager.models.models import (
    CotizacionDolarModel, EditorialModel, GeneroModel, LibroModel,
    MonedaModel, PrecioModel, StockModel, TipoCotizacionModel)

T = TypeVar('T', bound=EntidadBase)


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


# ----- Conversión entre modelos ORM y entidades del dominio -----

def genero_a_entidad(modelo: GeneroModel) -> Genero:
    """Convierte un GeneroModel en la entidad Genero."""
    return Genero(modelo.nombre, modelo.descripcion, modelo.id)


def editorial_a_entidad(modelo: EditorialModel) -> Editorial:
    """Convierte un EditorialModel en la entidad Editorial."""
    return Editorial(modelo.nombre, modelo.cuit, modelo.condicion_iva,
                     modelo.direccion, modelo.email, modelo.telefono,
                     modelo.id)


def moneda_a_entidad(modelo: MonedaModel) -> Moneda:
    """Convierte un MonedaModel en la entidad Moneda."""
    return Moneda(modelo.codigo, modelo.nombre, modelo.simbolo, modelo.id)


def tipo_a_entidad(modelo: TipoCotizacionModel) -> TipoCotizacion:
    """Convierte un TipoCotizacionModel en la entidad TipoCotizacion."""
    return TipoCotizacion(modelo.nombre, modelo.descripcion, modelo.id)


def libro_a_entidad(modelo: LibroModel) -> Libro:
    """Convierte un LibroModel (con editorial y género) en Libro."""
    return Libro(modelo.isbn, modelo.titulo, modelo.autor,
                 editorial_a_entidad(modelo.editorial),
                 genero_a_entidad(modelo.genero), modelo.fecha_impresion,
                 modelo.numero_impresion, modelo.id)


def precio_a_entidad(modelo: PrecioModel) -> Precio:
    """Convierte un PrecioModel (con libro y moneda) en Precio."""
    return Precio(libro_a_entidad(modelo.libro),
                  moneda_a_entidad(modelo.moneda), modelo.valor,
                  modelo.fecha, modelo.id)


def stock_a_entidad(modelo: StockModel) -> Stock:
    """Convierte un StockModel (con su libro) en Stock."""
    return Stock(libro_a_entidad(modelo.libro), modelo.cantidad,
                 modelo.stock_minimo)


def cotizacion_a_entidad(modelo: CotizacionDolarModel) -> CotizacionDolar:
    """Convierte un CotizacionDolarModel (con su tipo) en CotizacionDolar."""
    return CotizacionDolar(tipo_a_entidad(modelo.tipo), modelo.fecha,
                           modelo.compra, modelo.venta)


# ----- Repositorio genérico -----

class RepositorioDB(IRepositorio[T]):
    """Repositorio genérico con CRUD completo sobre una tabla con ID."""

    MODELO: Type[Any]

    def __init__(self, conexion: ConexionDB) -> None:
        """Recibe la conexión a la base de datos."""
        self._conexion = conexion

    @abc.abstractmethod
    def _a_entidad(self, modelo: Any) -> T:
        """Convierte el modelo ORM en la entidad del dominio."""

    @abc.abstractmethod
    def _copiar_a_modelo(self, entidad: T, modelo: Any) -> None:
        """Copia los datos de la entidad en el modelo ORM."""

    def crear(self, entidad: T) -> T:
        """Inserta la entidad; si no tiene ID la base le asigna uno."""
        with self._conexion.transaccion() as sesion:
            if (entidad.id is not None
                    and sesion.get(self.MODELO, entidad.id) is not None):
                raise ValueError(f"Ya existe una entidad con ID {entidad.id}.")
            modelo = self.MODELO(id=entidad.id)
            self._copiar_a_modelo(entidad, modelo)
            sesion.add(modelo)
            sesion.flush()
            entidad.id = modelo.id
        return entidad

    def leer_por_id(self, id: int) -> Optional[T]:
        """Busca una entidad por su ID."""
        with self._conexion.transaccion() as sesion:
            modelo = sesion.get(self.MODELO, id)
            return None if modelo is None else self._a_entidad(modelo)

    def leer_todos(self) -> List[T]:
        """Devuelve todas las entidades ordenadas por ID."""
        with self._conexion.transaccion() as sesion:
            return self._consultar(sesion, select(self.MODELO)
                                   .order_by(self.MODELO.id))

    def actualizar(self, entidad: T) -> T:
        """Guarda los cambios de una entidad existente."""
        with self._conexion.transaccion() as sesion:
            modelo = sesion.get(self.MODELO, entidad.id)
            if modelo is None:
                raise ValueError(f"No existe una entidad con ID {entidad.id}.")
            self._copiar_a_modelo(entidad, modelo)
        return entidad

    def eliminar(self, id: int) -> bool:
        """Borra la entidad con el ID indicado."""
        with self._conexion.transaccion() as sesion:
            modelo = sesion.get(self.MODELO, id)
            if modelo is None:
                return False
            sesion.delete(modelo)
        return True

    def _consultar(self, sesion: Session, consulta: Any) -> List[T]:
        """Ejecuta una consulta y convierte los resultados en entidades."""
        return [self._a_entidad(m) for m in sesion.scalars(consulta)]


# ----- Repositorios de cada entidad -----

class RepositorioGenero(RepositorioDB[Genero]):
    """Persistencia de géneros literarios (tabla generos)."""

    MODELO = GeneroModel

    def _a_entidad(self, modelo: GeneroModel) -> Genero:
        """Convierte el modelo en Genero."""
        return genero_a_entidad(modelo)

    def _copiar_a_modelo(self, entidad: Genero, modelo: GeneroModel) -> None:
        """Copia los datos del género al modelo."""
        modelo.nombre = entidad.nombre
        modelo.descripcion = entidad.descripcion


class RepositorioEditorial(RepositorioDB[Editorial]):
    """Persistencia de editoriales (tabla editoriales)."""

    MODELO = EditorialModel

    def _a_entidad(self, modelo: EditorialModel) -> Editorial:
        """Convierte el modelo en Editorial."""
        return editorial_a_entidad(modelo)

    def _copiar_a_modelo(self, entidad: Editorial,
                         modelo: EditorialModel) -> None:
        """Copia los datos de la editorial al modelo."""
        modelo.nombre = entidad.nombre
        modelo.cuit = entidad.cuit
        modelo.condicion_iva = entidad.condicion_iva
        modelo.direccion = entidad.direccion
        modelo.email = entidad.email
        modelo.telefono = entidad.telefono


class RepositorioMoneda(RepositorioDB[Moneda]):
    """Persistencia de monedas (tabla monedas)."""

    MODELO = MonedaModel

    def _a_entidad(self, modelo: MonedaModel) -> Moneda:
        """Convierte el modelo en Moneda."""
        return moneda_a_entidad(modelo)

    def _copiar_a_modelo(self, entidad: Moneda, modelo: MonedaModel) -> None:
        """Copia los datos de la moneda al modelo."""
        modelo.codigo = entidad.codigo
        modelo.nombre = entidad.nombre
        modelo.simbolo = entidad.simbolo

    def leer_por_codigo(self, codigo: str) -> Optional[Moneda]:
        """Busca una moneda por su código ISO (ARS, USD, ...)."""
        with self._conexion.transaccion() as sesion:
            modelo = sesion.scalar(select(MonedaModel).where(
                MonedaModel.codigo == codigo.upper()))
            return None if modelo is None else moneda_a_entidad(modelo)


class RepositorioTipoCotizacion(RepositorioDB[TipoCotizacion]):
    """Persistencia de tipos de cotización (tabla tipos_cotizacion)."""

    MODELO = TipoCotizacionModel

    def _a_entidad(self, modelo: TipoCotizacionModel) -> TipoCotizacion:
        """Convierte el modelo en TipoCotizacion."""
        return tipo_a_entidad(modelo)

    def _copiar_a_modelo(self, entidad: TipoCotizacion,
                         modelo: TipoCotizacionModel) -> None:
        """Copia los datos del tipo de cotización al modelo."""
        modelo.nombre = entidad.nombre
        modelo.descripcion = entidad.descripcion

    def leer_por_nombre(self, nombre: str) -> Optional[TipoCotizacion]:
        """Busca un tipo de cotización por nombre (ignora mayúsculas)."""
        with self._conexion.transaccion() as sesion:
            modelo = sesion.scalar(select(TipoCotizacionModel).where(
                func.lower(TipoCotizacionModel.nombre) == nombre.lower()))
            return None if modelo is None else tipo_a_entidad(modelo)


class RepositorioLibro(RepositorioDB[Libro]):
    """Persistencia de libros (relacionados con Editorial y Genero)."""

    MODELO = LibroModel

    def _a_entidad(self, modelo: LibroModel) -> Libro:
        """Convierte el modelo en Libro."""
        return libro_a_entidad(modelo)

    def _copiar_a_modelo(self, entidad: Libro, modelo: LibroModel) -> None:
        """Copia los datos del libro al modelo (relaciones por ID)."""
        modelo.isbn = entidad.isbn
        modelo.titulo = entidad.titulo
        modelo.autor = entidad.autor
        modelo.editorial_id = entidad.editorial.id
        modelo.genero_id = entidad.genero.id
        modelo.fecha_impresion = entidad.fecha_impresion
        modelo.numero_impresion = entidad.numero_impresion

    def leer_por_isbn(self, isbn: str) -> Optional[Libro]:
        """Busca un libro por ISBN."""
        isbn = isbn.replace("-", "").replace(" ", "").upper()
        with self._conexion.transaccion() as sesion:
            modelo = sesion.scalar(select(LibroModel).where(
                LibroModel.isbn == isbn))
            return None if modelo is None else libro_a_entidad(modelo)


class RepositorioPrecio(RepositorioDB[Precio]):
    """Persistencia de precios (relacionados con Libro y Moneda)."""

    MODELO = PrecioModel

    def _a_entidad(self, modelo: PrecioModel) -> Precio:
        """Convierte el modelo en Precio."""
        return precio_a_entidad(modelo)

    def _copiar_a_modelo(self, entidad: Precio, modelo: PrecioModel) -> None:
        """Copia los datos del precio al modelo (relaciones por ID)."""
        modelo.libro_id = entidad.libro.id
        modelo.moneda_id = entidad.moneda.id
        modelo.valor = entidad.valor
        modelo.fecha = entidad.fecha

    def leer_por_libro(self, libro_id: int) -> List[Precio]:
        """Devuelve los precios de un libro, del más reciente al más viejo."""
        with self._conexion.transaccion() as sesion:
            return self._consultar(sesion, select(PrecioModel)
                                   .where(PrecioModel.libro_id == libro_id)
                                   .order_by(PrecioModel.fecha.desc()))


class RepositorioStock(IRepositorioStock):
    """Persistencia del stock (tabla stock, clave: ID del libro)."""

    def __init__(self, conexion: ConexionDB) -> None:
        """Recibe la conexión a la base de datos."""
        self._conexion = conexion

    def crear(self, stock: Stock) -> Stock:
        """Crea el registro de stock de un libro."""
        with self._conexion.transaccion() as sesion:
            if sesion.get(StockModel, stock.libro_id) is not None:
                raise ValueError("Ya existe stock para ese libro.")
            sesion.add(StockModel(libro_id=stock.libro_id,
                                  cantidad=stock.cantidad,
                                  stock_minimo=stock.stock_minimo))
        return stock

    def leer_por_libro(self, libro_id: int) -> Optional[Stock]:
        """Busca el stock de un libro."""
        with self._conexion.transaccion() as sesion:
            modelo = sesion.get(StockModel, libro_id)
            return None if modelo is None else stock_a_entidad(modelo)

    def leer_todos(self) -> List[Stock]:
        """Devuelve todos los registros de stock ordenados por libro."""
        with self._conexion.transaccion() as sesion:
            return [stock_a_entidad(m) for m in sesion.scalars(
                select(StockModel).order_by(StockModel.libro_id))]

    def actualizar(self, stock: Stock) -> Stock:
        """Guarda la cantidad y el stock mínimo del libro."""
        with self._conexion.transaccion() as sesion:
            modelo = sesion.get(StockModel, stock.libro_id)
            if modelo is None:
                raise ValueError("No existe stock para ese libro.")
            modelo.cantidad = stock.cantidad
            modelo.stock_minimo = stock.stock_minimo
        return stock

    def eliminar(self, libro_id: int) -> bool:
        """Borra el stock del libro."""
        with self._conexion.transaccion() as sesion:
            modelo = sesion.get(StockModel, libro_id)
            if modelo is None:
                return False
            sesion.delete(modelo)
        return True


class RepositorioCotizacionDolar(IRepositorioCotizacionDolar):
    """Persistencia del histórico de cotizaciones (clave: tipo y fecha)."""

    def __init__(self, conexion: ConexionDB) -> None:
        """Recibe la conexión a la base de datos."""
        self._conexion = conexion

    def crear(self, cotizacion: CotizacionDolar) -> CotizacionDolar:
        """Registra una nueva cotización."""
        clave = (cotizacion.tipo_id, cotizacion.fecha)
        with self._conexion.transaccion() as sesion:
            if sesion.get(CotizacionDolarModel, clave) is not None:
                raise ValueError(
                    "Ya existe una cotización para ese tipo y fecha.")
            sesion.add(CotizacionDolarModel(
                tipo_id=cotizacion.tipo_id, fecha=cotizacion.fecha,
                compra=cotizacion.compra, venta=cotizacion.venta))
        return cotizacion

    def leer_por_tipo_y_fecha(self, tipo_id: int, fecha: datetime.date
                              ) -> Optional[CotizacionDolar]:
        """Busca la cotización de un tipo en una fecha."""
        with self._conexion.transaccion() as sesion:
            modelo = sesion.get(CotizacionDolarModel, (tipo_id, fecha))
            return None if modelo is None else cotizacion_a_entidad(modelo)

    def leer_historico_por_tipo(self, tipo_id: int) -> List[CotizacionDolar]:
        """Devuelve las cotizaciones de un tipo ordenadas por fecha."""
        with self._conexion.transaccion() as sesion:
            return [cotizacion_a_entidad(m) for m in sesion.scalars(
                select(CotizacionDolarModel)
                .where(CotizacionDolarModel.tipo_id == tipo_id)
                .order_by(CotizacionDolarModel.fecha))]

    def leer_todos(self) -> List[CotizacionDolar]:
        """Devuelve todas las cotizaciones ordenadas por tipo y fecha."""
        with self._conexion.transaccion() as sesion:
            return [cotizacion_a_entidad(m) for m in sesion.scalars(
                select(CotizacionDolarModel).order_by(
                    CotizacionDolarModel.tipo_id,
                    CotizacionDolarModel.fecha))]

    def actualizar(self, cotizacion: CotizacionDolar) -> CotizacionDolar:
        """Guarda los valores de la cotización del mismo tipo y fecha."""
        clave = (cotizacion.tipo_id, cotizacion.fecha)
        with self._conexion.transaccion() as sesion:
            modelo = sesion.get(CotizacionDolarModel, clave)
            if modelo is None:
                raise ValueError("No existe la cotización a actualizar.")
            modelo.compra = cotizacion.compra
            modelo.venta = cotizacion.venta
        return cotizacion

    def eliminar(self, tipo_id: int, fecha: datetime.date) -> bool:
        """Borra la cotización de un tipo en una fecha."""
        with self._conexion.transaccion() as sesion:
            modelo = sesion.get(CotizacionDolarModel, (tipo_id, fecha))
            if modelo is None:
                return False
            sesion.delete(modelo)
        return True
