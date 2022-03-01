# -*- mode: python ; coding: utf-8 -*-

block_cipher = None


a = Analysis(['ScreenClippingToolMaster.py'],
             pathex=['X:\\Languages\\Python\\Apps\\ScreenClippingToolMaster'],
             binaries=[],
             datas=[('pyclip_bringforward.ico', '.'), ('pyclip_default.ico', '.'), ('pyclip_delay.ico', '.'), ('pyclip_destroy.ico', '.'), ('pyclip_multi.ico', '.'), ('pyclip_reload.ico', '.'), ('pyclip_screenshot.ico', '.'), ('pyclip_settings.ico', '.'), ('pyclip_snapshot.ico', '.'), ('pyclip_gif.ico', '.'), ('tess_folder', '.')],
             hiddenimports=['pkg_resources.py2_warn'],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          [],
          name='ScreenClippingToolMaster',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          upx_exclude=[],
          runtime_tmpdir=None,
          console=False )
