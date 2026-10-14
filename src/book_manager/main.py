"""Punto de entrada del sistema Book Manager."""

from book_manager.database.connection import ConexionDB
from book_manager.preload_data.preload_data import hay_datos, importar_datos
from book_manager.repositories.repositories import (
    RepositorioCotizacionDolar, RepositorioEditorial, RepositorioGenero,
    RepositorioLibro, RepositorioMoneda, RepositorioPrecio, RepositorioStock,
    RepositorioTipoCotizacion)
from book_manager.services.services import (
    ServicioCompetencia, ServicioCotizacionDolar, ServicioEditorial,
    ServicioGenero, ServicioLibro, ServicioMoneda, ServicioPrecio,
    ServicioReportes, ServicioStock, ServicioTipoCotizacion)
from book_manager.ui.console import Consola, Servicios


def crear_servicios(conexion: ConexionDB) -> Servicios:
    """Construye repositorios y servicios con sus dependencias."""
    repo_genero = RepositorioGenero(conexion)
    repo_editorial = RepositorioEditorial(conexion)
    repo_moneda = RepositorioMoneda(conexion)
    repo_tipo = RepositorioTipoCotizacion(conexion)
    repo_libro = RepositorioLibro(conexion)
    repo_precio = RepositorioPrecio(conexion)
    repo_stock = RepositorioStock(conexion)
    repo_cotizacion = RepositorioCotizacionDolar(conexion)

    libro = ServicioLibro(repo_libro, repo_precio, repo_stock)
    precio = ServicioPrecio(repo_precio)
    stock = ServicioStock(repo_stock, repo_libro)
    cotizacion = ServicioCotizacionDolar(repo_cotizacion, repo_tipo)
    reportes = ServicioReportes(libro, precio, stock, cotizacion,
                                ServicioCompetencia())
    return Servicios(
        genero=ServicioGenero(repo_genero, repo_libro),
        editorial=ServicioEditorial(repo_editorial, repo_libro),
        moneda=ServicioMoneda(repo_moneda, repo_precio),
        tipo_cotizacion=ServicioTipoCotizacion(repo_tipo, repo_cotizacion),
        libro=libro, precio=precio, stock=stock, cotizacion=cotizacion,
        reportes=reportes)


def main(import_default_data: bool = True) -> None:
    """Inicia la aplicación de consola sobre la base de datos.

    Args:
        import_default_data (bool): Si es True, recrea las tablas y carga
            los datos de migrations/csv. Si la base está vacía se cargan
            igualmente.
    """
    conexion = ConexionDB()
    conexion.crear_tablas()
    print(f"Base de datos: {conexion.url}")
    if import_default_data or not hay_datos(conexion):
        resumen = importar_datos(conexion)
        print("Datos iniciales importados:")
        for tabla, cantidad in resumen.items():
            print(f"  {tabla}: {cantidad} registros")
    try:
        Consola(crear_servicios(conexion)).ejecutar()
    finally:
        conexion.cerrar()


if __name__ == "__main__":
    main()
