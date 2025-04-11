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

    # Función para mostrar mensajes
    def mostrar_mensaje(mensaje, tipo):
        color = "green" if tipo == "success" else "red"
        page.snack_bar = ft.SnackBar(ft.Text(mensaje, color="black"), bgcolor=color, open=True)
        page.update()

    # Función para limpiar los campos del formulario
    def limpiar_campos():
        nombre_input.value = ""
        descripcion_input.value = ""
        marca_input.value = ""
        categoria_input.value = ""
        talla_input.value = ""
        color_input.value = ""
        stock_input.value = ""
        precio_input.value = ""
        id_proveedor_input.value = ""
        qr_input.value = ""
        registrar_button.text = "Registrar Producto"
        registrar_button.on_click = registrar_producto
        page.update()

    # Función para registrar un producto
    def registrar_producto(e):
        nombre = nombre_input.value.strip()
        descripcion = descripcion_input.value.strip()
        marca = marca_input.value.strip()
        categoria = categoria_input.value.strip()
        talla_str = talla_input.value.strip()
        color = color_input.value.strip()
        stock_str = stock_input.value.strip()
        precio_str = precio_input.value.strip()
        id_proveedor_str = id_proveedor_input.value.strip()
        qr = qr_input.value.strip()

        if not (nombre and talla_str and stock_str and precio_str and qr):
            mostrar_mensaje("Por favor, completa los campos obligatorios.", "error")
            print("Campos faltantes:", nombre, talla_str, stock_str, precio_str, qr)
            return

        try:
            talla = float(talla_str)
            stock = int(stock_str)
            precio = float(precio_str)
            id_proveedor = int(id_proveedor_str) if id_proveedor_str else None
        except ValueError as ex:
            mostrar_mensaje("Error al convertir talla, stock o precio. Revisa los datos numéricos.", "error")
            print("Error en conversión:", ex)
            return

        try:
            print("Insertando producto:", (nombre, descripcion, marca, categoria, talla, color, stock, precio, id_proveedor, qr))
            cursor.execute(
                "INSERT INTO productos (nombre, descripcion, marca, categoria, talla, color, stock, precio, id_proveedor, qr) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                (nombre, descripcion, marca, categoria, talla, color, stock, precio, id_proveedor, qr)
            )
            conn.commit()
            print("Producto insertado correctamente")
            mostrar_mensaje("Producto registrado exitosamente!", "success")
            limpiar_campos()
            cargar_productos()
        except Exception as ex:
            mostrar_mensaje(f"Error al registrar producto: {ex}", "error")
            print("Excepción en INSERT:", ex)

    # Función para cargar productos
    def cargar_productos():
        productos_container.controls.clear()
        try:
            cursor.execute("SELECT id_producto, nombre, categoria, stock, precio FROM productos")
            productos = cursor.fetchall()
            for producto in productos:
                productos_container.controls.append(
                    ft.Row(
                        [
                            ft.Text(f"{producto[1]} - {producto[2]} - Stock: {producto[3]} - ${producto[4]:,.2f}", expand=True, color="black"),
                            ft.ElevatedButton("Editar", on_click=lambda e, id=producto[0]: cargar_datos_para_editar(id), bgcolor="blue", color="black"),
                            ft.ElevatedButton("Eliminar", on_click=lambda e, id=producto[0]: eliminar_producto(id), bgcolor="red", color="black"),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    )
                )
            page.update()
        except Exception as ex:
            mostrar_mensaje(f"Error al cargar productos: {ex}", "error")

    # Función para cargar datos en los campos para editar
    def cargar_datos_para_editar(producto_id):
        try:
            cursor.execute("SELECT nombre, descripcion, marca, categoria, talla, color, stock, precio, id_proveedor, qr FROM productos WHERE id_producto = %s", (producto_id,))
            producto = cursor.fetchone()
            if producto:
                nombre_input.value = producto[0]
                descripcion_input.value = producto[1]
                marca_input.value = producto[2]
                categoria_input.value = producto[3]
                talla_input.value = producto[4]
                color_input.value = producto[5]
                stock_input.value = producto[6]
                precio_input.value = producto[7]
                id_proveedor_input.value = producto[8]
                qr_input.value = producto[9]
                registrar_button.text = "Actualizar Producto"
                registrar_button.on_click = lambda e: actualizar_producto(producto_id)
                page.update()
        except Exception as ex:
            mostrar_mensaje(f"Error al cargar datos: {ex}", "error")

    # Función para actualizar producto
    def actualizar_producto(producto_id):
        registrar_producto(None)

    # Función para eliminar producto
    def eliminar_producto(producto_id):
        try:
            cursor.execute("DELETE FROM productos WHERE id_producto = %s", (producto_id,))
            conn.commit()
            mostrar_mensaje("Producto eliminado correctamente", "success")
            cargar_productos()
        except Exception as ex:
            mostrar_mensaje(f"Error al eliminar producto: {ex}", "error")

    # Configuración de la página
    page.title = "Gestión de Productos"
    page.bgcolor = "#F5F5F5"

    # Controles de entrada
    nombre_input = ft.TextField(label="Nombre", width=300, color="black")
    descripcion_input = ft.TextField(label="Descripción", width=300, hint_text="Opcional", color="black")
    marca_input = ft.TextField(label="Marca", width=300, hint_text="Opcional", color="black")
    categoria_input = ft.TextField(label="Categoría", width=300, hint_text="Opcional", color="black")
    talla_input = ft.TextField(label="Talla", width=300, color="black")
    color_input = ft.TextField(label="Color", width=300, hint_text="Opcional", color="black")
    stock_input = ft.TextField(label="Stock", width=300, color="black")
    precio_input = ft.TextField(label="Precio", width=300, color="black")
    id_proveedor_input = ft.TextField(label="ID Proveedor", width=300, hint_text="Opcional", color="black")
    qr_input = ft.TextField(label="QR", width=300, color="black")

    # Botones
    registrar_button = ft.ElevatedButton("Registrar Producto", on_click=registrar_producto, bgcolor="green", color="black")

    # Contenedor para productos
    productos_container = ft.Column(scroll="adaptive")

    # Layout principal
    page.add(
        ft.Column(
            [
                ft.Text("Gestión de Productos", size=30, weight="bold", color="black"),
                ft.Divider(),
                ft.Column(
                    [
                        ft.Row(
                            [
                                ft.Column(
                                    [
                                        nombre_input,
                                        descripcion_input,
                                        marca_input,
                                        categoria_input,
                                        talla_input,
                                    ],
                                    spacing=10,
                                ),
                                ft.Column(
                                    [
                                        color_input,
                                        stock_input,
                                        precio_input,
                                        id_proveedor_input,
                                        qr_input,
                                    ],
                                    spacing=10,
                                ),
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        ),
                        ft.Row([registrar_button], alignment=ft.MainAxisAlignment.CENTER),
                    ],
                    spacing=20,
                ),
                ft.Divider(),
                ft.Text("Productos Registrados:", size=20, weight="bold", color="black"),
                productos_container,
            ],
            spacing=20,
            alignment=ft.MainAxisAlignment.START,
            scroll="adaptive",
        )
    )

    cargar_productos()
    page.on_close = lambda e: conn.close()

ft.app(target=main)
