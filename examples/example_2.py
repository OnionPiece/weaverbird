# revision identifiers, used by Alembic.
revision = 'whatever-rev'
down_revision = 'whatever-down-rev'

from alembic import op
import sqlalchemy as sa

import uuid

from yourmodel import somemodel


standardattrs = sa.Table(
    'standardattributes', sa.MetaData(),
    sa.Column('id', sa.BigInteger(), primary_key=True, autoincrement=True),
    sa.Column('resource_type', sa.String(length=255), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False))


def get_values():
    session = sa.orm.Session(bind=op.get_bind())
    values = []

    with session.begin(subtransactions=True):
        for row in session.query(somemodel.YourOrmClaas).all():
            created_at = rec.standard_attr.created_at
            updated_at = rec.standard_attr.updated_at
            std_attr = session.execute(
                # NOTE **{} is a little trick to pass pylink test
                # it doesn't impact migraion job. Ref:
                # - https://github.com/PyCQA/pylint/issues/722
                # - https://segmentfault.com/q/1010000002486818
                standardattrs.insert(**{}).values(
                    resource_type='Custom_resource',
                    created_at=created_at,
                    updated_at=updated_at))
            values.append({
                'id': uuid.uuid4(),
                'tenant_id': rec.tenant_id,
                'name': rec.name,
                'description': rec.description,
                'usage': 0,
                'quota': 0,
                'standard_attr_id': std_attr.inserted_primary_key[0]})

    # this commit is necessary to allow further operations
    session.commit()
    return values


def get_init_values():
    return [
        {'id': uuid.uuid4(),
         'tenant_id': '0',
         'name': name,
         'description': name,
         'usage': 0,
         'quota': 100,
         # consume standard_attr_id 0 has been inserted
         'standard_attr_id': 0}
        for name in ('admin', 'game_master1', 'game_master2')
    ]


def upgrade():
    new_table = op.create_table(
        'some_new_table',
        sa.Column('id', sa.String(36), nullable=False, primary_key=True),
        sa.Column('tenant_id', sa.String(length=255), nullable=False,
                  index=True),
        sa.Column('name', sa.String(64), nullable=False),
        sa.Column('description', sa.String(length=36), nullable=False),
        sa.Column('standard_attr_id', sa.BigInteger(),
                  sa.ForeignKey('standardattributes.id', ondelete='CASCADE'),
                  nullable=False),
        sa.Column('usage', sa.BigInteger(), nullable=False,
                  server_default='0'),
        sa.Column('quota', sa.BigInteger(), nullable=False,
                  server_default='0'),
        sa.Column('deleted_at', sa.DateTime()),
    )
    op.bulk_insert(new_table, get_init_values())
    op.bulk_insert(new_table, get_values())
