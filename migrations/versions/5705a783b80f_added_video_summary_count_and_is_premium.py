"""added video_summary_count and is_premium

Revision ID: 5705a783b80f
Revises: 338a164d6b02
Create Date: 2023-10-23 09:55:11.499942

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '5705a783b80f'
down_revision = '338a164d6b02'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.add_column(sa.Column('video_summary_count', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('is_premium', sa.Boolean(), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.drop_column('is_premium')
        batch_op.drop_column('video_summary_count')

    # ### end Alembic commands ###