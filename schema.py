#!/usr/bin/env python3
import os
import sqlite3
from datetime import datetime
import colorama
from colorama import Fore, Style

# Initialize colorama for Windows support
colorama.init()

def print_success(message):
    """Print success message in green"""
    print(f"{Fore.GREEN}{message}{Style.RESET_ALL}")

def print_error(message):
    """Print error message in red"""
    print(f"{Fore.RED}{message}{Style.RESET_ALL}")

def get_supported_formats():
    """Return a list of supported file formats with their categories"""
    return [
        ('pdf', 'document', 'PDF Document'),
        ('pptx', 'presentation', 'PowerPoint'),
        ('ppt', 'presentation', 'PowerPoint Legacy'),
        ('docx', 'document', 'Word Document'),
        ('doc', 'document', 'Word Legacy'),
        ('xlsx', 'spreadsheet', 'Excel Workbook'),
        ('xls', 'spreadsheet', 'Excel Legacy'),
        ('jpg', 'image', 'JPEG Image'),
        ('jpeg', 'image', 'JPEG Image'),
        ('png', 'image', 'PNG Image'),
        ('gif', 'image', 'GIF Image'),
        ('mp3', 'audio', 'MP3 Audio'),
        ('wav', 'audio', 'WAV Audio'),
        ('html', 'web', 'HTML Document'),
        ('htm', 'web', 'HTML Document'),
        ('csv', 'data', 'CSV Data'),
        ('json', 'data', 'JSON Data'),
        ('xml', 'data', 'XML Data'),
        ('zip', 'archive', 'ZIP Archive'),
        ('txt', 'text', 'Text Document')
    ]

def init_database(db_path='file_index.db'):
    """Initialize SQLite database with all required tables"""
    print(f"\nInitializing database at: {os.path.abspath(db_path)}")
    
    try:
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        
        print("\nCreating tables...")
        
        # Files table
        c.execute('''
        CREATE TABLE IF NOT EXISTS files (
            id INTEGER PRIMARY KEY,
            file_path TEXT NOT NULL UNIQUE,
            file_name TEXT NOT NULL,
            file_extension TEXT,
            file_size INTEGER,
            created_at TIMESTAMP,
            modified_at TIMESTAMP,
            indexed_at TIMESTAMP,
            checksum TEXT,
            markdown_content TEXT,
            content_summary TEXT,
            processing_status TEXT,
            error_message TEXT,
            last_summary_update TIMESTAMP
        )
        ''')
        print_success("✓ Created files table")
        
        # Directories table
        c.execute('''
        CREATE TABLE IF NOT EXISTS directories (
            id INTEGER PRIMARY KEY,
            dir_path TEXT NOT NULL UNIQUE,
            dir_name TEXT NOT NULL,
            parent_dir_path TEXT,
            depth INTEGER,
            created_at TIMESTAMP,
            modified_at TIMESTAMP,
            indexed_at TIMESTAMP,
            title TEXT,
            status TEXT DEFAULT 'active',
            owner TEXT,
            last_documented_at TIMESTAMP
        )
        ''')
        print_success("✓ Created directories table")
        
        # Directory documentation table
        c.execute('''
        CREATE TABLE IF NOT EXISTS directory_docs (
            id INTEGER PRIMARY KEY,
            directory_id INTEGER NOT NULL,
            version INTEGER NOT NULL,
            title TEXT NOT NULL,
            description TEXT,
            purpose TEXT,
            guidelines TEXT,
            created_at TIMESTAMP,
            created_by TEXT,
            is_current BOOLEAN DEFAULT TRUE,
            metadata TEXT,
            FOREIGN KEY (directory_id) REFERENCES directories(id),
            UNIQUE (directory_id, version)
        )
        ''')
        print_success("✓ Created directory_docs table")
        
        # Directory tags table
        c.execute('''
        CREATE TABLE IF NOT EXISTS directory_tags (
            id INTEGER PRIMARY KEY,
            directory_id INTEGER NOT NULL,
            tag_name TEXT NOT NULL,
            created_at TIMESTAMP,
            created_by TEXT,
            FOREIGN KEY (directory_id) REFERENCES directories(id),
            UNIQUE (directory_id, tag_name)
        )
        ''')
        print_success("✓ Created directory_tags table")
        
        # Directory relationships table
        c.execute('''
        CREATE TABLE IF NOT EXISTS directory_relations (
            id INTEGER PRIMARY KEY,
            source_dir_id INTEGER NOT NULL,
            target_dir_id INTEGER NOT NULL,
            relation_type TEXT NOT NULL,
            description TEXT,
            created_at TIMESTAMP,
            FOREIGN KEY (source_dir_id) REFERENCES directories(id),
            FOREIGN KEY (target_dir_id) REFERENCES directories(id)
        )
        ''')
        print_success("✓ Created directory_relations table")
        
        # File formats table
        c.execute('''
        CREATE TABLE IF NOT EXISTS file_formats (
            id INTEGER PRIMARY KEY,
            extension TEXT NOT NULL UNIQUE,
            category TEXT NOT NULL,
            description TEXT,
            is_enabled BOOLEAN DEFAULT TRUE,
            processing_options TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        print_success("✓ Created file_formats table")
        
        # Processing queue table
        c.execute('''
        CREATE TABLE IF NOT EXISTS processing_queue (
            id INTEGER PRIMARY KEY,
            file_id INTEGER NOT NULL,
            priority INTEGER DEFAULT 0,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP,
            started_at TIMESTAMP,
            completed_at TIMESTAMP,
            error_message TEXT,
            FOREIGN KEY (file_id) REFERENCES files(id)
        )
        ''')
        print_success("✓ Created processing_queue table")

        print("\nCreating indices...")
        # Create indices
        c.execute('CREATE INDEX IF NOT EXISTS idx_file_path ON files(file_path)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_file_ext ON files(file_extension)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_dir_path ON directories(dir_path)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_parent_dir ON directories(parent_dir_path)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_dir_docs ON directory_docs(directory_id, version)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_dir_tags ON directory_tags(directory_id)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_dir_relations ON directory_relations(source_dir_id, target_dir_id)')
        print_success("✓ Created all indices")

        print("\nInitializing supported formats...")
        # Insert supported formats
        formats = get_supported_formats()
        format_count = 0
        for ext, category, description in formats:
            c.execute('''
            INSERT OR IGNORE INTO file_formats (extension, category, description)
            VALUES (?, ?, ?)
            ''', (ext, category, description))
            format_count += 1
        print_success(f"✓ Added {format_count} supported file formats")
        
        conn.commit()
        conn.close()
        
        print("\nDatabase initialization completed successfully!")
        print(f"Database location: {os.path.abspath(db_path)}")
        
        # Verify the database
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM file_formats")
        format_count = c.fetchone()[0]
        conn.close()
        
        print("\nVerification:")
        print(f"- Database file exists: {os.path.exists(db_path)}")
        print(f"- Supported formats loaded: {format_count}")
        print_success("\n✓ Database is ready to use!")
        
        return True
        
    except Exception as e:
        print_error(f"\nError during database initialization: {str(e)}")
        return False

if __name__ == "__main__":
    init_database()