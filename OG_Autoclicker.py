"""
OG Autoclicker con interfaz gráfica en Tkinter.

Funciones incluidas:
- Dos paneles independientes: uno para click izquierdo y otro para click derecho.
- Cada panel tiene su propia hotkey global capturada por pulsación real.
- Reconoce teclado, botones del mouse y la ruedita (arriba/abajo) como hotkey.
- Cada panel puede funcionar en modo hotkey o en modo Hold click.
- En modo Hold click, la hotkey del panel funciona como seguro para habilitarlo o deshabilitarlo.
- Barra de desplazamiento vertical para usar la app aunque la ventana sea pequeña.
- Click de prueba, detener ahora, intervalo y tipo de click por separado.
- Marca de agua visual con el texto: Developed By Valentino Galli / KidOGzz

Dependencia externa:
    pip install pynput

Notas:
- Si usas el mismo botón para Hold click y para el autoclick, el primer clic automático
  espera el intervalo configurado para evitar una sensación de doble clic instantáneo.
- El Hold click prioriza el estado físico que sigue el listener global, ignorando los
  clicks sintéticos del propio autoclicker para que no se corte tras el primer disparo.
- En Linux/macOS también funciona, pero el comportamiento puede variar más según el sistema.
"""

from __future__ import annotations

import json
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
            "Dependencia faltante",
            "No se encontró 'pynput'.\n\nInstálalo con:\n\npip install pynput",
        )
    raise SystemExit("Falta instalar 'pynput': pip install pynput") from exc


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


KEY_DISPLAY = {
    "alt": "ALT",
    "alt_gr": "ALT GR",
    "alt_l": "ALT IZQ",
    "alt_r": "ALT DER",
    "backspace": "RETROCESO",
    "caps_lock": "BLOQ MAYÚS",
    "cmd": "CMD",
    "cmd_l": "CMD IZQ",
    "cmd_r": "CMD DER",
    "ctrl": "CTRL",
    "ctrl_l": "CTRL IZQ",
    "ctrl_r": "CTRL DER",
    "delete": "SUPR",
    "down": "FLECHA ABAJO",
    "end": "FIN",
    "enter": "ENTER",
    "esc": "ESC",
    "f1": "F1",
    "f2": "F2",
    "f3": "F3",
    "f4": "F4",
    "f5": "F5",
    "f6": "F6",
    "f7": "F7",
    "f8": "F8",
    "f9": "F9",
    "f10": "F10",
    "f11": "F11",
    "f12": "F12",
    "home": "INICIO",
    "insert": "INSERT",
    "left": "FLECHA IZQ",
    "menu": "MENÚ",
    "num_lock": "BLOQ NUM",
    "page_down": "RE PÁG",
    "page_up": "AV PÁG",
    "pause": "PAUSA",
    "print_screen": "IMPR PANT",
    "right": "FLECHA DER",
    "scroll_lock": "BLOQ DESPL",
    "shift": "SHIFT",
    "shift_l": "SHIFT IZQ",
    "shift_r": "SHIFT DER",
    "space": "ESPACIO",
    "tab": "TAB",
    "up": "FLECHA ARRIBA",
}

MOUSE_DISPLAY = {
    "left": "Click izquierdo",
    "right": "Click derecho",
    "middle": "Click medio",
    "x1": "Botón lateral 1",
    "x2": "Botón lateral 2",
}

MOUSE_OPTION_TO_NAME = {
    "Click izquierdo": "left",
    "Click derecho": "right",
    "Click medio": "middle",
}
if hasattr(mouse.Button, "x1"):
    MOUSE_OPTION_TO_NAME["Botón lateral 1"] = "x1"
if hasattr(mouse.Button, "x2"):
    MOUSE_OPTION_TO_NAME["Botón lateral 2"] = "x2"

