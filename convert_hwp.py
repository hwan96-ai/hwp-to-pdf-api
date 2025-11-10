import win32com.client
import sys
import os
import winreg
from pathlib import Path


def register_dll():
    """DLL 명시적 등록 - 동적 경로 사용"""
    try:
        # 현재 스크립트의 디렉터리 가져오기
        current_dir = Path(__file__).parent.resolve()
        
        # scripts 폴더의 DLL 경로 구성
        dll_path = current_dir / "scripts" / "FilePathCheckerModule.dll"
        
        # 레지스트리 경로
        reg_path = r"Software\HNC\HwpAutomation\Modules"
        
        # HKEY_CURRENT_USER 사용
        key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, reg_path)
        winreg.SetValueEx(key, "FilePathCheckerModule", 0, winreg.REG_SZ, str(dll_path))
        winreg.CloseKey(key)
        
        print(f"[OK] DLL registered: {dll_path}")  # 이모지 제거
    except Exception as e:
        print(f"[WARNING] DLL registration failed: {e}")  # 이모지 제거
        pass


def convert_hwp_to_pdf(input_file, output_file):
    """HWP/HWPX/HWT/HWTZ를 PDF로 변환"""
    try:
        register_dll()
        
        if not os.path.exists(input_file):
            print(f"[ERROR] File not found: {input_file}")  # 이모지 제거
            return False
        
        hwp = win32com.client.gencache.EnsureDispatch("HWPFrame.HwpObject")
        
        try:
            hwp.RegisterModule("FilePathCheckDLL", "FilePathCheckerModule")
            print("[OK] Security module registered")  # 이모지 제거
        except Exception as e:
            print(f"[WARNING] Security module registration failed: {e}")  # 이모지 제거
            pass
        
        hwp.Open(str(input_file), "")
        print(f"[OK] File opened: {input_file}")  # 이모지 제거
        
        hwp.HParameterSet.HFileOpenSave.filename = output_file
        hwp.HParameterSet.HFileOpenSave.Format = "PDF"
        hwp.HAction.Execute("FileSaveAs_S", hwp.HParameterSet.HFileOpenSave.HSet)
        
        hwp.Quit()
        print(f"[OK] PDF saved: {output_file}")  # 이모지 제거
        return True
    
    except Exception as e:
        print(f"[ERROR] Conversion failed: {e}")  # 이모지 제거
        return False


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python convert_hwp.py <input_file> <output_file>")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    
    print("=" * 70)
    print("HWP to PDF Conversion Started")
    print(f"Input: {input_file}")
    print(f"Output: {output_file}")
    print("=" * 70)
    
    success = convert_hwp_to_pdf(input_file, output_file)
    sys.exit(0 if success else 1)
