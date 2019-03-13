#!/usr/bin/env python2.7

from models import utils as modutils
import utils


from sqlalchemy.ext.automap import automap_base
from sqlalchemy import exc
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.dialects.mysql import types


confs = utils.load_config()
rows_slice_len = confs['rows_slice_len']

from_url = "mysql://%(user)s:%(password)s@%(host)s:%(port)s/%(database)s" % (
    confs["from"])
to_url = "mysql://%(user)s:%(password)s@%(host)s:%(port)s/%(database)s" % (
    confs["to"])
all_models = modutils.get_ordered_tables()

from_engine = create_engine(from_url)
from_session = Session(from_engine)

to_engine = create_engine(to_url)
to_session = Session(to_engine)

for mod_name in all_models:
    print "Output data for table", mod_name
    mod = __import__("models.%s" % mod_name, fromlist=[mod_name])
    orm_cls = getattr(mod, mod_name[0].upper() + mod_name[1:])
    attrs = [attr for attr in dir(orm_cls) if not attr.startswith('_')]
    rows = [
        orm_cls(**{
            attr: getattr(row, attr)
            for attr in attrs
        })
        for row in from_session.query(orm_cls).all()]
    try:
        to_session.add_all(rows)
        to_session.commit()
    except exc.OperationalError as e:
        if e.connection_invalidated:
            to_session.rollback()
            to_session = Session(to_engine)
            try:
                for i in range(len(rows)/rows_slice_len + 1):
                    to_session.add_all(
                        rows[i*rows_slice_len:(i+1)*rows_slice_len])
                    to_session.commit()
            except Exception as e:
                print "Try to decrease rows_slice_len to mitigate this problem"
                raise
    except Exception:
        to_session.rollback()
        raise
