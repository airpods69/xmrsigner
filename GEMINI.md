# XmrSigner: Air-Gapped Monero Hardware Wallet

## Project Overview

XmrSigner is an open-source, DIY hardware wallet for Monero. It's designed to be air-gapped, meaning it operates without network connectivity (WiFi, Bluetooth) to enhance security. The device is built using a Raspberry Pi Zero, a camera module, and an LCD screen.

The project is a fork of the SeedSigner Bitcoin project and is adapted for the Monero ecosystem. It allows users to create Monero wallets, sign transactions offline using QR codes, and manage their keys securely.

**Key Technologies:**

*   **Python:** The core application is written in Python.
*   **Raspberry Pi:** The hardware platform for the device.
*   **Monero, Polyseed, pyzbar:** Key Python libraries for Monero integration, seed phrase generation, and QR code scanning.

**Architecture:**

The application follows a Model-View-Controller (MVC) pattern:

*   **`src/xmrsigner/models`:** Contains the data structures and business logic for seeds, keys, and settings.
*   **`src/xmrsigner/views`:** Manages the user interface on the LCD screen.
*   **`src/xmrsigner/controller.py`:** Handles user input and coordinates the interaction between models and views.

## Building and Running

### Dependencies

The project's Python dependencies are listed in `requirements.txt` and `pyproject.toml`. Key dependencies include:

*   `monero`: For Monero-specific functionality.
*   `polyseed`: For Polyseed mnemonic generation.
*   `pyzbar`: For QR code scanning.
*   `urtypes`: For handling Uniform Resources (UR) data formats.

### Build and Run Commands

The `Makefile` provides several commands for managing the project:

*   **`make install`:** Installs the required dependencies.
*   **`make dev`:** Installs development dependencies.
*   **`make test`:** Runs the test suite.
*   **`make run`:** Executes the main application.

To run the application:

```bash
make run
```

## Development Conventions

The `CONTRIBUTING.md` file outlines the development guidelines. Key conventions include:

*   **Code Style:** The project follows the PEP 8 style guide for Python code.
*   **Testing:** Tests are located in the `tests` directory and can be run using `make test`. New features should include corresponding tests.
*   **Pull Requests:** Contributions are made through pull requests to the `dev` branch. Pull requests should be well-documented and include a clear description of the changes.
*   **Versioning:** The project uses semantic versioning. The `tools/increment_version.py` script is used to update the version number.
