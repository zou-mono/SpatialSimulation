# -*- mode: python ; coding: utf-8 -*-

block_cipher = None


a = Analysis(['frmMainWindow.py', 'icons_rc.py',
              'UI\\UIIdentifyResult.py',
              'UI\\UILogView.py',
              'UI\\UIMainWindow.py',
              'UI\\UIModelCal.py',
              'UICore\\common.py',
              'UICore\\DataFactory.py',
              'UICore\\Gv.py',
              'UICore\\log4p.py',
              'UICore\\fgdberror.py',
              'UICore\\fgdb.py',
              'UICore\\filegdbapi.py',
              'widgets\\CollapsibleSplitter.py',
              'widgets\\mapTool.py',
              'widgets\\mDock.py',
              'forms\\frmIdentifyResult.py',
              'forms\\frmLogView.py',
              'forms\\frmModelCal.py'],
             pathex=['D:\\空间模拟\\SpatialSimulation'],
             binaries=[('C:\\OSGeo4W64\\apps\\gdal\\lib\\gdalplugins', 'Library\\lib\\gdalplugins'),
                       ('C:\\OSGeo4W64\\bin\\FileGDBAPI.dll', '.'),
                       ('D:\\空间模拟\\SpatialSimulation\\UICore\\_filegdbapi.pyd', 'UICore')],
             datas=[('C:\\Program Files\\GDAL\\projlib', 'Library\\share\\proj'),
                    ('C:\\OSGeo4W64\\apps\\qgis-ltr\\plugins', 'qgis\\plugins'),
                    ('C:\\OSGeo4W64\\apps\\Python39\\lib\\site-packages\\PyQt5\\*.pyd', 'PyQt5'),
                    ('C:\\OSGeo4W64\\apps\\Qt5\\plugins\\styles', 'PyQt5\\Qt\\plugins\\styles'),
                    ('C:\\OSGeo4W64\\apps\\Qt5\\plugins\\iconengines', 'PyQt5\\Qt\\plugins\\iconengines'),
                    ('C:\\OSGeo4W64\\apps\\Qt5\\plugins\\imageformats', 'PyQt5\\Qt\\plugins\\imageformats'),
                    ('C:\\OSGeo4W64\\apps\\Qt5\\plugins\\platforms', 'PyQt5\\Qt\\plugins\\platforms'),
                    ('C:\\OSGeo4W64\\apps\\Qt5\\plugins\\platformthemes', 'PyQt5\\Qt\\plugins\\platformthemes')],
             hiddenimports=['osgeo', 'filegdbapi'],
             hookspath=[],
             runtime_hooks=['hook.py'],
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
          exclude_binaries=False,
          name='SpatialSimulation',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=False,
          icon="D:\\空间模拟\\SpatialSimulation\\icons\\ArcScene.ico",
          upx_exclude=[],
          runtime_tmpdir=None,
          console=False,
          version="version.py")
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=False,
               upx_exclude=[],
               name='SpatialSimulation')