#\. C:\Base de Datos\dbtaller2.sql

DROP DATABASE IF EXISTS dbtaller;
CREATE DATABASE dbtaller;
USE dbtaller;

CREATE TABLE lineainv (
    clavein CHAR(10) PRIMARY KEY,  
    nombre VARCHAR(250)           
);

CREATE TABLE profesor (
    idprofesor INT AUTO_INCREMENT PRIMARY KEY,  
    nombreProf VARCHAR(200)           
);

CREATE TABLE tipoproyecto (
    tipo CHAR(10) PRIMARY KEY, 
    nombre VARCHAR(150)        
);

CREATE TABLE proyecto (
    clave CHAR(10) PRIMARY KEY,  
    nombre VARCHAR(250),        
    clavein CHAR(10),            
    tipo CHAR(10),              
    CONSTRAINT corresponde FOREIGN KEY (clavein) REFERENCES lineainv(clavein),
    CONSTRAINT asignado FOREIGN KEY (tipo) REFERENCES tipoproyecto(tipo)
);

CREATE TABLE alumno (
    nocontrol CHAR(10) PRIMARY KEY,  
    nombre VARCHAR(150),             
    clave CHAR(10),                 
    CONSTRAINT elige FOREIGN KEY (clave) REFERENCES proyecto(clave)
);


CREATE TABLE profesorproy (
    idprofesor INT,                  
    clave CHAR(10),                 
    calificacion FLOAT,              
    rol VARCHAR(45),              
    CONSTRAINT asesora FOREIGN KEY (idprofesor) REFERENCES profesor(idprofesor),
    CONSTRAINT asigna FOREIGN KEY (clave) REFERENCES proyecto(clave)
);

CREATE TABLE datos (
    clave CHAR(10),                 
    proyecto VARCHAR(250),          
    linea CHAR(10),                 
    tipo CHAR(10),                  
    nocontrol CHAR(10),             
    nombre_alumno VARCHAR(150),      
    nombreProf VARCHAR(150),        
    revisor1 VARCHAR(150),           
    revisor2 VARCHAR(150)           
);

-- Crear usuarios
CREATE USER 'alumno'@'localhost' IDENTIFIED BY 'alumno123';
CREATE USER 'profesor'@'localhost' IDENTIFIED BY 'profesor123';
CREATE USER 'admin'@'localhost' IDENTIFIED BY 'admin123';

-- Permisos para alumnos (solo pueden ver y agregar datos de alumnos y proyectos)
GRANT SELECT, INSERT ON dbtaller.alumno TO 'alumno'@'localhost';
GRANT SELECT ON dbtaller.proyecto TO 'alumno'@'localhost';

-- Permisos para profesores (pueden ver y agregar datos en profesor y profesorproy)
GRANT SELECT, INSERT ON dbtaller.profesor TO 'profesor'@'localhost';
GRANT SELECT, INSERT, UPDATE ON dbtaller.profesorproy TO 'profesor'@'localhost';

-- Permisos para administrador (todos los privilegios)
GRANT ALL PRIVILEGES ON dbtaller.* TO 'admin'@'localhost';

-- Aplicar cambios
FLUSH PRIVILEGES;

CREATE TABLE usuarios_permisos (
    id INT AUTO_INCREMENT PRIMARY KEY,  
    usuario VARCHAR(50),               
    permisos TEXT                      
);

INSERT INTO usuarios_permisos (usuario, permisos) 
VALUES 
('alumno', 'SELECT, INSERT en alumno, SELECT en proyecto'),
('profesor', 'SELECT, INSERT en profesor, SELECT, INSERT, UPDATE en profesorproy'),
('admin', 'ALL PRIVILEGES en toda la base de datos dbtaller');


CREATE TABLE area_conocimiento (
    idarea INT AUTO_INCREMENT,  
    nombre_area VARCHAR(150) PRIMARY KEY         
);




INSERT INTO area_conocimiento (nombre_area) VALUES 
('Arquitectura de Computadoras'),
('Ingeniería de Software'),
('Bases de Datos'),
('Redes de Computadoras'),
('Sistemas Operativos'),
('Inteligencia Artificial');

INSERT INTO rubrica (nombre_rubrica, id_area, descripcion) VALUES 
('Rúbrica de Arquitectura de Computadoras', 1, 'Rúbrica para evaluar proyectos de arquitectura de computadoras.'),
('Rúbrica de Ingeniería de Software', 2, 'Rúbrica para evaluar proyectos de ingeniería de software.'),
('Rúbrica de Bases de Datos', 3, 'Rúbrica para evaluar proyectos de bases de datos.'),
('Rúbrica de Redes de Computadoras', 4, 'Rúbrica para evaluar proyectos de redes de computadoras.');

INSERT INTO indicador_rubrica (id_rubrica, descripcion, ponderacion) VALUES 
(1, 'Portada (Obligatoria)', 0),
(1, 'Protocolo con las observaciones resueltas', 0),
(1, 'Desarrollo del proyecto', 20),
(2, 'Marco Teórico Conceptual', 4),
(2, 'Descripción de Procesos', 9),
(3, 'Fundamentación del modelo de base de datos', 10),
(4, 'Definición del problema', 10);
