"""empty message

Revision ID: 218ca7a2c9a2
Revises: 047b98a45156
Create Date: 2019-04-12 15:21:22.906603

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '218ca7a2c9a2'
down_revision = '047b98a45156'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('budget',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('cur_amount', sa.String(length=16), nullable=True),
    sa.Column('max_amount', sa.String(length=16), nullable=True),
    sa.Column('category', sa.String(length=32), nullable=True),
    sa.Column('timestamp', sa.DateTime(), nullable=True),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('category')
    )
    op.create_index(op.f('ix_budget_timestamp'), 'budget', ['timestamp'], unique=False)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_budget_timestamp'), table_name='budget')
    op.drop_table('budget')
    # ### end Alembic commands ###
