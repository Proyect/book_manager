"""Carga inicial de datos en la base de datos.

Reutiliza la migración de ``migrations/migrations.py`` para poblar la base
con los datos del TP1 (archivos de ``migrations/csv``).
"""

from typing import Dict

from sqlalchemy import func, select

from book_manager.database.connection import ConexionDB
from book_manager.migrations.migrations import migrar_datos
from book_manager.models.models import LibroModel


def importar_datos(conexion: ConexionDB) -> Dict[str, int]:
    """Recrea las tablas y carga los datos iniciales.

    Args:
        conexion (ConexionDB): Conexión a la base de datos.

    Returns:
        Dict[str, int]: Cantidad de registros cargados por tabla.
    """
    conexion.eliminar_tablas()
    conexion.crear_tablas()
    return migrar_datos(conexion=conexion)


def hay_datos(conexion: ConexionDB) -> bool:
    """Indica si la base ya tiene libros cargados."""
    if not conexion.existe_tabla(LibroModel.__tablename__):
        return False
    with conexion.transaccion() as sesion:
        cantidad = sesion.scalar(select(func.count()).select_from(LibroModel))
    return bool(cantidad)
