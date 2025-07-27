from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Any
import os
import json
import asyncio
from datetime import datetime
import uvicorn

from dotenv import load_dotenv
load_dotenv()

app = FastAPI(title="DCSH-X : Tablero digital de aulas - API Realtime", version="1.0.0")

# CORS para que React pueda conectarse
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Almacenamiento en memoria para el estado actual
current_classrooms_data = {}

# Lista de conexiones WebSocket activas
active_connections: List[WebSocket] = []

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        print(f"Nueva conexión WebSocket. Total: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        print(f"Conexión cerrada. Total: {len(self.active_connections)}")

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except:
                # Si falla, remover la conexión
                self.active_connections.remove(connection)

manager = ConnectionManager()

@app.get("/")
async def root():
    return {"message": "DCSH-X : Tablero de aulas - API Realtime funcionando correctamente"}

@app.get("/api/classrooms")
async def get_classrooms():
    """Obtener el estado actual de las aulas"""
    return current_classrooms_data

def parse_program(program_str: str) -> Dict[str, str]:
    import re
    """Extrae Programa, Curso, Profesor desde un string como 'Programa|Curso|Profesor', tolerando espacios extra."""
    parts = re.split(r'\s*\|\s*', program_str.strip())

    if len(parts) < 3:
        return {
            "program": parts[0] if len(parts) > 0 else "",
            "subject": parts[1] if len(parts) > 1 else "",
            "professor": "No especificado"
        }

    return {
        "program": parts[0],
        "subject": parts[1],
        "professor": parts[2]
    }

def process_classroom_data(raw_data: Dict[Any, Any]) -> Dict[Any, Any]:
    """Procesa los datos crudos para extraer solo lo necesario para el frontend"""
        
    if os.getenv('TEST_MONDAY') == 'true':
        # Forzar el día a lunes para pruebas
        print ("Forzando día a lunes para pruebas")
        current_time = datetime(2024, 6, 10, 8, 0)
    else:
        # Obtener la fecha y hora actual
        print ("Usando fecha y hora actual")
        current_time = datetime.now()
    current_day = current_time.strftime('%A').lower()
    
    processed_classrooms = []
    
    for idx, classroom in enumerate(raw_data.get('classrooms', [])):
        day_schedule = classroom.get('schedule', {}).get(current_day, [])
        
        # Filtrar franjas horarias entre 7:00 y 21:00
        filtered_schedule = [
            slot for slot in day_schedule
            if "07:00" <= slot.get('start_time', '') <= "21:00"
        ]
        
        # Iniciar variables DENTRO del bucle de aula
        schedule_for_day = []
        current_program = None
        
        for slot in filtered_schedule:
            slot_program = slot.get('program', '').strip()
            start_time = slot['start_time']
            end_time = slot['end_time']
            
            # Lógica corregida para extensiones
            if slot_program == "":
                # String vacío = extensión del programa anterior
                # Mantener current_program como está (puede ser None o un programa)
                pass
            elif slot_program == "_":
                # Guión bajo = fin de programa o slot explícitamente vacío
                current_program = None
            else:
                # Nuevo programa encontrado
                current_program = parse_program(slot_program)
            
            if current_program:
                schedule_for_day.append({
                    "program": current_program["program"],
                    "subject": current_program["subject"],
                    "professor": current_program["professor"],
                    "time": f"{start_time}-{end_time}",
                    "status": "occupied"
                })
            else:
                schedule_for_day.append({
                    "program": "",
                    "subject": "",
                    "professor": "",
                    "time": f"{start_time}-{end_time}",
                    "status": "available"
                })
        
        # Crear el objeto de aula con su propio schedule
        processed_classroom = {
            "number": classroom.get('number'),
            "building": classroom.get('building'),
            "name": classroom.get('name'),
            "capacity": classroom.get('capacity'),
            "schedule_for_day": schedule_for_day,
            "last_updated": classroom.get('last_updated')
        }
        
        processed_classrooms.append(processed_classroom)
    
    return {
        "timestamp": raw_data.get('timestamp'),
        "classrooms": processed_classrooms,
        "total_classrooms": len(processed_classrooms),
        "current_time": current_time.isoformat(),
        "current_day": current_day
    }


@app.post("/api/classrooms")
async def update_classrooms(data: Dict[Any, Any]):
    """Endpoint para que el script de Python envíe actualizaciones"""
    global current_classrooms_data
    
    # Procesar los datos para extraer solo lo necesario
    processed_data = process_classroom_data(data)
    
    # Actualizar datos
    current_classrooms_data = processed_data
    current_classrooms_data["last_updated"] = datetime.now().isoformat()
    
    # Enviar actualización a todos los clientes conectados via WebSocket
    message = json.dumps({
        "type": "classrooms_update",
        "data": current_classrooms_data
    }, indent=2)
    await manager.broadcast(message)
    
    return {"status": "success", "message": "Datos procesados y enviados a clientes"}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    
    try:
        # Enviar datos actuales al cliente recién conectado
        if current_classrooms_data:
            initial_message = json.dumps({
                "type": "classrooms_update",
                "data": current_classrooms_data
            })
            await websocket.send_text(initial_message)
        
        # Mantener conexión activa
        while True:
            # Esperar por mensajes del cliente (opcional)
            data = await websocket.receive_text()
            
            # Responder con ping/pong para mantener conexión
            if data == "ping":
                await websocket.send_text("pong")
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# Endpoint para simular actualizaciones con datos reales
@app.post("/api/simulate-update")
async def simulate_update():
    """Simular una actualización de datos usando el formato real"""
    sample_data = {
        "timestamp": datetime.now().isoformat(),
        "classrooms": [
            {
                "number": "15",
                "building": "A",
                "name": "AULA 16",
                "capacity": 25,
                "schedule": {
                    "monday": [
                        {
                            "start_time": "08:00",
                            "end_time": "09:00",
                            "subject": "",
                            "professor": "",
                            "program": "MCP Seminario Teórico I Dr. Jerónimo Repoll"
                        },
                        {
                            "start_time": "11:00",
                            "end_time": "12:00",
                            "subject": "",
                            "professor": "",
                            "program": "MCP Seminario Metodológico Dra. Dulce Martínez"
                        },
                        {
                            "start_time": "14:00",
                            "end_time": "15:00",
                            "subject": "",
                            "professor": "",
                            "program": "_"
                        }
                    ]
                }
            },
            {
                "number": "17",
                "building": "A",
                "name": "CDOC",
                "capacity": 10,
                "schedule": {
                    "monday": [
                        {
                            "start_time": "08:00",
                            "end_time": "09:00",
                            "subject": "",
                            "professor": "",
                            "program": "DH Seminario de Tesis IX Drs. Lizarazo/Závala/Dulce/Andión/Vicente"
                        },
                        {
                            "start_time": "11:00",
                            "end_time": "12:00",
                            "subject": "",
                            "professor": "",
                            "program": "_"
                        }
                    ]
                }
            },
            {
                "number": "20",
                "building": "A",
                "name": "AULA USOS MULTIPLES",
                "capacity": 40,
                "schedule": {
                    "monday": [
                        {
                            "start_time": "07:00",
                            "end_time": "08:00",
                            "subject": "",
                            "professor": "",
                            "program": "alfa_lunes"
                        },
                        {
                            "start_time": "11:00",
                            "end_time": "12:00",
                            "subject": "",
                            "professor": "",
                            "program": "PSI"
                        },
                        {
                            "start_time": "20:00",
                            "end_time": "21:00",
                            "subject": "",
                            "professor": "",
                            "program": "omega_lunes"
                        }
                    ]
                }
            }
        ],
        "total_classrooms": 3
    }
    
    await update_classrooms(sample_data)
    return {"status": "success", "message": "Datos de ejemplo procesados y enviados"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)