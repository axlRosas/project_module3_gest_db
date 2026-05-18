# ============================================================
# TRABAJO FINAL: Arquitectura de Datos Híbrida para E-Commerce
# Parte 2: Gestor Transaccional - Python + SQLAlchemy
# ============================================================

from datetime import datetime
from sqlalchemy import (
    create_engine, Column, Integer, String,
    Numeric, Text, DateTime, Date, CheckConstraint,
    ForeignKey
)
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
import subprocess
import os

# ------------------------------------------------------------
# i) CONFIGURACIÓN DEL ORM
# ------------------------------------------------------------
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "admin")
DB_HOST = os.getenv("DB_HOST", subprocess.check_output(
    "ip route | awk '/default/ {print $3}'",
    shell=True,
    text=True
).strip())
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "ecommerce_db")

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

engine  = create_engine(DATABASE_URL, echo=True)   # echo=True imprime el SQL generado
Session = sessionmaker(bind=engine)

Base = declarative_base()


# ------------------------------------------------------------
# MAPEO DE TABLAS A CLASES PYTHON
# ------------------------------------------------------------

class Cliente(Base):
    __tablename__ = "clientes"

    cliente_id     = Column(Integer, primary_key=True, autoincrement=True)
    nombre         = Column(String(100), nullable=False)
    email          = Column(String(150), nullable=False, unique=True)
    telefono       = Column(String(20))
    direccion      = Column(Text)
    fecha_registro = Column(Date, default=datetime.utcnow)

    # Relación 1-a-muchos con Ventas
    ventas = relationship("Venta", back_populates="cliente", cascade="all, delete")

    def __repr__(self):
        return f"<Cliente(id={self.cliente_id}, nombre='{self.nombre}')>"


class Producto(Base):
    __tablename__ = "productos"

    producto_id = Column(Integer, primary_key=True, autoincrement=True)
    nombre      = Column(String(150), nullable=False)
    descripcion = Column(Text)
    precio      = Column(Numeric(10, 2), nullable=False)
    stock       = Column(Integer, nullable=False)
    categoria   = Column(String(80))

    __table_args__ = (
        CheckConstraint("precio > 0",  name="chk_precio_positivo"),
        CheckConstraint("stock >= 0",  name="chk_stock_positivo"),
    )

    ventas = relationship("Venta", back_populates="producto", cascade="all, delete")

    def __repr__(self):
        return f"<Producto(id={self.producto_id}, nombre='{self.nombre}', stock={self.stock})>"


class Venta(Base):
    __tablename__ = "ventas"

    venta_id        = Column(Integer, primary_key=True, autoincrement=True)
    cliente_id      = Column(Integer, ForeignKey("clientes.cliente_id",  ondelete="CASCADE"), nullable=False)
    producto_id     = Column(Integer, ForeignKey("productos.producto_id", ondelete="CASCADE"), nullable=False)
    cantidad        = Column(Integer, nullable=False)
    precio_unitario = Column(Numeric(10, 2), nullable=False)
    monto_total     = Column(Numeric(10, 2), nullable=False)
    fecha_venta     = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        CheckConstraint("cantidad > 0",    name="chk_cantidad_positiva"),
        CheckConstraint("monto_total > 0", name="chk_monto_positivo"),
    )

    cliente  = relationship("Cliente",  back_populates="ventas")
    producto = relationship("Producto", back_populates="ventas")

    def __repr__(self):
        return f"<Venta(id={self.venta_id}, total={self.monto_total})>"


# ------------------------------------------------------------
# ii) LÓGICA DE VENTA CON TRANSACCIÓN (try-except)
# ------------------------------------------------------------

