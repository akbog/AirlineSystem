"""long lat

Revision ID: b72de3508458
Revises: 0f6a991b4ac5
Create Date: 2019-10-13 11:41:13.319666

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b72de3508458'
down_revision = '0f6a991b4ac5'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('airport', sa.Column('latitude', sa.Float(), nullable=True))
    op.add_column('airport', sa.Column('longitude', sa.Float(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('airport', 'longitude')
    op.drop_column('airport', 'latitude')
    # ### end Alembic commands ###
