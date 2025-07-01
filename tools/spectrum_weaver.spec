# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for SpectrumWeaver
This spec file addresses common issues with SciPy and other scientific libraries
when building with PyInstaller.
"""

import os
import sys
from pathlib import Path

# Get the project root directory
project_root = Path(os.getcwd())

# Add the src directory to the path
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

# Define the main script
main_script = src_path / "spectrum_weaver.py"

# Hidden imports for SciPy and other scientific libraries
hidden_imports = [
    # SciPy modules that are often missed by PyInstaller
    'scipy._lib.messagestream',
    'scipy._lib._ccallback_c',
    'scipy.special._ufuncs_cxx',
    'scipy.linalg.cython_blas',
    'scipy.linalg.cython_lapack',
    'scipy.special.cython_special',
    'scipy.linalg._decomp_update',
    'scipy.sparse.csgraph._validation',
    'scipy.sparse._matrix',
    'scipy.special._ellip_harm_2',
    'scipy.integrate._ode',
    'scipy.integrate._odepack',
    'scipy.integrate._quadpack',
    'scipy.optimize._minpack',
    'scipy.stats._stats',
    'scipy.stats._continuous_distns',
    'scipy.stats._discrete_distns',
    'scipy.linalg._solve_toeplitz',
    'scipy.linalg._decomp_cossin',
    'scipy.linalg._matfuncs_sqrtm',
    'scipy.optimize._lbfgsb',
    'scipy.optimize._trustregion_exact',
    'scipy.optimize._group_columns',
    'scipy.sparse.linalg._dsolve._superlu',
    'scipy.sparse.linalg._eigen._arpack',
    'scipy.sparse.csgraph._shortest_path',
    'scipy.sparse.csgraph._traversal',
    'scipy.sparse.csgraph._min_spanning_tree',
    'scipy.sparse.csgraph._flow',
    'scipy.sparse.csgraph._matching',
    'scipy.sparse.csgraph._reordering',
    'scipy.sparse.csgraph._tools',
    'scipy._cyutility',  # This is the specific module causing your error
    
    # SciPy spatial modules
    'scipy.spatial',
    'scipy.spatial.distance',
    'scipy.spatial._kdtree',
    'scipy.spatial._ckdtree',
    'scipy.spatial._qhull',
    'scipy.spatial._spherical_voronoi',
    'scipy.spatial._plotutils',
    'scipy.spatial._procrustes',
    
    # SciPy ndimage modules (needed for convolve1d and other functions)
    'scipy.ndimage',
    'scipy.ndimage._ni_support',
    'scipy.ndimage._nd_image',
    'scipy.ndimage._filters',
    'scipy.ndimage._interpolation',
    'scipy.ndimage._measurements',
    'scipy.ndimage._morphology',
    
    # NumPy modules
    'numpy.core._methods',
    'numpy.lib.format',
    'numpy.core.multiarray',
    'numpy.core.umath',
    'numpy.linalg._umath_linalg',
    'numpy.random._pickle',
    
    # Librosa and audio processing
    'librosa.util',
    'librosa.core',
    'librosa.feature',
    'resampy',
    'soundfile',
    'audioread',
    
    # PySide6/Qt modules
    'PySide6.QtCore',
    'PySide6.QtGui', 
    'PySide6.QtWidgets',
    'PySide6.QtOpenGL',
    'PySide6.QtOpenGLWidgets',
    
    # PyQtGraph
    'pyqtgraph.exporters',
    'pyqtgraph.graphicsItems',
    'pyqtgraph.widgets',
    
    # Other modules
    'mutagen',
    'queue',
    'threading',
    'pkg_resources',
    'pkg_resources.py2_warn',
]

# Data files to include
datas = [
    (str(src_path / "assets" / "icon.png"), "assets"),
    (str(src_path / "assets" / "styles.qss"), "assets"),
    (str(project_root / "images" / "icon.ico"), "images"),
]

# Binary files to exclude (to reduce size)
excludes = [
    'tkinter',
    'matplotlib',
    'IPython',
    'jupyter',
    'notebook',
    'pandas',
    'sklearn',
    'PIL',
    'cv2',
    'torch',
    'tensorflow',
]

block_cipher = None

a = Analysis(
    [str(main_script)],
    pathex=[str(src_path)],
    binaries=[],
    datas=datas,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# Remove duplicates and optimize
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='spectrum_weaver',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # Set to True for debugging
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(project_root / "images" / "icon.ico"),
    version=None,
)
