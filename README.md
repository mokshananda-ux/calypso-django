# calypso-django

Calypso-Django

Tienda en línea de artículos únicos (sin cantidad ni variación)
En esta tienda los usuarios pueden explorar un catálogo de productos únicos para agregar los productos deseados a un carrito de compras desde donde se ordena un pedido. Una vez que el pedido está ordenado se configura el tipo de envío para poder efectuar el pago del pedido más el envío. Cuando el pago es confirmado se procede a realizar el envío. Cabe destacar que para poder ordenar un pedido el usuario debe registrarse. El usuario registrado tiene acceso a un panel de control que incluye las secciones: perfil, pedidos, envíos, pagos, reseñas, contraseña. Finalmente, el dueño tiene acceso a un panel de administración que controla todo el sistema y flujo de la tienda.
 
Index(Home):
Presentación
Productos populares
Reseñas
Tienda:
Categorías
Catálogo (paginado)
Detalle del producto:
Imagen principal
Imagenes
Descripción
Marca
Añadir al carrito de compras
Carrito de compras:
Añadir/Quitar
Hacer pedido
Pedido:
Datos personales
Datos producto
Envío:
Datos envío
Pago:
Realizar pago
Panel:
Mi perfil
Mis pedidos
Mis pagos
Mis envíos
Mi contraseña

## Requisitos

- Python 3.13 (o una versión compatible con Django 6.1).
- `pip`, incluido con Python.
- Credenciales de prueba de Stripe para probar los pagos. Para enviar correos, también se necesita acceso a un servidor SMTP.

> La raíz del proyecto Django es esta carpeta (`calypso-django/`), no la carpeta que la contiene. Abre esta carpeta en VS Code o entra en ella en la terminal antes de ejecutar los comandos: aquí están `manage.py`, `requirements.txt` y `calypso/settings.py`.

## Preparar el entorno

Desde una terminal, entra primero en `calypso-django/` y crea el entorno virtual:

```bash
cd calypso-django
python3 -m venv env
```

Actívalo:

```bash
# Linux / macOS
source env/bin/activate

# Windows PowerShell
env\Scripts\Activate.ps1

# Windows (cmd)
env\Scripts\activate.bat
```

Instala las dependencias:

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## Configurar variables de entorno

Crea un archivo `.env` junto a `manage.py` (en `calypso-django/`). Django lo carga desde esa ubicación. Como mínimo, configura estos valores:

```dotenv
SECRET_KEY=pon-aqui-una-clave-secreta-unica
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

EMAIL_HOST=tu-servidor-smtp
EMAIL_PORT=587
EMAIL_HOST_USER=tu-usuario
EMAIL_HOST_PASSWORD=tu-contrasena
EMAIL_USE_TLS=True

STRIPE_SECRET_KEY=sk_test_tu_clave_de_prueba
STRIPE_WEBHOOK_SECRET=
```

Usa una clave secreta propia para `SECRET_KEY` y una clave de prueba de Stripe para `STRIPE_SECRET_KEY`. Sustituye los datos SMTP por los de tu proveedor de correo. `STRIPE_WEBHOOK_SECRET` es opcional; se necesita si vas a validar webhooks de Stripe. `DEBUG` y `ALLOWED_HOSTS` tienen valores predeterminados, pero se muestran arriba para facilitar la configuración local.

El archivo `.env` está excluido de Git: no compartas ni subas claves, contraseñas o credenciales reales al repositorio.

## Migrar la base de datos e iniciar

Con el entorno virtual activado, desde `calypso-django/` ejecuta:

```bash
python manage.py migrate
python manage.py runserver
```

Abre <http://127.0.0.1:8000/>. La base de datos local usa SQLite (`db.sqlite3`). Si necesitas crear un usuario administrador para `/admin/`, ejecuta `python manage.py createsuperuser`.

## Comprobaciones útiles

```bash
python manage.py check
python manage.py test
```