def registrar_venta(cliente_id: int, producto_id: int, cantidad: int) -> dict:
    """
    Registra una venta y descuenta el stock del producto de forma atómica.

    - Si todo sale bien  → session.commit()   (cambios persistidos)
    - Si algo falla      → session.rollback() (ningún cambio queda guardado)

    Args:
        cliente_id:  ID del cliente que realiza la compra.
        producto_id: ID del producto a comprar.
        cantidad:    Número de unidades a adquirir.

    Returns:
        dict con el resultado de la operación.
    """
    session = Session()

    try:
        # 1. Verificar que el cliente existe
        cliente = session.get(Cliente, cliente_id)
        if cliente is None:
            raise ValueError(f"Cliente con ID {cliente_id} no encontrado.")

        # 2. Verificar que el producto existe
        producto = session.get(Producto, producto_id)
        if producto is None:
            raise ValueError(f"Producto con ID {producto_id} no encontrado.")

        # 3. Verificar stock suficiente
        if producto.stock < cantidad:
            raise ValueError(
                f"Stock insuficiente para '{producto.nombre}'. "
                f"Disponible: {producto.stock}, Solicitado: {cantidad}."
            )

        # 4. Calcular monto total
        monto_total = float(producto.precio) * cantidad

        # 5. Descontar stock del producto
        producto.stock -= cantidad

        # 6. Crear y registrar la venta
        nueva_venta = Venta(
            cliente_id      = cliente_id,
            producto_id     = producto_id,
            cantidad        = cantidad,
            precio_unitario = producto.precio,
            monto_total     = monto_total,
            fecha_venta     = datetime.utcnow()
        )
        session.add(nueva_venta)

        # 7. Confirmar TODOS los cambios en una sola transacción atómica
        session.commit()

        print(f"✅ Venta registrada exitosamente.")
        print(f"   Cliente : {cliente.nombre}")
        print(f"   Producto: {producto.nombre}")
        print(f"   Cantidad: {cantidad}")
        print(f"   Total   : ${monto_total:,.2f}")
        print(f"   Stock restante: {producto.stock}")

        return {
            "exito"      : True,
            "venta_id"   : nueva_venta.venta_id,
            "cliente"    : cliente.nombre,
            "producto"   : producto.nombre,
            "monto_total": monto_total,
            "stock_restante": producto.stock
        }

    except ValueError as ve:
        # Error de negocio (stock, ID inválido, etc.)
        session.rollback()
        print(f"❌ Error de negocio: {ve}")
        return {"exito": False, "error": str(ve)}

    except Exception as e:
        # Error inesperado (BD, red, etc.) → revertir todo
        session.rollback()
        print(f"❌ Error inesperado, transacción revertida: {e}")
        return {"exito": False, "error": str(e)}

    finally:
        session.close()


# ------------------------------------------------------------
# FUNCIÓN AUXILIAR: Reporte de ventas por cliente
# ------------------------------------------------------------

def reporte_ventas_cliente(cliente_id: int):
    """Muestra todas las ventas de un cliente con INNER JOIN vía ORM."""
    session = Session()
    try:
        cliente = session.get(Cliente, cliente_id)
        if not cliente:
            print(f"Cliente {cliente_id} no encontrado.")
            return

        print(f"\n📋 Ventas de: {cliente.nombre} ({cliente.email})")
        print("-" * 55)
        total_gastado = 0
        for venta in cliente.ventas:
            print(f"  • {venta.producto.nombre:30s} "
                  f"x{venta.cantidad:3d}  ${float(venta.monto_total):>10,.2f}")
            total_gastado += float(venta.monto_total)
        print(f"{'TOTAL GASTADO':>45s}  ${total_gastado:>10,.2f}")
    finally:
        session.close()


# ------------------------------------------------------------
# PUNTO DE ENTRADA - DEMOSTRACIÓN
# ------------------------------------------------------------
if __name__ == "__main__":
    # Crear tablas (si no existen aún)
    Base.metadata.create_all(engine)
    print("✅ Tablas creadas / verificadas en PostgreSQL.\n")

    # --- Caso 1: Venta exitosa ---
    print("=== CASO 1: Venta exitosa ===")
    registrar_venta(cliente_id=1, producto_id=1, cantidad=2)

    # --- Caso 2: Stock insuficiente (debe hacer rollback) ---
    print("\n=== CASO 2: Stock insuficiente (rollback esperado) ===")
    registrar_venta(cliente_id=2, producto_id=2, cantidad=9999)

    # --- Caso 3: Cliente inexistente (debe hacer rollback) ---
    print("\n=== CASO 3: Cliente inexistente (rollback esperado) ===")
    registrar_venta(cliente_id=999, producto_id=1, cantidad=1)

    # --- Reporte de ventas ---
    print("\n=== REPORTE DE VENTAS ===")
    reporte_ventas_cliente(cliente_id=1)
