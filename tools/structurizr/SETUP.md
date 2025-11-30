# Structurizr Tools Setup Guide

Complete setup instructions for Structurizr architecture documentation tools.

---

## Prerequisites

### Required

1. **Docker Desktop** (Windows/macOS) or **Docker Engine** (Linux)
   - Download: https://www.docker.com/products/docker-desktop
   - Verify: `docker --version`
   - Ensure Docker is running: `docker ps`

### Optional

2. **Python 3.8+** (for helper scripts)
   - Verify: `python --version`
   - Used for: Enhanced CLI wrapper with progress tracking

---

## Installation Steps

### Step 1: Install Docker

#### Windows

1. Download Docker Desktop from https://www.docker.com/products/docker-desktop
2. Run installer and follow prompts
3. Restart computer if prompted
4. Start Docker Desktop from Start menu
5. Verify installation:
   ```powershell
   docker --version
   docker ps
   ```

#### macOS

1. Download Docker Desktop from https://www.docker.com/products/docker-desktop
2. Drag Docker.app to Applications folder
3. Open Docker.app from Applications
4. Verify installation:
   ```bash
   docker --version
   docker ps
   ```

#### Linux

```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install docker.io
sudo systemctl start docker
sudo systemctl enable docker

# Add user to docker group (optional, to avoid sudo)
sudo usermod -aG docker $USER
# Log out and back in

# Verify
docker --version
docker ps
```

### Step 2: Pull Structurizr CLI Image

```bash
# Windows (PowerShell)
cd structurizr-tools
.\structurizr.bat check

# Linux/macOS
cd structurizr-tools
./structurizr.sh check
```

This will automatically pull the Docker image if not present.

### Step 3: (Optional) Set Up Python Virtual Environment

```bash
# Create virtual environment
python -m venv venv-structurizr

# Activate (Windows)
.\venv-structurizr\Scripts\Activate.ps1

# Activate (Linux/macOS)
source venv-structurizr/bin/activate

# Install Python dependencies (optional)
pip install -r structurizr-tools/requirements-structurizr.txt
```

---

## Verification

### Test Installation

```bash
# Windows
cd structurizr-tools
.\structurizr.bat check

# Linux/macOS
cd structurizr-tools
./structurizr.sh check
```

Expected output:
```
[OK] Docker found: Docker version ...
[OK] Docker is running
[OK] Structurizr CLI image found
```

### Test Export

```bash
# Export a test diagram (if you have a DSL file)
.\structurizr.bat export --workspace ../docs/ReportingManager_Phase0_Architecture.dsl --format mermaid --output ../docs/
```

---

## Troubleshooting

### Docker Not Running

**Problem:** `[ERROR] Docker is not running`

**Solution:**
- Windows/macOS: Start Docker Desktop from Applications
- Linux: `sudo systemctl start docker`

### Permission Denied (Linux)

**Problem:** `permission denied while trying to connect to the Docker daemon socket`

**Solution:**
```bash
sudo usermod -aG docker $USER
# Log out and back in
```

### Docker Image Not Found

**Problem:** `[WARN] Structurizr CLI image not found`

**Solution:**
```bash
docker pull structurizr/cli:latest
```

### Port Already in Use (Serve Command)

**Problem:** `port 8080 is already allocated`

**Solution:**
- Stop other service using port 8080
- Or use custom port (modify script)

---

## Next Steps

1. **Create your first DSL file:**
   - See `docs/ReportingManager_Phase0_Architecture.dsl` for example
   - Or start with Structurizr DSL documentation: https://github.com/structurizr/dsl

2. **Generate diagrams:**
   ```bash
   structurizr.bat export --workspace docs/your-file.dsl --format mermaid --output docs/
   ```

3. **View interactively:**
   ```bash
   structurizr.bat serve --workspace docs/your-file.dsl
   # Open http://localhost:8080
   ```

4. **Integrate with PDF generation:**
   - Generate diagrams first
   - Include in Markdown
   - Generate PDF with pdf-tools

---

## Additional Resources

- **Structurizr DSL Documentation:** https://github.com/structurizr/dsl
- **C4 Model:** https://c4model.com/
- **Structurizr Lite:** https://github.com/structurizr/lite
- **Example DSL:** `docs/ReportingManager_Phase0_Architecture.dsl`

---

**Last Updated:** November 2025

