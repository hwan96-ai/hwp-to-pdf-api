import win32com.client
import sys
import os
import winreg

def register_dll():
    """DLL 명시적 등록"""
    try:
        reg_path = r"Software\HNC\HwpCtrl\Modules"
        dll_path = r"C:\hwp-api\scripts\FilePathCheckerModule.dll"
        
        key = winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, reg_path)
        winreg.SetValueEx(key, "FilePathCheckerModule", 0, winreg.REG_SZ, dll_path)
        winreg.CloseKey(key)
    except:
        pass

def convert_hwp_to_pdf(input_file, output_file):
    """HWP/HWPX/HWT/HWTZ를 PDF로 변환"""
    try:
        register_dll()
        
        if not os.path.exists(input_file):
            return False
        
        hwp = win32com.client.gencache.EnsureDispatch("HWPFrame.HwpObject")
        
        try:
            hwp.RegisterModule("FilePathCheckDLL", "FilePathCheckerModule")
        except:
            pass
        
        hwp.Open(str(input_file), "")
        
        hwp.HParameterSet.HFileOpenSave.filename = output_file
        hwp.HParameterSet.HFileOpenSave.Format = "PDF"
        hwp.HAction.Execute("FileSaveAs_S", hwp.HParameterSet.HFileOpenSave.HSet)
        
        hwp.Quit()
        return True
    
    except Exception as e:
        return False

if __name__ == "__main__":
    if len(sys.argv) < 3:
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    
    success = convert_hwp_to_pdf(input_file, output_file)
    sys.exit(0 if success else 1)