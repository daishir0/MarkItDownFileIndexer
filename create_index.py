import os
import sys
import sqlite3
import hashlib
import magic
import logging
from datetime import datetime
from pathlib import Path
from tqdm import tqdm
from markitdown import MarkItDown
from schema import init_database, get_supported_formats
import datetime as dt
import warnings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('file_indexer.log'),
        logging.StreamHandler()
    ]
)

# ファイルの先頭に追加
warnings.filterwarnings('ignore', category=UserWarning, module='openpyxl')

class FileIndexer:
    def __init__(self, db_path='file_index.db'):
        """Initialize the file indexer"""
        self.db_path = db_path
        self.md = MarkItDown()
        if not Path(db_path).exists():
            init_database(db_path)
        self.supported_formats = self._get_supported_formats()
        
        self.conn = sqlite3.connect(
            db_path,
            detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES
        )
        # datetime型のアダプターを登録
        sqlite3.register_adapter(dt.datetime, lambda x: x.isoformat())
        sqlite3.register_converter("datetime", lambda x: dt.datetime.fromisoformat(x.decode()))
        
    def _get_supported_formats(self):
        """Get list of supported file extensions from database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT extension FROM file_formats WHERE is_enabled = TRUE')
        formats = {row[0] for row in cursor.fetchall()}
        conn.close()
        return formats

    def _calculate_checksum(self, file_path):
        """Calculate MD5 checksum of a file"""
        try:
            hash_md5 = hashlib.md5()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception as e:
            logging.error(f"Error calculating checksum for {file_path}: {e}")
            return None

    def _process_file(self, file_path):
        """Process a single file and convert to markdown if supported"""
        try:
            file_stat = os.stat(file_path)
            file_ext = Path(file_path).suffix.lower().lstrip('.')
            
            # 基本的なファイル情報を収集
            file_info = {
                'file_path': str(file_path),
                'file_name': Path(file_path).name,
                'file_extension': file_ext,
                'file_size': file_stat.st_size,
                'created_at': dt.datetime.fromtimestamp(file_stat.st_ctime),
                'modified_at': dt.datetime.fromtimestamp(file_stat.st_mtime),
                'indexed_at': dt.datetime.now(),
                'checksum': self._calculate_checksum(file_path),
                'processing_status': 'skipped',
                'markdown_content': None,
                'error_message': None
            }
            
            # サポートされている形式の場合のみ変換を試みる
            if file_ext in self.supported_formats:
                try:
                    result = self.md.convert(str(file_path))
                    file_info['markdown_content'] = result.text_content
                    file_info['processing_status'] = 'processed'
                except self.md.UnsupportedFormatException as e:
                    file_info['processing_status'] = 'skipped'
                    file_info['error_message'] = f"Unsupported format: {e}"
                    logging.info(f"Skipping unsupported file: {file_path} - {e}")
                except Exception as e:
                    file_info['processing_status'] = 'failed'
                    file_info['error_message'] = str(e)
                    logging.warning(f"Error processing {file_path}: {e}")
            else:
                file_info['processing_status'] = 'skipped'
                file_info['error_message'] = f"Unsupported file format: .{file_ext}"
                logging.debug(f"Skipping unsupported file: {file_path}")

            return file_info

        except Exception as e:
            logging.error(f"Error processing {file_path}: {e}")
            return None

    def _save_to_db(self, file_info):
        """Save file information to database"""
        cursor = self.conn.cursor()
        
        try:
            cursor.execute('''
                INSERT OR REPLACE INTO files (
                    file_path, file_name, file_extension, file_size,
                    created_at, modified_at, indexed_at, checksum,
                    markdown_content, processing_status, error_message
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                file_info['file_path'],
                file_info['file_name'],
                file_info['file_extension'],
                file_info['file_size'],
                file_info['created_at'],
                file_info['modified_at'],
                file_info['indexed_at'],
                file_info['checksum'],
                file_info.get('markdown_content'),
                file_info['processing_status'],
                file_info.get('error_message')
            ))
            
            if file_info['processing_status'] == 'processed':
                cursor.execute('''
                    INSERT INTO processing_queue (file_id, status, created_at)
                    VALUES ((SELECT id FROM files WHERE file_path = ?), 'pending', ?)
                ''', (file_info['file_path'], dt.datetime.now()))
            
            self.conn.commit()
            
        except Exception as e:
            logging.error(f"Error saving to database: {e}")
            self.conn.rollback()

    def _process_directory(self, dir_path):
        """Process directory information"""
        cursor = self.conn.cursor()
        
        try:
            dir_stat = os.stat(dir_path)
            dir_info = {
                'dir_path': str(dir_path),
                'dir_name': Path(dir_path).name,
                'parent_dir_path': str(Path(dir_path).parent),
                'depth': len(Path(dir_path).parts),
                'created_at': dt.datetime.fromtimestamp(dir_stat.st_ctime),
                'modified_at': dt.datetime.fromtimestamp(dir_stat.st_mtime),
                'indexed_at': dt.datetime.now()
            }
            
            cursor.execute('''
                INSERT OR REPLACE INTO directories (
                    dir_path, dir_name, parent_dir_path, depth,
                    created_at, modified_at, indexed_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                dir_info['dir_path'],
                dir_info['dir_name'],
                dir_info['parent_dir_path'],
                dir_info['depth'],
                dir_info['created_at'],
                dir_info['modified_at'],
                dir_info['indexed_at']
            ))
            
            self.conn.commit()
            
        except Exception as e:
            logging.error(f"Error processing directory {dir_path}: {e}")
            self.conn.rollback()

    def index_directory(self, root_path):
        """Recursively index all files in the given directory"""
        root_path = Path(root_path)
        if not root_path.exists():
            logging.error(f"Error: Path {root_path} does not exist")
            return

        # Get total file count for progress bar
        total_files = sum(1 for _ in root_path.rglob('*') if _.is_file())
        
        logging.info(f"Starting indexing of {root_path}")
        logging.info(f"Total files found: {total_files}")

        processed = 0
        skipped = 0
        failed = 0

        # Process all files with progress bar
        with tqdm(total=total_files, desc="Indexing files") as pbar:
            for path in root_path.rglob('*'):
                if path.is_file():
                    file_info = self._process_file(path)
                    if file_info:
                        self._save_to_db(file_info)
                        if file_info['processing_status'] == 'processed':
                            processed += 1
                        elif file_info['processing_status'] == 'skipped':
                            skipped += 1
                        else:
                            failed += 1
                    pbar.update(1)
                elif path.is_dir():
                    self._process_directory(path)

        logging.info("Indexing completed!")
        
        # Print summary
        logging.info(f"\nProcessing Summary:")
        logging.info(f"Total files indexed: {total_files}")
        logging.info(f"Successfully processed: {processed}")
        logging.info(f"Skipped files: {skipped}")
        logging.info(f"Failed to process: {failed}")

    def add_directory_documentation(self, dir_path, title, description, purpose, guidelines, created_by="system"):
        """Add or update documentation for a directory"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Get directory ID
            cursor.execute('SELECT id FROM directories WHERE dir_path = ?', (dir_path,))
            result = cursor.fetchone()
            if not result:
                logging.error(f"Directory not found: {dir_path}")
                return False
            
            dir_id = result[0]
            
            # Get next version number
            cursor.execute('SELECT MAX(version) FROM directory_docs WHERE directory_id = ?', (dir_id,))
            current_version = cursor.fetchone()[0] or 0
            next_version = current_version + 1
            
            # Set all previous versions as not current
            cursor.execute('''
                UPDATE directory_docs 
                SET is_current = FALSE 
                WHERE directory_id = ?
            ''', (dir_id,))
            
            # Add new documentation
            cursor.execute('''
                INSERT INTO directory_docs (
                    directory_id, version, title, description,
                    purpose, guidelines, created_at, created_by,
                    is_current
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, TRUE)
            ''', (
                dir_id, next_version, title, description,
                purpose, guidelines, datetime.now(), created_by
            ))
            
            # Update last_documented_at in directories table
            cursor.execute('''
                UPDATE directories 
                SET last_documented_at = ? 
                WHERE id = ?
            ''', (datetime.now(), dir_id))
            
            conn.commit()
            logging.info(f"Added documentation version {next_version} for directory: {dir_path}")
            return True
            
        except Exception as e:
            logging.error(f"Error adding directory documentation: {e}")
            conn.rollback()
            return False
            
        finally:
            conn.close()

    def add_directory_tags(self, dir_path, tags, created_by="system"):
        """Add tags to a directory"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Get directory ID
            cursor.execute('SELECT id FROM directories WHERE dir_path = ?', (dir_path,))
            result = cursor.fetchone()
            if not result:
                logging.error(f"Directory not found: {dir_path}")
                return False
            
            dir_id = result[0]
            
            # Add tags
            for tag in tags:
                cursor.execute('''
                    INSERT OR IGNORE INTO directory_tags (
                        directory_id, tag_name, created_at, created_by
                    ) VALUES (?, ?, ?, ?)
                ''', (dir_id, tag, datetime.now(), created_by))
            
            conn.commit()
            logging.info(f"Added tags {tags} to directory: {dir_path}")
            return True
            
        except Exception as e:
            logging.error(f"Error adding directory tags: {e}")
            conn.rollback()
            return False
            
        finally:
            conn.close()

    def add_directory_relation(self, source_path, target_path, relation_type, description):
        """Add a relationship between two directories"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO directory_relations (
                    source_dir_id, target_dir_id, relation_type,
                    description, created_at
                ) SELECT d1.id, d2.id, ?, ?, ?
                FROM directories d1, directories d2
                WHERE d1.dir_path = ? AND d2.dir_path = ?
            ''', (relation_type, description, datetime.now(), source_path, target_path))
            
            conn.commit()
            logging.info(f"Added relation {relation_type} between {source_path} and {target_path}")
            return True
            
        except Exception as e:
            logging.error(f"Error adding directory relation: {e}")
            conn.rollback()
            return False
            
        finally:
            conn.close()

    def __del__(self):
        """デストラクタでデータベース接続を閉じる"""
        if hasattr(self, 'conn'):
            self.conn.close()

def main():
    if len(sys.argv) != 2:
        print("Usage: python create_index.py <directory_path>")
        sys.exit(1)

    # Initialize indexer and process directory
    indexer = FileIndexer()
    indexer.index_directory(sys.argv[1])

if __name__ == "__main__":
    main()