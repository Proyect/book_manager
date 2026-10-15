#@title Escritura de main.py
"""Punto de entrada del sistema Book Manager.

Arma la conexión a la base de datos, los repositorios y los servicios, carga
los datos iniciales si hace falta e inicia la consola.
"""

from typing import Optional

from book_manager.database.connection import ConexionDB
from book_manager.preload_data.preload_data import hay_datos, importar_datos
from book_manager.repositories.repositories import (
    RepositorioCotizacionDolar, RepositorioEditorial, RepositorioGenero,
    RepositorioLibro, RepositorioMoneda, RepositorioPrecio, RepositorioStock,
    RepositorioTipoCotizacion)
from book_manager.services.services import (
    ServicioCompetencia, ServicioCotizacion, ServicioEditorial,
    ServicioGenero, ServicioLibro, ServicioMoneda, ServicioPrecio,
    ServicioReportes, ServicioStock, ServicioTipoCotizacion)
from book_manager.ui.console import Consola, Servicios


def crear_servicios(conexion_db: ConexionDB) -> Servicios:
    """Construye repositorios y servicios con sus dependencias.

    Args:
        conexion_db (ConexionDB): Conexión que comparten todos los
            repositorios del sistema.

    Returns:
        Servicios: Servicios listos para la consola.
    """
    repo_genero = RepositorioGenero(conexion_db)
    repo_editorial = RepositorioEditorial(conexion_db)
    repo_moneda = RepositorioMoneda(conexion_db)
    repo_tipo = RepositorioTipoCotizacion(conexion_db)
    repo_libro = RepositorioLibro(conexion_db, repo_editorial, repo_genero)
    repo_precio = RepositorioPrecio(conexion_db, repo_libro, repo_moneda)
    repo_stock = RepositorioStock(conexion_db, repo_libro)
    repo_cotizacion = RepositorioCotizacionDolar(conexion_db, repo_tipo)

    libro = ServicioLibro(repo_libro, repo_precio, repo_stock, conexion_db)
    precio = ServicioPrecio(repo_precio)
    stock = ServicioStock(repo_stock, repo_libro)
    cotizacion = ServicioCotizacion(repo_cotizacion, repo_tipo)
    reportes = ServicioReportes(libro, precio, stock, cotizacion,
                                ServicioCompetencia())
    return Servicios(
        genero=ServicioGenero(repo_genero, repo_libro),
        editorial=ServicioEditorial(repo_editorial, repo_libro),
        moneda=ServicioMoneda(repo_moneda, repo_precio),
        tipo_cotizacion=ServicioTipoCotizacion(repo_tipo, repo_cotizacion),
        libro=libro, precio=precio, stock=stock, cotizacion=cotizacion,
        reportes=reportes)


def main(import_default_data: bool = True,
         conexion_db: Optional[ConexionDB] = None) -> None:
    """Inicia la aplicación de consola.

    Args:
        import_default_data (bool): Si es True, recrea la base con los
            datos de migrations/csv. Si es False, usa la base existente;
            si la base no existe o está vacía, igual importa los datos.
        conexion_db (Optional[ConexionDB]): Conexión a usar. Si es None,
            se usa la base SQLite del proyecto y se cierra al salir.
    """
    conexion_propia: bool = conexion_db is None
    conexion: ConexionDB = ConexionDB() if conexion_propia else conexion_db
    try:
        if import_default_data or not hay_datos(conexion):
            resumen = importar_datos(conexion)
            print("Datos iniciales importados en la base:")
            for tabla, cantidad in resumen.items():
                print(f"  {tabla}: {cantidad} registros")
        Consola(crear_servicios(conexion)).ejecutar()
    finally:
        if conexion_propia:
            conexion.cerrar()


if __name__ == "__main__":
    main()
