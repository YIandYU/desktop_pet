"""
硬件实时监测模块

通过 psutil 库采集系统硬件数据，包括 CPU、内存、磁盘、
GPU、网络、系统信息、电池、风扇和温度。
后台线程每 2 秒自动采集一次，面板关闭时停止。
"""
import sys
import psutil
import platform
import time
import threading


class HardwareMonitor:
    """硬件监测器 - 后台线程采集数据"""

    def __init__(self):
        self.data = {}             # 最新采集的数据缓存
        self.last_net_io = None    # 上次网络 IO 计数（用于计算网速）
        self.last_net_time = None  # 上次网络采集时间
        self._lock = threading.Lock()   # 线程锁，保证数据安全
        self._running = False       # 采集线程是否运行
        self._thread = None         # 后台采集线程

    def start(self):
        """启动后台采集线程"""
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._collect_loop, daemon=True)
        self._thread.start()

    def stop(self):
        """停止采集线程"""
        self._running = False

    def _collect_loop(self):
        """后台循环采集，每 1 秒执行一次"""
        while self._running:
            self._collect_once()
            time.sleep(1)

    def _collect_once(self):
        """执行一次完整的数据采集"""
        data = {}

        # ===== CPU 信息 =====
        data['cpu_percent'] = psutil.cpu_percent(interval=None)    # CPU 总使用率
        data['cpu_count'] = psutil.cpu_count(logical=True)         # 逻辑核心数（含超线程）
        data['cpu_phys'] = psutil.cpu_count(logical=False) or 'N/A' # 物理核心数
        data['cpu_per_core'] = psutil.cpu_percent(interval=None, percpu=True)  # 每核使用率

        # ===== 内存信息 =====
        mem = psutil.virtual_memory()
        data['mem_percent'] = mem.percent          # 内存使用率
        data['mem_used'] = mem.used / (1024 ** 3)  # 已用内存 (GB)
        data['mem_total'] = mem.total / (1024 ** 3) # 总内存 (GB)

        # ===== 磁盘信息 =====
        disk_parts = []
        for part in psutil.disk_partitions():
            try:
                usage = psutil.disk_usage(part.mountpoint)
                disk_parts.append({
                    'device': part.device,          # 设备名（如 C:）
                    'mount': part.mountpoint,       # 挂载点
                    'percent': usage.percent,        # 使用率
                    'total': usage.total / (1024 ** 3),  # 总容量 (GB)
                    'used': usage.used / (1024 ** 3),    # 已用 (GB)
                    'free': usage.free / (1024 ** 3),    # 可用 (GB)
                })
            except (PermissionError, OSError):
                pass  # 跳过无法访问的分区
        data['disk'] = disk_parts

        # ===== GPU 信息（通过 nvidia-smi 获取）=====
        data['gpu'] = self._get_gpu_info()

        # ===== 网络流量 =====
        net = psutil.net_io_counters()
        ct = time.time()
        if self.last_net_io is not None and self.last_net_time is not None:
            elapsed = ct - self.last_net_time
            if elapsed > 0:
                # 计算网速：KB/s
                data['net_sent'] = (net.bytes_sent - self.last_net_io.bytes_sent) / elapsed / 1024
                data['net_recv'] = (net.bytes_recv - self.last_net_io.bytes_recv) / elapsed / 1024
            else:
                data['net_sent'] = data['net_recv'] = 0
        else:
            data['net_sent'] = data['net_recv'] = 0
        self.last_net_io = net
        self.last_net_time = ct

        # ===== 系统信息 =====
        data['os'] = platform.system() + ' ' + platform.release()  # 操作系统名称+版本
        data['boot_time'] = time.time() - psutil.boot_time()       # 系统已运行时长（秒）

        # ===== 电池信息 =====
        try:
            batt = psutil.sensors_battery()
            if batt:
                data['battery_percent'] = batt.percent         # 电池电量
                data['battery_power_plugged'] = batt.power_plugged  # 是否在充电
            else:
                data['battery_percent'] = data['battery_power_plugged'] = None
        except Exception:
            data['battery_percent'] = data['battery_power_plugged'] = None

        # ===== 风扇转速 =====
        fan_data = {}
        # 1. 尝试 psutil（Linux）
        try:
            fans = psutil.sensors_fans()
            for name, entries in fans.items():
                for entry in entries:
                    fan_data[f'CPU/{name}'] = f'{entry.current} RPM'
        except Exception:
            pass
        # 2. Windows 下用 WMI 获取 CPU 风扇
        if sys.platform == 'win32':
            try:
                import subprocess
                # Win32_Fan - CPU/机箱风扇
                res = subprocess.run(
                    ['wmic', 'path', 'Win32_Fan', 'get', 'Name,DesiredSpeed',
                     '/format:csv'],
                    capture_output=True, text=True, timeout=3
                )
                if res.returncode == 0:
                    for line in res.stdout.strip().split(chr(10)):
                        if not line or line.startswith('Node'):
                            continue
                        cols = line.split(',')
                        if len(cols) >= 3:
                            fname = cols[1].strip()
                            speed = cols[2].strip()
                            if speed and speed.isdigit() and int(speed) > 0:
                                fan_data[fname or 'CPU_Fan'] = f'{speed} RPM'
            except Exception:
                pass
        # 3. 合并 GPU 风扇数据（已在 _get_gpu_info 中采集）
        gpu_data = data.get('gpu')
        if gpu_data and gpu_data.get('gpus'):
            for i, g in enumerate(gpu_data['gpus']):
                if g.get('fan_speed'):
                    name = g.get('name', f'GPU{i}')
                    for prefix in ['NVIDIA GeForce ', 'NVIDIA ', 'AMD Radeon ', 'Intel Arc ', 'Intel ']:
                        if name.startswith(prefix):
                            name = name[len(prefix):]
                            break
                    fan_data[f'GPU_{name}'] = f'{g["fan_speed"]}%'

        data['fans'] = fan_data if fan_data else None

        # ===== 温度传感器 =====
        try:
            temps = psutil.sensors_temperatures()
            tdata = {}
            for name, entries in temps.items():
                for entry in entries:
                    tdata[name] = entry.current  # 温度 (摄氏度)
            data['temperatures'] = tdata if tdata else None
        except Exception:
            data['temperatures'] = None

        # 线程安全地更新数据缓存
        with self._lock:
            self.data = data

    def _get_gpu_info(self):
        """
        获取独立显卡信息

        优先使用 nvidia-smi 查 NVIDIA 显卡（含使用率和显存），
        如果没有则通过 Windows WMI 获取独立显卡名称。
        返回: {"gpus": [{"name": 名称, "util": 使用率or"N/A"}]}
        """
        info = {}
        gpus = []

        # 1. 尝试 nvidia-smi（获取 NVIDIA 使用率和显存）
        try:
            import subprocess
            res = subprocess.run(
                ['nvidia-smi', '--query-gpu=index,name,utilization.gpu,memory.used,memory.total,fan.speed',
                 '--format=csv,noheader,nounits'],
                capture_output=True, text=True, timeout=2
            )
            if res.returncode == 0 and res.stdout.strip():
                for line in res.stdout.strip().split(chr(10)):
                    parts = line.split(', ')
                    if len(parts) >= 5:
                        fan_speed = parts[5].strip() if len(parts) >= 6 and parts[5].strip() else ''
                        fan_speed = fan_speed if fan_speed and fan_speed != '[N/A]' else None
                        gpus.append({
                            'id': parts[0],
                            'name': parts[1],
                            'util': parts[2],
                            'mem_used': parts[3],
                            'mem_total': parts[4],
                            'fan_speed': fan_speed,
                        })
        except Exception:
            pass

        # 2. 如果 nvidia-smi 没找到，用 Windows WMI 获取独立显卡信息
        if not gpus and sys.platform == 'win32':
            try:
                import subprocess
                # 用 WMIC 获取显卡信息
                res = subprocess.run(
                    ['wmic', 'path', 'win32_VideoController', 'get', 'name,adapterram',
                     '/format:csv'],
                    capture_output=True, text=True, timeout=3
                )
                if res.returncode == 0 and res.stdout.strip():
                    for line in res.stdout.strip().split(chr(10)):
                        if not line or line.startswith('Node'):
                            continue
                        parts = line.split(',')
                        if len(parts) >= 3:
                            name = parts[1].strip()
                            if name and any(kw in name.upper() for kw in
                                            ['NVIDIA', 'AMD', 'RTX', 'GTX', 'RX',
                                             'RADEON', 'INTEL', 'ARC',
                                             'DISCRETE', '独立']):
                                gpus.append({
                                    'name': name,
                                    'util': 'N/A',
                                    'mem_used': 0,
                                    'mem_total': 0,
                                })
            except Exception:
                pass

        if gpus:
            info['gpus'] = gpus
        return info if info else None

    def get_data(self):
        """线程安全地获取最新采集数据"""
        with self._lock:
            return dict(self.data)

    def format_boot_time(self, seconds):
        """将秒数格式化为 天数+小时+分钟 的可读格式"""
        days = int(seconds // 86400)
        hours = int((seconds % 86400) // 3600)
        mins = int((seconds % 3600) // 60)
        if days > 0:
            return f'{days}d {hours}h {mins}m'
        elif hours > 0:
            return f'{hours}h {mins}m'
        else:
            return f'{mins}m'

    def get_display_data(self):
        """
        获取适合在监测面板中显示的格式化数据

        返回字符串列表，每行一条数据
        CPU 和内存使用率 >80% 显示红色，>50% 显示黄色，<50% 显示绿色
        """
        data = self.get_data()
        if not data:
            return ['[采集数据中...]']

        lines = []
        lines.append('=== HARDWARE MONITOR ===')

        # 系统与运行时间
        lines.append(f'SYS: {data.get("os", "Unknown")}')
        lines.append(f'UPTIME: {self.format_boot_time(data.get("boot_time", 0))}')

        # 电池
        batt = data.get('battery_percent')
        if batt is not None:
            plugged = data.get('battery_power_plugged')
            status = 'CHARGING' if plugged else 'BATTERY'
            lines.append(f'BATT: {batt}% {status}')

        # CPU
        cpu = f'CPU: {data.get("cpu_percent", "N/A")}% ({data.get("cpu_phys", "?")}c{data.get("cpu_count", "?")}t)'
        lines.append(cpu)

        # GPU
        gpu = data.get('gpu')
        if gpu and gpu.get('gpus'):
            for g in gpu['gpus']:
                name = g.get('name', f'GPU')
                util = g.get('util', 'N/A')
                if util != 'N/A' and float(util) >= 0:
                    try:
                        mem_used = float(g.get('mem_used', 0))
                        mem_total = float(g.get('mem_total', 0))
                        for prefix in ['NVIDIA GeForce ', 'NVIDIA ', 'AMD Radeon ', 'Intel Arc ', 'Intel ']:
                            if name.startswith(prefix):
                                name = name[len(prefix):]
                                break
                        fan_text = f" FAN:{g.get('fan_speed')}%" if g.get('fan_speed') else ''
                        lines.append(f'{name}: {util}% VRAM:{mem_used:.0f}/{mem_total:.0f}MB{fan_text}')
                    except (ValueError, TypeError):
                        for prefix in ['NVIDIA GeForce ', 'NVIDIA ', 'AMD Radeon ', 'Intel Arc ', 'Intel ']:
                            if name.startswith(prefix):
                                name = name[len(prefix):]
                                break
                        lines.append(f'{name}')
                else:
                    # 去掉 NVIDIA GeForce / AMD Radeon 等前缀，只留型号
                    short_name = name.split('(')[0].strip()
                    for prefix in ['NVIDIA GeForce ', 'NVIDIA ', 'AMD Radeon ', 'Intel Arc ', 'Intel ']:
                        if short_name.startswith(prefix):
                            short_name = short_name[len(prefix):]
                            break
                    short_name = short_name[:30]
                    lines.append(f'GPU: {short_name}')

        # 内存
        lines.append(f'MEM: {data.get("mem_percent", 0)}% ({data.get("mem_used", 0):.1f}/{data.get("mem_total", 0):.1f}GB)')

        # 磁盘（显示所有盘符）
        disks = data.get('disk', [])
        if disks:
            for m in disks:
                label = m['device']
                lines.append(f'{label} {m["percent"]}% ({m["used"]:.0f}/{m["total"]:.0f}GB)')

        # 网络速度
        lines.append(f'NET: {data.get("net_sent", 0):.1f}/{data.get("net_recv", 0):.1f} KB/s')

        # 风扇
        fans = data.get('fans')
        if fans:
            for name, val in fans.items():
                lines.append(f'FAN[{name}]: {val}')


        return lines
