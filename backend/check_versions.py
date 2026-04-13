import importlib
import packaging.version
import sys

mods = ['cycler', 'dateutil', 'kiwisolver', 'numpy', 'pyparsing', 'matplotlib', 'matplotlib_inline', 'pandas', 'pandasai', 'packaging']

print("Checking versions...")
for m in mods:
    try:
        mod = importlib.import_module(m)
        version = getattr(mod, '__version__', 'unknown')
        print(f"{m}: {version}")
        try:
            packaging.version.parse(version)
            print(f"  - Version string '{version}' is valid for packaging")
        except Exception as e:
            print(f"  - !!! Version string '{version}' is INVALID: {e}")
    except ImportError:
        print(f"{m}: Not Found")
    except Exception as e:
        print(f"{m}: Error importing or checking: {e}")
