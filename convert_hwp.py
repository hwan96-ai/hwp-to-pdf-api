import win32com.client
import sys
import os
import winreg
from pathlib import Path

from worker_runtime import COM_CLEANUP_UNCERTAIN_EXIT_CODE


class HancomCleanupError(RuntimeError):
    """The COM object was created, but its termination could not be confirmed."""


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
    """HWP/HWPX/HWT/HWTX를 PDF로 변환; always close the automation object."""
    hwp = None
    try:
        register_dll()
        
        if not os.path.exists(input_file):
            print(f"[ERROR] File not found: {input_file}")  # 이모지 제거
            return False
        
        hwp = win32com.client.DispatchEx("HWPFrame.HwpObject")
        
        try:
            hwp.RegisterModule("FilePathCheckDLL", "FilePathCheckerModule")
            print("[OK] Security module registered")  # 이모지 제거
        except Exception as e:
            print(f"[WARNING] Security module registration failed: {e}")  # 이모지 제거
            pass
        
        if not hwp.Open(str(input_file), ""):
            raise RuntimeError("Hancom could not open the document")
        print(f"[OK] File opened: {input_file}")  # 이모지 제거
        
        hwp.HParameterSet.HFileOpenSave.filename = output_file
        hwp.HParameterSet.HFileOpenSave.Format = "PDF"
        if not hwp.HAction.Execute("FileSaveAs_S", hwp.HParameterSet.HFileOpenSave.HSet):
            raise RuntimeError("Hancom could not save the PDF")
        
        print(f"[OK] PDF saved: {output_file}")  # 이모지 제거
        return True
    
    except Exception as e:
        print(f"[ERROR] Conversion failed: {e}")  # 이모지 제거
        return False
    finally:
        if hwp is not None:
            try:
                hwp.Quit()
            except Exception as error:
                print("[WARNING] Hancom automation cleanup failed")
                raise HancomCleanupError("Hancom termination is uncertain") from error


def main(arguments=None):
    arguments = sys.argv[1:] if arguments is None else arguments
    if len(arguments) != 2:
        print("Usage: python convert_hwp.py <input_file> <output_file>")
        return 1
    
    input_file, output_file = arguments
    
    print("=" * 70)
    print("HWP to PDF Conversion Started")
    print(f"Input: {input_file}")
    print(f"Output: {output_file}")
    print("=" * 70)
    
    try:
        success = convert_hwp_to_pdf(input_file, output_file)
    except HancomCleanupError:
        return COM_CLEANUP_UNCERTAIN_EXIT_CODE
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