CLICK_TYPE_TO_COUNT = {
    "Simple": 1,
    "Doble": 2,
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
        self.root.title("OG Autoclicker")
        self.root.geometry("560x860")
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

        self.note_var = tk.StringVar(
            value=(
                "Ubicación del click: donde esté el cursor. "
                "Ahora tienes un panel para izquierdo y otro para derecho."
            )
        )
        self.data_folder_var = tk.StringVar(value="Carpeta de datos: no configurada")

        if not self._ensure_data_folder_selected():
            self.root.after(0, self.root.destroy)
            return

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

    def _ensure_data_folder_selected(self) -> bool:
        locator_path = DATA_FOLDER_LOCATOR
        stored_folder = self._read_data_folder_from_locator(locator_path)
        if stored_folder is not None and stored_folder.exists():
            self._set_data_folder(stored_folder)
            return True

        while True:
            messagebox.showinfo(
                "Carpeta de datos",
                "Es la primera vez que inicias OG Autoclicker, o la carpeta anterior ya no existe.\n\n"
                "Selecciona o crea una carpeta donde se guardarán tus configuraciones.",
                parent=self.root,
            )
            chosen = filedialog.askdirectory(
                parent=self.root,
                mustexist=False,
                title="Selecciona o crea la carpeta de datos de OG Autoclicker",
            )
            if chosen:
                folder = Path(chosen).expanduser()
                try:
                    folder.mkdir(parents=True, exist_ok=True)
                    self._set_data_folder(folder)
                    self._save_data_folder_locator()
                    self.note_var.set(
                        f"Carpeta de datos configurada en: {folder}"
                    )
                    return True
                except Exception as exc:
                    messagebox.showerror(
                        "No se pudo usar la carpeta",
                        f"No se pudo preparar la carpeta seleccionada.\n\n{exc}",
                        parent=self.root,
                    )
                    continue

            retry = messagebox.askretrycancel(
                "Carpeta requerida",
                "OG Autoclicker necesita una carpeta para guardar tus datos.\n\n"
                "Pulsa Reintentar para elegir una carpeta o Cancelar para cerrar la app.",
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
        self.data_folder_var.set(f"Carpeta de datos: {folder}")

    def _change_data_folder(self) -> None:
        chosen = filedialog.askdirectory(
            parent=self.root,
            mustexist=False,
            title="Selecciona o crea una nueva carpeta de datos",
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
            self.note_var.set(f"Nueva carpeta de datos: {new_folder}")
            messagebox.showinfo(
                "Carpeta actualizada",
                "La carpeta de datos se actualizó correctamente.",
                parent=self.root,
            )
        except Exception as exc:
            messagebox.showerror(
                "Error al cambiar carpeta",
                f"No se pudo cambiar la carpeta de datos.\n\n{exc}",
                parent=self.root,
            )

    def _save_config(self, show_message: bool = True) -> bool:
        if self.config_path is None:
            if show_message:
                messagebox.showerror(
                    "Sin carpeta de datos",
                    "Todavía no hay una carpeta de datos configurada.",
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
                    "No se pudo guardar",
                    f"Ocurrió un error al guardar la configuración.\n\n{exc}",
                    parent=self.root,
                )
            return False

        if show_message:
            messagebox.showinfo(
                "Configuración guardada",
                f"La configuración se guardó en:\n\n{self.config_path}",
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
            "version": 1,
            "saved_at_epoch": time.time(),
            "window_geometry": self.root.geometry(),
            "profiles": profiles_payload,
        }

    def _load_config(self, show_message: bool = True) -> bool:
        if self.config_path is None or not self.config_path.exists():
            if show_message:
                messagebox.showinfo(
                    "Sin configuración guardada",
                    "Todavía no existe un archivo de configuración en la carpeta de datos actual.",
                    parent=self.root,
                )
            return False

        try:
            data = json.loads(self.config_path.read_text(encoding="utf-8"))
        except Exception as exc:
            if show_message:
                messagebox.showerror(
                    "No se pudo cargar",
                    f"El archivo de configuración no se pudo leer.\n\n{exc}",
                    parent=self.root,
                )
            return False

        profiles_data = data.get("profiles")
        if not isinstance(profiles_data, dict):
            if show_message:
                messagebox.showerror(
                    "Formato inválido",
                    "El archivo de configuración no tiene un formato válido.",
                    parent=self.root,
                )
            return False

        for profile_key, profile in self.profiles.items():
            saved = profiles_data.get(profile_key, {})
            if not isinstance(saved, dict):
                continue

            mode = saved.get("mode", profile.mode)
            if mode not in {"hotkey", "hold"}:
                mode = "hotkey"

            hold_same = bool(saved.get("hold_same_as_output", True))
            hold_button = saved.get("hold_button", profile.output_button)
            if hold_button not in MOUSE_DISPLAY:
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
            profile.hold_button_var.set(MOUSE_DISPLAY.get(hold_button, MOUSE_DISPLAY[profile.output_button]))
            profile.click_type_var.set("Doble" if click_count == 2 else "Simple")
            profile.interval_var.set(str(interval_ms))

            with self.lock:
                profile.hotkey_binding = binding
                profile.hold_gate_enabled = bool(saved.get("hold_gate_enabled", True))
                profile.active = False
                profile.hold_engaged = False
                profile.next_due_at = 0.0

            profile.hotkey_text_var.set(binding["display"] if binding else "Haz clic aquí para elegir hotkey")
            self._sync_profile_from_ui(profile_key)
            self._update_profile_widgets(profile_key)

        geometry = data.get("window_geometry")
        if isinstance(geometry, str) and "x" in geometry and "+" in geometry:
            try:
                self.root.geometry(geometry)
            except Exception:
                pass

        self.note_var.set("Configuración cargada correctamente.")
        if show_message:
            messagebox.showinfo(
                "Configuración cargada",
                f"Se cargó la configuración desde:\n\n{self.config_path}",
                parent=self.root,
            )
        return True

    @staticmethod
    def _is_valid_binding(binding: object) -> bool:
        if not isinstance(binding, dict):
            return False
        return all(
            isinstance(binding.get(field), str) and binding.get(field)
            for field in ("kind", "code", "display")
        )

    def _open_data_folder(self) -> None:
        if self.data_folder is None:
            messagebox.showerror(
                "Sin carpeta de datos",
                "Todavía no hay una carpeta de datos configurada.",
                parent=self.root,
            )
            return

        try:
            if sys.platform.startswith("win"):
                import os

                os.startfile(str(self.data_folder))
            elif sys.platform == "darwin":
                import subprocess

                subprocess.Popen(["open", str(self.data_folder)])
            else:
                import subprocess

                subprocess.Popen(["xdg-open", str(self.data_folder)])
        except Exception as exc:
            messagebox.showerror(
                "No se pudo abrir la carpeta",
                f"No se pudo abrir la carpeta de datos.\n\n{exc}",
                parent=self.root,
            )

    def _create_profiles(self) -> None:
        for key, title in (("left", "Click izquierdo"), ("right", "Click derecho")):
            default_hold_name = MOUSE_DISPLAY.get(key, key)
            profile = ClickProfile(
                key=key,
                title=title,
                output_button=key,
                hold_button=key,
                mode_var=tk.StringVar(value="hotkey"),
                hotkey_text_var=tk.StringVar(value="Haz clic aquí para elegir hotkey"),
                hold_same_var=tk.BooleanVar(value=True),
                hold_button_var=tk.StringVar(value=default_hold_name),
                click_type_var=tk.StringVar(value="Simple"),
                interval_var=tk.StringVar(value="100"),
                status_var=tk.StringVar(value="Detenido | Sin hotkey"),
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
            text="OG Autoclicker",
            font=("Segoe UI", 16, "bold"),
        ).grid(row=0, column=0, sticky="w", padx=14, pady=(14, 6))

        ttk.Label(
            body,
            text=(
                "Ahora tienes dos configuraciones independientes: una para click izquierdo y otra para click derecho. "
                "Cada una tiene su propia hotkey, su propio modo Hold click, su propio intervalo y su propio estado."
            ),
            wraplength=500,
            justify="left",
        ).grid(row=1, column=0, sticky="ew", padx=14, pady=(0, 10))

        self._build_profile_section(body, row=2, profile=self.profiles["left"])
        self._build_profile_section(body, row=3, profile=self.profiles["right"])

        note_frame = ttk.LabelFrame(body, text="Notas generales", padding=12)
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
            text=(
                "• Cada panel funciona por separado.\n"
                "• En modo Hotkey: la hotkey activa o desactiva ese panel.\n"
                "• En modo Hold click: mantener presionado el botón dispara clicks; al soltar, se detiene.\n"
                "• En modo Hold click: la hotkey del panel funciona como seguro para habilitarlo o deshabilitarlo.\n"
                "• Si usas el mismo botón para Hold y para autoclick, el primer autoclick espera el intervalo configurado."
            ),
            wraplength=490,
            justify="left",
        ).grid(row=1, column=0, sticky="w", pady=(10, 0))

        storage_frame = ttk.LabelFrame(body, text="Guardar configuración", padding=12)
        storage_frame.grid(row=5, column=0, sticky="ew", padx=14, pady=(0, 8))
        storage_frame.columnconfigure(0, weight=1)
        storage_frame.columnconfigure(1, weight=1)

        ttk.Label(
            storage_frame,
            textvariable=self.data_folder_var,
            wraplength=490,
            justify="left",
        ).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 10))

        ttk.Button(storage_frame, text="Guardar ahora", command=self._save_config).grid(
            row=1, column=0, sticky="ew", padx=(0, 6), pady=3
        )
        ttk.Button(storage_frame, text="Cargar guardado", command=self._load_config).grid(
            row=1, column=1, sticky="ew", padx=(6, 0), pady=3
        )
        ttk.Button(storage_frame, text="Abrir carpeta", command=self._open_data_folder).grid(
            row=2, column=0, sticky="ew", padx=(0, 6), pady=3
        )
        ttk.Button(storage_frame, text="Cambiar carpeta", command=self._change_data_folder).grid(
            row=2, column=1, sticky="ew", padx=(6, 0), pady=3
        )

        ttk.Label(
            storage_frame,
            text=(
                "La app también guarda automáticamente al cerrar. Si vuelves a abrirla, "
                "intentará cargar la última configuración desde esta carpeta."
            ),
            wraplength=490,
            justify="left",
        ).grid(row=3, column=0, columnspan=2, sticky="w", pady=(8, 0))

        ttk.Label(
            body,
            text="Developed By Valentino Galli / KidOGzz",
            font=("Segoe UI", 9, "italic"),
            anchor="center",
            justify="center",
        ).grid(row=6, column=0, sticky="ew", padx=14, pady=(0, 16))

    def _build_profile_section(self, parent: ttk.Frame, row: int, profile: ClickProfile) -> None:
        section = ttk.LabelFrame(parent, text=profile.title, padding=12)
        section.grid(row=row, column=0, sticky="ew", padx=14, pady=6)
        section.columnconfigure(0, weight=1)

        ttk.Label(
            section,
            text=f"Este panel controla solamente el {profile.title.lower()}.",
            wraplength=490,
            justify="left",
        ).grid(row=0, column=0, sticky="w", pady=(0, 10))

        mode_frame = ttk.LabelFrame(section, text="Modo de activación", padding=10)
        mode_frame.grid(row=1, column=0, sticky="ew", pady=4)
        mode_frame.columnconfigure(0, weight=1)

        assert profile.mode_var is not None
        ttk.Radiobutton(
            mode_frame,
            text="Hotkey global (activa / desactiva)",
            variable=profile.mode_var,
            value="hotkey",
            command=lambda profile_key=profile.key: self._update_profile_widgets(profile_key),
        ).grid(row=0, column=0, sticky="w", pady=(0, 5))

        ttk.Radiobutton(
            mode_frame,
            text="Hold click (mientras mantengo presionado el click)",
            variable=profile.mode_var,
            value="hold",
            command=lambda profile_key=profile.key: self._update_profile_widgets(profile_key),
        ).grid(row=1, column=0, sticky="w")

        hotkey_frame = ttk.LabelFrame(section, text="Hotkey global", padding=10)
        hotkey_frame.grid(row=2, column=0, sticky="ew", pady=4)
        hotkey_frame.columnconfigure(0, weight=1)
        hotkey_frame.columnconfigure(1, weight=0)
        hotkey_frame.columnconfigure(2, weight=0)

        ttk.Label(
            hotkey_frame,
            text="Toca la casilla y luego presiona la tecla, botón del mouse o ruedita que quieres usar:",
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
            text="Capturar",
            command=lambda profile_key=profile.key: self.start_hotkey_capture(profile_key),
        )
        capture_button.grid(row=1, column=1, padx=(0, 8))

        clear_button = ttk.Button(
            hotkey_frame,
            text="Limpiar",
            command=lambda profile_key=profile.key: self.clear_hotkey(profile_key),
        )
        clear_button.grid(row=1, column=2)

        ttk.Label(
            hotkey_frame,
            text=(
                "Admite teclado, botones del mouse y ruedita arriba/abajo. "
                "Si el panel está en Hold click, esta hotkey funciona como seguro."
            ),
            wraplength=470,
            justify="left",
        ).grid(row=2, column=0, columnspan=3, sticky="w", pady=(8, 0))

        hold_frame = ttk.LabelFrame(section, text="Modo Hold click", padding=10)
        hold_frame.grid(row=3, column=0, sticky="ew", pady=4)
        hold_frame.columnconfigure(1, weight=1)

        hold_same_check = ttk.Checkbutton(
            hold_frame,
            text=f"Usar el mismo botón que se autoclickea ({profile.title.lower()})",
            variable=profile.hold_same_var,
            command=lambda profile_key=profile.key: self._update_profile_widgets(profile_key),
        )
        hold_same_check.grid(row=0, column=0, columnspan=2, sticky="w")

        ttk.Label(
            hold_frame,
            text="Si desactivas la casilla, puedes elegir otro botón para mantener apretado:",
            wraplength=470,
            justify="left",
        ).grid(row=1, column=0, columnspan=2, sticky="w", pady=(8, 6))

        ttk.Label(hold_frame, text="Botón a mantener presionado:").grid(
            row=2, column=0, sticky="w", padx=(0, 10)
        )

        hold_combo = ttk.Combobox(
            hold_frame,
            textvariable=profile.hold_button_var,
            state="readonly",
            values=list(MOUSE_OPTION_TO_NAME.keys()),
        )
        hold_combo.grid(row=2, column=1, sticky="ew")

        ttk.Label(
            hold_frame,
            text=(
                "Mientras mantienes el botón apretado, dispara clicks; cuando sueltas el dedo, se detiene. "
                "La hotkey de este panel puede desactivar el Hold si no quieres que arranque por accidente."
            ),
            wraplength=470,
            justify="left",
        ).grid(row=3, column=0, columnspan=2, sticky="w", pady=(8, 0))

        click_frame = ttk.LabelFrame(section, text="Click automático", padding=10)
        click_frame.grid(row=4, column=0, sticky="ew", pady=4)
        click_frame.columnconfigure(1, weight=1)

        ttk.Label(click_frame, text="Botón que se autoclickea:").grid(
            row=0, column=0, sticky="w", padx=(0, 10), pady=4
        )
        ttk.Label(click_frame, text=profile.title).grid(
            row=0, column=1, sticky="w", pady=4
        )

        ttk.Label(click_frame, text="Tipo de click:").grid(
            row=1, column=0, sticky="w", padx=(0, 10), pady=4
        )
        ttk.Combobox(
            click_frame,
            textvariable=profile.click_type_var,
            state="readonly",
            values=list(CLICK_TYPE_TO_COUNT.keys()),
        ).grid(row=1, column=1, sticky="ew", pady=4)

        ttk.Label(click_frame, text="Intervalo (ms):").grid(
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
            text="Ejemplo: 100 ms = 10 clicks por segundo aprox.",
            wraplength=470,
            justify="left",
        ).grid(row=3, column=0, columnspan=2, sticky="w", pady=(8, 0))

        control_frame = ttk.LabelFrame(section, text="Control", padding=10)
        control_frame.grid(row=5, column=0, sticky="ew", pady=4)
        control_frame.columnconfigure(0, weight=1)
        control_frame.columnconfigure(1, weight=1)

        ttk.Button(
            control_frame,
            text="Detener ahora",
            command=lambda profile_key=profile.key: self.force_stop(profile_key),
        ).grid(row=0, column=0, sticky="ew", padx=(0, 6))

        ttk.Button(
            control_frame,
            text="Click de prueba",
            command=lambda profile_key=profile.key: self.test_click(profile_key),
        ).grid(row=0, column=1, sticky="ew", padx=(6, 0))

        status_frame = ttk.LabelFrame(section, text="Estado", padding=10)
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
                else MOUSE_OPTION_TO_NAME.get(profile.hold_button_var.get(), profile.output_button)
            )
            profile.click_count = CLICK_TYPE_TO_COUNT.get(profile.click_type_var.get(), 1)

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

        profile.hotkey_text_var.set("Presione la tecla que desea usar para activar...")
        self.note_var.set(
            f"Esperando hotkey para {profile.title.lower()}: tecla, botón del mouse o ruedita."
        )
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

        profile.hotkey_text_var.set("Haz clic aquí para elegir hotkey")
        self.note_var.set(f"Hotkey borrada para {profile.title.lower()}.")

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
                self.note_var.set(
                    f"{profile.title} detenido manualmente. El Hold quedó deshabilitado hasta volver a activarlo con su hotkey."
                )
            else:
                self.note_var.set(
                    f"{profile.title} detenido manualmente. Como ese panel no tiene hotkey, el Hold sigue disponible cuando vuelvas a mantener presionado."
                )
        else:
            self.note_var.set(f"{profile.title} detenido manualmente.")

    def test_click(self, profile_key: str) -> None:
        profile = self.profiles[profile_key]
        delay_seconds = 0.35
        self.note_var.set(
            f"{profile.title}: click de prueba en {delay_seconds:.2f} segundos para que puedas mover el cursor."
        )
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
                lambda: self.note_var.set(f"Click de prueba realizado para {profile.title.lower()}."),
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
            base = "Esperando hotkey..."
        elif mode == "hotkey":
            base = "Activo" if active else "Detenido"
        else:
            if not hold_gate_enabled:
                base = "Hold deshabilitado"
            elif hold_is_pressed:
                base = "Activo (mantener presionado)"
            else:
                base = "Esperando que mantengas presionado"

        if hotkey_binding:
            return f"{base} | Hotkey: {hotkey_binding['display']}"
        return f"{base} | Sin hotkey"

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

    def _is_mouse_button_physically_pressed(self, button_name: str) -> bool:
        with self.lock:
            if button_name in self.pressed_mouse_buttons:
                return True

        if _USER32 is not None:
            vk_code = _VK_BY_MOUSE_NAME.get(button_name)
            if vk_code is not None:
                return bool(_USER32.GetAsyncKeyState(vk_code) & 0x8000)

        return False

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

    def _on_mouse_click(
        self,
        _x: int,
        _y: int,
        button: mouse.Button,
        pressed: bool,
    ) -> None:
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

    def _on_mouse_scroll(
        self,
        _x: int,
        _y: int,
        _dx: int,
        dy: int,
    ) -> None:
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
        profile.hotkey_text_var.set(binding["display"])
        self.note_var.set(f"Hotkey capturada para {profile.title.lower()}: {binding['display']}")

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
                    messages.append(
                        f"{profile.title}: {'activado' if profile.active else 'desactivado'}"
                    )
                else:
                    profile.hold_gate_enabled = not profile.hold_gate_enabled
                    if not profile.hold_gate_enabled:
                        profile.next_due_at = 0.0
                        profile.hold_engaged = False
                    messages.append(
                        f"{profile.title}: hold {'habilitado' if profile.hold_gate_enabled else 'deshabilitado'}"
                    )

            if not messages:
                return

            if use_debounce:
                self.debounced_triggers.add(binding_id)

        if self.running:
            joined = " | ".join(messages)
            self.root.after(
                0,
                lambda: self.note_var.set(f"{joined} por {binding['display']}"),
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

    @staticmethod
    def _binding_from_mouse_button(button: mouse.Button) -> dict[str, str] | None:
        name = getattr(button, "name", None)
        if not name:
            raw = str(button)
            name = raw.replace("Button.", "")

        if not name:
            return None

        return {
            "kind": "mouse",
            "code": f"button:{name}",
            "display": MOUSE_DISPLAY.get(name, f"Mouse {name}"),
        }

    @staticmethod
    def _binding_from_wheel(direction: str) -> dict[str, str]:
        return {
            "kind": "wheel",
            "code": direction,
            "display": "Ruedita arriba" if direction == "up" else "Ruedita abajo",
        }

    @staticmethod
    def _binding_from_key(key: keyboard.Key | keyboard.KeyCode) -> dict[str, str] | None:
        char = getattr(key, "char", None)
        if char:
            if char == "\r":
                char = "enter"
            elif char == "\t":
                char = "tab"
            elif char == " ":
                char = "space"

            display = KEY_DISPLAY.get(char, char.upper() if len(char) == 1 else char.upper())
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

        display = KEY_DISPLAY.get(name, name.replace("_", " ").upper())
        return {
            "kind": "keyboard",
            "code": f"key:{name}",
            "display": display,
        }

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
