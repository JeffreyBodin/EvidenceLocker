"""empty message

Revision ID: 11e9230e61c9
Revises: 4c25fbc99415
Create Date: 2022-09-08 14:03:12.919597

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '11e9230e61c9'
down_revision = '4c25fbc99415'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('victim_users', sa.Column('_rsa_e', sa.Integer(), nullable=True))
    op.add_column('victim_users', sa.Column('_rsa_d', sa.Integer(), nullable=True))
    op.add_column('victim_users', sa.Column('_rsa_n', sa.Integer(), nullable=True))
    op.add_column('victim_users', sa.Column('_rsa_p', sa.Integer(), nullable=True))
    op.add_column('victim_users', sa.Column('_rsa_q', sa.Integer(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('victim_users', '_rsa_q')
    op.drop_column('victim_users', '_rsa_p')
    op.drop_column('victim_users', '_rsa_n')
    op.drop_column('victim_users', '_rsa_d')
    op.drop_column('victim_users', '_rsa_e')
    # ### end Alembic commands ###
