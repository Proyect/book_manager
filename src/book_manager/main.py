"""Punto de entrada del sistema Book Manager."""

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


def crear_servicios() -> Servicios:
    """Construye repositorios y servicios con sus dependencias."""
    repo_genero = RepositorioGenero()
    repo_editorial = RepositorioEditorial()
    repo_moneda = RepositorioMoneda()
    repo_tipo = RepositorioTipoCotizacion()
    repo_libro = RepositorioLibro(repo_editorial, repo_genero)
    repo_precio = RepositorioPrecio(repo_libro, repo_moneda)
    repo_stock = RepositorioStock(repo_libro)
    repo_cotizacion = RepositorioCotizacionDolar(repo_tipo)

    libro = ServicioLibro(repo_libro, repo_precio, repo_stock)
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


def main(import_default_data: bool = True) -> None:
    """Inicia la aplicación de consola.

    Args:
        import_default_data (bool): Si es True, reemplaza los datos de
            trabajo por los de migrations/csv. Si no hay datos cargados se
            importan igualmente.
    """
    if import_default_data or not hay_datos():
        resumen = importar_datos()
        print("Datos iniciales importados:")
        for archivo, cantidad in resumen.items():
            print(f"  {archivo}: {cantidad} registros")
    Consola(crear_servicios()).ejecutar()


if __name__ == "__main__":
    main()
