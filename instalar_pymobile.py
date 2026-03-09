from pathlib import Path
import shutil
import subprocess
import sys


BASE_DIR = Path(__file__).resolve().parent
APP_DIR = Path("/storage/emulated/0/CorrecaoQRApp")

ARQUIVOS_OBRIGATORIOS = [
    "app_mobile_kivy.py",
    "correcao_qrcode_simples.py",
    "main.py",
]

ARQUIVOS_OPCIONAIS = [
    "prova_config.json",
    "logoiema.png",
]

PACOTES = [
    "numpy",
    "opencv-python",
    "qrcode",
    "pillow",
    "reportlab",
    "kivy",
]


def run(cmd: list[str]) -> None:
    print(">", " ".join(cmd))
    subprocess.check_call(cmd)


def instalar_dependencias() -> None:
    run([sys.executable, "-m", "pip", "install", "--upgrade", "pip", "setuptools", "wheel"])
    for pacote in PACOTES:
        run([sys.executable, "-m", "pip", "install", pacote])


def copiar_arquivos() -> None:
    APP_DIR.mkdir(parents=True, exist_ok=True)
    (APP_DIR / "resultado").mkdir(parents=True, exist_ok=True)

    for nome in ARQUIVOS_OBRIGATORIOS:
        origem = BASE_DIR / nome
        if not origem.exists():
            raise FileNotFoundError(f"Arquivo obrigatorio ausente: {origem}")
        shutil.copy2(origem, APP_DIR / nome)

    for nome in ARQUIVOS_OPCIONAIS:
        origem = BASE_DIR / nome
        if origem.exists():
            shutil.copy2(origem, APP_DIR / nome)

    launcher = APP_DIR / "rodar_app.py"
    launcher.write_text(
        "from app_mobile_kivy import MobileApp\n\n"
        "if __name__ == '__main__':\n"
        "    MobileApp().run()\n",
        encoding="utf-8",
    )


def main() -> None:
    print("Instalador Py Mobile (Pydroid 3)")
    instalar_dependencias()
    copiar_arquivos()
    print("\nInstalacao concluida.")
    print(f"Pasta do app: {APP_DIR}")
    print("No Pydroid 3, execute:")
    print(f"  {APP_DIR / 'rodar_app.py'}")


if __name__ == "__main__":
    main()
