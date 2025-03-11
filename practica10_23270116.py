import mysql.connector

def conectar_bd():
    return mysql.connector.connect(
        host="tu_host",
        user="tu_usuario",
        password="tu_contraseña",
        database="tu_base_de_datos"
    )

def crear_profesor(nombre):
    conexion = conectar_bd()
    cursor = conexion.cursor()
    cursor.execute("INSERT INTO profesor (nombreProf) VALUES (%s)", (nombre,))
    conexion.commit()
    conexion.close()

def obtener_profesores():
    conexion = conectar_bd()
    cursor = conexion.cursor()
    cursor.execute("SELECT * FROM profesor")
    profesores = cursor.fetchall()
    conexion.close()
    return profesores

def actualizar_profesor(id, nuevo_nombre):
    conexion = conectar_bd()
    cursor = conexion.cursor()
    cursor.execute("UPDATE profesor SET nombreProf = %s WHERE idprofesor = %s", (nuevo_nombre, id))
    conexion.commit()
    conexion.close()

def eliminar_profesor(id):
    conexion = conectar_bd()
    cursor = conexion.cursor()
    cursor.execute("DELETE FROM profesor WHERE idprofesor = %s", (id,))
    conexion.commit()
    conexion.close()
