import subprocess
from pathlib import Path

def jpegtran_lossless_rotate(filepath: Path, degrees: int) -> bool:
    """Rotate a JPEG file losslessly using jpegtran. Returns True if successful."""
    assert degrees in (90, 180, 270), "Only 90, 180, 270 degrees supported"
    tmp_path = filepath.with_suffix('.rotating_tmp.jpg')
    try:
        result = subprocess.run([
            'jpegtran', f'-rotate', str(degrees), '-copy', 'all', '-outfile', str(tmp_path), str(filepath)
        ], capture_output=True)
        if result.returncode == 0 and tmp_path.exists():
            tmp_path.replace(filepath)
            return True
        else:
            print(f"jpegtran failed: {result.stderr.decode()}")
            if tmp_path.exists():
                tmp_path.unlink()
            return False
    except Exception as e:
        print(f"jpegtran exception: {e}")
        if tmp_path.exists():
            tmp_path.unlink()
        return False
