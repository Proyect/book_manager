#@title Escritura de repositories.py
"""Repositorios responsables de la persistencia de datos (CRUD por entidad).

Cada repositorio lee y escribe en su tabla de la base de datos usando SQL
parametrizado sobre la ConexionDB del sistema. Las relaciones entre
entidades se guardan por id y se resuelven al leer, usando los repositorios
de las entidades relacionadas. Todas las operaciones usan el context manager
de transacciones, así que pueden ejecutarse solas o sumarse a una
transacción mayor abierta por un servicio. Las sentencias funcionan en
SQLite y en PostgreSQL (Supabase).
"""

import abc
import datetime
from typing import Any, Dict, Generic, List, Mapping, Optional, TypeVar

from sqlalchemy.exc import IntegrityError
from sqlalchemy.sql import text

from book_manager.database.connection import ConexionDB
from book_manager.entities.entities import (
    CotizacionDolar, Editorial, EntidadBase, Genero, Libro, Moneda, Precio,
    Stock, TipoCotizacion)

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


def _a_fecha(valor: Any) -> datetime.date:
    """Convierte una fecha leída de la base en un objeto date.

    Args:
        valor (Any): Fecha como texto ISO (AAAA-MM-DD, SQLite) o como date
            (PostgreSQL).

    Returns:
        datetime.date: La fecha convertida.
    """
    if isinstance(valor, datetime.date):
        return valor
    return datetime.date.fromisoformat(str(valor))


class RepositorioBaseSQL:
    """Base común de los repositorios: conexión y ejecución de SQL.

    Toda sentencia se ejecuta con parámetros con nombre (:campo) dentro del
    context manager de transacciones. Los errores de integridad de la base
    se convierten en ValueError, como indican las interfaces.
    """

    def __init__(self, conexion_db: ConexionDB) -> None:
        """Guarda la conexión a la base de datos.

        Args:
            conexion_db (ConexionDB): Conexión a la base de datos.

        Raises:
            TypeError: Si conexion_db no es una ConexionDB.
        """
        if not isinstance(conexion_db, ConexionDB):
            raise TypeError("El repositorio requiere una ConexionDB.")
        self.__conexion_db: ConexionDB = conexion_db

    def _seleccionar(self, sentencia: str,
                     parametros: Optional[Dict[str, Any]] = None
                     ) -> List[Mapping[str, Any]]:
        """Ejecuta una consulta y devuelve sus filas.

        Args:
            sentencia (str): Sentencia SELECT con parámetros con nombre.
            parametros (Optional[Dict[str, Any]]): Valores de los parámetros.

        Returns:
            List[Mapping[str, Any]]: Filas como diccionarios (columna: valor).
        """
        with self.__conexion_db.transaccion() as conexion:
            resultado = conexion.execute(text(sentencia), parametros or {})
            return list(resultado.mappings().all())

    def _ejecutar(self, sentencia: str, parametros: Dict[str, Any],
                  accion: str) -> int:
        """Ejecuta una sentencia que modifica datos.

        Args:
            sentencia (str): Sentencia INSERT, UPDATE o DELETE.
            parametros (Dict[str, Any]): Valores de los parámetros.
            accion (str): Descripción de la operación, para el mensaje de
                error (por ejemplo, 'crear el registro').

        Returns:
            int: Cantidad de filas afectadas.

        Raises:
            ValueError: Si la base rechaza la operación (clave duplicada,
                clave foránea o restricción CHECK).
        """
        try:
            with self.__conexion_db.transaccion() as conexion:
                return conexion.execute(text(sentencia), parametros).rowcount
        except IntegrityError as error:
            raise ValueError(
                f"No se pudo {accion}: {error.orig}"
            ) from error

    def _insertar_devolviendo_id(self, sentencia: str,
                                 parametros: Dict[str, Any],
                                 accion: str) -> int:
        """Ejecuta un INSERT ... RETURNING id y devuelve el id asignado.

        RETURNING funciona en PostgreSQL y en SQLite (desde la versión
        3.35); lastrowid, en cambio, no devuelve el id en PostgreSQL.

        Args:
            sentencia (str): Sentencia INSERT terminada en RETURNING id.
            parametros (Dict[str, Any]): Valores de los parámetros.
            accion (str): Descripción de la operación, para el mensaje de
                error.

        Returns:
            int: Id asignado por la base.

        Raises:
            ValueError: Si la base rechaza la operación.
        """
        try:
            with self.__conexion_db.transaccion() as conexion:
                return int(
                    conexion.execute(text(sentencia), parametros).scalar_one()
                )
        except IntegrityError as error:
            raise ValueError(
                f"No se pudo {accion}: {error.orig}"
            ) from error


