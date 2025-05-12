"""
Pruebas para el servicio de backup
"""
import unittest
import os
import tempfile
import shutil
from app import create_app
from app.core.config import config
from app.database.models import db
from app.services.implementations.backup_service import BackupService
from flask import current_app

class TestBackupService(unittest.TestCase):
    """Pruebas para el servicio de backup"""
    
    def setUp(self):
        """Configurar el entorno de prueba"""
        self.app = create_app(config['testing'])
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        
        # Crear un directorio temporal para backups
        self.backup_dir = tempfile.mkdtemp()
        current_app.config['BACKUP_DIR'] = self.backup_dir
        
        # Crear mock para DATABASE_PATH
        fd, self.db_path = tempfile.mkstemp()
        os.close(fd)
        with open(self.db_path, 'w') as f:
            f.write('mock database content')
        current_app.config['DATABASE_PATH'] = self.db_path
        
        # Inicializar servicio de backup
        self.backup_service = BackupService()
        
    def tearDown(self):
        """Limpiar después de las pruebas"""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
        
        # Eliminar archivos temporales
        if os.path.exists(self.backup_dir):
            shutil.rmtree(self.backup_dir)
        if os.path.exists(self.db_path):
            os.unlink(self.db_path)
    
    def test_create_backup(self):
        """Prueba la creación de backup"""
        # Crear un backup
        backup_info = self.backup_service.create_backup("Backup de prueba")
        
        # Verificar que se creó correctamente
        self.assertIsNotNone(backup_info)
        self.assertIn('id', backup_info)
        self.assertIn('filename', backup_info)
        self.assertEqual(backup_info['description'], "Backup de prueba")
        
        # Verificar que el archivo existe
        backup_file_path = os.path.join(self.backup_dir, backup_info['filename'])
        self.assertTrue(os.path.exists(backup_file_path))
        
        # Verificar que se guardó en la base de datos
        from app.database.models import Backup
        backup_db = Backup.query.get(backup_info['id'])
        self.assertIsNotNone(backup_db)
        self.assertEqual(backup_db.filename, backup_info['filename'])
    
    def test_list_backups(self):
        """Prueba el listado de backups"""
        # Crear varios backups
        self.backup_service.create_backup("Backup 1")
        self.backup_service.create_backup("Backup 2")
        self.backup_service.create_backup("Backup 3")
        
        # Obtener la lista de backups
        backups = self.backup_service.list_backups()
        
        # Verificar la lista
        self.assertEqual(len(backups), 3)
        self.assertIn('filename', backups[0])
        self.assertIn('created_at', backups[0])
    
    def test_delete_backup(self):
        """Prueba la eliminación de backup"""
        # Crear un backup
        backup_info = self.backup_service.create_backup("Backup para eliminar")
        
        # Verificar que existe
        backup_file_path = os.path.join(self.backup_dir, backup_info['filename'])
        self.assertTrue(os.path.exists(backup_file_path))
        
        # Eliminar el backup
        result = self.backup_service.delete_backup(backup_info['id'])
        self.assertTrue(result)
        
        # Verificar que se eliminó
        self.assertFalse(os.path.exists(backup_file_path))
        
        # Verificar que se eliminó de la base de datos
        from app.database.models import Backup
        self.assertIsNone(Backup.query.get(backup_info['id']))
    
    def test_restore_backup(self):
        """Prueba la restauración de backup"""
        # Crear un backup
        backup_info = self.backup_service.create_backup("Backup para restaurar")
        
        # Cambiar el contenido del archivo de base de datos
        with open(self.db_path, 'w') as f:
            f.write('changed database content')
        
        # Restaurar el backup
        result = self.backup_service.restore_backup(backup_info['id'])
        self.assertTrue(result)
        
        # Verificar que se restauró correctamente
        with open(self.db_path, 'r') as f:
            content = f.read()
        self.assertEqual(content, 'mock database content')

if __name__ == '__main__':
    unittest.main() 