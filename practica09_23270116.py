import mysql.connector

config = {
    "host": "localhost",       
    "user": "root",            
    "password": "k921k76", 
    "database": "dbtaller"     
}

def conectar():
    try:
        conn = mysql.connector.connect(**config)
        return conn
    except mysql.connector.Error as e:
        print(f"Error de conexión: {e}")
        return None

def insertar_tipo_proyecto(tipo, nombre):
    conn = conectar()
    if conn:
        cursor = conn.cursor()
        sql = "INSERT INTO tipoproyecto (tipo, nombre) VALUES (%s, %s)"
        try:
            cursor.execute(sql, (tipo, nombre))
            conn.commit()
            print("Tipo de proyecto insertado correctamente.")
        except mysql.connector.Error as e:
            print(f"Error al insertar: {e}")
        finally:
            cursor.close()
            conn.close()

def obtener_tipos_proyecto():
    conn = conectar()
    if conn:
        cursor = conn.cursor()
        sql = "SELECT * FROM tipoproyecto"
        try:
            cursor.execute(sql)
            proyectos = cursor.fetchall()
            print("\nLista de Tipos de Proyecto:")
            for proyecto in proyectos:
                print(f"Tipo: {proyecto[0]}, Nombre: {proyecto[1]}")
        except mysql.connector.Error as e:
            print(f"Error al obtener datos: {e}")
        finally:
            cursor.close()
            conn.close()

def actualizar_tipo_proyecto(tipo, nuevo_nombre):
    conn = conectar()
    if conn:
        cursor = conn.cursor()
        sql = "UPDATE tipoproyecto SET nombre = %s WHERE tipo = %s"
        try:
            cursor.execute(sql, (nuevo_nombre, tipo))
            conn.commit()
            print("Tipo de proyecto actualizado correctamente.")
        except mysql.connector.Error as e:
            print(f"Error al actualizar: {e}")
        finally:
            cursor.close()
            conn.close()

def eliminar_tipo_proyecto(tipo):
    conn = conectar()
    if conn:
        cursor = conn.cursor()
        sql = "DELETE FROM tipoproyecto WHERE tipo = %s"
        try:
            cursor.execute(sql, (tipo,))
            conn.commit()
            print("Tipo de proyecto eliminado correctamente.")
        except mysql.connector.Error as e:
            print(f"Error al eliminar: {e}")
        finally:
            cursor.close()
            conn.close()

# Menú para probar las funciones
if __name__ == "__main__":
    while True:
        print("\n=== CRUD Tipos de Proyecto ===")
        print("1. Insertar Tipo de Proyecto")
        print("2. Mostrar Tipos de Proyecto")
        print("3. Actualizar Tipo de Proyecto")
        print("4. Eliminar Tipo de Proyecto")
        print("5. Salir")
        opcion = input("Seleccione una opción: ")

        if opcion == "1":
            tipo = input("Ingrese el código del tipo de proyecto: ")
            nombre = input("Ingrese el nombre del tipo de proyecto: ")
            insertar_tipo_proyecto(tipo, nombre)

        elif opcion == "2":
            obtener_tipos_proyecto()

        elif opcion == "3":
            tipo = input("Ingrese el código del tipo de proyecto a actualizar: ")
            nuevo_nombre = input("Ingrese el nuevo nombre del tipo de proyecto: ")
            actualizar_tipo_proyecto(tipo, nuevo_nombre)

        elif opcion == "4":
            tipo = input("Ingrese el código del tipo de proyecto a eliminar: ")
            eliminar_tipo_proyecto(tipo)

        elif opcion == "5":
            print("Saliendo del programa...")
            break

        else:
            print("Opción no válida. Intente de nuevo.")
