"""long

Revision ID: 9ef6cf4e4c55
Revises: 46443cd86541
Create Date: 2019-10-14 15:09:38.273087

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9ef6cf4e4c55'
down_revision = '46443cd86541'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('airline_stock', sa.Column('id', sa.Integer(), nullable=False))
    op.create_unique_constraint(None, 'airline_stock', ['id'])
    op.create_foreign_key(None, 'flight', 'airline_stock', ['airplane_model'], ['model'])
    op.create_foreign_key(None, 'flight', 'airline_stock', ['airplane_id'], ['unique_id'])
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'flight', type_='foreignkey')
    op.drop_constraint(None, 'flight', type_='foreignkey')
    op.drop_constraint(None, 'airline_stock', type_='unique')
    op.drop_column('airline_stock', 'id')
    # ### end Alembic commands ###
