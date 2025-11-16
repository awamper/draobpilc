# GEMINI Project Context: draobpilc

## Project Overview

`draobpilc` is a graphical user interface (GUI) for the `GPaste` clipboard manager, designed for GNOME and other GTK-based desktop environments. It allows users to browse, search, edit, and manage their clipboard history.

The application is built with Python and `PyGObject`, utilizing GTK3 for the user interface. It communicates with the underlying `GPaste` daemon via DBus to fetch history, select items, and perform other clipboard-related actions.

The architecture is well-structured:
- **`draobpilc/application.py`**: The core `Gtk.Application` class that manages the main window, UI components, and application lifecycle.
- **`draobpilc/widgets/`**: Contains the various GTK widgets that make up the UI, such as the main window, item list, search box, and preview panes.
- **`draobpilc/lib/gpaste_client.py`**: A dedicated module that handles all DBus communication with the `GPaste` service.
- **`draobpilc/main.py`**: The main entry point, responsible for parsing command-line arguments, checking dependencies, and launching the application.
- **`pyproject.toml`**: Defines project metadata, dependencies, and the `draobpilc` command-line entry point.

## Building and Running

### Dependencies

The project requires Python 3 and the following packages, as defined in `pyproject.toml`:
- `pygobject` (for GTK3)
- `humanize`
- `blinker`
- `python3-xlib`

It also requires a running `GPaste` daemon on the system.

### Installation

To install the application and its dependencies, run the following command from the project's root directory:

```bash
pip3 install .
```

This will install the `draobpilc` command into your local environment (typically `~/.local/bin`).

### Running the Application

Once installed, you can run the application using:

```bash
draobpilc
```

You can also launch it with command-line arguments:
- `draobpilc --preferences`: Open the preferences window.
- `draobpilc --debug`: Run in debug mode with verbose logging.

### Running from Source for Development

To run the application directly from the source code without installation, you can execute the main module:

```bash
python3 -m draobpilc.main
```

## Development Conventions

### Code Style

The codebase generally follows the PEP 8 style guide for Python. It emphasizes a clear separation of concerns, with UI components, application logic, and service communication isolated in their respective modules.

### User Interface

The UI is constructed programmatically using the `PyGObject` library. The main window is defined in `draobpilc/widgets/window.py`, and it is composed of various custom widgets found in the `draobpilc/widgets/` directory. A CSS file (`draobpilc/data/style.css`) is used for custom styling.

### Configuration

Application settings are managed through GSettings. The schema is defined in `draobpilc/data/schemas/apps.Draobpilc.gschema.xml`. These settings are accessed throughout the application via the `common.SETTINGS` object.

### Entry Point

The application is packaged using `setuptools`. The `[project.gui-scripts]` table in `pyproject.toml` defines the `draobpilc` command, which maps to the `run` function in `draobpilc.main`.
