"""
OG Autoclicker con interfaz gráfica en Tkinter.

Incluye:
- Dos paneles independientes: uno para click izquierdo y otro para click derecho.
- Hotkeys globales capturadas por pulsación real.
- Reconoce teclado, botones del mouse y la ruedita como hotkey.
- Modo Hotkey o Hold click para cada panel.
- Barra de desplazamiento vertical.
- Guardado/carga de configuración en carpeta elegida por el usuario.
- Selector de idioma Español / English.
- Marca de agua visual: Developed By Valentino Galli / KidOGzz

Dependencia externa:
    pip install pynput
"""

from __future__ import annotations

import json
import os
import sys
import threading
import time
import tkinter as tk
from dataclasses import dataclass, field
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

try:
    from pynput import keyboard, mouse
except ImportError as exc:
    if __name__ == "__main__":
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror(
            "Missing dependency",
            "Could not find 'pynput'.\n\nInstall it with:\n\npip install pynput",
        )
    raise SystemExit("Missing dependency 'pynput': pip install pynput") from exc


if sys.platform.startswith("win"):
    import ctypes

    _USER32 = ctypes.windll.user32
    _VK_BY_MOUSE_NAME = {
        "left": 0x01,
        "right": 0x02,
        "middle": 0x04,
        "x1": 0x05,
        "x2": 0x06,
    }
    _LLMHF_INJECTED = 0x00000001
else:
    _USER32 = None
    _VK_BY_MOUSE_NAME = {}
    _LLMHF_INJECTED = 0


