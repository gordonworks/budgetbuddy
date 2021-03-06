"""empty message

Revision ID: b751db36d9a5
Revises: 218ca7a2c9a2
Create Date: 2019-05-01 10:16:31.127373

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b751db36d9a5'
down_revision = '218ca7a2c9a2'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('arc__transaction',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('note', sa.String(length=16), nullable=True),
    sa.Column('amount', sa.String(length=16), nullable=True),
    sa.Column('category', sa.String(length=32), nullable=True),
    sa.Column('timestamp', sa.DateTime(), nullable=True),
    sa.Column('recurring', sa.Boolean(), nullable=True),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_arc__transaction_timestamp'), 'arc__transaction', ['timestamp'], unique=False)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_arc__transaction_timestamp'), table_name='arc__transaction')
    op.drop_table('arc__transaction')
    # ### end Alembic commands ###