class RepositorioSQL(RepositorioBaseSQL, IRepositorio[T]):
    """Repositorio genérico con CRUD completo sobre una tabla con id.

    Cada subclase define TABLA, CAMPOS (con 'id' primero, en el mismo orden
    y con los mismos nombres que devuelve to_dict()) y _desde_fila.
    """

    TABLA: str = ""
    CAMPOS: List[str] = []

    @abc.abstractmethod
    def _desde_fila(self, fila: Mapping[str, Any]) -> T:
        """Construye la entidad a partir de una fila de la tabla."""

    def _consultar(self, condicion: str = "",
                   parametros: Optional[Dict[str, Any]] = None,
                   orden: str = "id") -> List[T]:
        """Lee entidades de la tabla, opcionalmente filtradas.

        Args:
            condicion (str): Condición WHERE con parámetros con nombre (vacía
                para traer todo). Se escribe en el código, nunca con datos
                del usuario.
            parametros (Optional[Dict[str, Any]]): Valores de la condición.
            orden (str): Columnas del ORDER BY.

        Returns:
            List[T]: Entidades encontradas.
        """
        sentencia: str = f"SELECT {', '.join(self.CAMPOS)} FROM {self.TABLA}"
        if condicion:
            sentencia += f" WHERE {condicion}"
        sentencia += f" ORDER BY {orden}"
        filas = self._seleccionar(sentencia, parametros)
        return [self._desde_fila(fila) for fila in filas]

    @staticmethod
    def _primero(entidades: List[T]) -> Optional[T]:
        """Devuelve la primera entidad de una lista, o None si está vacía."""
        return entidades[0] if entidades else None

    def crear(self, entidad: T) -> T:
        """Inserta la entidad; si no tiene id, la base asigna el siguiente."""
        datos: Dict[str, Any] = entidad.to_dict()
        columnas: List[str] = [
            campo for campo in self.CAMPOS
            if campo != "id" or datos["id"] is not None
        ]
        sentencia: str = (
            f"INSERT INTO {self.TABLA} ({', '.join(columnas)}) "
            f"VALUES ({', '.join(':' + campo for campo in columnas)})"
        )
        parametros: Dict[str, Any] = {campo: datos[campo] for campo in columnas}
        if entidad.id is None:
            entidad.id = self._insertar_devolviendo_id(
                sentencia + " RETURNING id", parametros, "crear el registro"
            )
        else:
            self._ejecutar(sentencia, parametros, "crear el registro")
        return entidad

    def leer_por_id(self, id: int) -> Optional[T]:
        """Busca una entidad por su id."""
        return self._primero(self._consultar("id = :id", {"id": id}))

    def leer_todos(self) -> List[T]:
        """Devuelve todas las entidades ordenadas por id."""
        return self._consultar()

    def actualizar(self, entidad: T) -> T:
        """Reemplaza los datos de la entidad con el mismo id."""
        datos: Dict[str, Any] = entidad.to_dict()
        asignaciones: str = ", ".join(
            f"{campo} = :{campo}" for campo in self.CAMPOS if campo != "id"
        )
        filas: int = self._ejecutar(
            f"UPDATE {self.TABLA} SET {asignaciones} WHERE id = :id",
            datos, "actualizar el registro"
        )
        if filas == 0:
            raise ValueError(f"No existe una entidad con ID {entidad.id}.")
        return entidad

    def eliminar(self, id: int) -> bool:
        """Borra la entidad con el id indicado."""
        filas: int = self._ejecutar(
            f"DELETE FROM {self.TABLA} WHERE id = :id", {"id": id},
            "eliminar el registro"
        )
        return filas > 0


