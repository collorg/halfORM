import sys
from os import listdir, path
 
import half_orm
from half_orm.model import CONF_DIR, Model

def check_peer_authentication():
    try:
        template1 = Model('template1')
        print("✅ Connected to template1 database (default setup)")
    except Exception as exc:
        print(f'⚠️  Unable to connect to template1 with peer authentication.')

def check_databases_access():
    print(f"\n== Checking connections for files in HALFORM_CONF_DIR={CONF_DIR}")
    try:
        files = [file for file in listdir(CONF_DIR) if path.isfile(path.join(CONF_DIR, file))]
        if files:
            for cnx_file in files:
                try:
                    model = Model(cnx_file)
                    print(f"✅ {cnx_file}")
                except Exception as exc:
                    sys.stderr.write(f'❌ {cnx_file}: {exc}')
        else:
            print("💡 No database configuration files found.")
            print(f"   To add database connections:")
            print(f"   • Create config files in: {CONF_DIR}")
            print(f"   • Or set different config directory: export HALFORM_CONF_DIR=/path/to/configs")
    except FileNotFoundError:
        sys.stderr.write(f"❌ '{CONF_DIR}' does not exists.\nChange HALFORM_CONF_DIR variable\n")
    sys.stderr.flush()
    print(f"\nCheck the documentation on https://collorg.github.io/halfORM")

if __name__ == '__main__':
  print(f"[halfORM] version {half_orm.__version__}")
  check_peer_authentication()
  check_databases_access()
