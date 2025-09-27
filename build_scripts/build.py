#!/usr/bin/env python
"""
msvcp140.dll 問題を解決するための包括的スクリプト
"""

import os
import sys
import shutil
import subprocess
import winreg
from pathlib import Path

def find_all_vcredist_dlls():
    """システム内のVC++ Redistributable DLLを全て検索"""
    print("=== VC++ Redistributable DLL検索 ===")
    
    required_dlls = [
        'msvcp140.dll',
        'vcruntime140.dll',
        'msvcp140_1.dll',
        'msvcp140_2.dll',
        'concrt140.dll',
        'vccorlib140.dll',
        'ucrtbase.dll'
    ]
    
    # 検索対象ディレクトリ
    search_paths = [
        # System directories
        r'C:\Windows\System32',
        r'C:\Windows\SysWOW64',
        
        # Visual Studio installations
        r'C:\Program Files\Microsoft Visual Studio',
        r'C:\Program Files (x86)\Microsoft Visual Studio',
        
        # VC Redist installations
        r'C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Redist',
        r'C:\Program Files\Microsoft Visual Studio\2019\Community\VC\Redist',
        r'C:\Program Files (x86)\Microsoft Visual Studio\2019\Community\VC\Redist',
        r'C:\Program Files (x86)\Microsoft Visual Studio\2017\Community\VC\Redist',
        
        # Windows Kits
        r'C:\Program Files (x86)\Windows Kits\10\Redist\ucrt\DLLs\x64',
        r'C:\Program Files (x86)\Windows Kits\8.1\Redist\ucrt\DLLs\x64',
        
        # Common installation paths
        r'C:\Windows\WinSxS',
        
        # Python/Conda environments
        sys.prefix,
        os.path.join(sys.prefix, 'DLLs'),
        os.path.join(sys.prefix, 'Library', 'bin'),
    ]
    
    found_dlls = {}
    
    for search_path in search_paths:
        if not os.path.exists(search_path):
            continue
            
        print(f"検索中: {search_path}")
        
        # WinSxSの場合は特別な処理
        if 'WinSxS' in search_path:
            for root, dirs, files in os.walk(search_path):
                for dll in required_dlls:
                    if dll in files and 'amd64' in root:  # 64bit版を優先
                        dll_path = os.path.join(root, dll)
                        if dll not in found_dlls:
                            found_dlls[dll] = dll_path
                            print(f"✓ {dll}: {dll_path}")
        else:
            # 通常のディレクトリ検索
            for root, dirs, files in os.walk(search_path):
                # 深すぎる階層は避ける
                level = root.replace(search_path, '').count(os.sep)
                if level > 3:
                    continue
                    
                for dll in required_dlls:
                    if dll in files:
                        dll_path = os.path.join(root, dll)
                        if dll not in found_dlls:
                            found_dlls[dll] = dll_path
                            print(f"✓ {dll}: {dll_path}")
    
    return found_dlls

