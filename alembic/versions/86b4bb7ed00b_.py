"""empty message

Revision ID: 86b4bb7ed00b
Revises: a656d79f64b3
Create Date: 2022-02-23 09:44:54.095240

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '86b4bb7ed00b'
down_revision = 'a656d79f64b3'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('police_users', sa.Column('agency_id', sa.Integer(), nullable=True))
    op.create_foreign_key(None, 'police_users', 'agencies', ['agency_id'], ['id'])
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'police_users', type_='foreignkey')
    op.drop_column('police_users', 'agency_id')
    # ### end Alembic commands ###