class RepositorioGenero(RepositorioSQL[Genero]):
    """Persistencia de géneros literarios."""

    TABLA = "generos"
    CAMPOS = ["id", "nombre", "descripcion"]

    def _desde_fila(self, fila: Mapping[str, Any]) -> Genero:
        """Construye un Genero desde una fila."""
        return Genero(fila["nombre"], fila["descripcion"], int(fila["id"]))


class RepositorioEditorial(RepositorioSQL[Editorial]):
    """Persistencia de editoriales."""

    TABLA = "editoriales"
    CAMPOS = ["id", "nombre", "cuit", "condicion_iva", "direccion", "email",
              "telefono"]

    def _desde_fila(self, fila: Mapping[str, Any]) -> Editorial:
        """Construye una Editorial desde una fila."""
        return Editorial(fila["nombre"], fila["cuit"], fila["condicion_iva"],
                         fila["direccion"], fila["email"], fila["telefono"],
                         int(fila["id"]))


class RepositorioMoneda(RepositorioSQL[Moneda]):
    """Persistencia de monedas."""

    TABLA = "monedas"
    CAMPOS = ["id", "codigo", "nombre", "simbolo"]

    def _desde_fila(self, fila: Mapping[str, Any]) -> Moneda:
        """Construye una Moneda desde una fila."""
        return Moneda(fila["codigo"], fila["nombre"], fila["simbolo"],
                      int(fila["id"]))

    def leer_por_codigo(self, codigo: str) -> Optional[Moneda]:
        """Busca una moneda por su código ISO (ARS, USD, ...)."""
        return self._primero(
            self._consultar("codigo = :codigo", {"codigo": codigo.upper()})
        )


class RepositorioTipoCotizacion(RepositorioSQL[TipoCotizacion]):
    """Persistencia de tipos de cotización del dólar."""

    TABLA = "tipos_cotizacion"
    CAMPOS = ["id", "nombre", "descripcion"]

    def _desde_fila(self, fila: Mapping[str, Any]) -> TipoCotizacion:
        """Construye un TipoCotizacion desde una fila."""
        return TipoCotizacion(fila["nombre"], fila["descripcion"],
                              int(fila["id"]))

    def leer_por_nombre(self, nombre: str) -> Optional[TipoCotizacion]:
        """Busca un tipo de cotización por nombre (ignora mayúsculas)."""
        return self._primero(
            self._consultar("lower(nombre) = lower(:nombre)",
                            {"nombre": nombre})
        )


class RepositorioLibro(RepositorioSQL[Libro]):
    """Persistencia de libros (relacionados con Editorial y Genero)."""

    TABLA = "libros"
    CAMPOS = ["id", "isbn", "titulo", "autor", "editorial_id", "genero_id",
              "fecha_impresion", "numero_impresion"]

    def __init__(self, conexion_db: ConexionDB,
                 repo_editorial: RepositorioEditorial,
                 repo_genero: RepositorioGenero) -> None:
        """Recibe la conexión y los repositorios de las relaciones.

        Args:
            conexion_db (ConexionDB): Conexión a la base de datos.
            repo_editorial (RepositorioEditorial): Para resolver la editorial.
            repo_genero (RepositorioGenero): Para resolver el género.
        """
        super().__init__(conexion_db)
        self.__repo_editorial: RepositorioEditorial = repo_editorial
        self.__repo_genero: RepositorioGenero = repo_genero

    def _desde_fila(self, fila: Mapping[str, Any]) -> Libro:
        """Construye un Libro resolviendo su editorial y su género."""
        editorial = self.__repo_editorial.leer_por_id(int(fila["editorial_id"]))
        genero = self.__repo_genero.leer_por_id(int(fila["genero_id"]))
        return Libro(fila["isbn"], fila["titulo"], fila["autor"], editorial,
                     genero, _a_fecha(fila["fecha_impresion"]),
                     int(fila["numero_impresion"]), int(fila["id"]))

    def leer_por_isbn(self, isbn: str) -> Optional[Libro]:
        """Busca un libro por ISBN."""
        isbn_limpio: str = isbn.replace("-", "").replace(" ", "").upper()
        return self._primero(
            self._consultar("isbn = :isbn", {"isbn": isbn_limpio})
        )


