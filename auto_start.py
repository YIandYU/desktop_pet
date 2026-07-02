"""
开机自启动管理模块

Windows 下通过注册表 HKCU\Run 实现开机自启动（更可靠），
VBScript 启动文件夹快捷方式作为备用方案。
"""
import os
import sys
import subprocess


def _get_reg_key_path():
    """获取注册表启动项名称"""
    return "DesktopPet"


def _get_startup_folder():
    """获取 Windows 启动文件夹路径"""
    try:
        import ctypes
        buf = ctypes.create_unicode_buffer(260)
        ctypes.windll.shell32.SHGetFolderPathW(None, 0x0007, None, 0, buf)
        return buf.value
    except Exception:
        return None


def is_auto_start_enabled():
    """检查开机自启动是否已启用（读取注册表和启动文件夹）"""
    # 检查注册表
    try:
        import winreg
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                             r"Software\Microsoft\Windows\CurrentVersion\Run",
                             0, winreg.KEY_READ)
        try:
            winreg.QueryValueEx(key, _get_reg_key_path())
            winreg.CloseKey(key)
            return True
        except FileNotFoundError:
            winreg.CloseKey(key)
    except Exception:
        pass

    # 检查启动文件夹快捷方式
    path = get_startup_shortcut_path()
    if path and os.path.exists(path):
        return True
    return False


def get_startup_shortcut_path():
    """获取启动文件夹中的快捷方式路径"""
    startup_dir = _get_startup_folder()
    if startup_dir:
        return os.path.join(startup_dir, "\u684c\u9762\u5ba0\u7269.lnk")
    return None


def enable_auto_start():
    """启用开机自启动"""
    # 指向 main.pyw 实现无窗口启动
    base_dir = os.path.dirname(os.path.abspath(__file__))
    script_path = os.path.join(base_dir, "main.pyw")
    # 优先用 pythonw.exe，找不到就用 python.exe
    for candidate in ["pythonw.exe", "python.exe"]:
        python_exe = sys.executable.replace("python.exe", candidate)
        if os.path.exists(python_exe):
            break
    else:
        python_exe = sys.executable

    # 方法1：注册表方式（推荐）
    try:
        import winreg
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                             r"Software\Microsoft\Windows\CurrentVersion\Run",
                             0, winreg.KEY_SET_VALUE)
        winreg.SetValueEx(key, _get_reg_key_path(), 0, winreg.REG_SZ,
                          python_exe + " " + script_path)
        winreg.CloseKey(key)
        return True
    except Exception:
        pass

    # 方法2：VBScript 创建启动文件夹快捷方式（备用）
    try:
        startup_path = get_startup_shortcut_path()
        if startup_path:
            vbs_code = (
                'Set ws = CreateObject("Wscript.Shell")\n'
                'Set sc = ws.CreateShortcut("' + startup_path + '")\n'
                'sc.TargetPath = "' + python_exe + '"\n'
                'sc.Arguments = "' + script_path + '"\n'
                'sc.WorkingDirectory = "' + os.path.dirname(script_path) + '"\n'
                'sc.Description = "\u684c\u9762\u5ba0\u7269"\n'
                'sc.WindowStyle = 6\n'
                'sc.Save()'
            )
            vbs_file = os.path.join(os.path.dirname(startup_path), "_create_startup.vbs")
            with open(vbs_file, "w", encoding="utf-8") as f:
                f.write(vbs_code)
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            subprocess.run(['cscript.exe', vbs_file, '//nologo'],
                           capture_output=True, text=True, timeout=10,
                           startupinfo=startupinfo)
            try:
                os.remove(vbs_file)
            except:
                pass
            return os.path.exists(startup_path)
    except Exception:
        pass

    return False


def disable_auto_start():
    """禁用开机自启动"""
    # 删除注册表项
    try:
        import winreg
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                             r"Software\Microsoft\Windows\CurrentVersion\Run",
                             0, winreg.KEY_SET_VALUE)
        try:
            winreg.DeleteValue(key, _get_reg_key_path())
        except FileNotFoundError:
            pass
        winreg.CloseKey(key)
    except Exception:
        pass

    # 删除启动文件夹快捷方式
    path = get_startup_shortcut_path()
    if path and os.path.exists(path):
        try:
            os.remove(path)
        except Exception:
            pass

    return not is_auto_start_enabled()


def toggle_auto_start():
    """切换开机自启动状态，返回新状态"""
    if is_auto_start_enabled():
        disable_auto_start()
        return False
    else:
        enable_auto_start()
        return True
