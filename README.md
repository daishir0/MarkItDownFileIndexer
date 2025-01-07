## Overview
MarkItDownFileIndexer is a powerful Python-based file indexing system that specializes in converting various file formats to markdown while creating a searchable database. Built around the MarkItDown library, it automatically processes files, generates markdown content, and maintains a comprehensive index of your directory structure. The system tracks detailed metadata about files and directories, including creation dates, modifications, and processing status.

## Installation
1. Clone the repository:
```bash
git clone https://github.com/daishir0/MarkItDownFileIndexer.git
cd MarkItDownFileIndexer
```

2. Create a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows, use: venv\Scripts\activate
```

3. Install required packages:
```bash
pip install -r requirements.txt
```

## Usage
1. Basic file indexing:
```bash
python create_index.py /path/to/directory
```

2. Directory documentation can be added programmatically:
```python
indexer = MarkItDownFileIndexer()
indexer.add_directory_documentation(
    dir_path="/path/to/directory",
    title="Project Documentation",
    description="Main project files",
    purpose="Store project-related documents",
    guidelines="Keep files organized by category"
)
```

3. Adding tags to directories:
```python
indexer.add_directory_tags(
    dir_path="/path/to/directory",
    tags=["project", "documentation", "active"]
)
```

## Notes
- Built around the MarkItDown library for robust file format conversion to markdown
- Provides a unified text representation of various file formats
- Supports file integrity checking through MD5 checksums
- Maintains a SQLite database for storing file and directory information
- Logs all operations to both file (file_indexer.log) and console
- Provides progress bars for long operations
- Handles errors gracefully with detailed logging

## License
This project is licensed under the MIT License - see the LICENSE file for details.

---

# MarkItDownFileIndexer

## 概要
MarkItDownFileIndexerは、様々なファイル形式をマークダウンに変換しながら検索可能なデータベースを作成する、Pythonベースの強力なファイルインデックスシステムです。MarkItDownライブラリを中核として、ファイルの自動処理、マークダウンコンテンツの生成、ディレクトリ構造の包括的なインデックス作成を行います。システムは、作成日、変更履歴、処理状態など、ファイルとディレクトリに関する詳細なメタデータを追跡します。

## インストール方法
1. レポジトリをクローンします：
```bash
git clone https://github.com/daishir0/MarkItDownFileIndexer.git
cd MarkItDownFileIndexer
```

2. 仮想環境を作成します（推奨）：
```bash
python -m venv venv
source venv/bin/activate  # Windowsの場合: venv\Scripts\activate
```

3. 必要なパッケージをインストールします：
```bash
pip install -r requirements.txt
```

## 使い方
1. 基本的なファイルインデックス作成：
```bash
python create_index.py /path/to/directory
```

2. ディレクトリドキュメントのプログラムによる追加：
```python
indexer = MarkItDownFileIndexer()
indexer.add_directory_documentation(
    dir_path="/path/to/directory",
    title="プロジェクトドキュメント",
    description="メインプロジェクトファイル",
    purpose="プロジェクト関連文書の保存",
    guidelines="カテゴリごとにファイルを整理する"
)
```

3. ディレクトリへのタグ追加：
```python
indexer.add_directory_tags(
    dir_path="/path/to/directory",
    tags=["project", "documentation", "active"]
)
```

## 注意点
- MarkItDownライブラリを中核とした堅牢なファイル形式変換機能を提供します
- 様々なファイル形式の統一されたテキスト表現を提供します
- MD5チェックサムによるファイル整合性チェックをサポートします
- ファイルとディレクトリ情報の保存にSQLiteデータベースを使用します
- すべての操作をファイル（file_indexer.log）とコンソールの両方にログ記録します
- 長時間の操作にはプログレスバーを表示します
- 詳細なログ記録により、エラーを適切に処理します

## ライセンス
このプロジェクトはMITライセンスの下でライセンスされています。詳細はLICENSEファイルを参照してください。
