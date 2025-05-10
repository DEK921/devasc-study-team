 -- MySQL Workbench Forward Engineering

SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0;
SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0;
SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION';

-- -----------------------------------------------------
-- Schema mydb
-- -----------------------------------------------------
-- -----------------------------------------------------
-- Schema zapateria
-- -----------------------------------------------------

-- -----------------------------------------------------
-- Schema zapateria
-- -----------------------------------------------------
CREATE SCHEMA IF NOT EXISTS `zapateria` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci ;
USE `zapateria` ;

-- -----------------------------------------------------
-- Table `zapateria`.`clientes`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `zapateria`.`clientes` (
  `id_cliente` INT NOT NULL AUTO_INCREMENT,
  `nombre` VARCHAR(100) NOT NULL,
  `apellido` VARCHAR(100) NOT NULL,
  `email` VARCHAR(150) NOT NULL,
  `telefono` VARCHAR(15) NULL DEFAULT NULL,
  `direccion` TEXT NULL DEFAULT NULL,
  `fecha_registro` DATETIME NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id_cliente`),
  UNIQUE INDEX `email` (`email` ASC) VISIBLE)
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8mb4
COLLATE = utf8mb4_0900_ai_ci;


-- -----------------------------------------------------
-- Table `zapateria`.`pedidos`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `zapateria`.`pedidos` (
  `id_pedido` INT NOT NULL AUTO_INCREMENT,
  `id_cliente` INT NULL DEFAULT NULL,
  `fecha_pedido` DATETIME NULL DEFAULT CURRENT_TIMESTAMP,
  `total_pagar` DECIMAL(10,2) NOT NULL,
  `estado` ENUM('Pendiente', 'Enviado', 'Entregado', 'Cancelado') NULL DEFAULT 'Pendiente',
  PRIMARY KEY (`id_pedido`),
  INDEX `id_cliente` (`id_cliente` ASC) VISIBLE,
  CONSTRAINT `pedidos_ibfk_1`
    FOREIGN KEY (`id_cliente`)
    REFERENCES `zapateria`.`clientes` (`id_cliente`)
    ON DELETE CASCADE)
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8mb4
COLLATE = utf8mb4_0900_ai_ci;


-- -----------------------------------------------------
-- Table `zapateria`.`proveedores`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `zapateria`.`proveedores` (
  `id_proveedor` INT NOT NULL AUTO_INCREMENT,
  `nombre_empresa` VARCHAR(150) NOT NULL,
  `contacto` VARCHAR(100) NULL DEFAULT NULL,
  `telefono` VARCHAR(15) NULL DEFAULT NULL,
  `email` VARCHAR(150) NULL DEFAULT NULL,
  `direccion` TEXT NULL DEFAULT NULL,
  PRIMARY KEY (`id_proveedor`))
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8mb4
COLLATE = utf8mb4_0900_ai_ci;


-- -----------------------------------------------------
-- Table `zapateria`.`productos`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `zapateria`.`productos` (
  `id_producto` INT NOT NULL AUTO_INCREMENT,
  `nombre` VARCHAR(100) NOT NULL,
  `descripcion` TEXT NULL DEFAULT NULL,
  `marca` VARCHAR(50) NULL DEFAULT NULL,
  `categoria` VARCHAR(50) NULL DEFAULT NULL,
  `talla` DECIMAL(5,2) NOT NULL,
  `color` VARCHAR(50) NULL DEFAULT NULL,
  `stock` INT NOT NULL DEFAULT '0',
  `precio` DECIMAL(10,2) NOT NULL,
  `fecha_ingreso` DATETIME NULL DEFAULT CURRENT_TIMESTAMP,
  `id_proveedor` INT NULL DEFAULT NULL,
  `qr` CHAR(13) NOT NULL,
  PRIMARY KEY (`id_producto`),
  INDEX `id_proveedor` (`id_proveedor` ASC) VISIBLE,
  CONSTRAINT `productos_ibfk_1`
    FOREIGN KEY (`id_proveedor`)
    REFERENCES `zapateria`.`proveedores` (`id_proveedor`)
    ON DELETE SET NULL)
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8mb4
COLLATE = utf8mb4_0900_ai_ci;


-- -----------------------------------------------------
-- Table `zapateria`.`detalles_pedido`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `zapateria`.`detalles_pedido` (
  `id_detalle` INT NOT NULL AUTO_INCREMENT,
  `id_pedido` INT NULL DEFAULT NULL,
  `id_producto` INT NULL DEFAULT NULL,
  `cantidad` INT NOT NULL,
  `precio_unitario` DECIMAL(10,2) NOT NULL,
  `subtotal` DECIMAL(10,2) NOT NULL,
  PRIMARY KEY (`id_detalle`),
  INDEX `id_pedido` (`id_pedido` ASC) VISIBLE,
  INDEX `id_producto` (`id_producto` ASC) VISIBLE,
  CONSTRAINT `detalles_pedido_ibfk_1`
    FOREIGN KEY (`id_pedido`)
    REFERENCES `zapateria`.`pedidos` (`id_pedido`)
    ON DELETE CASCADE,
  CONSTRAINT `detalles_pedido_ibfk_2`
    FOREIGN KEY (`id_producto`)
    REFERENCES `zapateria`.`productos` (`id_producto`)
    ON DELETE CASCADE)
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8mb4
COLLATE = utf8mb4_0900_ai_ci;


-- -----------------------------------------------------
-- Table `zapateria`.`empleados`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `zapateria`.`empleados` (
  `id_empleado` INT NOT NULL AUTO_INCREMENT,
  `nombre` VARCHAR(100) NOT NULL,
  `apellido` VARCHAR(100) NOT NULL,
  `cargo` VARCHAR(50) NULL DEFAULT NULL,
  `telefono` VARCHAR(10) NULL DEFAULT NULL,
  `email` VARCHAR(150) NULL DEFAULT NULL,
  `contrasena_hash` VARCHAR(60) NULL DEFAULT NULL,
  `fecha_contrato` DATETIME NULL DEFAULT CURRENT_TIMESTAMP,
  `salario` DECIMAL(10,2) NOT NULL,
  PRIMARY KEY (`id_empleado`),
  UNIQUE INDEX `email` (`email` ASC) VISIBLE)
ENGINE = InnoDB
AUTO_INCREMENT = 2
DEFAULT CHARACTER SET = utf8mb4
COLLATE = utf8mb4_0900_ai_ci;


-- -----------------------------------------------------
-- Table `zapateria`.`ventas`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `zapateria`.`ventas` (
  `id_venta` INT NOT NULL AUTO_INCREMENT,
  `id_cliente` INT NULL DEFAULT NULL,
  `id_empleado` INT NULL DEFAULT NULL,
  `fecha_venta` DATETIME NULL DEFAULT CURRENT_TIMESTAMP,
  `total_venta` DECIMAL(10,2) NOT NULL,
  PRIMARY KEY (`id_venta`),
  INDEX `id_cliente` (`id_cliente` ASC) VISIBLE,
  INDEX `id_empleado` (`id_empleado` ASC) VISIBLE,
  CONSTRAINT `ventas_ibfk_1`
    FOREIGN KEY (`id_cliente`)
    REFERENCES `zapateria`.`clientes` (`id_cliente`)
    ON DELETE SET NULL,
  CONSTRAINT `ventas_ibfk_2`
    FOREIGN KEY (`id_empleado`)
    REFERENCES `zapateria`.`empleados` (`id_empleado`)
    ON DELETE SET NULL)
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8mb4
COLLATE = utf8mb4_0900_ai_ci;


-- -----------------------------------------------------
-- Table `zapateria`.`detalles_venta`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `zapateria`.`detalles_venta` (
  `id_detalle` INT NOT NULL AUTO_INCREMENT,
  `id_venta` INT NULL DEFAULT NULL,
  `id_producto` INT NULL DEFAULT NULL,
  `cantidad` INT NOT NULL,
  `precio_unitario` DECIMAL(10,2) NOT NULL,
  `subtotal` DECIMAL(10,2) NOT NULL,
  PRIMARY KEY (`id_detalle`),
  INDEX `id_venta` (`id_venta` ASC) VISIBLE,
  INDEX `id_producto` (`id_producto` ASC) VISIBLE,
  CONSTRAINT `detalles_venta_ibfk_1`
    FOREIGN KEY (`id_venta`)
    REFERENCES `zapateria`.`ventas` (`id_venta`)
    ON DELETE CASCADE,
  CONSTRAINT `detalles_venta_ibfk_2`
    FOREIGN KEY (`id_producto`)
    REFERENCES `zapateria`.`productos` (`id_producto`)
    ON DELETE CASCADE)
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8mb4
COLLATE = utf8mb4_0900_ai_ci;


SET SQL_MODE=@OLD_SQL_MODE;
SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS;
SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS;
