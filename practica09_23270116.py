import mysql.connector

def conectar_db():
    return mysql.connector.connect(
        host="localhost",
        user="root",  
        password="k921k76",
        database="dbtaller"
    )

def crear_tipo_proyecto(tipo, nombre):
    conn = conectar_db()
    cursor = conn.cursor()
    sql = "INSERT INTO tipoproyecto (tipo, nombre) VALUES (%s, %s)"
    cursor.execute(sql, (tipo, nombre))
    conn.commit()
    conn.close()
    print("Tipo de proyecto creado exitosamente.")

def leer_tipos_proyecto():
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tipoproyecto")
    resultados = cursor.fetchall()
    conn.close()
    for tipo in resultados:
        print(tipo)

def actualizar_tipo_proyecto(tipo, nuevo_nombre):
    conn = conectar_db()
    cursor = conn.cursor()
    sql = "UPDATE tipoproyecto SET nombre = %s WHERE tipo = %s"
    cursor.execute(sql, (nuevo_nombre, tipo))
    conn.commit()
    conn.close()
    print("Tipo de proyecto actualizado correctamente.")

def eliminar_tipo_proyecto(tipo):
    conn = conectar_db()
    cursor = conn.cursor()
    sql = "DELETE FROM tipoproyecto WHERE tipo = %s"
    cursor.execute(sql, (tipo,))
    conn.commit()
    conn.close()
    print("Tipo de proyecto eliminado correctamente.")

# Ejemplo de uso
if __name__ == "__main__":
    while True:
        print("\nGestión de Tipos de Proyecto")
        print("1. Crear Tipo de Proyecto")
        print("2. Leer Tipos de Proyecto")
        print("3. Actualizar Tipo de Proyecto")
        print("4. Eliminar Tipo de Proyecto")
        print("5. Salir")
        opcion = input("Seleccione una opción: ")
        
        if opcion == "1":
            tipo = input("Ingrese el código del tipo: ")
            nombre = input("Ingrese el nombre: ")
            crear_tipo_proyecto(tipo, nombre)
        elif opcion == "2":
            leer_tipos_proyecto()
        elif opcion == "3":
            tipo = input("Ingrese el código del tipo a actualizar: ")
            nuevo_nombre = input("Ingrese el nuevo nombre: ")
            actualizar_tipo_proyecto(tipo, nuevo_nombre)
        elif opcion == "4":
            tipo = input("Ingrese el código del tipo a eliminar: ")
            eliminar_tipo_proyecto(tipo)
        elif opcion == "5":
            break
        else:
            print("Opción no válida. Intente nuevamente.")
