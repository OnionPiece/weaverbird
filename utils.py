import models

import jinja2
import json
import os
from sqlalchemy.sql import sqltypes as types
from sqlalchemy.schema import MetaData
from sqlalchemy import create_engine
from sqlalchemy import exc


TEMPLATE = None


def load_config():
    ret = {}
    conf = './conf.json'
    if not os.path.exists(conf):
        print 'The config file conf.json not exists.'
        os.sys.exit(1)

    try:
        with open(conf) as f:
            ret = json.load(f)
    except Exception:
        print 'Failed to load conf.json, try to check its schema'
        os.sys.exit(1)

    for i in ('from', 'to'):
        if i not in ret:
            print 'Section "%s" not in conf.json, please define it' % i
            os.sys.exit(1)
        for j in ('user', 'password', 'host', 'port'):
            if j not in ret[i]:
                print ('Key "%s" not in "%s" section in conf.json, '
                       'please define it' % (j, i))
                os.sys.exit(1)
    if "database" not in ret["from"] or "database" in ret["to"]:
        print ('Key "database" should exists in "from" section, but not '
               '"to" section.')
        os.sys.exit(1)

    ret['to']['database'] = ret['from']['database']
    return ret


def convert_default_arg(arg):
    if arg.lower() == 'ture':
        return 'sa.sql.true()'
    elif arg.lower() == 'false':
        return 'sa.sql.false()'
    elif 'CURRENT_TIMESTAMP' in arg:
        return "sa.text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP')"
    return arg


def get_extensions(column, coltype):
    ret = {}
    # won't consider 'auto' as True
    ret['auto_increment'] = True if column.autoincrement is True else False

    if hasattr(coltype, "length"):
        ret['length'] = coltype.length
    elif hasattr(coltype, "display_width"):
        ret['display_width'] = coltype.display_width
    elif hasattr(coltype, "precision"):
        ret['precision'] = coltype.precision
        ret['scale'] = coltype.scale

    if column.server_default and column.server_default.has_argument:
        if isinstance(coltype, types.TIMESTAMP):
            ret['default_arg'] = column.server_default.arg
        else:
            ret['default_arg'] = column.server_default.arg.text
        ret['default_arg'] = convert_default_arg(str(ret['default_arg']))

    if column.foreign_keys:
        fk = iter(column.foreign_keys).next()
        ret['foreign_key_ondelete'] = fk.ondelete
        ret['foreign_key_onupdate'] = fk.onupdate
        ret['foreign_key'] = fk.target_fullname

    # consider column.comment and column.constraints
    return ret


def convert_type(coltype):
    if coltype == "VARCHAR":
        return "sa.String"
    elif coltype == "DATETIME":
        return "sa.DateTime"
    elif coltype in ("INTEGER", "LONGTEXT", "TINYINT", "BIGINT", "MEDIUMTEXT"):
        return "mysql." + coltype
    return "sa." + coltype


def try_parse_table(table):
    ret = []
    for column_name, column in table.columns.items():
        coltype = column.type
        coltype_name = column.type.__visit_name__
        nullable = column.nullable
        is_pri_key = column.primary_key
        default = column.default
        ext = get_extensions(column, coltype)

        info = {
            'name': column_name,
            'type': convert_type(coltype_name),
            'nullable': nullable,
            'is_primary_key': is_pri_key,
            'default': default
        }
        info.update(ext)
        ret.append(info)
    return ret


class ModelTemplate(object):
    def __init__(self):
        template_loader = jinja2.FileSystemLoader(
            searchpath=models.templates_path)
        self._template_env = jinja2.Environment(
            loader=template_loader, trim_blocks=True, lstrip_blocks=True)

    @property
    def _model_template(self):
        return self._template_env.get_template(
            models.model_template_name)

    def get_model_content(self, table):
        return self._model_template.render({"table": table})


def write_parsed_table_to_file(table):
    global TEMPLATE
    if not TEMPLATE:
        TEMPLATE = ModelTemplate()
    model_content = TEMPLATE.get_model_content(table)
    with open('./models/%s.py' % table['name'], 'w+') as f:
        f.write(model_content)


def refresh_alembic_ini():
    confs = load_config()["to"]
    src = './alembic.ini'
    dst = './alembic.ini.new'
    lines = open(src).read().strip().split('\n')
    new_lines = []
    for line in lines:
        if line.startswith('script_location'):
            new_lines.append('#script_location = alembic')
            new_lines.append('script_location = %(here)s/alembic')
        elif line.startswith('sqlalchemy.url'):
            new_lines.append(
                '#sqlalchemy.url = driver://user:pass@localhost/dbname')
            new_lines.append(
                'sqlalchemy.url = mysql://%(user)s:%(password)s@%(host)s'
                '/%(database)s' % confs)
        else:
            new_lines.append(line)
    with open(dst, 'w+') as f:
        f.write('\n'.join(new_lines))
        f.write('\n')
    os.rename(dst, src)


def refresh_alembic_versions_init():
    init = [f for f in os.listdir('./alembic/versions') if f.endswith('py')][0]
    src = './alembic/versions/%s' % init
    dst = src + '.new'
    lines = open(src).read().strip().split('\n')
    new_lines = []
    replace_here = False
    for line in lines:
        if replace_here:
            new_lines.append('    import os')
            new_lines.append(
                '    os.sys.path.append(__file__.rsplit(os.sep, 3)[0])')
            new_lines.append('    from models import utils')
            new_lines.append('    utils.create_tables()')
            replace_here = False
        else:
            new_lines.append(line)
        if line.startswith('def upgrade'):
            replace_here = True
    with open(dst, 'w+') as f:
        f.write('\n'.join(new_lines))
        f.write('\n')
    os.rename(dst, src)
    os.remove(src + 'c')


def export_tables():
    confs = load_config()['from']
    url = "mysql://%(user)s:%(password)s@%(host)s:%(port)s/%(database)s" % (
        confs)

    engine = create_engine(url)
    metadata = MetaData(engine)
    metadata.reflect(engine)
    for table in metadata.sorted_tables:
        if table.key in ('alembic_version'):
            continue
        columns = try_parse_table(table)
        write_parsed_table_to_file({'name': table.key, 'columns': columns})


def ensure_target_database():
    confs = load_config()['to']
    url = "mysql://%(user)s:%(password)s@%(host)s:%(port)s" % confs
    engine = create_engine(url)
    engine.execute('create database if not exists %(database)s' % confs)
