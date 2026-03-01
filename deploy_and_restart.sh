#!/bin/bash
# Script para copiar los cambios al entorno de produccion y reiniciar el servicio
# de forma limpia asegurando que el dispositivo se inicialice correctamente.

echo "Copiando app.py a /home/juan/projects/loupedeckjuan/..."
cp /home/juan/codigo/projects/loupdeckPopOs/app.py /home/juan/projects/loupedeckjuan/app.py

echo "Deteniendo servicio (esto ahora cierra la conexión de forma segura gracias al signal handler)..."
systemctl --user stop loupedeck

echo "Esperando 5 segundos para liberar el hardware..."
sleep 5

echo "Iniciando servicio..."
systemctl --user start loupedeck

echo "Mostrando estado..."
sleep 1
systemctl --user status loupedeck --no-pager | grep "Active"
echo "¡Despliegue y reinicio completado!"