class RepositorioPrecio(RepositorioSQL[Precio]):
    """Persistencia de precios (relacionados con Libro y Moneda)."""

    TABLA = "precios"
    CAMPOS = ["id", "libro_id", "moneda_id", "valor", "fecha"]

    def __init__(self, conexion_db: ConexionDB, repo_libro: RepositorioLibro,
                 repo_moneda: RepositorioMoneda) -> None:
        """Recibe la conexión y los repositorios de las relaciones.

        Args:
            conexion_db (ConexionDB): Conexión a la base de datos.
            repo_libro (RepositorioLibro): Para resolver el libro.
            repo_moneda (RepositorioMoneda): Para resolver la moneda.
        """
        super().__init__(conexion_db)
        self.__repo_libro: RepositorioLibro = repo_libro
        self.__repo_moneda: RepositorioMoneda = repo_moneda

    def _desde_fila(self, fila: Mapping[str, Any]) -> Precio:
        """Construye un Precio resolviendo su libro y su moneda."""
        return Precio(self.__repo_libro.leer_por_id(int(fila["libro_id"])),
                      self.__repo_moneda.leer_por_id(int(fila["moneda_id"])),
                      float(fila["valor"]), _a_fecha(fila["fecha"]),
                      int(fila["id"]))

    def leer_por_libro(self, libro_id: int) -> List[Precio]:
        """Devuelve los precios de un libro, del más reciente al más viejo."""
        return self._consultar("libro_id = :libro_id",
                               {"libro_id": libro_id},
                               orden="fecha DESC, id ASC")


class RepositorioStock(RepositorioBaseSQL, IRepositorioStock):
    """Persistencia del stock, identificado por el ID del libro."""

    TABLA: str = "stock"
    CAMPOS: List[str] = ["libro_id", "cantidad", "stock_minimo"]

    def __init__(self, conexion_db: ConexionDB,
                 repo_libro: RepositorioLibro) -> None:
        """Recibe la conexión y el repositorio de libros.

        Args:
            conexion_db (ConexionDB): Conexión a la base de datos.
            repo_libro (RepositorioLibro): Para resolver el libro.
        """
        super().__init__(conexion_db)
        self.__repo_libro: RepositorioLibro = repo_libro

    def _desde_fila(self, fila: Mapping[str, Any]) -> Stock:
        """Construye un Stock resolviendo su libro."""
        return Stock(self.__repo_libro.leer_por_id(int(fila["libro_id"])),
                     int(fila["cantidad"]), int(fila["stock_minimo"]))

    def _consultar(self, condicion: str = "",
                   parametros: Optional[Dict[str, Any]] = None
                   ) -> List[Stock]:
        """Lee registros de stock, opcionalmente filtrados por libro."""
        sentencia: str = f"SELECT {', '.join(self.CAMPOS)} FROM {self.TABLA}"
        if condicion:
            sentencia += f" WHERE {condicion}"
        sentencia += " ORDER BY libro_id"
        return [self._desde_fila(fila)
                for fila in self._seleccionar(sentencia, parametros)]

    def crear(self, stock: Stock) -> Stock:
        """Crea el registro de stock de un libro."""
        self._ejecutar(
            "INSERT INTO stock (libro_id, cantidad, stock_minimo) "
            "VALUES (:libro_id, :cantidad, :stock_minimo)",
            stock.to_dict(), "crear el stock"
        )
        return stock

    def leer_por_libro(self, libro_id: int) -> Optional[Stock]:
        """Busca el stock de un libro."""
        encontrados: List[Stock] = self._consultar(
            "libro_id = :libro_id", {"libro_id": libro_id}
        )
        return encontrados[0] if encontrados else None

    def leer_todos(self) -> List[Stock]:
        """Devuelve todos los registros de stock ordenados por libro."""
        return self._consultar()

    def actualizar(self, stock: Stock) -> Stock:
        """Reemplaza la cantidad y el stock mínimo del libro."""
        filas: int = self._ejecutar(
            "UPDATE stock SET cantidad = :cantidad, "
            "stock_minimo = :stock_minimo WHERE libro_id = :libro_id",
            stock.to_dict(), "actualizar el stock"
        )
        if filas == 0:
            raise ValueError("No existe stock para ese libro.")
        return stock

    def eliminar(self, libro_id: int) -> bool:
        """Borra el stock del libro."""
        filas: int = self._ejecutar(
            "DELETE FROM stock WHERE libro_id = :libro_id",
            {"libro_id": libro_id}, "eliminar el stock"
        )
        return filas > 0


