-- ============================================================
-- TRABAJO FINAL: Arquitectura de Datos Híbrida para E-Commerce
-- Parte 1: Modelado DDL - PostgreSQL
-- ============================================================

-- Eliminar tablas si existen (para re-ejecución limpia)
DROP TABLE IF EXISTS Ventas CASCADE;
DROP TABLE IF EXISTS Productos CASCADE;
DROP TABLE IF EXISTS Clientes CASCADE;

-- ------------------------------------------------------------
-- TABLA: Clientes
-- ------------------------------------------------------------
CREATE TABLE Clientes (
    cliente_id    SERIAL          PRIMARY KEY,
    nombre        VARCHAR(100)    NOT NULL,
    email         VARCHAR(150)    NOT NULL UNIQUE,
    telefono      VARCHAR(20),
    direccion     TEXT,
    fecha_registro DATE           NOT NULL DEFAULT CURRENT_DATE
);

-- ------------------------------------------------------------
-- TABLA: Productos
-- ------------------------------------------------------------
CREATE TABLE Productos (
    producto_id   SERIAL          PRIMARY KEY,
    nombre        VARCHAR(150)    NOT NULL,
    descripcion   TEXT,
    precio        NUMERIC(10, 2)  NOT NULL,
    stock         INTEGER         NOT NULL,
    categoria     VARCHAR(80),
    -- CHECK: precio y stock deben ser valores positivos
    CONSTRAINT chk_precio_positivo CHECK (precio > 0),
    CONSTRAINT chk_stock_positivo  CHECK (stock >= 0)
);

-- ------------------------------------------------------------
-- TABLA: Ventas
-- ------------------------------------------------------------
CREATE TABLE Ventas (
    venta_id      SERIAL          PRIMARY KEY,
    cliente_id    INTEGER         NOT NULL,
    producto_id   INTEGER         NOT NULL,
    cantidad      INTEGER         NOT NULL,
    precio_unitario NUMERIC(10,2) NOT NULL,
    monto_total   NUMERIC(10, 2)  NOT NULL,
    fecha_venta   TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP,
    -- FOREIGN KEYs con ON DELETE CASCADE
    CONSTRAINT fk_cliente  FOREIGN KEY (cliente_id)
        REFERENCES Clientes(cliente_id) ON DELETE CASCADE,
    CONSTRAINT fk_producto FOREIGN KEY (producto_id)
        REFERENCES Productos(producto_id) ON DELETE CASCADE,
    -- CHECK: cantidad y monto positivos
    CONSTRAINT chk_cantidad_positiva CHECK (cantidad > 0),
    CONSTRAINT chk_monto_positivo    CHECK (monto_total > 0)
);

-- ------------------------------------------------------------
-- Datos de prueba
-- ------------------------------------------------------------
INSERT INTO Clientes (nombre, email, telefono, direccion) VALUES
    ('Ana García',    'ana.garcia@email.com',    '555-1001', 'Av. Reforma 100, CDMX'),
    ('Luis Martínez', 'luis.martinez@email.com', '555-1002', 'Calle 5 de Mayo 45, Guadalajara'),
    ('María López',   'maria.lopez@email.com',   '555-1003', 'Blvd. Kukulcán 88, Cancún');

INSERT INTO Productos (nombre, descripcion, precio, stock, categoria) VALUES
    ('Panel Solar 400W',  'Panel fotovoltaico monocristalino 400W, resistencia UV',  4500.00, 50, 'Energía Solar'),
    ('Inversor 3kW',      'Inversor de onda senoidal pura 3000W para sistemas off-grid', 7200.00, 20, 'Inversores'),
    ('Cable Solar 6mm²',  'Cable fotovoltaico doble aislamiento, bobina 100m',         850.00, 100, 'Cableado'),
    ('Tornillo M8 x 40',  'Tornillo acero inoxidable para estructura, pack 50 piezas',  120.00, 200, 'Accesorios');

INSERT INTO Ventas (cliente_id, producto_id, cantidad, precio_unitario, monto_total) VALUES
    (1, 1, 4,  4500.00, 18000.00),
    (1, 2, 1,  7200.00,  7200.00),
    (2, 3, 2,   850.00,  1700.00),
    (3, 1, 6,  4500.00, 27000.00),
    (3, 4, 10,  120.00,  1200.00);

-- ------------------------------------------------------------
-- PARTE 1 - iii) Consulta de Negocio con INNER JOIN
-- Reporte: cliente + producto adquirido + monto total
-- ------------------------------------------------------------
SELECT
    v.venta_id,
    c.nombre                          AS cliente,
    c.email                           AS correo_cliente,
    p.nombre                          AS producto,
    p.categoria,
    v.cantidad,
    v.precio_unitario,
    v.monto_total,
    v.fecha_venta
FROM Ventas v
INNER JOIN Clientes  c ON v.cliente_id  = c.cliente_id
INNER JOIN Productos p ON v.producto_id = p.producto_id
ORDER BY v.fecha_venta DESC;