def download_vcredist():
    """VC++ Redistributable の自動ダウンロード・インストール"""
    print("=== VC++ Redistributable インストール ===")
    
    # まずインストール済みかチェック
    try:
        import winreg
        reg_key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, 
                                r"SOFTWARE\Microsoft\VisualStudio\14.0\VC\Runtimes\x64")
        version, _ = winreg.QueryValueEx(reg_key, "Version")
        print(f"VC++ Redistributable 既にインストール済み: {version}")
        return True
    except:
        print("VC++ Redistributable が見つからないか、古いバージョンです")
    
    # ダウンロードURL（2019-2022対応版）
    vcredist_url = "https://aka.ms/vs/17/release/vc_redist.x64.exe"
    vcredist_file = "vc_redist.x64.exe"
    
    print(f"ダウンロード中: {vcredist_url}")
    
    try:
        import urllib.request
        urllib.request.urlretrieve(vcredist_url, vcredist_file)
        print(f"ダウンロード完了: {vcredist_file}")
        
        # インストール実行（サイレント）
        print("インストール中...")
        result = subprocess.run([vcredist_file, "/quiet", "/norestart"], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✓ VC++ Redistributable インストール成功")
            # ファイルを削除
            os.remove(vcredist_file)
            return True
        else:
            print(f"インストール失敗: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"ダウンロード/インストール エラー: {e}")
        return False

def create_dll_directory():
    """プロジェクト内にDLLディレクトリを作成して手動配置"""
    print("=== 手動DLL配置 ===")
    
    dll_dir = Path("runtime_dlls")
    dll_dir.mkdir(exist_ok=True)
    
    found_dlls = find_all_vcredist_dlls()
    
    if not found_dlls:
        print("必要なDLLが見つかりませんでした")
        return False
    
    # 最重要DLLをコピー
    critical_dlls = ['msvcp140.dll', 'vcruntime140.dll', 'msvcp140_1.dll']
    
    for dll_name in critical_dlls:
        if dll_name in found_dlls:
            src_path = found_dlls[dll_name]
            dst_path = dll_dir / dll_name
            
            shutil.copy2(src_path, dst_path)
            print(f"コピー: {dll_name} -> {dst_path}")
        else:
            print(f"⚠️  {dll_name} が見つかりませんでした")
    
    return True

def create_runtime_hook():
    """PyInstaller用ランタイムフックを作成"""
    print("=== ランタイムフック作成 ===")
    
    hook_dir = Path("hooks")
    hook_dir.mkdir(exist_ok=True)
    
    # ランタイムフック作成
    runtime_hook = hook_dir / "pyi_rth_tensorflow.py"
    
    hook_content = '''
import os
import sys

# DLLパスを追加
if hasattr(sys, '_MEIPASS'):
    # PyInstallerの実行時
    dll_dirs = [
        sys._MEIPASS,
        os.path.join(sys._MEIPASS, 'tensorflow'),
        os.path.join(sys._MEIPASS, 'tensorflow', 'python'),
        os.path.join(sys._MEIPASS, 'cv2'),
    ]
    
    # Windows 10以降の場合
    if hasattr(os, 'add_dll_directory'):
        for dll_dir in dll_dirs:
            if os.path.exists(dll_dir):
                try:
                    os.add_dll_directory(dll_dir)
                except:
                    pass
    
    # PATHにも追加（フォールバック）
    current_path = os.environ.get('PATH', '')
    new_paths = [d for d in dll_dirs if os.path.exists(d)]
    if new_paths:
        os.environ['PATH'] = ';'.join(new_paths) + ';' + current_path

# システムDLLディレクトリも追加
system_dll_dirs = [
    r'C:\\Windows\\System32',
    r'C:\\Windows\\SysWOW64',
]

if hasattr(os, 'add_dll_directory'):
    for sys_dir in system_dll_dirs:
        if os.path.exists(sys_dir):
            try:
                os.add_dll_directory(sys_dir)
            except:
                pass
'''
    
    with open(runtime_hook, 'w', encoding='utf-8') as f:
        f.write(hook_content)
    
    print(f"ランタイムフック作成: {runtime_hook}")
    return str(runtime_hook)

def create_enhanced_spec():
    """強化版specファイルを作成"""
    print("=== 強化版specファイル作成 ===")
    
    runtime_hook = create_runtime_hook()
    
    spec_content = f'''# -*- mode: python ; coding: utf-8 -*-
# DLL問題対策強化版

import os
import sys
import glob
from PyInstaller.utils.hooks import collect_all

# 仮想環境のパスを取得
venv_path = sys.prefix

def get_all_vcredist_dlls():
    """全てのVC++ Redistributable DLLを検索・収集"""
    found_dlls = []
    
    required_dlls = [
        'msvcp140.dll', 'vcruntime140.dll', 'msvcp140_1.dll',
        'msvcp140_2.dll', 'concrt140.dll', 'vccorlib140.dll',
        'ucrtbase.dll', 'api-ms-win-crt-runtime-l1-1-0.dll',
    ]
    
    # 手動配置したDLLディレクトリ
    runtime_dll_dir = 'runtime_dlls'
    if os.path.exists(runtime_dll_dir):
        for dll in required_dlls:
            dll_path = os.path.join(runtime_dll_dir, dll)
            if os.path.exists(dll_path):
                found_dlls.append((dll_path, '.'))
                print(f"手動DLL追加: {{dll}}")
    
    # システムからも検索
    search_paths = [
        os.path.join(venv_path, 'DLLs'),
        r'C:\\Windows\\System32',
        r'C:\\Windows\\SysWOW64',
    ]
    
    for search_path in search_paths:
        if os.path.exists(search_path):
            for dll in required_dlls:
                dll_path = os.path.join(search_path, dll)
                if os.path.exists(dll_path):
                    # 重複チェック
                    if dll_path not in [f[0] for f in found_dlls]:
                        found_dlls.append((dll_path, '.'))
                        print(f"システムDLL追加: {{dll}}")
    
    return found_dlls

# モジュール収集
numpy_datas, numpy_binaries, numpy_hiddenimports = collect_all('numpy')
cv2_datas, cv2_binaries, cv2_hiddenimports = collect_all('cv2')

# その他必要なモジュール
other_datas, other_binaries, other_hiddenimports = [], [], []
other_modules = ['pygrabber', 'comtypes']

for module in other_modules:
    try:
        datas, binaries, hiddenimports = collect_all(module)
        other_datas.extend(datas)
        other_binaries.extend(binaries)
        other_hiddenimports.extend(hiddenimports)
    except:
        pass

# VC++ Redistributable DLLs
vcredist_dlls = get_all_vcredist_dlls()

# 全て統合
all_binaries = numpy_binaries + cv2_binaries + other_binaries + vcredist_dlls
all_datas = numpy_datas + cv2_datas + other_datas

# 重複除去
def remove_duplicates(items):
    seen = set()
    unique = []
    for item in items:
        key = item[0]
        if key not in seen:
            unique.append(item)
            seen.add(key)
    return unique

all_binaries = remove_duplicates(all_binaries)
all_datas = remove_duplicates(all_datas)

# hidden imports
all_hiddenimports = [
    'numpy', 'cv2', 'unittest', 'unittest.mock', 'test',
] + numpy_hiddenimports + cv2_hiddenimports + other_hiddenimports

all_hiddenimports = list(dict.fromkeys(all_hiddenimports))

print(f"最終ファイル数: {{len(all_datas)}} データ, {{len(all_binaries)}} バイナリ")

a = Analysis(
    ['src\\\\PokemonAutoCapture\\\\main.py'],
    pathex=[],
    binaries=all_binaries,
    datas=all_datas,
    hiddenimports=all_hiddenimports,
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=['{runtime_hook.replace(os.sep, "/")}'],  # ランタイムフック追加
    excludes=['matplotlib', 'IPython', 'sphinx'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='PokemonAutoCapture',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/icons/icon.ico' if os.path.exists('assets/icons/icon.ico') else None
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='PokemonAutoCapture'
)
'''
    
    with open('main_dll_fix.spec', 'w', encoding='utf-8') as f:
        f.write(spec_content)
    
    print("強化版specファイル作成: main_dll_fix.spec")

def main():
    """メイン処理"""
    print("msvcp140.dll 問題修正スクリプト")
    print("=" * 50)
    
    # 1. VC++ Redistributable の確認・インストール
    if not download_vcredist():
        print("VC++ Redistributable のインストールに失敗しました")
        print("手動でインストールしてください:")
        print("https://aka.ms/vs/17/release/vc_redist.x64.exe")
    
    # 2. DLLの手動配置
    create_dll_directory()
    
    # 3. 強化版specファイル作成
    create_enhanced_spec()
    
    print("\n=== 修正完了 ===")
    print("以下のコマンドでビルドしてください:")
    print("python -m PyInstaller --clean --noconfirm main_dll_fix.spec")
    
    # 4. 自動ビルド（オプション）
    print("\n自動ビルドを実行しますか？ (y/n): ", end="")
    if input().lower().startswith('y'):
        print("ビルド開始...")
        result = subprocess.run([
            sys.executable, '-m', 'PyInstaller', 
            '--clean', '--noconfirm', 'main_dll_fix.spec'
        ])
        
        if result.returncode == 0:
            print("✓ ビルド成功！")
            
            # DLLを出力ディレクトリにもコピー
            dist_dir = Path("dist/PokemonAutoCapture")
            runtime_dll_dir = Path("runtime_dlls")
            
            if dist_dir.exists() and runtime_dll_dir.exists():
                for dll_file in runtime_dll_dir.glob("*.dll"):
                    dst_file = dist_dir / dll_file.name
                    shutil.copy2(dll_file, dst_file)
                    print(f"配布フォルダにDLL追加: {dll_file.name}")
        else:
            print("❌ ビルド失敗")

if __name__ == "__main__":
    main()
    input("Enterキーで終了...")