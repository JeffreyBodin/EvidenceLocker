"""empty message

Revision ID: 4cc92e5c46a2
Revises: 286444147b98
Create Date: 2022-04-20 14:45:28.940798

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '4cc92e5c46a2'
down_revision = '286444147b98'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('agencies', sa.Column('site', sa.String(length=128), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('agencies', 'site')
    # ### end Alembic commands ###
