#!/usr/bin/env python2.7

from models import utils as modutils
import utils

import os


os.system('rm -rf alembic*')
os.system('alembic init alembic')
utils.refresh_alembic_ini()
os.system('alembic revision -m "init"')
utils.refresh_alembic_versions_init()
for f in os.listdir('./models'):
    if f not in ('__init__.py', 'utils.py', 'model.j2'):
        os.remove('./models/%s' % f)
utils.export_tables()
utils.ensure_target_database()
os.system('alembic upgrade head')
