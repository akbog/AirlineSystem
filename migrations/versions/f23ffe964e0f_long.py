"""long

Revision ID: f23ffe964e0f
Revises: da98dbbe93ec
Create Date: 2019-10-14 14:44:54.210714

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f23ffe964e0f'
down_revision = 'da98dbbe93ec'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('flight', sa.Column('airplane_id', sa.String(length=64), nullable=True))
    op.add_column('flight', sa.Column('airplane_model', sa.String(length=64), nullable=True))
    op.create_foreign_key(None, 'flight', 'airline_stock', ['airplane_id'], ['unique_id'])
    op.create_foreign_key(None, 'flight', 'airline_stock', ['airplane_model'], ['model'])
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'flight', type_='foreignkey')
    op.drop_constraint(None, 'flight', type_='foreignkey')
    op.drop_column('flight', 'airplane_model')
    op.drop_column('flight', 'airplane_id')
    # ### end Alembic commands ###
