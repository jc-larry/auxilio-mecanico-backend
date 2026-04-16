# Backend - Sistema de Gestión de Servicios Mecánicos

## Objetivos

### Objetivo general

Desarrollar un backend robusto y eficiente para la gestión de servicios mecánicos y atención de emergencias.

### Objetivos específicos

* Implementar un sistema de autenticación seguro.
* Gestionar solicitudes de servicio en tiempo real.
* Administrar usuarios, talleres y personal.
* Garantizar la integridad y disponibilidad de los datos.
* Facilitar la integración con el frontend mediante APIs REST.

## Tecnologías utilizadas

* Python
* FastAPI
* SQL (base de datos relacional)
* ORM (por ejemplo, SQLAlchemy)
* Uvicorn (servidor ASGI)

## Estructura del proyecto

```
backend/
 ├── app/
 │   ├── api/
 │   ├── models/
 │   ├── schemas/
 │   ├── services/
 │   ├── core/
 │   └── main.py
 ├── requirements.txt
 └── README.md
```

### Descripción de componentes

* **api/**: Define los endpoints del sistema.
* **models/**: Representa las entidades de la base de datos.
* **schemas/**: Define los esquemas de validación.
* **services/**: Contiene la lógica de negocio.
* **core/**: Configuraciones generales (seguridad, base de datos, etc.).

## Funcionalidades principales

* Autenticación y autorización de usuarios.
* Registro y gestión de talleres mecánicos.
* Creación y seguimiento de solicitudes de servicio.
* Asignación de recursos (mecánicos, grúas, etc.).
* Manejo de estados de servicio.
* Registro histórico de operaciones.

## Diseño de la API

El sistema expone una API REST que permite la comunicación con el frontend. Las principales características incluyen:

* Uso de métodos HTTP (GET, POST, PUT, DELETE).
* Respuestas en formato JSON.
* Manejo de errores mediante códigos HTTP.

## Seguridad

El sistema implementa mecanismos de seguridad tales como:

* Autenticación basada en tokens (JWT).
* Protección de rutas.
* Validación de datos de entrada.
* Manejo seguro de credenciales.

## Despliegue

Para ejecutar el backend en un entorno local:

1. Crear entorno virtual:

```
python -m venv venv
```

2. Activar entorno virtual:

```
source venv/bin/activate
```

3. Instalar dependencias:

```
pip install -r requirements.txt
```

4. Ejecutar servidor:

```
uvicorn app.main:app --reload
```
---

Documento elaborado con fines académicos.
