"""empty message

Revision ID: 357eac7c3fff
Revises: 
Create Date: 2022-02-21 15:28:40.741866

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '357eac7c3fff'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('police_users',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=256), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('victim_users',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('created_utc', sa.Integer(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('victim_users')
    op.drop_table('police_users')
    # ### end Alembic commands ###