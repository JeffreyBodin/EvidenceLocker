"""empty message

Revision ID: f15ac7b9dfff
Revises: d5f354153c42
Create Date: 2022-09-12 15:12:22.353608

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f15ac7b9dfff'
down_revision = 'd5f354153c42'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('entries', 'signing_sha256')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('entries', sa.Column('signing_sha256', sa.VARCHAR(length=512), autoincrement=False, nullable=True))
    # ### end Alembic commands ###