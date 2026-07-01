# utils.py
from datetime import datetime, timedelta, timezone

# Zona horaria de Tijuana (UTC-8 en invierno / UTC-7 en verano)
UTC_TIJUANA = timezone(timedelta(hours=-7))  # Ajusta según horario actual

def fecha_local_tijuana():
    """Devuelve la hora local de Tijuana."""
    return datetime.now(UTC_TIJUANA)