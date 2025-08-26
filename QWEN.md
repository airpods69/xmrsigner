# XmrSigner Project Context

## Project Overview

XmrSigner is an open-source project that enables users to build their own secure, air-gapped Monero hardware wallet using affordable hardware like a Raspberry Pi Zero. It is inspired by and forked from the SeedSigner Bitcoin project. The primary goal is to provide a high level of security for Monero transactions by ensuring the signing device is completely isolated from any network (air-gapped).

### Key Features
- **Air-Gapped Security**: Built on Raspberry Pi Zero v1.3 (no WiFi/Bluetooth) to ensure no network connectivity.
- **Monero Compatibility**: Supports Monero's 25-word seed format and the newer 16-word Polyseed format.
- **QR Code Interface**: Uses QR codes for importing unsigned transactions and exporting signed transactions, maintaining the air-gap.
- **Stateless Design**: Does not store seeds or private keys persistently.
- **DIY Philosophy**: Encourages users to build and verify their own secure signing device.

### Core Components
- **Hardware**: Raspberry Pi Zero, Waveshare LCD, Camera Module.
- **Software**: Python-based application running on a custom OS (see related projects).
- **Architecture**: Follows a Model-View-Controller (MVC) pattern with distinct `models`, `views`, and `controllers`.
  - `controller.py`: The main application controller.
  - `models/`: Contains data models like `Seed`, `Settings`, `SeedJar`.
  - `views/`: Manages the user interface screens.
  - `gui/`: Handles rendering to the LCD screen.
  - `hardware/`: Interfaces with physical buttons and peripherals.
  - `helpers/`: Utility functions for network, Monero operations, etc.

## Building and Running

### Prerequisites
- A compatible Raspberry Pi (Zero v1.3 recommended for air-gap).
- A pre-built XmrSigner OS image, or a custom OS with the required Python environment.
- Relevant hardware (LCD, camera).

### Local Development & Testing
While the primary use case is on the Pi, development and testing can be done on other systems.

1.  **Setup Python Environment**:
    - Python 3.12+ is required.
    - Install dependencies listed in `pyproject.toml`. This includes specific forks of libraries like `monero-python` and `polyseed-python`.
    - `uv sync`

2.  **Running the Application (Emulator)**:
    - The project likely relies on the XmrSigner Emulator (a related project) for development. Check the emulator project for specific instructions.
    - Running directly on a non-Pi system without the emulator may not work due to hardware dependencies.

3.  **Testing**:
    - Tests are located in the `tests/` directory.
    - The project uses `pytest` for testing, as indicated by `pytest.ini`.
    - Run tests using the command: `pytest`

### Deployment (Building OS Image)
The `Makefile` contains several commands for building development OS images:
- `make image-bookworm`: Builds a PiOS (Debian Bookworm) image with XmrSigner for development.
- `make image-buster`: Builds a PiOS (Debian Buster) image with XmrSigner for development.

These commands likely use scripts in the `tools/` directory to create a complete SD card image.

### Key Makefile Commands for Development
- `make resources`: Compresses UI resources.
- `make clean`: Removes Python cache files.
- `make dev-device-*`: Commands for syncing code to, and managing, a development Pi device over SSH (requires setup, see Makefile variables).

## Development Conventions

### Code Structure
- Python is the primary language.
- Code is organized under `src/xmrsigner/` following an MVC-like structure.
- Dependencies are managed via `requirements.txt`, including specific git revisions for some libraries.

### Contribution Guidelines
- Follow the guidelines in `CONTRIBUTING.md`.
- Fork the repo and create branches for features/fixes.
- Add tests for new code.
- Ensure code passes the test suite (`pytest`).
- Pay special attention to security, given the nature of the project.
- Testing on actual hardware is preferred before submitting PRs.

### Style Guide
- No explicit style guide is defined in the reviewed files. PEP 8 (standard Python style) is generally expected for Python projects unless stated otherwise. The `CONTRIBUTING.md` file notes "There are none, yet" for style guidelines.
- Use uv for project management and running things.
