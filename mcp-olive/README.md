# Olive MCP Server

MCP server que permite editar y exportar proyectos de **Olive Video Editor** desde CLI/IA.

## Características

- **Backup automático** de proyectos `.ove`/`.ovexml` antes de cada modificación
- **Exportación headless** de secuencias a video
- **Creación de proyectos** desde cero con resolución/FPS configurables
- **Añadir footage** a proyectos existentes
- **Información detallada** del proyecto (secuencias, resolución, footage)

## Instalación

```bash
cd /home/adolph/proyectos/LFAD/en-curso/olive/mcp-olive
pip install -r requirements.txt
```

## Configuración en OpenCode

Añade esto a `~/.config/opencode/opencode.json`:

```json
{
  "mcpServers": {
    "olive": {
      "command": "python3",
      "args": ["/home/adolph/proyectos/LFAD/en-curso/olive/mcp-olive/mcp_olive_server.py"],
      "env": {
        "OLIVE_BINARY": "/usr/local/bin/olive-editor"
      }
    }
  }
}
```

## Herramientas

### `olive_export`
Exporta una secuencia de Olive a video.
```
project_path: Ruta al .ove o .ovexml
output_path:  Ruta de salida del video
```

### `olive_backup`
Gestiona backups del proyecto.
```
action:       create | list | restore
project_path: Ruta al proyecto
backup_id:    ID del backup (solo restore)
```

### `olive_project_info`
Muestra info detallada del proyecto.

### `olive_create_project`
Crea un proyecto nuevo con una secuencia.

### `olive_add_clip`
Añade un archivo de media al proyecto.

## Backups

Los backups se almacenan en `~/.olive-mcp/backups/`. Cada backup crea una copia timestampada del `.ovexml`. Al restaurar, se crea un backup automático del estado actual primero.

## Compilar Olive (si no está instalado)

```bash
cd /home/adolph/proyectos/LFAD/en-curso/olive
mkdir -p build && cd build
cmake .. -DCMAKE_BUILD_TYPE=Release
make -j$(nproc)
sudo make install
```
