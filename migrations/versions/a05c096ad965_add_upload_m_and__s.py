"""add upload_m and _s

Revision ID: a05c096ad965
Revises: ebb761e1f9f5
Create Date: 2021-06-13 10:28:41.189347

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a05c096ad965'
down_revision = 'ebb761e1f9f5'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('photo',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('description', sa.String(length=500), nullable=True),
    sa.Column('filename', sa.String(length=64), nullable=True),
    sa.Column('filename_s', sa.String(length=64), nullable=True),
    sa.Column('filename_m', sa.String(length=64), nullable=True),
    sa.Column('timestamp', sa.DateTime(), nullable=True),
    sa.Column('author_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['author_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('photo')
    # ### end Alembic commands ###