TRANSLATIONS = {
    "es": {
        "language_name": "Español",
        "app_title": "OG Autoclicker",
        "dependency_title": "Dependencia faltante",
        "dependency_body": "No se encontró 'pynput'.\n\nInstálalo con:\n\npip install pynput",
        "first_run_title": "Carpeta de datos",
        "first_run_body": (
            "Es la primera vez que inicias OG Autoclicker, o la carpeta anterior ya no existe.\n\n"
            "Selecciona o crea una carpeta donde se guardarán tus configuraciones."
        ),
        "select_data_folder_title": "Selecciona o crea la carpeta de datos de OG Autoclicker",
        "data_folder_required_title": "Carpeta requerida",
        "data_folder_required_body": (
            "OG Autoclicker necesita una carpeta para guardar tus datos.\n\n"
            "Pulsa Reintentar para elegir una carpeta o Cancelar para cerrar la app."
        ),
        "data_folder_error_title": "No se pudo usar la carpeta",
        "data_folder_error_body": "No se pudo preparar la carpeta seleccionada.\n\n{error}",
        "data_folder_set_note": "Carpeta de datos configurada en: {folder}",
        "data_folder_label": "Carpeta de datos: {folder}",
        "data_folder_not_set": "Carpeta de datos: no configurada",
        "change_folder_title": "Selecciona o crea una nueva carpeta de datos",
        "change_folder_ok_title": "Carpeta actualizada",
        "change_folder_ok_body": "La carpeta de datos se actualizó correctamente.",
        "change_folder_error_title": "Error al cambiar carpeta",
        "change_folder_error_body": "No se pudo cambiar la carpeta de datos.\n\n{error}",
        "save_title": "Configuración guardada",
        "save_body": "La configuración se guardó en:\n\n{path}",
        "save_error_title": "No se pudo guardar",
        "save_error_body": "Ocurrió un error al guardar la configuración.\n\n{error}",
        "no_data_folder_title": "Sin carpeta de datos",
        "no_data_folder_body": "Todavía no hay una carpeta de datos configurada.",
        "load_missing_title": "Sin configuración guardada",
        "load_missing_body": "Todavía no existe un archivo de configuración en la carpeta de datos actual.",
        "load_error_title": "No se pudo cargar",
        "load_error_body": "El archivo de configuración no se pudo leer.\n\n{error}",
        "invalid_format_title": "Formato inválido",
        "invalid_format_body": "El archivo de configuración no tiene un formato válido.",
        "load_ok_title": "Configuración cargada",
        "load_ok_body": "Se cargó la configuración desde:\n\n{path}",
        "load_ok_note": "Configuración cargada correctamente.",
        "open_folder_error_title": "No se pudo abrir la carpeta",
        "open_folder_error_body": "No se pudo abrir la carpeta de datos.\n\n{error}",
        "top_intro": (
            "Ahora tienes dos configuraciones independientes: una para click izquierdo y otra para click derecho. "
            "Cada una tiene su propia hotkey, su propio modo Hold click, su propio intervalo y su propio estado."
        ),
        "general_notes_title": "Notas generales",
        "general_notes_body": (
            "• Cada panel funciona por separado.\n"
            "• En modo Hotkey: la hotkey activa o desactiva ese panel.\n"
            "• En modo Hold click: mantener presionado el botón dispara clicks; al soltar, se detiene.\n"
            "• En modo Hold click: la hotkey del panel funciona como seguro para habilitarlo o deshabilitarlo.\n"
            "• Si usas el mismo botón para Hold y para autoclick, el primer autoclick espera el intervalo configurado."
        ),
        "storage_title": "Guardar configuración",
        "save_now": "Guardar ahora",
        "load_saved": "Cargar guardado",
        "open_folder": "Abrir carpeta",
        "change_folder": "Cambiar carpeta",
        "storage_note": (
            "La app también guarda automáticamente al cerrar. Si vuelves a abrirla, "
            "intentará cargar la última configuración desde esta carpeta."
        ),
        "language_title": "Idioma / Language",
        "language_label": "Idioma de la interfaz:",
        "apply_language": "Guardar idioma",
        "language_note": (
            "Para no interferir con lo que ya funciona, el cambio completo de idioma se aplica al reiniciar la app."
        ),
        "language_no_change_title": "Sin cambios",
        "language_no_change_body": "Ese idioma ya está activo.",
        "language_saved_title": "Idioma guardado",
        "language_saved_body": (
            "El idioma se guardó correctamente.\n\n"
            "Cierra y vuelve a abrir OG Autoclicker para aplicar todo el cambio sin riesgo."
        ),
        "language_save_error_title": "No se pudo guardar el idioma",
        "language_save_error_body": "No se pudo guardar la preferencia de idioma.",
        "watermark": "Developed By Valentino Galli / KidOGzz",
        "left_click": "Click izquierdo",
        "right_click": "Click derecho",
        "middle_click": "Click medio",
        "x1_click": "Botón lateral 1",
        "x2_click": "Botón lateral 2",
        "section_controls_only": "Este panel controla solamente el {title}.",
        "activation_mode_title": "Modo de activación",
        "hotkey_mode_label": "Hotkey global (activa / desactiva)",
        "hold_mode_label": "Hold click (mientras mantengo presionado el click)",
        "hotkey_group_title": "Hotkey global",
        "hotkey_help": "Toca la casilla y luego presiona la tecla, botón del mouse o ruedita que quieres usar:",
        "capture": "Capturar",
        "clear": "Limpiar",
        "hotkey_extra": (
            "Admite teclado, botones del mouse y ruedita arriba/abajo. "
            "Si el panel está en Hold click, esta hotkey funciona como seguro."
        ),
        "hold_group_title": "Modo Hold click",
        "hold_same_check": "Usar el mismo botón que se autoclickea ({title})",
        "hold_pick_help": "Si desactivas la casilla, puedes elegir otro botón para mantener apretado:",
        "hold_button_label": "Botón a mantener presionado:",
        "hold_group_note": (
            "Mientras mantienes el botón apretado, dispara clicks; cuando sueltas el dedo, se detiene. "
            "La hotkey de este panel puede desactivar el Hold si no quieres que arranque por accidente."
        ),
        "click_group_title": "Click automático",
        "output_button_label": "Botón que se autoclickea:",
        "click_type_label": "Tipo de click:",
        "interval_label": "Intervalo (ms):",
        "interval_help": "Ejemplo: 100 ms = 10 clicks por segundo aprox.",
        "control_title": "Control",
        "stop_now": "Detener ahora",
        "test_click": "Click de prueba",
        "status_title": "Estado",
        "simple": "Simple",
        "double": "Doble",
        "hotkey_prompt": "Haz clic aquí para elegir hotkey",
        "hotkey_capture_prompt": "Presione la tecla que desea usar para activar...",
        "waiting_hotkey_note": "Esperando hotkey para {title}: tecla, botón del mouse o ruedita.",
        "hotkey_cleared_note": "Hotkey borrada para {title}.",
        "manual_stop_hold_disabled": (
            "{title} detenido manualmente. El Hold quedó deshabilitado hasta volver a activarlo con su hotkey."
        ),
        "manual_stop_hold_available": (
            "{title} detenido manualmente. Como ese panel no tiene hotkey, el Hold sigue disponible cuando vuelvas a mantener presionado."
        ),
        "manual_stop": "{title} detenido manualmente.",
        "test_click_note": "{title}: click de prueba en {seconds:.2f} segundos para que puedas mover el cursor.",
        "test_click_done": "Click de prueba realizado para {title}.",
        "status_waiting_hotkey": "Esperando hotkey...",
        "status_active": "Activo",
        "status_stopped": "Detenido",
        "status_hold_disabled": "Hold deshabilitado",
        "status_hold_pressed": "Activo (mantener presionado)",
        "status_hold_waiting": "Esperando que mantengas presionado",
        "status_no_hotkey": "Sin hotkey",
        "status_hotkey": "Hotkey: {display}",
        "hotkey_captured_note": "Hotkey capturada para {title}: {display}",
        "toggle_active": "{title}: {state}",
        "toggle_active_on": "activado",
        "toggle_active_off": "desactivado",
        "toggle_hold": "{title}: hold {state}",
        "toggle_hold_on": "habilitado",
        "toggle_hold_off": "deshabilitado",
        "trigger_by_binding": "{text} por {display}",
        "wheel_up": "Ruedita arriba",
        "wheel_down": "Ruedita abajo",
        "key_alt_gr": "ALT GR",
        "key_alt_l": "ALT IZQ",
        "key_alt_r": "ALT DER",
        "key_backspace": "RETROCESO",
        "key_caps_lock": "BLOQ MAYÚS",
        "key_cmd_l": "CMD IZQ",
        "key_cmd_r": "CMD DER",
        "key_ctrl_l": "CTRL IZQ",
        "key_ctrl_r": "CTRL DER",
        "key_delete": "SUPR",
        "key_down": "FLECHA ABAJO",
        "key_end": "FIN",
        "key_enter": "ENTER",
        "key_esc": "ESC",
        "key_home": "INICIO",
        "key_left": "FLECHA IZQ",
        "key_menu": "MENÚ",
        "key_num_lock": "BLOQ NUM",
        "key_page_down": "RE PÁG",
        "key_page_up": "AV PÁG",
        "key_pause": "PAUSA",
        "key_print_screen": "IMPR PANT",
        "key_right": "FLECHA DER",
        "key_scroll_lock": "BLOQ DESPL",
        "key_shift_l": "SHIFT IZQ",
        "key_shift_r": "SHIFT DER",
        "key_space": "ESPACIO",
        "key_tab": "TAB",
        "key_up": "FLECHA ARRIBA",
        "initial_note": (
            "Ubicación del click: donde esté el cursor. "
            "Ahora tienes un panel para izquierdo y otro para derecho."
        ),
    },
    "en": {
        "language_name": "English",
        "app_title": "OG Autoclicker",
        "dependency_title": "Missing dependency",
        "dependency_body": "Could not find 'pynput'.\n\nInstall it with:\n\npip install pynput",
        "first_run_title": "Data folder",
        "first_run_body": (
            "This is your first time starting OG Autoclicker, or the previous folder no longer exists.\n\n"
            "Select or create a folder where your settings will be saved."
        ),
        "select_data_folder_title": "Select or create OG Autoclicker's data folder",
        "data_folder_required_title": "Folder required",
        "data_folder_required_body": (
            "OG Autoclicker needs a folder to save your data.\n\n"
            "Click Retry to choose a folder or Cancel to close the app."
        ),
        "data_folder_error_title": "Could not use the folder",
        "data_folder_error_body": "Could not prepare the selected folder.\n\n{error}",
        "data_folder_set_note": "Data folder set to: {folder}",
        "data_folder_label": "Data folder: {folder}",
        "data_folder_not_set": "Data folder: not configured",
        "change_folder_title": "Select or create a new data folder",
        "change_folder_ok_title": "Folder updated",
        "change_folder_ok_body": "The data folder was updated successfully.",
        "change_folder_error_title": "Error changing folder",
        "change_folder_error_body": "Could not change the data folder.\n\n{error}",
        "save_title": "Configuration saved",
        "save_body": "The configuration was saved to:\n\n{path}",
        "save_error_title": "Could not save",
        "save_error_body": "An error occurred while saving the configuration.\n\n{error}",
        "no_data_folder_title": "No data folder",
        "no_data_folder_body": "There is no configured data folder yet.",
        "load_missing_title": "No saved configuration",
        "load_missing_body": "There is no configuration file yet in the current data folder.",
        "load_error_title": "Could not load",
        "load_error_body": "The configuration file could not be read.\n\n{error}",
        "invalid_format_title": "Invalid format",
        "invalid_format_body": "The configuration file has an invalid format.",
        "load_ok_title": "Configuration loaded",
        "load_ok_body": "The configuration was loaded from:\n\n{path}",
        "load_ok_note": "Configuration loaded successfully.",
        "open_folder_error_title": "Could not open folder",
        "open_folder_error_body": "Could not open the data folder.\n\n{error}",
        "top_intro": (
            "You now have two independent configurations: one for left click and one for right click. "
            "Each one has its own hotkey, Hold click mode, interval and state."
        ),
        "general_notes_title": "General notes",
        "general_notes_body": (
            "• Each panel works independently.\n"
            "• In Hotkey mode: the hotkey turns that panel on or off.\n"
            "• In Hold click mode: holding the button down fires clicks; releasing it stops them.\n"
            "• In Hold click mode: the panel hotkey acts as a safety toggle to enable or disable Hold.\n"
            "• If you use the same button for Hold and autoclick, the first autoclick waits for the configured interval."
        ),
        "storage_title": "Save configuration",
        "save_now": "Save now",
        "load_saved": "Load saved",
        "open_folder": "Open folder",
        "change_folder": "Change folder",
        "storage_note": (
            "The app also saves automatically when closing. When you open it again, "
            "it will try to load the latest configuration from this folder."
        ),
        "language_title": "Language / Idioma",
        "language_label": "Interface language:",
        "apply_language": "Save language",
        "language_note": (
            "To avoid interfering with what already works, the full language change is applied after restarting the app."
        ),
        "language_no_change_title": "No changes",
        "language_no_change_body": "That language is already active.",
        "language_saved_title": "Language saved",
        "language_saved_body": (
            "The language was saved successfully.\n\n"
            "Close and reopen OG Autoclicker to apply the full change safely."
        ),
        "language_save_error_title": "Could not save language",
        "language_save_error_body": "Could not save the language preference.",
        "watermark": "Developed By Valentino Galli / KidOGzz",
        "left_click": "Left Click",
        "right_click": "Right Click",
        "middle_click": "Middle Click",
        "x1_click": "Side Button 1",
        "x2_click": "Side Button 2",
        "section_controls_only": "This panel controls only {title}.",
        "activation_mode_title": "Activation mode",
        "hotkey_mode_label": "Global hotkey (toggle on / off)",
        "hold_mode_label": "Hold click (while I keep the click pressed)",
        "hotkey_group_title": "Global hotkey",
        "hotkey_help": "Click the box and then press the key, mouse button or wheel action you want to use:",
        "capture": "Capture",
        "clear": "Clear",
        "hotkey_extra": (
            "Supports keyboard, mouse buttons and mouse wheel up/down. "
            "If the panel is in Hold click, this hotkey works as a safety toggle."
        ),
        "hold_group_title": "Hold click mode",
        "hold_same_check": "Use the same button that gets auto-clicked ({title})",
        "hold_pick_help": "If you uncheck the box, you can choose a different button to keep pressed:",
        "hold_button_label": "Button to keep pressed:",
        "hold_group_note": (
            "While you keep the button pressed, it fires clicks; when you release it, it stops. "
            "This panel hotkey can disable Hold if you do not want it to start by accident."
        ),
        "click_group_title": "Automatic click",
        "output_button_label": "Button being auto-clicked:",
        "click_type_label": "Click type:",
        "interval_label": "Interval (ms):",
        "interval_help": "Example: 100 ms = about 10 clicks per second.",
        "control_title": "Control",
        "stop_now": "Stop now",
        "test_click": "Test click",
        "status_title": "Status",
        "simple": "Single",
        "double": "Double",
        "hotkey_prompt": "Click here to choose a hotkey",
        "hotkey_capture_prompt": "Press the key you want to use to activate...",
        "waiting_hotkey_note": "Waiting for hotkey for {title}: key, mouse button or wheel.",
        "hotkey_cleared_note": "Hotkey cleared for {title}.",
        "manual_stop_hold_disabled": (
            "{title} stopped manually. Hold was disabled until you enable it again with its hotkey."
        ),
        "manual_stop_hold_available": (
            "{title} stopped manually. Since that panel has no hotkey, Hold stays available when you press and hold again."
        ),
        "manual_stop": "{title} stopped manually.",
        "test_click_note": "{title}: test click in {seconds:.2f} seconds so you can move the cursor.",
        "test_click_done": "Test click completed for {title}.",
        "status_waiting_hotkey": "Waiting for hotkey...",
        "status_active": "Active",
        "status_stopped": "Stopped",
        "status_hold_disabled": "Hold disabled",
        "status_hold_pressed": "Active (holding pressed)",
        "status_hold_waiting": "Waiting for you to hold the button",
        "status_no_hotkey": "No hotkey",
        "status_hotkey": "Hotkey: {display}",
        "hotkey_captured_note": "Hotkey captured for {title}: {display}",
        "toggle_active": "{title}: {state}",
        "toggle_active_on": "enabled",
        "toggle_active_off": "disabled",
        "toggle_hold": "{title}: hold {state}",
        "toggle_hold_on": "enabled",
        "toggle_hold_off": "disabled",
        "trigger_by_binding": "{text} by {display}",
        "wheel_up": "Wheel up",
        "wheel_down": "Wheel down",
        "key_alt_gr": "ALT GR",
        "key_alt_l": "LEFT ALT",
        "key_alt_r": "RIGHT ALT",
        "key_backspace": "BACKSPACE",
        "key_caps_lock": "CAPS LOCK",
        "key_cmd_l": "LEFT CMD",
        "key_cmd_r": "RIGHT CMD",
        "key_ctrl_l": "LEFT CTRL",
        "key_ctrl_r": "RIGHT CTRL",
        "key_delete": "DELETE",
        "key_down": "DOWN ARROW",
        "key_end": "END",
        "key_enter": "ENTER",
        "key_esc": "ESC",
        "key_home": "HOME",
        "key_left": "LEFT ARROW",
        "key_menu": "MENU",
        "key_num_lock": "NUM LOCK",
        "key_page_down": "PAGE DOWN",
        "key_page_up": "PAGE UP",
        "key_pause": "PAUSE",
        "key_print_screen": "PRINT SCREEN",
        "key_right": "RIGHT ARROW",
        "key_scroll_lock": "SCROLL LOCK",
        "key_shift_l": "LEFT SHIFT",
        "key_shift_r": "RIGHT SHIFT",
        "key_space": "SPACE",
        "key_tab": "TAB",
        "key_up": "UP ARROW",
        "initial_note": (
            "Click position: wherever the cursor is. "
            "You now have one panel for left click and another for right click."
        ),
    },
}


