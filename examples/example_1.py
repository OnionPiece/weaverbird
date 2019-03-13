# revision identifiers, used by Alembic.
revision = 'whatever_rev'
down_revision = 'whatever_down_rev'

from alembic import op
import six
import sqlalchemy as sa

import uuid

from yourmodel import label
from yourmodel import related_model
from yourmigration import labels_and_rules_migration


tenant_labels = sa.Table(
    'tenantlabels', sa.MetaData(),
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('tenant_id', sa.String(length=255), nullable=True,
              index=True),
    sa.Column('name', sa.String(length=255), nullable=True),
    sa.Column('description', sa.String(length=1024), nullable=True),
    sa.Column('shared', sa.Boolean(), server_default=sa.sql.false(),
              nullable=True))


label_rules = sa.Table(
    'labelrules', sa.MetaData(),
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('direction', sa.Enum('ingress', 'egress'), nullable=True),
    sa.Column('action', sa.String(length=64), nullable=True),
    sa.Column('label_id', sa.String(length=36), nullable=False),
    sa.Column('excluded', sa.Boolean(), nullable=True),
    sa.Column('reverse', sa.Boolean(), nullable=True))


def get_prev_records():
    session = sa.orm.Session(bind=op.get_bind())
    labels = []
    rules = []
    with session.begin(subtransactions=True):
        for label in session.query(label.LabelOrmClass).all():
            rules.extend([{
                'id': rule.id,
                'direction': rule.direction,
                'action': rule.action,
                'label_id': rule.label_id,
                'excluded': rule.excluded,
                'reverse': rule.reverse} for rule in label.rules])
            labels.append({
                'id': label.id,
                'tenant_id': label.tenant_id,
                'name': label.name,
                'description': label.description,
                'shared': label.shared})
    # this commit appears to be necessary to allow further operations
    session.commit()
    return labels, rules


def gen_new_records():
    session = sa.orm.Session(bind=op.get_bind())
    labels = []
    rules = []
    with session.begin(subtransactions=True):
        for related_row in session.query(related_model.RelatedOrmClass).all()
            direction = {
                'ingress': str(uuid.uuid4()),
                'egress': str(uuid.uuid4())}
            labels.extend([{
                'id': i,
                'tenant_id': related_row.tenant_id,
                'name': '%s-%s' % (related_row.id, d),
                'description': 'Auto-inserted record by data migration',
                'shared': False}
                for (d, i) in six.iteritems(direction)])
            for child in related_row.children:
                rules.extend([{
                    'id': str(uuid.uuid4()),
                    'direction': d,
                    'action': 'default',
                    'label_id': i,
                    'excluded': True,
                    'reverse': True} for (d, i) in six.iteritems(direction)])

    # this commit appears to be necessary to allow further operations
    session.commit()
    return labels, rules


def upgrade():
    labels, rules = get_prev_records()

    op.drop_table('labelrules')
    op.drop_table('tenantlabels')
    labels_and_rules_migration.upgrade()
    op.add_column(
        'labelrules',
        sa.Column('reverse', sa.Boolean(), nullable=True,
                  server_default=sa.sql.false()))
    op.add_column(
        'tenantlabels',
        sa.Column('shared', sa.Boolean(), server_default=sa.sql.false(),
                  nullable=True))

    op.bulk_insert(tenant_labels, labels)
    op.bulk_insert(label_rules, rules)

    labels, rules = gen_new_records()
    op.bulk_insert(tenant_labels, labels)
    op.bulk_insert(label_rules, rules)
