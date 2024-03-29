"""new airplane

Revision ID: 0f6a991b4ac5
Revises: f73992bf0ba6
Create Date: 2019-10-12 19:38:50.902555

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '0f6a991b4ac5'
down_revision = 'f73992bf0ba6'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('airline_stock', sa.Column('airline_name', sa.String(length=64), nullable=False))
    op.drop_constraint('airline_stock_ibfk_2', 'airline_stock', type_='foreignkey')
    op.create_foreign_key(None, 'airline_stock', 'airline', ['airline_name'], ['name'])
    op.drop_column('airline_stock', 'name')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('airline_stock', sa.Column('name', mysql.VARCHAR(length=64), nullable=False))
    op.drop_constraint(None, 'airline_stock', type_='foreignkey')
    op.create_foreign_key('airline_stock_ibfk_2', 'airline_stock', 'airline', ['name'], ['name'])
    op.drop_column('airline_stock', 'airline_name')
    # ### end Alembic commands ###
