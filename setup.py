import os
import sys
import subprocess
from pathlib import Path

# Requirements specific to your Flask EduPortal app
REQUIRED_PACKAGES = [
    "Flask",
    "Flask-SQLAlchemy",
    "Flask-Login",
    "Werkzeug",
    "python-dotenv"
]

def in_venv():
    """Verify if the script is running inside a virtual environment."""
    return sys.prefix != sys.base_prefix

def run_cmd(cmd):
    """Run a shell command."""
    subprocess.check_call(cmd, shell=True)

def setup_and_run():
    print("🚀 Iniciando EduPortal Setup...")
    
    venv_dir = Path("venv")
    
    # 1. Check if virtual environment exists, create if it doesn't
    if not venv_dir.exists():
        print("📦 Criando Virtual Environment (venv)...")
        run_cmd(f'"{sys.executable}" -m venv venv')
    else:
        print("✅ Virtual Environment (venv) encontrado.")

    # 2. Determine the path to the python executable inside the venv
    if os.name == 'nt':
        venv_python = venv_dir / "Scripts" / "python.exe"
        venv_pip = venv_dir / "Scripts" / "pip.exe"
    else:
        venv_python = venv_dir / "bin" / "python"
        venv_pip = venv_dir / "bin" / "pip"

    if not venv_python.exists():
        print(f"❌ Erro crítico: O executável do Python não foi encontrado no venv ({venv_python}).")
        print("Por favor, delete a pasta 'venv' e tente rodar novamente.")
        sys.exit(1)

    # 3. Check and install dependencies inside the venv
    print("🔍 Verificando dependências...")
    
    try:
        # Get list of installed packages
        output = subprocess.check_output([str(venv_pip), "list", "--format=freeze"], text=True)
        installed_packages = [line.split('==')[0].lower() for line in output.split()]
        
        packages_to_install = []
        for pkg in REQUIRED_PACKAGES:
            if pkg.lower() not in installed_packages:
                packages_to_install.append(pkg)
                
        if packages_to_install:
            print(f"📥 Instalando os seguintes pacotes faltantes: {', '.join(packages_to_install)}")
            # Install missing packages inside the virtual environment
            run_cmd(f'"{venv_pip}" install ' + " ".join(packages_to_install))
            print("✅ Dependências instaladas com sucesso.")
        else:
            print("✅ Todas as dependências já estão instaladas.")
            
    except subprocess.CalledProcessError as e:
        print(f"❌ Erro ao verificar ou instalar pacotes: {e}")
        sys.exit(1)

    # 4. Activate the virtual environment context and run app.py
    # Since we cannot completely change the current active shell process (like a batch script would), 
    # we just execute our `app.py` script specifically utilizing the python executable
    # that resides inside the virtual environment. This behaves equivalently to activating it and running it.
    print("🌐 Iniciando servidor Flask (app.py) usando o ambiente virtual...")
    print("-" * 50)
    
    try:
        # Execute app.py inside the venv python interpreter
        subprocess.check_call([str(venv_python), "app.py"])
    except KeyboardInterrupt:
        print("\n👋 Servidor desligado. Tchau!")
    except Exception as e:
        print(f"\n❌ Erro ao rodar a aplicação: {e}")

if __name__ == "__main__":
    setup_and_run()
