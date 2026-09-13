"""Punto de entrada: python -m taitai"""

import warnings

# Este Mac corre Python 3.9 (el del sistema) y las librerías de Google avisan en
# cada ejecución que ya no le dan soporte. Es cierto y está anotado en el README,
# pero no aporta nada verlo cada vez. Se silencia solo aquí, en el ejecutable:
# si algún día se importa taitai como librería, las advertencias siguen visibles.
warnings.filterwarnings("ignore", category=FutureWarning, module=r"google\.")
warnings.filterwarnings("ignore", message=r".*OpenSSL 1\.1\.1\+.*")

from .cli import main  # noqa: E402

raise SystemExit(main())
