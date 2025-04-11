import flet as ft
import mysql.connector

def main(page: ft.Page):
    # Conexión a la base de datos MySQL
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="k921k76",
        database="zapateria"
    )
    cursor = conn.cursor()

    # Función para registrar un proveedor
    def registrar_proveedor(e):
        nombre_empresa = nombre_empresa_input.value
        contacto = contacto_input.value
        telefono = telefono_input.value
        email = email_input.value
        direccion = direccion_input.value

        if nombre_empresa:
            try:
                cursor.execute(
                    "INSERT INTO proveedores (nombre_empresa, contacto, telefono, email, direccion) VALUES (%s, %s, %s, %s, %s)",
                    (nombre_empresa, contacto, telefono, email, direccion)
                )
                conn.commit()
                mostrar_mensaje("Proveedor registrado exitosamente!", "success")
                limpiar_campos()
                cargar_proveedores()
            except Exception as ex:
                mostrar_mensaje(f"Error: {ex}", "error")
        else:
            mostrar_mensaje("Por favor, completa los campos obligatorios.", "error")

    # Función para actualizar un proveedor
    def actualizar_proveedor(proveedor_id):
        nombre_empresa = nombre_empresa_input.value
        contacto = contacto_input.value
        telefono = telefono_input.value
        email = email_input.value
        direccion = direccion_input.value

        if nombre_empresa:
            try:
                cursor.execute(
                    "UPDATE proveedores SET nombre_empresa = %s, contacto = %s, telefono = %s, email = %s, direccion = %s WHERE id_proveedor = %s",
                    (nombre_empresa, contacto, telefono, email, direccion, proveedor_id)
                )
                conn.commit()
                mostrar_mensaje("Proveedor actualizado exitosamente!", "success")
                limpiar_campos()
                cargar_proveedores()
            except Exception as ex:
                mostrar_mensaje(f"Error: {ex}", "error")
        else:
            mostrar_mensaje("Por favor, completa los campos obligatorios.", "error")

    # Función para eliminar un proveedor
    def eliminar_proveedor(proveedor_id):
        try:
            cursor.execute("DELETE FROM proveedores WHERE id_proveedor = %s", (proveedor_id,))
            conn.commit()
            mostrar_mensaje("Proveedor eliminado exitosamente!", "success")
            cargar_proveedores()
        except Exception as ex:
            mostrar_mensaje(f"Error: {ex}", "error")

    # Función para cargar proveedores
    def cargar_proveedores():
        proveedores_container.controls.clear()
        cursor.execute("SELECT id_proveedor, nombre_empresa, contacto, telefono FROM proveedores")
        proveedores = cursor.fetchall()
        for proveedor in proveedores:
            proveedores_container.controls.append(
                ft.Row(
                    [
                        ft.Text(f"{proveedor[1]} - {proveedor[2]} - {proveedor[3]}", expand=True, color="black"),
                        ft.ElevatedButton("Editar", on_click=lambda e, id=proveedor[0]: cargar_datos_para_editar(id), bgcolor="blue", color="black"),
                        ft.ElevatedButton("Eliminar", on_click=lambda e, id=proveedor[0]: eliminar_proveedor(id), bgcolor="red", color="black"),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                )
            )
        page.update()

    # Función para cargar datos en los campos para editar
    def cargar_datos_para_editar(proveedor_id):
        cursor.execute("SELECT nombre_empresa, contacto, telefono, email, direccion FROM proveedores WHERE id_proveedor = %s", (proveedor_id,))
        proveedor = cursor.fetchone()
        if proveedor:
            nombre_empresa_input.value = proveedor[0]
            contacto_input.value = proveedor[1]
            telefono_input.value = proveedor[2]
            email_input.value = proveedor[3]
            direccion_input.value = proveedor[4]
            registrar_button.text = "Actualizar Proveedor"
            registrar_button.on_click = lambda e: actualizar_proveedor(proveedor_id)
            page.update()

    # Función para limpiar los campos del formulario
    def limpiar_campos():
        nombre_empresa_input.value = ""
        contacto_input.value = ""
        telefono_input.value = ""
        email_input.value = ""
        direccion_input.value = ""
        registrar_button.text = "Registrar Proveedor"
        registrar_button.on_click = registrar_proveedor
        page.update()

    # Función para mostrar mensajes
    def mostrar_mensaje(mensaje, tipo):
        color = "green" if tipo == "success" else "red"
        page.snack_bar = ft.SnackBar(ft.Text(mensaje, color="black"), bgcolor=color, open=True)
        page.update()

    # Configuración de la página
    page.title = "Gestión de Proveedores"
    page.bgcolor = "#F5F5F5"

    # Controles de entrada
    nombre_empresa_input = ft.TextField(label="Nombre de la Empresa", width=300, color="black")
    contacto_input = ft.TextField(label="Contacto", width=300, hint_text="Opcional", color="black")
    telefono_input = ft.TextField(label="Teléfono", width=300, hint_text="Opcional", color="black")
    email_input = ft.TextField(label="Email", width=300, hint_text="Opcional", color="black")
    direccion_input = ft.TextField(label="Dirección", width=300, hint_text="Opcional", color="black")

    # Botones
    registrar_button = ft.ElevatedButton("Registrar Proveedor", on_click=registrar_proveedor, bgcolor="green", color="black")

    # Contenedor para proveedores
    proveedores_container = ft.Column(scroll="adaptive")

    # Layout principal
    page.add(
        ft.Column(
            [
                ft.Text("Gestión de Proveedores", size=30, weight="bold", color="black"),
                ft.Divider(),
                ft.Column(
                    [
                        nombre_empresa_input,
                        contacto_input,
                        telefono_input,
                        email_input,
                        direccion_input,
                        ft.Row([registrar_button], alignment=ft.MainAxisAlignment.CENTER),
                    ],
                    spacing=10,
                ),
                ft.Divider(),
                ft.Text("Proveedores Registrados:", size=20, weight="bold", color="black"),
                proveedores_container,
            ],
            spacing=20,
            alignment=ft.MainAxisAlignment.START,
        )
    )

    # Cargar proveedores al iniciar
    cargar_proveedores()

    # Cerrar conexión al salir
    page.on_close = lambda e: conn.close()

ft.app(target=main)