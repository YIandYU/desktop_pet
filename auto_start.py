"""
开机自启动管理模块

Windows 下通过在「启动」文件夹中创建快捷方式实现开机自启动。
支持启用/禁用/检查状态。
"""
import os
import sys


def get_startup_shortcut_path():
    """获取启动文件夹中的快捷方式路径"""
    startup_dir = _get_startup_folder()
    if startup_dir:
        return os.path.join(startup_dir, "桌面宠物.lnk")
    return None


def _get_startup_folder():
    """获取 Windows 当前用户的启动文件夹路径"""
    try:
        import ctypes
        CSIDL_STARTUP = 0x0007
        buf = ctypes.create_unicode_buffer(260)
        ctypes.windll.shell32.SHGetFolderPathW(None, CSIDL_STARTUP, None, 0, buf)
        return buf.value
    except Exception:
        return None


def is_auto_start_enabled():
    """检查开机自启动是否已启用"""
    path = get_startup_shortcut_path()
    if path:
        return os.path.exists(path)
    return False


def enable_auto_start():
    """启用开机自启动"""
    startup_path = get_startup_shortcut_path()
    if not startup_path:
        return False

    script_path = os.path.abspath(sys.argv[0])
    python_exe = sys.executable

    # 使用 VBScript 创建快捷方式（无需额外依赖）
    vbs_code = (
        'Set ws = CreateObject("Wscript.Shell")\n'
        'Set sc = ws.CreateShortcut("' + startup_path.replace("\\", "\\\\") + '")\n'
        'sc.TargetPath = "' + python_exe.replace("\\", "\\\\") + '"\n'
        'sc.Arguments = "' + script_path.replace("\\", "\\\\") + '"\n'
        'sc.WorkingDirectory = "' + os.path.dirname(script_path).replace("\\", "\\\\") + '"\n'
        'sc.Description = "桌面宠物"\n'
        'sc.WindowStyle = 6\n'
        'sc.Save()\n'
    )

    vbs_file = os.path.join(os.path.dirname(startup_path), "_create_startup.vbs")
    try:
        with open(vbs_file, "w", encoding="utf-8") as f:
            f.write(vbs_code)
        os.system('cscript.exe "' + vbs_file + '" //nologo')
        os.remove(vbs_file)
        return os.path.exists(startup_path)
    except Exception:
        return False


def disable_auto_start():
    """禁用开机自启动"""
    path = get_startup_shortcut_path()
    if path and os.path.exists(path):
        try:
            os.remove(path)
            return True
        except Exception:
            return False
    return True


def toggle_auto_start():
    """切换开机自启动状态，返回新状态"""
    if is_auto_start_enabled():
        disable_auto_start()
        return False
    else:
        enable_auto_start()
        return True
