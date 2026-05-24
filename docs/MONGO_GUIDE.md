# Guía de instalación de MongoDB

Cómo dejar MongoDB corriendo en `localhost:27017` según tu sistema operativo.
Una vez instalado, vuelve al [README](../README.md) para cargar los datos y analizarlos.

> **Verificar que quedó listo** (en cualquier sistema):
> ```bash
> mongosh --quiet --eval "db.runCommand({ping: 1})"
> ```
> Si responde `{ ok: 1 }`, MongoDB está corriendo y aceptando conexiones.

---

## Tabla de contenido

- [Linux — Fedora / RHEL](#linux--fedora--rhel)
- [Linux / Windows / macOS — con Podman o Docker (recomendado)](#con-podman-o-docker-recomendado)
- [Windows — instalación nativa](#windows--instalación-nativa)
- [macOS — instalación nativa](#macos--instalación-nativa)
- [Cambiar la URL de conexión](#cambiar-la-url-de-conexión)

---

## Linux — Fedora / RHEL

> ⚠️ **Importante (Fedora 41+):** MongoDB 8.0 **no arranca** en kernels Linux 6.19 o
> superiores por un bug conocido ([SERVER-121912](https://jira.mongodb.org/browse/SERVER-121912)).
> Comprueba tu kernel con `uname -r`. Si es ≥ 6.19, **usa Podman**
> (ver la [sección de contenedores](#con-podman-o-docker-recomendado)); es la vía que funciona.

Para Fedora con kernel < 6.19, la instalación nativa sí funciona:

### 1. Agregar el repositorio

```bash
sudo tee /etc/yum.repos.d/mongodb-org-8.0.repo << 'EOF'
[mongodb-org-8.0]
name=MongoDB Repository
baseurl=https://repo.mongodb.org/yum/redhat/9/mongodb-org/8.0/x86_64/
gpgcheck=1
enabled=1
gpgkey=https://pgp.mongodb.com/server-8.0.asc
EOF
```

### 2. Instalar y arrancar

```bash
sudo dnf install -y mongodb-org
sudo systemctl enable --now mongod     # arranca y habilita el autoarranque
sudo systemctl status mongod           # debe mostrar "active (running)"
```

Para detenerlo: `sudo systemctl stop mongod`.

---

## Con Podman o Docker (recomendado)

Funciona igual en Linux, Windows (WSL2) y macOS, y **evita el problema de kernel de Fedora**.
Podman viene preinstalado en Fedora; en otros sistemas usa Docker (los comandos son idénticos,
solo cambia `podman` por `docker`).

### 1. Descargar la imagen

```bash
podman pull docker.io/mongo:7.0
```

### 2. Iniciar el contenedor

```bash
podman run -d \
  --name mongodb \
  -p 27017:27017 \
  -v mongodb_data:/data/db \
  docker.io/mongo:7.0
```

- `-d` → en segundo plano.
- `--name mongodb` → nombre fijo para manejarlo después.
- `-p 27017:27017` → expone el puerto al host (el proyecto conecta a `localhost:27017`).
- `-v mongodb_data:/data/db` → persiste los datos entre reinicios.

### 3. Autoarranque al iniciar sesión (Linux, opcional)

```bash
podman generate systemd --new --name mongodb > ~/.config/systemd/user/mongodb.service
systemctl --user daemon-reload
systemctl --user enable mongodb.service
```

### Comandos del día a día

```bash
podman ps                 # ver si está corriendo
podman start mongodb      # iniciar
podman stop mongodb       # detener
podman restart mongodb    # reiniciar
podman logs -f mongodb    # ver logs en vivo
```

> Con Docker, sustituye `podman` por `docker` en todos los comandos.

---

## Windows — instalación nativa

### Opción A — Instalador gráfico (MSI)

1. Descarga el instalador desde <https://www.mongodb.com/try/download/community>.
2. Ejecuta el `.msi` y elige **"Complete"**.
3. Marca **"Install MongoDB as a Service"** → arranca solo con Windows.
4. Opcional: instala también **MongoDB Compass** (interfaz gráfica para ver los datos).

El servicio queda escuchando en `localhost:27017` automáticamente.

### Opción B — winget (línea de comandos)

```powershell
winget install MongoDB.Server
```

### Manejar el servicio en Windows

```powershell
net start MongoDB     # iniciar
net stop  MongoDB     # detener
```

> Alternativa sencilla en Windows: instalar **Docker Desktop** y seguir la
> [sección de contenedores](#con-podman-o-docker-recomendado).

---

## macOS — instalación nativa

Con [Homebrew](https://brew.sh):

```bash
brew tap mongodb/brew
brew install mongodb-community@8.0

# Arrancar como servicio (autoarranque)
brew services start mongodb-community@8.0

# O arrancar manualmente en primer plano
mongod --config /opt/homebrew/etc/mongod.conf
```

Para detener el servicio: `brew services stop mongodb-community@8.0`.

---

## Cambiar la URL de conexión

Por defecto el proyecto conecta a `mongodb://localhost:27017`. Si tu MongoDB corre en otro
host o puerto, define la variable de entorno `MONGO_URI`:

```bash
# Linux / macOS
MONGO_URI="mongodb://mi-servidor:27017" python scripts/build_nosql.py
```

```powershell
# Windows (PowerShell)
$env:MONGO_URI = "mongodb://mi-servidor:27017"; python scripts/build_nosql.py
```

---

Listo el servidor → vuelve al **[README](../README.md)** y corre `python scripts/build_nosql.py`
para cargar los datos.
