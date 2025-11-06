import win32com.client
import sys
import os
import winreg

def convert_hwp_to_pdf(input_file, output_file):
    """HWP to PDF with popup suppression"""
    
    try:
        # 레지스트리 설정 (강제)
        reg_path = r"Software\HNC\HwpCtrl\Modules"
        script_dir = os.path.dirname(os.path.abspath(__file__))
        dll_path = os.path.join(script_dir, "FilePathCheckerModule.dll")
        
        try:
            key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, reg_path)
            winreg.SetValueEx(key, "FilePathCheckerModule", 0, winreg.REG_SZ, dll_path)
            winreg.CloseKey(key)
        except:
            pass
        
        if not os.path.exists(input_file):
            return False
        
        # 한컴 오피스 실행
        hwp = win32com.client.gencache.EnsureDispatch("HWPFrame.HwpObject")
        
        # 보안 모듈 등록
        try:
            hwp.RegisterModule("FilePathCheckDLL", "FilePathCheckerModule")
        except:
            pass
        
        # 파일 열기
        hwp.Open(str(input_file), "")
        
        # PDF 저장
        hwp.HParameterSet.HFileOpenSave.filename = output_file
        hwp.HParameterSet.HFileOpenSave.Format = "PDF"
        hwp.HAction.Execute("FileSaveAs_S", hwp.HParameterSet.HFileOpenSave.HSet)
        
        # 종료
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
