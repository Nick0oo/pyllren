"""unified_user_model_and_pharmacy_tables

Revision ID: d07c67f7f25f
Revises: dcb63cdbec33
Create Date: 2025-10-25 19:43:53.485762

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel.sql.sqltypes


# revision identifiers, used by Alembic.
revision = 'd07c67f7f25f'
down_revision = 'dcb63cdbec33'
branch_labels = None
depends_on = None


def upgrade():
    # 1. Agregar campos farmacéuticos a la tabla user
    op.add_column('user', sa.Column('id_sucursal', sa.Integer(), nullable=True))
    op.add_column('user', sa.Column('id_rol', sa.Integer(), nullable=True))
    op.add_column('user', sa.Column('fecha_creacion', sa.DateTime(), nullable=True))
    
    # 2. Agregar foreign keys en user
    op.create_foreign_key('fk_user_sucursal', 'user', 'sucursal', ['id_sucursal'], ['id_sucursal'])
    op.create_foreign_key('fk_user_rol', 'user', 'rol', ['id_rol'], ['id_rol'])
    
    # 3. Migrar datos de usuario a user si existen
    # Primero verificar si hay datos en usuario y migrarlos
    connection = op.get_bind()
    result = connection.execute(sa.text("SELECT COUNT(*) FROM usuario"))
    count = result.scalar()
    
    if count > 0:
        # Migrar datos
        connection.execute(sa.text("""
            INSERT INTO "user" (id, email, hashed_password, full_name, is_active, is_superuser, id_sucursal, id_rol, fecha_creacion)
            SELECT 
                gen_random_uuid() as id,
                email,
                hash_password as hashed_password,
                nombre_completo as full_name,
                activo as is_active,
                false as is_superuser,
                id_sucursal,
                id_rol,
                fecha_creacion
            FROM usuario
            WHERE email NOT IN (SELECT email FROM "user")
        """))
    
    # 4. Actualizar foreign keys en auditoria para que apunten a user en lugar de usuario
    # Primero necesitamos crear una columna temporal
    op.add_column('auditoria', sa.Column('id_usuario_uuid', sa.String(), nullable=True))
    
    # Migrar los IDs de usuario a UUID (crear una tabla de mapeo temporal)
    connection.execute(sa.text("""
        CREATE TEMP TABLE usuario_to_user_mapping AS
        SELECT u2.id as uuid, u1.id_usuario as int_id
        FROM usuario u1
        INNER JOIN "user" u2 ON u1.email = u2.email
    """))
    
    # Actualizar auditoria con los UUIDs
    connection.execute(sa.text("""
        UPDATE auditoria
        SET id_usuario_uuid = mapping.uuid
        FROM usuario_to_user_mapping mapping
        WHERE auditoria.id_usuario = mapping.int_id
    """))
    
    # 5. Eliminar foreign key antigua y columnas antiguas de auditoria
    op.drop_constraint('auditoria_id_usuario_fkey', 'auditoria', type_='foreignkey')
    op.drop_column('auditoria', 'id_usuario')
    
    # Renombrar columna temporal
    op.alter_column('auditoria', 'id_usuario_uuid', new_column_name='id_usuario')
    
    # Cambiar tipo a UUID
    op.execute('ALTER TABLE auditoria ALTER COLUMN id_usuario TYPE uuid USING id_usuario::uuid')
    
    # Crear nueva foreign key
    op.create_foreign_key('fk_auditoria_user', 'auditoria', 'user', ['id_usuario'], ['id'])
    
    # Cambiar id_registro_afectado a String
    op.alter_column('auditoria', 'id_registro_afectado', type_=sa.String(), postgresql_type=sa.String())
    
    # 6. Actualizar foreign keys en movimientoinventario
    op.add_column('movimientoinventario', sa.Column('id_usuario_uuid', sa.String(), nullable=True))
    
    # Migrar los IDs
    connection.execute(sa.text("""
        UPDATE movimientoinventario
        SET id_usuario_uuid = mapping.uuid
        FROM usuario_to_user_mapping mapping
        WHERE movimientoinventario.id_usuario = mapping.int_id
    """))
    
    # Eliminar foreign key antigua
    op.drop_constraint('movimientoinventario_id_usuario_fkey', 'movimientoinventario', type_='foreignkey')
    op.drop_column('movimientoinventario', 'id_usuario')
    
    # Renombrar columna
    op.alter_column('movimientoinventario', 'id_usuario_uuid', new_column_name='id_usuario')
    
    # Cambiar tipo a UUID
    op.execute('ALTER TABLE movimientoinventario ALTER COLUMN id_usuario TYPE uuid USING id_usuario::uuid')
    
    # Crear nueva foreign key
    op.create_foreign_key('fk_movimientoinventario_user', 'movimientoinventario', 'user', ['id_usuario'], ['id'])
    
    # Eliminar tabla temporal
    connection.execute(sa.text("DROP TABLE IF EXISTS usuario_to_user_mapping"))
    
    # 7. Eliminar tabla usuario
    op.drop_index('ix_usuario_email', table_name='usuario')
    op.drop_table('usuario')


def downgrade():
    # Revertir cambios en orden inverso
    
    # Recrear tabla usuario
    op.create_table('usuario',
        sa.Column('nombre_completo', sa.String(length=255), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('activo', sa.Boolean(), nullable=False),
        sa.Column('id_usuario', sa.Integer(), nullable=False),
        sa.Column('id_sucursal', sa.Integer(), nullable=False),
        sa.Column('id_rol', sa.Integer(), nullable=False),
        sa.Column('hash_password', sa.String(), nullable=False),
        sa.Column('fecha_creacion', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['id_rol'], ['rol.id_rol']),
        sa.ForeignKeyConstraint(['id_sucursal'], ['sucursal.id_sucursal']),
        sa.PrimaryKeyConstraint('id_usuario')
    )
    op.create_index('ix_usuario_email', 'usuario', ['email'], unique=True)
    
    # Revertir movimientoinventario
    op.drop_constraint('fk_movimientoinventario_user', 'movimientoinventario', type_='foreignkey')
    op.alter_column('movimientoinventario', 'id_usuario', type_=sa.Integer())
    op.alter_column('movimientoinventario', 'id_usuario', new_column_name='id_usuario_temp')
    op.add_column('movimientoinventario', sa.Column('id_usuario', sa.Integer(), nullable=True))
    op.drop_column('movimientoinventario', 'id_usuario_temp')
    op.create_foreign_key('movimientoinventario_id_usuario_fkey', 'movimientoinventario', 'usuario', ['id_usuario'], ['id_usuario'])
    
    # Revertir auditoria
    op.drop_constraint('fk_auditoria_user', 'auditoria', type_='foreignkey')
    op.alter_column('auditoria', 'id_registro_afectado', type_=sa.Integer())
    op.alter_column('auditoria', 'id_usuario', type_=sa.Integer())
    op.alter_column('auditoria', 'id_usuario', new_column_name='id_usuario_temp')
    op.add_column('auditoria', sa.Column('id_usuario', sa.Integer(), nullable=True))
    op.drop_column('auditoria', 'id_usuario_temp')
    op.create_foreign_key('auditoria_id_usuario_fkey', 'auditoria', 'usuario', ['id_usuario'], ['id_usuario'])
    
    # Eliminar campos de user
    op.drop_constraint('fk_user_rol', 'user', type_='foreignkey')
    op.drop_constraint('fk_user_sucursal', 'user', type_='foreignkey')
    op.drop_column('user', 'fecha_creacion')
    op.drop_column('user', 'id_rol')
    op.drop_column('user', 'id_sucursal')
