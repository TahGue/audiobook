#!/usr/bin/env python3
"""
Build script for creating the Python backend sidecar binary.
Uses PyInstaller to bundle the FastAPI app into a single executable.
"""

import subprocess
import sys
import os
import shutil
import platform


def build_sidecar():
    """Build the Python backend as a standalone executable."""
    
    print("Building Audiobook Maker Backend Sidecar...")
    print(f"Platform: {platform.system()}")
    
    # Ensure PyInstaller is installed
    try:
        import PyInstaller
    except ImportError:
        print("PyInstaller not found. Installing...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"], check=True)
    
    # Create spec file for PyInstaller
    spec_content = '''
# -*- mode: python ; coding: utf-8 -*-

import sys
import os

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('models', 'models'),
        ('routers', 'routers'),
        ('services', 'services'),
        ('alembic', 'alembic'),
        ('alembic.ini', '.'),
    ],
    hiddenimports=[
        'uvicorn',
        'uvicorn.logging',
        'uvicorn.loops',
        'uvicorn.loops.auto',
        'uvicorn.protocols',
        'uvicorn.protocols.http',
        'uvicorn.protocols.http.auto',
        'uvicorn.protocols.websockets',
        'uvicorn.protocols.websockets.auto',
        'fastapi',
        'sqlmodel',
        'sqlalchemy',
        'alembic',
        'alembic.config',
        'alembic.command',
        'pdfplumber',
        'fitz',
        'ebooklib',
        'docx',
        'bs4',
        'mishkal',
        'pyarabic',
        'piper',
        'edge_tts',
        'pydub',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='audiobook-backend',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    
)
'''
    
    # Write spec file
    spec_path = 'audiobook-backend.spec'
    with open(spec_path, 'w') as f:
        f.write(spec_content)
    
    print("Created PyInstaller spec file")
    
    # Run PyInstaller
    cmd = [
        sys.executable, '-m', 'PyInstaller',
        spec_path,
        '--clean',
        '--noconfirm',
    ]
    
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        print("ERROR: PyInstaller failed!")
        print("STDOUT:", result.stdout)
        print("STDERR:", result.stderr)
        sys.exit(1)
    
    print("PyInstaller build completed successfully")
    
    # Copy the built binary to the Tauri binaries directory
    source_dir = 'dist/audiobook-backend'
    target_dir = '../frontend/src-tauri/binaries'
    
    # Create target directory if it doesn't exist
    os.makedirs(target_dir, exist_ok=True)
    
    # Determine binary extension based on platform
    if platform.system() == 'Windows':
        binary_name = 'audiobook-backend.exe'
    else:
        binary_name = 'audiobook-backend'
    
    source_path = os.path.join(source_dir, binary_name)
    target_path = os.path.join(target_dir, binary_name)
    
    if os.path.exists(source_path):
        shutil.copy2(source_path, target_path)
        print(f"Copied binary to: {target_path}")
    else:
        print(f"WARNING: Could not find built binary at {source_path}")
        print("Contents of dist directory:")
        if os.path.exists('dist'):
            for item in os.listdir('dist'):
                print(f"  - {item}")
    
    # Clean up
    if os.path.exists(spec_path):
        os.remove(spec_path)
        print("Cleaned up spec file")
    
    print("\\nBuild complete!")
    print(f"Binary location: {target_path}")


if __name__ == '__main__':
    build_sidecar()
