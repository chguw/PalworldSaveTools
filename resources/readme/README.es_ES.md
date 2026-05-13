<div align="center">

![PalworldSaveTools Logo](../PalworldSaveTools_Blue.png)

# PalworldSaveTools

**Un kit de herramientas completo para editar archivos de guardado de Palworld**

[![Downloads](https://img.shields.io/github/downloads/deafdudecomputers/PalworldSaveTools/total)](https://github.com/deafdudecomputers/PalworldTools/releases/latest)
[![License](https://img.shields.io/github/license/deafdudecomputers/PalworldSaveTools)](LICENSE)
[![Discord](https://img.shields.io/badge/Discord-Join_for_support-blue)](https://discord.gg/sYcZwcT4cT)
[![NexusMods](https://img.shields.io/badge/NexusMods-Download-orange)](https://www.nexusmods.com/palworld/mods/3190)

[English](../../README.md) | [简体中文](README.zh_CN.md) | [Deutsch](README.de_DE.md) | [Español](README.es_ES.md) | [Français](README.fr_FR.md) | [Русский](README.ru_RU.md) | [日本語](README.ja_JP.md) | [한국어](README.ko_KR.md)

---

### **Descarga la versión independiente de [GitHub Releases](https://github.com/deafdudecomputers/PalworldSaveTools/releases/latest)** 

---

</div>

## Índice

- [Características](#características)
- [Instalación](#instalación)
- [Inicio rápido](#inicio-rápido)
- [Descripción general de las herramientas](#descripción-general-de-las-herramientas)
- [Guías](#guías)
- [Solución de problemas](#solución-de-problemas)
- [Creación de ejecutable independiente (solo Windows)](#creación-de-ejecutable-independiente-solo-windows)
- [Contribuyendo](#contribuyendo)
- [Licencia](#licencia)

---

## Características

### Funcionalidad principal

| Característica | Descripción |
|---------|-------------|
| **Análisis de guardado rápido** | Uno de los lectores de archivos guardados más rápidos disponibles |
| **Gestión de jugadores** | Ver, editar, cambiar nombre, cambiar nivel, desbloquear tecnologías y administrar jugadores |
| **Gestión del gremio** | Crea, cambia el nombre, mueve jugadores, desbloquea investigaciones de laboratorio y gestiona gremios |
| **Pal Editor** | Editor completo de estadísticas, habilidades, IVs, rango, almas, género, jefe/alternancia de suerte |
| **Herramientas del campamento base** | Exportar, importar, clonar, ajustar radios y gestionar bases |
| **Visor de mapas** | Mapa interactivo de base y jugadores con coordenadas y detalles |
| **Transferencia de personaje** | Transferir personajes entre diferentes mundos/servidores (guardado cruzado) |
| **Guardar conversión** | Convertir entre formatos Steam y GamePass |
| **Configuración mundial** | Editar la configuración de WorldOption y LevelMeta |
| **Herramientas de marca de tiempo** | Corregir marcas de tiempo negativas y restablecer los tiempos de los jugadores |

### Herramientas todo en uno

El paquete **Herramientas todo en uno** proporciona una gestión integral de guardado:

- **Herramientas de eliminación**
  - Eliminar jugadores, bases o gremios
  - Eliminar jugadores inactivos según los umbrales de tiempo.
  - Elimina jugadores duplicados y gremios vacíos.
  - Eliminar datos sin referencia/huérfanos

- **Herramientas de limpieza**
  - Eliminar elementos no válidos/modificados
  - Eliminar pals y passives no válidos
  - Arreglar pals ilegal (límite máximo de estadísticas legales)
  - Eliminar estructuras no válidas
  - Restablecer torretas antiaéreas
  - Desbloquear private chests

- **Herramientas del gremio**
  - Reconstruir todos los gremios
  - Mover jugadores entre gremios
  - Convertir al líder del gremio de jugadores
  - Cambiar el nombre de los gremios
  - Nivel máximo de gremio
  - Desbloquear todas las investigaciones de laboratorio

- **Herramientas del reproductor**
  - Editar estadísticas y habilidades del jugador pal
  - Desbloquear todas las tecnologías
  - Desbloquear la jaula de visualización
  - Subir o bajar de nivel a los jugadores.
  - Cambiar el nombre de los jugadores

- **Guardar Utilidades**
  - Restablecer misiones
  - Restablecer mazmorras
  - Corregir marcas de tiempo
  - Recortar inventarios sobrellenados
  - Generar comandos de PalDefender

### Herramientas adicionales

| Herramienta | Descripción |
|------|-------------|
| **Editar jugador Pals** | pal editor completo con estadísticas, habilidades, IVs, talentos, almas, rango y género |
| **SteamConvertidor ID** | Convierta ID de Steam a UID de Palworld |
| **Reparar el guardado del host** | Intercambiar UID entre dos jugadores (por ejemplo, para intercambio de host) |
| **Inyector de ranura** | Aumentar espacios de palbox por jugador |
| **Restaurar mapa** | Aplicar el progreso del mapa desbloqueado en todos los mundos/servidores |
| **Cambiar nombre del mundo** | Cambiar el nombre del mundo en LevelMeta |
| **Editor de opciones mundiales** | Editar configuración y configuración mundial |
| **Editor LevelMeta** | Editar metadatos mundiales (nombre, host, nivel) |

---

## Instalación

### Requisitos previos

**Para independiente (Windows):**
-Windows 10/11
- [Microsoft Visual C++ Redistributable](https://learn.microsoft.com/en-us/cpp/windows/latest-supported-vc-redist?view=msvc-170#latest-microsoft-visual-c-redistributable-version) (2015-2022)

**Para ejecutar desde el código fuente (todas las plataformas):**
- Python 3.11 o superior

### Independiente (Windows - Recomendado)

1. Descargue la última versión de [GitHub Releases](https://github.com/deafdudecomputers/PalworldSaveTools/releases/latest)
2. Extraiga el archivo zip
3. Ejecute `PalworldSaveTools.exe`

### Desde la fuente (todas las plataformas)

Los scripts de inicio crean automáticamente un entorno virtual e instalan todas las dependencias.

**Usando uv:**
```bash
git clone https://github.com/deafdudecomputers/PalworldSaveTools.git
cd PalworldSaveTools
uv venv --python 3.12
uv run start.py
```

**Windows:**
```bash
git clone https://github.com/deafdudecomputers/PalworldSaveTools.git
cd PalworldSaveTools
start_win.cmd
```

**Linux:**
```bash
git clone https://github.com/deafdudecomputers/PalworldSaveTools.git
cd PalworldSaveTools
chmod +x start_linux.sh
./start_linux.sh
```

### Sucursales

- **Estable** (recomendado): `git clone https://github.com/deafdudecomputers/PalworldSaveTools.git`
- **Beta** (últimas funciones): `git clone -b beta https://github.com/deafdudecomputers/PalworldSaveTools.git`

---

## Inicio rápido

1. **Carga tu guardado**
   - Haga clic en el botón de menú en el encabezado
   - Seleccione **Cargar Guardar**
   - Navega a tu carpeta de guardado de Palworld
   - Seleccione `Level.sav`

2. **Explora tus datos**
   - Utilice las pestañas para ver jugadores, gremios, bases o el mapa.
   - Buscar y filtrar para encontrar entradas específicas

3. **Hacer cambios**
   - Seleccionar elementos para editar, eliminar o modificar
   - Haga clic derecho para acceder a menús contextuales con opciones adicionales

4. **Guarde sus cambios**
   - Haga clic en el botón de menú → **Guardar cambios**
   - Las copias de seguridad se crean automáticamente

---

## Descripción general de las herramientas

### Herramientas todo en uno (AIO)

La interfaz principal para una gestión integral de guardados con cinco pestañas:

**Pestaña Inventario de jugadores**: vea y administre todos los inventarios de jugadores en el servidor
- Editar estadísticas de jugadores, inventario y equipo equipado.
- Posibilidad de editar la calidad, agregar y eliminar cualquier cosa del inventario y del equipo equipado.

**Pestaña Inventario de base**: vea y administre los inventarios de todas las bases en el servidor.
- Editar inventario base.
- Posibilidad de borrar contenedores, editar la calidad, agregar y eliminar cualquier cosa de los inventarios base.
- Filtrado incluido para cualquier posibilidad de trampa.

**Pestaña Jugadores** - Ver y administrar todos los jugadores en el servidor
- Editar nombres de jugadores, niveles y recuentos de pal
- Eliminar jugadores inactivos
- Ver gremios de jugadores y el último tiempo en línea

**Pestaña Gremios** - Administrar gremios y sus bases
- Cambiar el nombre de los gremios, cambiar los líderes
- Ver ubicaciones y niveles de bases
- Eliminar gremios vacíos o inactivos

**Pestaña Bases** - Ver todos los campamentos base
- Exportar/importar planos de base.
- Clonar bases a otros gremios.
- Ajustar el radio de la base

### Visor de mapas

Visualización interactiva de tu mundo:
- Ver todas las ubicaciones de las bases y posiciones de los jugadores.
- Filtrar por gremio o nombre de jugador
- Haga clic en los marcadores para obtener información detallada.
- Generar comandos `killnearestbase` para PalDefender

### Transferencia de personajes

Transferir personajes entre diferentes mundos/servidores (guardado cruzado):
- Transferir uno o todos los jugadores.
- Conserva personajes, pals, inventario y tecnología.
- Útil para migrar entre servidores cooperativos y dedicados

### Reparar host Guardar

Intercambia UID entre dos jugadores:
- Transferir el progreso de un jugador a otro.
- Esencial para transferencias de host/cooperativo a servidor
- Útil para intercambiar roles de anfitrión entre jugadores.
- Útil para cambios de plataforma (Xbox ↔ Steam)
- Resuelve problemas de asignación de UID de host/servidor.
- **Nota:** El jugador afectado debe tener un personaje creado en el objetivo guardado primero.

---

## Guías

### Guardar ubicaciones de archivos

**Anfitrión/Cooperativo:**
```
%localappdata%\Pal\Saved\SaveGames\YOURID\RANDOMID\
```

**Servidor Dedicado:**
```
steamapps\common\Palworld\Pal\Saved\SaveGames\0\RANDOMSERVERID\
```

### Desbloqueo del mapa

<details>
<summary>Haga clic para ampliar las instrucciones de desbloqueo del mapa</summary>

1. Copiar `LocalData.sav` de `resources\`
2. Encuentra tu servidor/carpeta de guardado mundial
3. Reemplace el `LocalData.sav` existente con el archivo copiado.
4. Inicie el juego con un mapa completamente desbloqueado.

> **Nota:** Utilice la herramienta **Restaurar mapa** en la pestaña Herramientas para aplicar el mapa desbloqueado a TODOS sus mundos/servidores a la vez con copias de seguridad automáticas.

</details>

### Host → Transferencia de servidor

<details>
<summary>Haga clic para expandir la guía de transferencia de host a servidor</summary>

1. Copie las carpetas `Level.sav` y `Players` desde el guardado del host.
2. Pegar en la carpeta de guardado del servidor dedicado.
3. Inicie el servidor, cree un nuevo personaje.
4. Espere a que se guarde automáticamente y luego cierre
5. Utilice **Fix Host Save** para migrar GUID
6. Copie los archivos y ejecútelos

**Utilizando Fix Host Save:**
- Seleccione el `Level.sav` de su carpeta temporal
- Elige el **carácter antiguo** (del guardado original)
- Elige el **nuevo personaje** (que acabas de crear)
- Haga clic en **Migrar**

</details>

### Intercambio de host (cambio de host)

<details>
<summary>Haga clic para expandir la guía de intercambio de host</summary>

**Antecedentes:**
- El anfitrión siempre usa `0001.sav`: el mismo UID para quien sea el anfitrión
- Cada cliente utiliza un guardado UID único y regular (por ejemplo, `123xxx.sav`, `987xxx.sav`)

**Requisitos previos:**
Ambos jugadores (antiguo anfitrión y nuevo anfitrión) deben generar sus partidas guardadas habituales. Esto sucede al unirse al mundo del anfitrión y crear un nuevo personaje.

**Pasos:**

1. **Asegúrese de que existan guardados regulares**
   - El jugador A (antiguo anfitrión) debe tener una partida guardada regularmente (por ejemplo, `123xxx.sav`)
   - El jugador B (nuevo anfitrión) debe tener una partida guardada regularmente (por ejemplo, `987xxx.sav`)

2. **Cambie el guardado del host anterior al guardado normal**
   - Utilice PalworldSaveTools **Fix Host Save** para intercambiar:
   - `0001.sav` → `123xxx.sav` del antiguo anfitrión
   - (Esto mueve el progreso del antiguo anfitrión del puesto de anfitrión al puesto de jugador habitual)

3. **Cambiar el guardado normal del nuevo anfitrión por el guardado del anfitrión**
   - Utilice PalworldSaveTools **Fix Host Save** para intercambiar:
   - `987xxx.sav` → `0001.sav` del nuevo anfitrión
   - (Esto mueve el progreso del nuevo anfitrión al espacio de anfitrión)

**Resultado:**
- El jugador B ahora es el anfitrión con su propio personaje y pals en `0001.sav`
- El jugador A se convierte en cliente con su progreso original en `123xxx.sav`

</details>

### Exportación/Importación básica

<details>
<summary>Haga clic para expandir la guía básica de exportación/importación</summary>

**Exportando una Base:**
1. Cargue su guardado en PST
2. Vaya a la pestaña Bases
3. Haga clic derecho en una base → Exportar base
4. Guardar como archivo `.json`

**Importando una base:**
1. Vaya a la pestaña Bases o al Visor de mapas base.
2. Haga clic derecho en el gremio al que desea importar la base.
3. Seleccione Importar base
4. Seleccione su archivo `.json` exportado

**Clonación de una base:**
1. Haga clic derecho en una base → Clonar base
2. Seleccione el gremio objetivo
3. La base se clonará con posicionamiento desplazado.

**Ajuste del radio de la base:**
1. Haga clic derecho en una base → Ajustar radio
2. Ingrese un nuevo radio (50% - 1000%)
3. Guarde y cargue el archivo guardado en el juego para las estructuras que desea reasignar.

</details>

---

## Solución de problemas

### "No se encontró VCRUNTIME140.dll"

**Solución:** Instalar [Microsoft Visual C++ Redistributable](https://learn.microsoft.com/en-us/cpp/windows/latest-supported-vc-redist?view=msvc-170#latest-microsoft-visual-c-redistributable-version)

### `struct.error` al analizar guardar

**Causa:** Formato de archivo guardado desactualizado

**Solución:**
1. Cargue el archivo guardado en el juego (modo Solo, Cooperativo o Servidor Dedicado)
2. Esto desencadena una actualización automática de la estructura.
3. Asegúrese de que el guardado se haya actualizado a partir del último parche del juego.

### El convertidor GamePass no funciona

**Solución:**
1. Cierra la versión GamePass de Palworld
2. Espera unos minutos
3. Ejecute el convertidor Steam → GamePass
4. Inicie Palworld en GamePass para verificar

---

## Creación de ejecutable independiente (solo Windows)

Ejecute el script de compilación para crear un ejecutable independiente:

```bash
scripts\build.cmd
```

Esto crea `PST_standalone_v{version}.7z` en la raíz del proyecto.

---

## Contribuyendo

¡Las contribuciones son bienvenidas! No dude en enviar una solicitud de extracción.

1. Bifurcar el repositorio
2. Crea tu rama de funciones (`git checkout -b feature/AmazingFeature`)
3. Confirme sus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Empuje hacia la rama (`git push origin feature/AmazingFeature`)
5. Abra una solicitud de extracción

---

## Descargo de responsabilidad

**Utilice esta herramienta bajo su propia responsabilidad. Siempre haga una copia de seguridad de sus archivos guardados antes de realizar modificaciones.**

Los desarrolladores no son responsables de ninguna pérdida de datos guardados o problemas que puedan surgir al utilizar esta herramienta.

---

## Soporte

- **Discord:** [Join us for support, base builds, and more!](https://discord.gg/sYcZwcT4cT)
- **GitHub Problemas:** [Report a bug](https://github.com/deafdudecomputers/PalworldSaveTools/issues)
- **Documentación:** [Wiki](https://github.com/deafdudecomputers/PalworldSaveTools/wiki) *(Actualmente en desarrollo)*

---

## Licencia

Este proyecto tiene la licencia MIT; consulte el archivo [LICENSE](LICENSE) para obtener más detalles.

---

## Agradecimientos

- **Palworld** desarrollado por Pocketpair, Inc.
- Gracias a todos los contribuyentes y miembros de la comunidad que han ayudado a mejorar esta herramienta.

---

<div align="center">

**Hecho con ❤️ para la comunidad Palworld**

[⬆ Back to Top](#palworldsavetools)

</div>