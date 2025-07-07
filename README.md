# DCSH-X: Tablero Digital de Aulas - API Realtime

Este proyecto es una API en tiempo real desarrollada con **FastAPI** que permite gestionar y visualizar el estado de las aulas en un entorno académico. La API proporciona endpoints para obtener y actualizar información sobre las aulas, así como soporte para conexiones WebSocket para actualizaciones en tiempo real.

## Características

- **API REST**: Endpoints para consultar y actualizar el estado de las aulas.
- **WebSocket**: Comunicación en tiempo real con los clientes conectados.
- **Procesamiento de datos**: Transformación de datos crudos en un formato adecuado para el frontend.
- **CORS habilitado**: Permite la integración con aplicaciones frontend como React.
- **Simulación de datos**: Endpoint para probar la API con datos de ejemplo.

## Requisitos

- Python 3.10 o superior
- FastAPI
- Uvicorn
- Dependencias adicionales especificadas en el archivo `requirements.txt` (si aplica)

## Instalación

1. Clona este repositorio:
   ```bash
   git clone https://github.com/tu-usuario/tablero-aulas-api.git
   cd tablero-aulas-api
   ```

2. Crea un entorno virtual y actívalo:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # En Windows: .venv\Scripts\activate
   ```

3. Instala las dependencias:
   ```bash
   pip install -r requirements.txt
   ```

## Uso

1. Inicia el servidor de desarrollo:
   ```bash
   uvicorn main:app --reload
   ```

2. Accede a la documentación interactiva de la API en:
   - Swagger UI: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
   - Redoc: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

3. Para probar las actualizaciones en tiempo real, conecta un cliente WebSocket al endpoint `/ws`.

## Endpoints Principales

- `GET /`: Verifica que la API está funcionando correctamente.
- `GET /api/classrooms`: Obtiene el estado actual de las aulas.
- `POST /api/classrooms`: Actualiza el estado de las aulas con datos proporcionados.
- `POST /api/simulate-update`: Simula una actualización de datos con un ejemplo predefinido.
- `WS /ws`: Endpoint WebSocket para actualizaciones en tiempo real.

## Estructura del Proyecto

```
tablero-aulas-api/
├── main.py          # Código principal de la API
├── .gitignore       # Archivos y carpetas ignorados por Git
├── README.md        # Documentación del proyecto
└── __pycache__/     # Archivos generados automáticamente (ignorados)
```

## Autor

**Daniel Limón**   
dani@dlimon.net

## Licencia

Este proyecto está bajo la licencia MIT. Consulta el archivo `LICENSE` para más detalles.