KEY_TEXT_KEYS = {
    "alt_gr": "key_alt_gr",
    "alt_l": "key_alt_l",
    "alt_r": "key_alt_r",
    "backspace": "key_backspace",
    "caps_lock": "key_caps_lock",
    "cmd_l": "key_cmd_l",
    "cmd_r": "key_cmd_r",
    "ctrl_l": "key_ctrl_l",
    "ctrl_r": "key_ctrl_r",
    "delete": "key_delete",
    "down": "key_down",
    "end": "key_end",
    "enter": "key_enter",
    "esc": "key_esc",
    "home": "key_home",
    "left": "key_left",
    "menu": "key_menu",
    "num_lock": "key_num_lock",
    "page_down": "key_page_down",
    "page_up": "key_page_up",
    "pause": "key_pause",
    "print_screen": "key_print_screen",
    "right": "key_right",
    "scroll_lock": "key_scroll_lock",
    "shift_l": "key_shift_l",
    "shift_r": "key_shift_r",
    "space": "key_space",
    "tab": "key_tab",
    "up": "key_up",
}

APP_STATE_DIR = Path.home() / ".og_autoclicker"
DATA_FOLDER_LOCATOR = APP_STATE_DIR / "data_folder.json"
CONFIG_FILENAME = "og_autoclicker_config.json"


