"""Modelos ORM (tablas) del sistema Book Manager.

Cada clase representa una tabla de la base de datos relacional. Las
entidades del dominio (``entities.py``) siguen siendo las que usa la lógica
del sistema; los repositorios se encargan de convertir entre ambas.
"""

import datetime
from typing import List, Optional

from sqlalchemy import (CheckConstraint, Date, ForeignKey, Integer, Numeric,
                        String, UniqueConstraint)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from book_manager.database.connection import Base

# Importes con dos decimales que se leen como float.
Importe = Numeric(12, 2, asdecimal=False)


class GeneroModel(Base):
    """Tabla de géneros literarios."""

    __tablename__ = "generos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nombre: Mapped[str] = mapped_column(String(100), unique=True)
    descripcion: Mapped[str] = mapped_column(String(255), default="")

    libros: Mapped[List["LibroModel"]] = relationship(
        back_populates="genero")


class EditorialModel(Base):
    """Tabla de editoriales (proveedores de libros)."""

    __tablename__ = "editoriales"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nombre: Mapped[str] = mapped_column(String(150))
    cuit: Mapped[str] = mapped_column(String(11), unique=True)
    condicion_iva: Mapped[str] = mapped_column(String(30))
    direccion: Mapped[str] = mapped_column(String(200), default="")
    email: Mapped[str] = mapped_column(String(150), default="")
    telefono: Mapped[str] = mapped_column(String(50), default="")

    libros: Mapped[List["LibroModel"]] = relationship(
        back_populates="editorial")


class MonedaModel(Base):
    """Tabla de monedas (código ISO 4217)."""

    __tablename__ = "monedas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    codigo: Mapped[str] = mapped_column(String(3), unique=True)
    nombre: Mapped[str] = mapped_column(String(100))
    simbolo: Mapped[str] = mapped_column(String(10), default="")

    precios: Mapped[List["PrecioModel"]] = relationship(
        back_populates="moneda")


class TipoCotizacionModel(Base):
    """Tabla de tipos de cotización del dólar (Oficial, Blue, MEP...)."""

    __tablename__ = "tipos_cotizacion"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nombre: Mapped[str] = mapped_column(String(50), unique=True)
    descripcion: Mapped[str] = mapped_column(String(255), default="")

    cotizaciones: Mapped[List["CotizacionDolarModel"]] = relationship(
        back_populates="tipo")


class LibroModel(Base):
    """Tabla de libros, relacionada con editorial y género."""

    __tablename__ = "libros"
    __table_args__ = (
        CheckConstraint("numero_impresion >= 1",
                        name="ck_libros_numero_impresion"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    isbn: Mapped[str] = mapped_column(String(13), unique=True)
    titulo: Mapped[str] = mapped_column(String(200))
    autor: Mapped[str] = mapped_column(String(150))
    editorial_id: Mapped[int] = mapped_column(
        ForeignKey("editoriales.id", ondelete="RESTRICT"))
    genero_id: Mapped[int] = mapped_column(
        ForeignKey("generos.id", ondelete="RESTRICT"))
    fecha_impresion: Mapped[datetime.date] = mapped_column(Date)
    numero_impresion: Mapped[int] = mapped_column(Integer, default=1)

    editorial: Mapped[EditorialModel] = relationship(back_populates="libros")
    genero: Mapped[GeneroModel] = relationship(back_populates="libros")
    precios: Mapped[List["PrecioModel"]] = relationship(
        back_populates="libro", cascade="all, delete-orphan")
    stock: Mapped[Optional["StockModel"]] = relationship(
        back_populates="libro", cascade="all, delete-orphan")


class PrecioModel(Base):
    """Tabla de precios de cada libro en una moneda y fecha."""

    __tablename__ = "precios"
    __table_args__ = (
        UniqueConstraint("libro_id", "moneda_id", "fecha",
                         name="uq_precios_libro_moneda_fecha"),
        CheckConstraint("valor >= 0", name="ck_precios_valor"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    libro_id: Mapped[int] = mapped_column(
        ForeignKey("libros.id", ondelete="CASCADE"))
    moneda_id: Mapped[int] = mapped_column(
        ForeignKey("monedas.id", ondelete="RESTRICT"))
    valor: Mapped[float] = mapped_column(Importe)
    fecha: Mapped[datetime.date] = mapped_column(Date)

    libro: Mapped[LibroModel] = relationship(back_populates="precios")
    moneda: Mapped[MonedaModel] = relationship(back_populates="precios")


class StockModel(Base):
    """Tabla de stock: una fila por libro (el libro es la clave)."""

    __tablename__ = "stock"
    __table_args__ = (
        CheckConstraint("cantidad >= 0", name="ck_stock_cantidad"),
        CheckConstraint("stock_minimo >= 0", name="ck_stock_minimo"),
    )

    libro_id: Mapped[int] = mapped_column(
        ForeignKey("libros.id", ondelete="CASCADE"), primary_key=True)
    cantidad: Mapped[int] = mapped_column(Integer, default=0)
    stock_minimo: Mapped[int] = mapped_column(Integer, default=0)

    libro: Mapped[LibroModel] = relationship(back_populates="stock")


class CotizacionDolarModel(Base):
    """Tabla con el histórico de cotizaciones (clave: tipo y fecha)."""

    __tablename__ = "cotizaciones_dolar"
    __table_args__ = (
        CheckConstraint("compra > 0 AND venta >= compra",
                        name="ck_cotizaciones_valores"),
    )

    tipo_id: Mapped[int] = mapped_column(
        ForeignKey("tipos_cotizacion.id", ondelete="RESTRICT"),
        primary_key=True)
    fecha: Mapped[datetime.date] = mapped_column(Date, primary_key=True)
    compra: Mapped[float] = mapped_column(Importe)
    venta: Mapped[float] = mapped_column(Importe)

    tipo: Mapped[TipoCotizacionModel] = relationship(
        back_populates="cotizaciones")