class RepositorioCotizacionDolar(RepositorioBaseSQL,
                                 IRepositorioCotizacionDolar):
    """Persistencia del histórico de cotizaciones (clave: tipo y fecha)."""

    TABLA: str = "cotizaciones_dolar"
    CAMPOS: List[str] = ["tipo_id", "fecha", "compra", "venta"]

    def __init__(self, conexion_db: ConexionDB,
                 repo_tipo: RepositorioTipoCotizacion) -> None:
        """Recibe la conexión y el repositorio de tipos de cotización.

        Args:
            conexion_db (ConexionDB): Conexión a la base de datos.
            repo_tipo (RepositorioTipoCotizacion): Para resolver el tipo.
        """
        super().__init__(conexion_db)
        self.__repo_tipo: RepositorioTipoCotizacion = repo_tipo

    def _desde_fila(self, fila: Mapping[str, Any]) -> CotizacionDolar:
        """Construye una CotizacionDolar resolviendo su tipo."""
        return CotizacionDolar(
            self.__repo_tipo.leer_por_id(int(fila["tipo_id"])),
            _a_fecha(fila["fecha"]), float(fila["compra"]),
            float(fila["venta"]))

    def _consultar(self, condicion: str = "",
                   parametros: Optional[Dict[str, Any]] = None
                   ) -> List[CotizacionDolar]:
        """Lee cotizaciones, opcionalmente filtradas, por tipo y fecha."""
        sentencia: str = f"SELECT {', '.join(self.CAMPOS)} FROM {self.TABLA}"
        if condicion:
            sentencia += f" WHERE {condicion}"
        sentencia += " ORDER BY tipo_id, fecha"
        return [self._desde_fila(fila)
                for fila in self._seleccionar(sentencia, parametros)]

    def crear(self, cotizacion: CotizacionDolar) -> CotizacionDolar:
        """Registra una nueva cotización."""
        self._ejecutar(
            "INSERT INTO cotizaciones_dolar (tipo_id, fecha, compra, venta) "
            "VALUES (:tipo_id, :fecha, :compra, :venta)",
            cotizacion.to_dict(), "crear la cotización"
        )
        return cotizacion

    def leer_por_tipo_y_fecha(self, tipo_id: int, fecha: datetime.date
                              ) -> Optional[CotizacionDolar]:
        """Busca la cotización de un tipo en una fecha."""
        encontradas: List[CotizacionDolar] = self._consultar(
            "tipo_id = :tipo_id AND fecha = :fecha",
            {"tipo_id": tipo_id, "fecha": fecha.isoformat()}
        )
        return encontradas[0] if encontradas else None

    def leer_historico_por_tipo(self, tipo_id: int) -> List[CotizacionDolar]:
        """Devuelve las cotizaciones de un tipo ordenadas por fecha."""
        return self._consultar("tipo_id = :tipo_id", {"tipo_id": tipo_id})

    def leer_todos(self) -> List[CotizacionDolar]:
        """Devuelve todas las cotizaciones ordenadas por tipo y fecha."""
        return self._consultar()

    def actualizar(self, cotizacion: CotizacionDolar) -> CotizacionDolar:
        """Reemplaza la cotización del mismo tipo y fecha."""
        filas: int = self._ejecutar(
            "UPDATE cotizaciones_dolar SET compra = :compra, venta = :venta "
            "WHERE tipo_id = :tipo_id AND fecha = :fecha",
            cotizacion.to_dict(), "actualizar la cotización"
        )
        if filas == 0:
            raise ValueError("No existe la cotización a actualizar.")
        return cotizacion

    def eliminar(self, tipo_id: int, fecha: datetime.date) -> bool:
        """Borra la cotización de un tipo en una fecha."""
        filas: int = self._ejecutar(
            "DELETE FROM cotizaciones_dolar "
            "WHERE tipo_id = :tipo_id AND fecha = :fecha",
            {"tipo_id": tipo_id, "fecha": fecha.isoformat()},
            "eliminar la cotización"
        )
        return filas > 0