class ScrollableFrame(ttk.Frame):
    def __init__(self, parent: tk.Misc) -> None:
        super().__init__(parent)

        self.canvas = tk.Canvas(self, highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.inner = ttk.Frame(self.canvas)

        self._window_id = self.canvas.create_window((0, 0), window=self.inner, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        self.inner.bind("<Configure>", self._on_inner_configure)
        self.canvas.bind("<Configure>", self._on_canvas_configure)

        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel, add="+")
        self.canvas.bind_all("<Button-4>", self._on_mousewheel_linux_up, add="+")
        self.canvas.bind_all("<Button-5>", self._on_mousewheel_linux_down, add="+")

    def _on_inner_configure(self, _event: tk.Event) -> None:
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _on_canvas_configure(self, event: tk.Event) -> None:
        self.canvas.itemconfigure(self._window_id, width=event.width)

    def _on_mousewheel(self, event: tk.Event) -> None:
        delta = getattr(event, "delta", 0)
        if delta:
            self.canvas.yview_scroll(int(-1 * (delta / 120)), "units")

    def _on_mousewheel_linux_up(self, _event: tk.Event) -> None:
        self.canvas.yview_scroll(-1, "units")

    def _on_mousewheel_linux_down(self, _event: tk.Event) -> None:
        self.canvas.yview_scroll(1, "units")


@dataclass
class ClickProfile:
    key: str
    title: str
    output_button: str
    mode: str = "hotkey"
    active: bool = False
    hold_gate_enabled: bool = True
    hold_engaged: bool = False
    hold_same_as_output: bool = True
    hold_button: str = ""
    click_count: int = 1
    interval_seconds: float = 0.1
    hotkey_binding: dict[str, str] | None = None
    next_due_at: float = 0.0
    mode_var: tk.StringVar | None = None
    hotkey_text_var: tk.StringVar | None = None
    hold_same_var: tk.BooleanVar | None = None
    hold_button_var: tk.StringVar | None = None
    click_type_var: tk.StringVar | None = None
    interval_var: tk.StringVar | None = None
    status_var: tk.StringVar | None = None
    widgets: dict[str, tk.Widget] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.hold_button:
            self.hold_button = self.output_button


class AutoClickerApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.current_language = "es"
        self.root.title(self.t("app_title"))
        self.root.geometry("560x920")
        self.root.minsize(500, 430)

        self.lock = threading.RLock()
        self.running = True
        self.initialized = False
        self.data_folder: Path | None = None
        self.config_path: Path | None = None
        self.capture_target: str | None = None
        self.capture_armed_at = 0.0
        self.debounced_triggers: set[tuple[str, str]] = set()
        self.pressed_mouse_buttons: set[str] = set()
        self.synthetic_event_budget: dict[str, int] = {}
        self.synthetic_ignore_until: dict[str, float] = {}
        self.last_synthetic_click_at: dict[str, float] = {}

        self.mouse_controller = mouse.Controller()
        self.keyboard_listener: keyboard.Listener | None = None
        self.mouse_listener: mouse.Listener | None = None
        self.worker_thread: threading.Thread | None = None

        self.note_var = tk.StringVar(value=self.t("initial_note"))
        self.data_folder_var = tk.StringVar(value=self.t("data_folder_not_set"))
        self.language_var = tk.StringVar(value=self.language_label(self.current_language))

        if not self._ensure_data_folder_selected():
            self.root.after(0, self.root.destroy)
            return

        self.current_language = self._load_language_preference()
        self.root.title(self.t("app_title"))
        self.note_var.set(self.t("initial_note"))
        self.data_folder_var.set(
            self.t("data_folder_label", folder=self.data_folder) if self.data_folder else self.t("data_folder_not_set")
        )
        self.language_var.set(self.language_label(self.current_language))

        self.profiles: dict[str, ClickProfile] = {}
        self._create_profiles()

        self._build_ui()
        self._sync_all_profiles_from_ui()
        self._load_config(show_message=False)
        self._refresh_all_mode_widgets()
        self._start_threads()
        self._refresh_status_loop()

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.initialized = True

    def t(self, key: str, **kwargs) -> str:
        language_pack = TRANSLATIONS.get(self.current_language, TRANSLATIONS["es"])
        text = language_pack.get(key, TRANSLATIONS["es"].get(key, key))
        return text.format(**kwargs) if kwargs else text

    def language_label(self, code: str) -> str:
        return TRANSLATIONS.get(code, TRANSLATIONS["es"]).get("language_name", code)

    def selected_language_code(self) -> str:
        label = self.language_var.get().strip()
        for code in ("es", "en"):
            if self.language_label(code) == label:
                return code
        return self.current_language

    def mouse_label(self, name: str) -> str:
        if name == "left":
            return self.t("left_click")
        if name == "right":
            return self.t("right_click")
        if name == "middle":
            return self.t("middle_click")
        if name == "x1":
            return self.t("x1_click")
        if name == "x2":
            return self.t("x2_click")
        return name

    def mouse_button_names(self) -> list[str]:
        names = ["left", "right", "middle"]
        if hasattr(mouse.Button, "x1"):
            names.append("x1")
        if hasattr(mouse.Button, "x2"):
            names.append("x2")
        return names

    def mouse_option_labels(self) -> list[str]:
        return [self.mouse_label(name) for name in self.mouse_button_names()]

    def mouse_name_from_label(self, label: str) -> str:
        for name in self.mouse_button_names():
            if self.mouse_label(name) == label:
                return name
        return "left"

    def click_type_label(self, count: int) -> str:
        return self.t("double") if count == 2 else self.t("simple")

    def click_count_from_label(self, label: str) -> int:
        return 2 if label == self.t("double") else 1

    def default_hotkey_prompt(self) -> str:
        return self.t("hotkey_prompt")

    def _load_language_preference(self) -> str:
        if self.config_path is None or not self.config_path.exists():
            return "es"
        try:
            data = json.loads(self.config_path.read_text(encoding="utf-8"))
            language = data.get("language", "es")
            return language if language in {"es", "en"} else "es"
        except Exception:
            return "es"

    def _ensure_data_folder_selected(self) -> bool:
        stored_folder = self._read_data_folder_from_locator(DATA_FOLDER_LOCATOR)
        if stored_folder is not None and stored_folder.exists():
            self._set_data_folder(stored_folder)
            return True

        while True:
            messagebox.showinfo(
                self.t("first_run_title"),
                self.t("first_run_body"),
                parent=self.root,
            )
            chosen = filedialog.askdirectory(
                parent=self.root,
                mustexist=False,
                title=self.t("select_data_folder_title"),
            )
            if chosen:
                folder = Path(chosen).expanduser()
                try:
                    folder.mkdir(parents=True, exist_ok=True)
                    self._set_data_folder(folder)
                    self._save_data_folder_locator()
                    self.note_var.set(self.t("data_folder_set_note", folder=folder))
                    return True
                except Exception as exc:
                    messagebox.showerror(
                        self.t("data_folder_error_title"),
                        self.t("data_folder_error_body", error=exc),
                        parent=self.root,
                    )
                    continue

            retry = messagebox.askretrycancel(
                self.t("data_folder_required_title"),
                self.t("data_folder_required_body"),
                parent=self.root,
            )
            if not retry:
                return False

    def _read_data_folder_from_locator(self, locator_path: Path) -> Path | None:
        try:
            if not locator_path.exists():
                return None
            data = json.loads(locator_path.read_text(encoding="utf-8"))
            folder = data.get("data_folder", "")
            if not folder:
                return None
            return Path(folder).expanduser()
        except Exception:
            return None

    def _save_data_folder_locator(self) -> None:
        if self.data_folder is None:
            return
        APP_STATE_DIR.mkdir(parents=True, exist_ok=True)
        DATA_FOLDER_LOCATOR.write_text(
            json.dumps({"data_folder": str(self.data_folder)}, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def _set_data_folder(self, folder: Path) -> None:
        folder = folder.expanduser().resolve()
        folder.mkdir(parents=True, exist_ok=True)
        self.data_folder = folder
        self.config_path = folder / CONFIG_FILENAME
        self.data_folder_var.set(self.t("data_folder_label", folder=folder))

    def _change_data_folder(self) -> None:
        chosen = filedialog.askdirectory(
            parent=self.root,
            mustexist=False,
            title=self.t("change_folder_title"),
            initialdir=str(self.data_folder) if self.data_folder else None,
        )
        if not chosen:
            return

        try:
            new_folder = Path(chosen).expanduser()
            new_folder.mkdir(parents=True, exist_ok=True)
            self._set_data_folder(new_folder)
            self._save_data_folder_locator()
            self._save_config(show_message=False)
            self.note_var.set(self.t("data_folder_set_note", folder=new_folder))
            messagebox.showinfo(
                self.t("change_folder_ok_title"),
                self.t("change_folder_ok_body"),
                parent=self.root,
            )
        except Exception as exc:
            messagebox.showerror(
                self.t("change_folder_error_title"),
                self.t("change_folder_error_body", error=exc),
                parent=self.root,
            )

    def _save_config(self, show_message: bool = True) -> bool:
        if self.config_path is None:
            if show_message:
                messagebox.showerror(
                    self.t("no_data_folder_title"),
                    self.t("no_data_folder_body"),
                    parent=self.root,
                )
            return False

        self._sync_all_profiles_from_ui()
        payload = self._build_config_payload()

        try:
            assert self.data_folder is not None
            self.data_folder.mkdir(parents=True, exist_ok=True)
            self.config_path.write_text(
                json.dumps(payload, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
        except Exception as exc:
            if show_message:
                messagebox.showerror(
                    self.t("save_error_title"),
                    self.t("save_error_body", error=exc),
                    parent=self.root,
                )
            return False

        if show_message:
            messagebox.showinfo(
                self.t("save_title"),
                self.t("save_body", path=self.config_path),
                parent=self.root,
            )
        return True

    def _build_config_payload(self) -> dict:
        with self.lock:
            profiles_payload: dict[str, dict] = {}
            for profile_key, profile in self.profiles.items():
                profiles_payload[profile_key] = {
                    "mode": profile.mode,
                    "hold_gate_enabled": profile.hold_gate_enabled,
                    "hold_same_as_output": profile.hold_same_as_output,
                    "hold_button": profile.hold_button,
                    "click_count": profile.click_count,
                    "interval_ms": int(round(profile.interval_seconds * 1000.0)),
                    "hotkey_binding": profile.hotkey_binding,
                }

        return {
            "version": 2,
            "saved_at_epoch": time.time(),
            "language": self.selected_language_code(),
            "window_geometry": self.root.geometry(),
            "profiles": profiles_payload,
        }

    def _load_config(self, show_message: bool = True) -> bool:
        if self.config_path is None or not self.config_path.exists():
            if show_message:
                messagebox.showinfo(
                    self.t("load_missing_title"),
                    self.t("load_missing_body"),
                    parent=self.root,
                )
            return False

        try:
            data = json.loads(self.config_path.read_text(encoding="utf-8"))
        except Exception as exc:
            if show_message:
                messagebox.showerror(
                    self.t("load_error_title"),
                    self.t("load_error_body", error=exc),
                    parent=self.root,
                )
            return False

        profiles_data = data.get("profiles")
        if not isinstance(profiles_data, dict):
            if show_message:
                messagebox.showerror(
                    self.t("invalid_format_title"),
                    self.t("invalid_format_body"),
                    parent=self.root,
                )
            return False

        self.language_var.set(self.language_label(self.current_language))

        for profile_key, profile in self.profiles.items():
            saved = profiles_data.get(profile_key, {})
            if not isinstance(saved, dict):
                continue

            mode = saved.get("mode", profile.mode)
            if mode not in {"hotkey", "hold"}:
                mode = "hotkey"

            hold_same = bool(saved.get("hold_same_as_output", True))
            hold_button = saved.get("hold_button", profile.output_button)
            if hold_button not in self.mouse_button_names():
                hold_button = profile.output_button

            click_count = int(saved.get("click_count", 1))
            if click_count not in {1, 2}:
                click_count = 1

            interval_ms = saved.get("interval_ms", int(round(profile.interval_seconds * 1000.0)))
            try:
                interval_ms = int(max(1, min(float(interval_ms), 60000)))
            except Exception:
                interval_ms = 100

            binding = saved.get("hotkey_binding")
            if not self._is_valid_binding(binding):
                binding = None

            assert profile.mode_var is not None
            assert profile.hold_same_var is not None
            assert profile.hold_button_var is not None
            assert profile.click_type_var is not None
            assert profile.interval_var is not None
            assert profile.hotkey_text_var is not None

            profile.mode_var.set(mode)
            profile.hold_same_var.set(hold_same)
            profile.hold_button_var.set(self.mouse_label(hold_button))
            profile.click_type_var.set(self.click_type_label(click_count))
            profile.interval_var.set(str(interval_ms))

            with self.lock:
                profile.hotkey_binding = binding
                profile.hold_gate_enabled = bool(saved.get("hold_gate_enabled", True))
                profile.active = False
                profile.hold_engaged = False
                profile.next_due_at = 0.0

            profile.hotkey_text_var.set(self._format_binding_display(binding) if binding else self.default_hotkey_prompt())
            self._sync_profile_from_ui(profile_key)
            self._update_profile_widgets(profile_key)

        geometry = data.get("window_geometry")
        if isinstance(geometry, str) and "x" in geometry and "+" in geometry:
            try:
                self.root.geometry(geometry)
            except Exception:
                pass

        self.note_var.set(self.t("load_ok_note"))
        if show_message:
            messagebox.showinfo(
                self.t("load_ok_title"),
                self.t("load_ok_body", path=self.config_path),
                parent=self.root,
            )
        return True

    @staticmethod
    def _is_valid_binding(binding: object) -> bool:
        if not isinstance(binding, dict):
            return False
        return all(
            isinstance(binding.get(field), str) and binding.get(field)
            for field in ("kind", "code")
        )

    def _open_data_folder(self) -> None:
        if self.data_folder is None:
            messagebox.showerror(
                self.t("no_data_folder_title"),
                self.t("no_data_folder_body"),
                parent=self.root,
            )
            return

        try:
            if sys.platform.startswith("win"):
                os.startfile(str(self.data_folder))
            elif sys.platform == "darwin":
                import subprocess
                subprocess.Popen(["open", str(self.data_folder)])
            else:
                import subprocess
                subprocess.Popen(["xdg-open", str(self.data_folder)])
        except Exception as exc:
            messagebox.showerror(
                self.t("open_folder_error_title"),
                self.t("open_folder_error_body", error=exc),
                parent=self.root,
            )

    def _apply_language_change(self) -> None:
        selected = self.selected_language_code()
        if selected == self.current_language:
            messagebox.showinfo(
                self.t("language_no_change_title"),
                self.t("language_no_change_body"),
                parent=self.root,
            )
            return

        if not self._save_config(show_message=False):
            messagebox.showerror(
                self.t("language_save_error_title"),
                self.t("language_save_error_body"),
                parent=self.root,
            )
            return

        messagebox.showinfo(
            self.t("language_saved_title"),
            self.t("language_saved_body"),
            parent=self.root,
        )

    def _create_profiles(self) -> None:
        for key in ("left", "right"):
            title = self.mouse_label(key)
            profile = ClickProfile(
                key=key,
                title=title,
                output_button=key,
                hold_button=key,
                mode_var=tk.StringVar(value="hotkey"),
                hotkey_text_var=tk.StringVar(value=self.default_hotkey_prompt()),
                hold_same_var=tk.BooleanVar(value=True),
                hold_button_var=tk.StringVar(value=self.mouse_label(key)),
                click_type_var=tk.StringVar(value=self.click_type_label(1)),
                interval_var=tk.StringVar(value="100"),
                status_var=tk.StringVar(value=f"{self.t('status_stopped')} | {self.t('status_no_hotkey')}"),
            )

            for var in (
                profile.mode_var,
                profile.hold_button_var,
                profile.click_type_var,
                profile.interval_var,
            ):
                assert var is not None
                var.trace_add(
                    "write",
                    lambda *_args, profile_key=key: self._on_profile_ui_changed(profile_key),
                )

            assert profile.hold_same_var is not None
            profile.hold_same_var.trace_add(
                "write",
                lambda *_args, profile_key=key: self._on_profile_ui_changed(profile_key),
            )

            self.profiles[key] = profile

    def _build_ui(self) -> None:
        outer = ScrollableFrame(self.root)
        outer.pack(fill="both", expand=True)
        body = outer.inner
        body.columnconfigure(0, weight=1)

        ttk.Label(
            body,
            text=self.t("app_title"),
            font=("Segoe UI", 16, "bold"),
        ).grid(row=0, column=0, sticky="w", padx=14, pady=(14, 6))

        ttk.Label(
            body,
            text=self.t("top_intro"),
            wraplength=500,
            justify="left",
        ).grid(row=1, column=0, sticky="ew", padx=14, pady=(0, 10))

        self._build_profile_section(body, row=2, profile=self.profiles["left"])
        self._build_profile_section(body, row=3, profile=self.profiles["right"])

        note_frame = ttk.LabelFrame(body, text=self.t("general_notes_title"), padding=12)
        note_frame.grid(row=4, column=0, sticky="ew", padx=14, pady=(6, 8))
        note_frame.columnconfigure(0, weight=1)

        ttk.Label(
            note_frame,
            textvariable=self.note_var,
            wraplength=490,
            justify="left",
        ).grid(row=0, column=0, sticky="w")

        ttk.Label(
            note_frame,
            text=self.t("general_notes_body"),
            wraplength=490,
            justify="left",
        ).grid(row=1, column=0, sticky="w", pady=(10, 0))

        storage_frame = ttk.LabelFrame(body, text=self.t("storage_title"), padding=12)
        storage_frame.grid(row=5, column=0, sticky="ew", padx=14, pady=(0, 8))
        storage_frame.columnconfigure(0, weight=1)
        storage_frame.columnconfigure(1, weight=1)

        ttk.Label(
            storage_frame,
            textvariable=self.data_folder_var,
            wraplength=490,
            justify="left",
        ).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 10))

        ttk.Button(storage_frame, text=self.t("save_now"), command=self._save_config).grid(
            row=1, column=0, sticky="ew", padx=(0, 6), pady=3
        )
        ttk.Button(storage_frame, text=self.t("load_saved"), command=self._load_config).grid(
            row=1, column=1, sticky="ew", padx=(6, 0), pady=3
        )
        ttk.Button(storage_frame, text=self.t("open_folder"), command=self._open_data_folder).grid(
            row=2, column=0, sticky="ew", padx=(0, 6), pady=3
        )
        ttk.Button(storage_frame, text=self.t("change_folder"), command=self._change_data_folder).grid(
            row=2, column=1, sticky="ew", padx=(6, 0), pady=3
        )

        ttk.Label(
            storage_frame,
            text=self.t("storage_note"),
            wraplength=490,
            justify="left",
        ).grid(row=3, column=0, columnspan=2, sticky="w", pady=(8, 0))

        language_frame = ttk.LabelFrame(body, text=self.t("language_title"), padding=12)
        language_frame.grid(row=6, column=0, sticky="ew", padx=14, pady=(0, 8))
        language_frame.columnconfigure(1, weight=1)

        ttk.Label(language_frame, text=self.t("language_label")).grid(
            row=0, column=0, sticky="w", padx=(0, 10)
        )

        ttk.Combobox(
            language_frame,
            textvariable=self.language_var,
            state="readonly",
            values=[self.language_label("es"), self.language_label("en")],
        ).grid(row=0, column=1, sticky="ew")

        ttk.Button(
            language_frame,
            text=self.t("apply_language"),
            command=self._apply_language_change,
        ).grid(row=1, column=0, columnspan=2, sticky="ew", pady=(8, 0))

        ttk.Label(
            language_frame,
            text=self.t("language_note"),
            wraplength=490,
            justify="left",
        ).grid(row=2, column=0, columnspan=2, sticky="w", pady=(8, 0))

        ttk.Label(
            body,
            text=self.t("watermark"),
            font=("Segoe UI", 9, "italic"),
            anchor="center",
            justify="center",
        ).grid(row=7, column=0, sticky="ew", padx=14, pady=(0, 16))

    def _build_profile_section(self, parent: ttk.Frame, row: int, profile: ClickProfile) -> None:
        section = ttk.LabelFrame(parent, text=profile.title, padding=12)
        section.grid(row=row, column=0, sticky="ew", padx=14, pady=6)
        section.columnconfigure(0, weight=1)

        ttk.Label(
            section,
            text=self.t("section_controls_only", title=profile.title.lower()),
            wraplength=490,
            justify="left",
        ).grid(row=0, column=0, sticky="w", pady=(0, 10))

        mode_frame = ttk.LabelFrame(section, text=self.t("activation_mode_title"), padding=10)
        mode_frame.grid(row=1, column=0, sticky="ew", pady=4)
        mode_frame.columnconfigure(0, weight=1)

        assert profile.mode_var is not None
        ttk.Radiobutton(
            mode_frame,
            text=self.t("hotkey_mode_label"),
            variable=profile.mode_var,
            value="hotkey",
            command=lambda profile_key=profile.key: self._update_profile_widgets(profile_key),
        ).grid(row=0, column=0, sticky="w", pady=(0, 5))

        ttk.Radiobutton(
            mode_frame,
            text=self.t("hold_mode_label"),
            variable=profile.mode_var,
            value="hold",
            command=lambda profile_key=profile.key: self._update_profile_widgets(profile_key),
        ).grid(row=1, column=0, sticky="w")

        hotkey_frame = ttk.LabelFrame(section, text=self.t("hotkey_group_title"), padding=10)
        hotkey_frame.grid(row=2, column=0, sticky="ew", pady=4)
        hotkey_frame.columnconfigure(0, weight=1)
        hotkey_frame.columnconfigure(1, weight=0)
        hotkey_frame.columnconfigure(2, weight=0)

        ttk.Label(
            hotkey_frame,
            text=self.t("hotkey_help"),
            wraplength=470,
            justify="left",
        ).grid(row=0, column=0, columnspan=3, sticky="w", pady=(0, 8))

        entry = ttk.Entry(
            hotkey_frame,
            textvariable=profile.hotkey_text_var,
            justify="center",
            state="readonly",
        )
        entry.grid(row=1, column=0, sticky="ew", padx=(0, 8))
        entry.bind(
            "<Button-1>",
            lambda event, profile_key=profile.key: self.start_hotkey_capture(profile_key, event),
        )

        capture_button = ttk.Button(
            hotkey_frame,
            text=self.t("capture"),
            command=lambda profile_key=profile.key: self.start_hotkey_capture(profile_key),
        )
        capture_button.grid(row=1, column=1, padx=(0, 8))

        clear_button = ttk.Button(
            hotkey_frame,
            text=self.t("clear"),
            command=lambda profile_key=profile.key: self.clear_hotkey(profile_key),
        )
        clear_button.grid(row=1, column=2)

        ttk.Label(
            hotkey_frame,
            text=self.t("hotkey_extra"),
            wraplength=470,
            justify="left",
        ).grid(row=2, column=0, columnspan=3, sticky="w", pady=(8, 0))

        hold_frame = ttk.LabelFrame(section, text=self.t("hold_group_title"), padding=10)
        hold_frame.grid(row=3, column=0, sticky="ew", pady=4)
        hold_frame.columnconfigure(1, weight=1)

        hold_same_check = ttk.Checkbutton(
            hold_frame,
            text=self.t("hold_same_check", title=profile.title.lower()),
            variable=profile.hold_same_var,
            command=lambda profile_key=profile.key: self._update_profile_widgets(profile_key),
        )
        hold_same_check.grid(row=0, column=0, columnspan=2, sticky="w")

        ttk.Label(
            hold_frame,
            text=self.t("hold_pick_help"),
            wraplength=470,
            justify="left",
        ).grid(row=1, column=0, columnspan=2, sticky="w", pady=(8, 6))

        ttk.Label(hold_frame, text=self.t("hold_button_label")).grid(
            row=2, column=0, sticky="w", padx=(0, 10)
        )

        hold_combo = ttk.Combobox(
            hold_frame,
            textvariable=profile.hold_button_var,
            state="readonly",
            values=self.mouse_option_labels(),
        )
        hold_combo.grid(row=2, column=1, sticky="ew")

        ttk.Label(
            hold_frame,
            text=self.t("hold_group_note"),
            wraplength=470,
            justify="left",
        ).grid(row=3, column=0, columnspan=2, sticky="w", pady=(8, 0))

        click_frame = ttk.LabelFrame(section, text=self.t("click_group_title"), padding=10)
        click_frame.grid(row=4, column=0, sticky="ew", pady=4)
        click_frame.columnconfigure(1, weight=1)

        ttk.Label(click_frame, text=self.t("output_button_label")).grid(
            row=0, column=0, sticky="w", padx=(0, 10), pady=4
        )
        ttk.Label(click_frame, text=profile.title).grid(
            row=0, column=1, sticky="w", pady=4
        )

        ttk.Label(click_frame, text=self.t("click_type_label")).grid(
            row=1, column=0, sticky="w", padx=(0, 10), pady=4
        )
        ttk.Combobox(
            click_frame,
            textvariable=profile.click_type_var,
            state="readonly",
            values=[self.click_type_label(1), self.click_type_label(2)],
        ).grid(row=1, column=1, sticky="ew", pady=4)

        ttk.Label(click_frame, text=self.t("interval_label")).grid(
            row=2, column=0, sticky="w", padx=(0, 10), pady=4
        )
        tk.Spinbox(
            click_frame,
            from_=1,
            to=60000,
            increment=1,
            textvariable=profile.interval_var,
        ).grid(row=2, column=1, sticky="ew", pady=4)

        ttk.Label(
            click_frame,
            text=self.t("interval_help"),
            wraplength=470,
            justify="left",
        ).grid(row=3, column=0, columnspan=2, sticky="w", pady=(8, 0))

        control_frame = ttk.LabelFrame(section, text=self.t("control_title"), padding=10)
        control_frame.grid(row=5, column=0, sticky="ew", pady=4)
        control_frame.columnconfigure(0, weight=1)
        control_frame.columnconfigure(1, weight=1)

        ttk.Button(
            control_frame,
            text=self.t("stop_now"),
            command=lambda profile_key=profile.key: self.force_stop(profile_key),
        ).grid(row=0, column=0, sticky="ew", padx=(0, 6))

        ttk.Button(
            control_frame,
            text=self.t("test_click"),
            command=lambda profile_key=profile.key: self.test_click(profile_key),
        ).grid(row=0, column=1, sticky="ew", padx=(6, 0))

        status_frame = ttk.LabelFrame(section, text=self.t("status_title"), padding=10)
        status_frame.grid(row=6, column=0, sticky="ew", pady=4)
        status_frame.columnconfigure(0, weight=1)

        ttk.Label(
            status_frame,
            textvariable=profile.status_var,
            font=("Segoe UI", 10, "bold"),
            wraplength=470,
            justify="left",
        ).grid(row=0, column=0, sticky="w")

        profile.widgets = {
            "hotkey_entry": entry,
            "capture_button": capture_button,
            "clear_hotkey_button": clear_button,
            "hold_same_check": hold_same_check,
            "hold_combo": hold_combo,
        }

    def _on_profile_ui_changed(self, profile_key: str) -> None:
        self._sync_profile_from_ui(profile_key)
        self._update_profile_widgets(profile_key)

    def _sync_all_profiles_from_ui(self) -> None:
        for profile_key in self.profiles:
            self._sync_profile_from_ui(profile_key)

    def _sync_profile_from_ui(self, profile_key: str) -> None:
        profile = self.profiles[profile_key]

        assert profile.mode_var is not None
        assert profile.hold_same_var is not None
        assert profile.hold_button_var is not None
        assert profile.click_type_var is not None
        assert profile.interval_var is not None

        with self.lock:
            previous_mode = profile.mode
            previous_hold_button = profile.hold_button
            profile.mode = profile.mode_var.get().strip() or "hotkey"
            profile.hold_same_as_output = bool(profile.hold_same_var.get())
            profile.hold_button = (
                profile.output_button
                if profile.hold_same_as_output
                else self.mouse_name_from_label(profile.hold_button_var.get())
            )
            profile.click_count = self.click_count_from_label(profile.click_type_var.get())

            try:
                interval_ms = float(str(profile.interval_var.get()).replace(",", "."))
            except ValueError:
                interval_ms = profile.interval_seconds * 1000.0

            interval_ms = max(1.0, min(interval_ms, 60000.0))
            profile.interval_seconds = interval_ms / 1000.0

            if previous_hold_button != profile.hold_button:
                profile.active = False
                profile.next_due_at = 0.0
                profile.hold_engaged = False

            if previous_mode != profile.mode:
                profile.active = False
                profile.next_due_at = 0.0
                profile.hold_engaged = False
                if profile.mode == "hold":
                    profile.hold_gate_enabled = True

    def _refresh_all_mode_widgets(self) -> None:
        for profile_key in self.profiles:
            self._update_profile_widgets(profile_key)

    def _update_profile_widgets(self, profile_key: str) -> None:
        profile = self.profiles[profile_key]
        assert profile.mode_var is not None
        assert profile.hold_same_var is not None

        hold_enabled = profile.mode_var.get() == "hold"
        hold_same = bool(profile.hold_same_var.get())

        hold_same_check = profile.widgets.get("hold_same_check")
        hold_combo = profile.widgets.get("hold_combo")
        capture_button = profile.widgets.get("capture_button")
        clear_button = profile.widgets.get("clear_hotkey_button")
        hotkey_entry = profile.widgets.get("hotkey_entry")

        if capture_button is not None:
            capture_button.configure(state="normal")
        if clear_button is not None:
            clear_button.configure(state="normal")
        if hotkey_entry is not None:
            hotkey_entry.configure(state="readonly")
        if hold_same_check is not None:
            hold_same_check.configure(state="normal" if hold_enabled else "disabled")
        if hold_combo is not None:
            hold_combo.configure(state="readonly" if hold_enabled and not hold_same else "disabled")

    def _start_threads(self) -> None:
        self.keyboard_listener = keyboard.Listener(
            on_press=self._on_key_press,
            on_release=self._on_key_release,
        )

        mouse_listener_kwargs = {
            "on_click": self._on_mouse_click,
            "on_scroll": self._on_mouse_scroll,
        }
        if sys.platform.startswith("win"):
            mouse_listener_kwargs["win32_event_filter"] = self._mouse_win32_filter

        self.mouse_listener = mouse.Listener(**mouse_listener_kwargs)

        self.keyboard_listener.start()
        self.mouse_listener.start()

        self.worker_thread = threading.Thread(target=self._click_loop, daemon=True)
        self.worker_thread.start()

    @staticmethod
    def _mouse_win32_filter(_msg, data):
        flags = getattr(data, "flags", 0)
        if flags & _LLMHF_INJECTED:
            return False
        return True

    def start_hotkey_capture(self, profile_key: str, _event: tk.Event | None = None) -> None:
        profile = self.profiles[profile_key]
        assert profile.hotkey_text_var is not None

        profile.hotkey_text_var.set(self.t("hotkey_capture_prompt"))
        self.note_var.set(self.t("waiting_hotkey_note", title=profile.title.lower()))
        with self.lock:
            self.capture_target = profile_key
            self.capture_armed_at = time.monotonic() + 0.15
            self.debounced_triggers.clear()

    def clear_hotkey(self, profile_key: str) -> None:
        profile = self.profiles[profile_key]
        assert profile.hotkey_text_var is not None

        with self.lock:
            profile.hotkey_binding = None
            if self.capture_target == profile_key:
                self.capture_target = None
            self.debounced_triggers.clear()

        profile.hotkey_text_var.set(self.default_hotkey_prompt())
        self.note_var.set(self.t("hotkey_cleared_note", title=profile.title.lower()))

    def force_stop(self, profile_key: str) -> None:
        profile = self.profiles[profile_key]
        with self.lock:
            profile.active = False
            profile.next_due_at = 0.0
            profile.hold_engaged = False
            has_hotkey = profile.hotkey_binding is not None
            if profile.mode == "hold" and has_hotkey:
                profile.hold_gate_enabled = False
            self.debounced_triggers.clear()

        if profile.mode == "hold":
            if has_hotkey:
                self.note_var.set(self.t("manual_stop_hold_disabled", title=profile.title))
            else:
                self.note_var.set(self.t("manual_stop_hold_available", title=profile.title))
        else:
            self.note_var.set(self.t("manual_stop", title=profile.title))

    def test_click(self, profile_key: str) -> None:
        profile = self.profiles[profile_key]
        delay_seconds = 0.35
        self.note_var.set(self.t("test_click_note", title=profile.title, seconds=delay_seconds))
        threading.Thread(
            target=self._delayed_test_click,
            args=(profile_key, delay_seconds),
            daemon=True,
        ).start()

    def _delayed_test_click(self, profile_key: str, delay_seconds: float) -> None:
        time.sleep(delay_seconds)
        with self.lock:
            profile = self.profiles[profile_key]
            output_button = profile.output_button
            click_count = profile.click_count

        self._emit_click(output_button, click_count)
        if self.running:
            profile = self.profiles[profile_key]
            self.root.after(
                0,
                lambda: self.note_var.set(self.t("test_click_done", title=profile.title.lower())),
            )

    def _refresh_status_loop(self) -> None:
        if not self.running:
            return

        for profile_key, profile in self.profiles.items():
            assert profile.status_var is not None
            profile.status_var.set(self._status_text_for_profile(profile_key))

        self.root.after(100, self._refresh_status_loop)

    def _status_text_for_profile(self, profile_key: str) -> str:
        with self.lock:
            profile = self.profiles[profile_key]
            capture_target = self.capture_target
            hotkey_binding = profile.hotkey_binding
            mode = profile.mode
            active = profile.active
            hold_gate_enabled = profile.hold_gate_enabled
            hold_is_pressed = profile.hold_engaged

        if capture_target == profile_key:
            base = self.t("status_waiting_hotkey")
        elif mode == "hotkey":
            base = self.t("status_active") if active else self.t("status_stopped")
        else:
            if not hold_gate_enabled:
                base = self.t("status_hold_disabled")
            elif hold_is_pressed:
                base = self.t("status_hold_pressed")
            else:
                base = self.t("status_hold_waiting")

        if hotkey_binding:
            return f"{base} | {self.t('status_hotkey', display=self._format_binding_display(hotkey_binding))}"
        return f"{base} | {self.t('status_no_hotkey')}"

    def _click_loop(self) -> None:
        while self.running:
            now = time.monotonic()
            did_click = False

            for profile_key in list(self.profiles.keys()):
                with self.lock:
                    profile = self.profiles[profile_key]
                    should_click = self._should_profile_click_locked(profile)
                    interval_seconds = profile.interval_seconds
                    output_button = profile.output_button
                    click_count = profile.click_count
                    same_button_hold = profile.mode == "hold" and profile.hold_button == profile.output_button

                    if should_click:
                        if profile.next_due_at <= 0.0:
                            initial_delay = interval_seconds if same_button_hold else 0.0
                            profile.next_due_at = now + initial_delay

                        if now >= profile.next_due_at:
                            profile.next_due_at = now + interval_seconds
                            fire_now = True
                        else:
                            fire_now = False
                    else:
                        profile.next_due_at = 0.0
                        fire_now = False

                if fire_now:
                    if same_button_hold and not sys.platform.startswith("win"):
                        self._emit_click_while_holding_same_button(output_button, click_count)
                    else:
                        self._emit_click(output_button, click_count)
                    did_click = True

            time.sleep(0.002 if did_click else 0.01)

    def _should_profile_click_locked(self, profile: ClickProfile) -> bool:
        if profile.mode == "hotkey":
            return profile.active
        if not profile.hold_gate_enabled:
            return False
        return profile.hold_engaged

    def _emit_click(self, button_name: str, click_count: int) -> None:
        button_obj = self._mouse_button_from_name(button_name)
        if button_obj is None:
            return

        if not sys.platform.startswith("win"):
            now = time.monotonic()
            with self.lock:
                self.synthetic_event_budget[button_name] = (
                    self.synthetic_event_budget.get(button_name, 0) + (6 * click_count)
                )
                self.synthetic_ignore_until[button_name] = max(
                    self.synthetic_ignore_until.get(button_name, 0.0),
                    now + 0.03,
                )
                self.last_synthetic_click_at[button_name] = now

        self.mouse_controller.click(button_obj, click_count)

    def _emit_click_while_holding_same_button(self, button_name: str, click_count: int) -> None:
        button_obj = self._mouse_button_from_name(button_name)
        if button_obj is None:
            return

        now = time.monotonic()
        with self.lock:
            self.synthetic_event_budget[button_name] = (
                self.synthetic_event_budget.get(button_name, 0) + (6 * click_count)
            )
            self.synthetic_ignore_until[button_name] = max(
                self.synthetic_ignore_until.get(button_name, 0.0),
                now + 0.03,
            )
            self.last_synthetic_click_at[button_name] = now

        for _ in range(max(1, click_count)):
            self.mouse_controller.release(button_obj)
            time.sleep(0.001)
            self.mouse_controller.press(button_obj)

    def _consume_synthetic_mouse_event(self, button_name: str) -> bool:
        if sys.platform.startswith("win"):
            return False

        now = time.monotonic()
        with self.lock:
            remaining = self.synthetic_event_budget.get(button_name, 0)
            if remaining > 0:
                remaining -= 1
                if remaining <= 0:
                    self.synthetic_event_budget.pop(button_name, None)
                else:
                    self.synthetic_event_budget[button_name] = remaining
                return True

            ignore_until = self.synthetic_ignore_until.get(button_name, 0.0)
            if now < ignore_until:
                return True

            if ignore_until:
                self.synthetic_ignore_until.pop(button_name, None)

            return False

    def _on_key_press(self, key: keyboard.Key | keyboard.KeyCode) -> None:
        binding = self._binding_from_key(key)
        if binding is None:
            return

        if self._maybe_capture_hotkey(binding):
            return

        self._trigger_binding(binding, use_debounce=True)

    def _on_key_release(self, key: keyboard.Key | keyboard.KeyCode) -> None:
        binding = self._binding_from_key(key)
        if binding is None:
            return
        self._release_trigger(binding)

    def _on_mouse_click(self, _x: int, _y: int, button: mouse.Button, pressed: bool) -> None:
        binding = self._binding_from_mouse_button(button)
        if binding is None:
            return

        button_name = binding["code"].split(":", 1)[1]
        if self._consume_synthetic_mouse_event(button_name):
            return

        with self.lock:
            if pressed:
                self.pressed_mouse_buttons.add(button_name)
            else:
                self.pressed_mouse_buttons.discard(button_name)

            for profile in self.profiles.values():
                if profile.mode == "hold" and profile.hold_button == button_name:
                    profile.hold_engaged = pressed
                    if not pressed:
                        profile.next_due_at = 0.0

        if pressed and self._maybe_capture_hotkey(binding):
            return

        if pressed:
            self._trigger_binding(binding, use_debounce=True)
        else:
            self._release_trigger(binding)

    def _on_mouse_scroll(self, _x: int, _y: int, _dx: int, dy: int) -> None:
        if dy == 0:
            return

        binding = self._binding_from_wheel("up" if dy > 0 else "down")
        if self._maybe_capture_hotkey(binding):
            return

        self._trigger_binding(binding, use_debounce=False)

    def _maybe_capture_hotkey(self, binding: dict[str, str]) -> bool:
        with self.lock:
            target = self.capture_target
            armed_at = self.capture_armed_at
            if target is None or time.monotonic() < armed_at:
                return False

            profile = self.profiles[target]
            profile.hotkey_binding = binding
            self.capture_target = None
            self.debounced_triggers.clear()

        assert profile.hotkey_text_var is not None

        if self.running:
            self.root.after(
                0,
                lambda: self._apply_hotkey_capture_ui(target, binding),
            )
        return True

    def _apply_hotkey_capture_ui(self, profile_key: str, binding: dict[str, str]) -> None:
        profile = self.profiles[profile_key]
        assert profile.hotkey_text_var is not None
        profile.hotkey_text_var.set(self._format_binding_display(binding))
        self.note_var.set(
            self.t("hotkey_captured_note", title=profile.title.lower(), display=self._format_binding_display(binding))
        )

    def _trigger_binding(self, binding: dict[str, str], use_debounce: bool) -> None:
        binding_id = self._binding_id(binding)

        with self.lock:
            if use_debounce and binding_id in self.debounced_triggers:
                return

            messages: list[str] = []
            for profile in self.profiles.values():
                hotkey_binding = profile.hotkey_binding
                if hotkey_binding is None:
                    continue
                if self._binding_id(hotkey_binding) != binding_id:
                    continue

                if profile.mode == "hotkey":
                    profile.active = not profile.active
                    if not profile.active:
                        profile.next_due_at = 0.0
                    state = self.t("toggle_active_on") if profile.active else self.t("toggle_active_off")
                    messages.append(self.t("toggle_active", title=profile.title, state=state))
                else:
                    profile.hold_gate_enabled = not profile.hold_gate_enabled
                    if not profile.hold_gate_enabled:
                        profile.next_due_at = 0.0
                        profile.hold_engaged = False
                    state = self.t("toggle_hold_on") if profile.hold_gate_enabled else self.t("toggle_hold_off")
                    messages.append(self.t("toggle_hold", title=profile.title, state=state))

            if not messages:
                return

            if use_debounce:
                self.debounced_triggers.add(binding_id)

        if self.running:
            joined = " | ".join(messages)
            self.root.after(
                0,
                lambda: self.note_var.set(self.t("trigger_by_binding", text=joined, display=self._format_binding_display(binding))),
            )

    def _release_trigger(self, binding: dict[str, str]) -> None:
        with self.lock:
            self.debounced_triggers.discard(self._binding_id(binding))

    @staticmethod
    def _binding_id(binding: dict[str, str]) -> tuple[str, str]:
        return (binding["kind"], binding["code"])

    @staticmethod
    def _mouse_button_from_name(name: str) -> mouse.Button | None:
        if name == "left":
            return mouse.Button.left
        if name == "right":
            return mouse.Button.right
        if name == "middle":
            return mouse.Button.middle
        if hasattr(mouse.Button, "x1") and name == "x1":
            return mouse.Button.x1
        if hasattr(mouse.Button, "x2") and name == "x2":
            return mouse.Button.x2
        return None

    def _binding_from_mouse_button(self, button: mouse.Button) -> dict[str, str] | None:
        name = getattr(button, "name", None)
        if not name:
            raw = str(button)
            name = raw.replace("Button.", "")

        if not name:
            return None

        return {
            "kind": "mouse",
            "code": f"button:{name}",
            "display": self.mouse_label(name),
        }

    def _binding_from_wheel(self, direction: str) -> dict[str, str]:
        return {
            "kind": "wheel",
            "code": direction,
            "display": self.t("wheel_up") if direction == "up" else self.t("wheel_down"),
        }

    def _key_display(self, name: str) -> str:
        key_text_key = KEY_TEXT_KEYS.get(name)
        if key_text_key:
            return self.t(key_text_key)
        return name.replace("_", " ").upper()

    def _binding_from_key(self, key: keyboard.Key | keyboard.KeyCode) -> dict[str, str] | None:
        char = getattr(key, "char", None)
        if char:
            if char == "\r":
                char = "enter"
            elif char == "\t":
                char = "tab"
            elif char == " ":
                char = "space"

            display = self._key_display(char) if len(char) > 1 else char.upper()
            return {
                "kind": "keyboard",
                "code": f"char:{char.lower()}",
                "display": display,
            }

        name = getattr(key, "name", None)
        if not name:
            raw = str(key)
            if raw.startswith("Key."):
                name = raw[4:]
            else:
                name = raw

        if not name:
            return None

        return {
            "kind": "keyboard",
            "code": f"key:{name}",
            "display": self._key_display(name),
        }

    def _format_binding_display(self, binding: dict[str, str] | None) -> str:
        if not binding:
            return self.default_hotkey_prompt()

        kind = binding.get("kind", "")
        code = binding.get("code", "")

        if kind == "mouse" and code.startswith("button:"):
            return self.mouse_label(code.split(":", 1)[1])
        if kind == "wheel":
            return self.t("wheel_up") if code == "up" else self.t("wheel_down")
        if kind == "keyboard":
            if code.startswith("char:"):
                value = code.split(":", 1)[1]
                return self._key_display(value) if len(value) > 1 else value.upper()
            if code.startswith("key:"):
                return self._key_display(code.split(":", 1)[1])

        return binding.get("display", code or self.default_hotkey_prompt())

    def on_close(self) -> None:
        if getattr(self, "initialized", False):
            try:
                self._save_config(show_message=False)
            except Exception:
                pass

        self.running = False
        with self.lock:
            self.capture_target = None
            self.debounced_triggers.clear()
            self.pressed_mouse_buttons.clear()
            self.synthetic_event_budget.clear()
            self.synthetic_ignore_until.clear()
            self.last_synthetic_click_at.clear()
            for profile in self.profiles.values():
                profile.active = False
                profile.next_due_at = 0.0
                profile.hold_engaged = False

        try:
            if self.keyboard_listener is not None:
                self.keyboard_listener.stop()
        except Exception:
            pass

        try:
            if self.mouse_listener is not None:
                self.mouse_listener.stop()
        except Exception:
            pass

        self.root.after(50, self.root.destroy)


def main() -> None:
    root = tk.Tk()
    style = ttk.Style(root)
    try:
        style.theme_use("clam")
    except Exception:
        pass
    app = AutoClickerApp(root)
    if not getattr(app, "initialized", False):
        try:
            root.update_idletasks()
        except Exception:
            pass
        return
    root.mainloop()


if __name__ == "__main__":
    main()
