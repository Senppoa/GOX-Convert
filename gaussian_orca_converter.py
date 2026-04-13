# -*- coding: utf-8 -*-
"""
Gaussian和ORCA文件格式转换工具
支持Gaussian (log, gjf), ORCA (inp) 和 xyz 文件之间的相互转换

@Author: 整合自多个脚本
@Date: 2025-10-20
"""

import os
import glob
import shutil
from typing import List, Optional, Tuple, Dict
from tqdm import tqdm
from natsort import ns, natsorted


class GaussianConverter:
    """
    Gaussian和ORCA文件格式转换器
    支持log、gjf、xyz、inp格式之间的相互转换
    """
    
    # 原子序数到元素符号的映射
    ATOM_SYMBOL_MAP = {
        '1': 'H', '2': 'He',
        '3': 'Li', '4': 'Be', '5': 'B', '6': 'C', '7': 'N', '8': 'O', '9': 'F', '10': 'Ne',
        '11': 'Na', '12': 'Mg', '13': 'Al', '14': 'Si', '15': 'P', '16': 'S', '17': 'Cl', '18': 'Ar',
        '19': 'K', '20': 'Ca', 
        '26': 'Fe', '27': 'Co', '28': 'Ni', '29': 'Cu', '30': 'Zn',
        '35': 'Br', '40': 'Zr', '45': 'Rh', '46': 'Pd', '47': 'Ag',
        '53': 'I', '77': 'Ir', '78': 'Pt', '79': 'Au'
    }
    
    def __init__(self, input_path: str, output_path: str = None):
        """
        初始化转换器
        
        :param input_path: 输入文件或文件夹路径
        :param output_path: 输出文件夹路径，如果为None则自动创建
        """
        self.input_path = input_path
        self.output_path = output_path or os.path.join(os.path.dirname(input_path) or '.', 'converted_files')
        
        # 确保输出目录存在
        os.makedirs(self.output_path, exist_ok=True)
    
    def _read_log_file(self, log_file: str) -> Tuple[bool, List[str]]:
        """
        读取log文件内容
        
        :param log_file: log文件路径
        :return: (是否正常终止, 文件内容行列表)
        """
        try:
            with open(log_file, 'r', encoding='UTF8') as f:
                lines = f.readlines()
            
            # 检查是否正常终止
            is_normal = False
            if lines and len(lines[-1]) > 19:
                is_normal = (lines[-1][1:19] == 'Normal termination')
            
            return is_normal, lines
        except Exception as e:
            print(f"Error reading {log_file}: {e}")
            return False, []
    
    def _extract_standard_orientation(self, lines: List[str]) -> Tuple[str, int, int]:
        """
        从log文件中提取标准坐标
        
        :param lines: log文件内容行列表
        :return: (电荷和自旋多重度字符串, 坐标起始行, 坐标结束行)
        """
        charge_mult = ''
        stl, enl = -1, -1
        
        # 提取电荷和自旋多重度
        for i, line in enumerate(lines):
            if 'Charge' in line and 'Multiplicity' in line:
                a = line[11:13].strip()
                b = line[27:].strip()
                charge_mult = f"{a}  {b}"
                break
        
        # 从后向前查找标准坐标
        for i in range(len(lines) - 1, -1, -1):
            if 'Standard orientation:' in lines[i] or 'Standard orientation' in lines[i]:
                stl = i + 5
                flag = stl
                while flag < len(lines) and len(lines[flag].split()) == 6:
                    flag += 1
                enl = flag - 1
                break
        
        return charge_mult, stl, enl
    
    def _lines_to_xyz_format(self, lines: List[str], stl: int, enl: int, title: str = '') -> str:
        """
        将坐标行转换为xyz格式
        
        :param lines: 文件行列表
        :param stl: 起始行
        :param enl: 结束行
        :param title: xyz文件标题
        :return: xyz格式字符串
        """
        if stl < 0 or enl < 0:
            return ''
        
        num_atoms = enl - stl + 1
        xyz_content = f"{num_atoms}\n{title}\n"
        
        try:
            for i in range(stl, enl + 1):
                atom_num = lines[i][15:20].strip()
                symbol = self.ATOM_SYMBOL_MAP.get(atom_num, atom_num)
                coords = lines[i][36:].strip()
                xyz_content += f"{symbol}   {coords}\n"
        except Exception as e:
            print(f"Error converting coordinates: {e}")
            return ''
        
        return xyz_content
    
    def log_to_xyz(self, check_termination: bool = True, 
                   save_success_list: bool = True) -> Tuple[int, List[str], List[str]]:
        """
        将log文件转换为xyz文件
        
        :param check_termination: 是否检查正常终止
        :param save_success_list: 是否保存成功和失败文件列表
        :return: (成功数量, 成功文件列表, 失败文件列表)
        """
        success_files = []
        error_files = []
        
        # 获取所有log文件
        if os.path.isfile(self.input_path):
            log_files = [self.input_path]
        else:
            log_files = glob.glob(os.path.join(self.input_path, '*.log'))
            log_files = natsorted(log_files, alg=ns.PATH)
        
        if not log_files:
            print("No log files found!")
            return 0, [], []
        
        print(f"Found {len(log_files)} log file(s)")
        
        # 转换每个log文件
        for log_file in tqdm(log_files, desc="Converting log to xyz"):
            is_normal, lines = self._read_log_file(log_file)
            filename = os.path.basename(log_file)
            
            # 检查是否需要验证正常终止
            if check_termination and not is_normal:
                error_files.append(filename)
                continue
            
            # 提取坐标
            charge_mult, stl, enl = self._extract_standard_orientation(lines)
            
            if stl < 0 or enl < 0:
                error_files.append(filename)
                continue
            
            # 转换为xyz格式
            xyz_content = self._lines_to_xyz_format(lines, stl, enl, filename.replace('.log', ''))
            
            if xyz_content:
                output_file = os.path.join(self.output_path, filename.replace('.log', '.xyz'))
                with open(output_file, 'w') as f:
                    f.write(xyz_content)
                success_files.append(filename)
            else:
                error_files.append(filename)
        
        # 保存成功和失败文件列表
        if save_success_list:
            with open(os.path.join(self.output_path, 'success_files.txt'), 'w') as f:
                f.write('\n'.join(success_files))
            
            with open(os.path.join(self.output_path, 'error_files.txt'), 'w') as f:
                f.write('\n'.join(error_files))
        
        print(f"\nConversion complete!")
        print(f"Success: {len(success_files)}, Failed: {len(error_files)}")
        print(f"Output directory: {self.output_path}")
        
        return len(success_files), success_files, error_files
    
    def log_to_gjf(self, nproc: str = '32', mem: str = '64GB',
                   method: str = 'b3lyp', basis: str = 'def2svp',
                   extra_keywords: str = 'opt freq',
                   link1_method: str = '', link1_basis: str = '',
                   charge: int = 0, mult: int = 1,
                   nosave: bool = False) -> int:
        """
        将log文件转换为gjf文件
        
        :param nproc: 处理器核心数
        :param mem: 内存大小
        :param method: 计算方法
        :param basis: 基组
        :param extra_keywords: 额外关键词
        :param link1_method: Link1的计算方法（如果需要）
        :param link1_basis: Link1的基组
        :param charge: 电荷（如果指定则覆盖log中的值）
        :param mult: 自旋多重度（如果指定则覆盖log中的值）
        :param nosave: 是否添加nosave关键词
        :return: 成功转换的文件数
        """
        # 获取所有log文件
        if os.path.isfile(self.input_path):
            log_files = [self.input_path]
        else:
            log_files = glob.glob(os.path.join(self.input_path, '*.log')) or glob.glob(os.path.join(self.input_path, '*.out'))
            log_files = natsorted(log_files, alg=ns.PATH)
        
        if not log_files:
            print("No log files found!")
            return 0
        
        success_count = 0
        print(f"Found {len(log_files)} log file(s)")
        
        for log_file in tqdm(log_files, desc="Converting log to gjf"):
            is_normal, lines = self._read_log_file(log_file)
            filename = os.path.basename(log_file)
            name = filename.replace('.log', '')
            
            # 提取坐标和电荷信息
            charge_mult_str, stl, enl = self._extract_standard_orientation(lines)
            
            if stl < 0 or enl < 0:
                print(f"Warning: Could not extract coordinates from {filename}")
                continue
            
            # 使用log文件中的电荷和多重度（如果未指定）
            if charge_mult_str:
                parts = charge_mult_str.split()
                if len(parts) >= 2 and charge == 0 and mult == 1:
                    try:
                        charge = int(parts[0])
                        mult = int(parts[1])
                    except:
                        pass
            
            # 构建坐标部分
            coord_section = f"{charge}  {mult}\n"
            for i in range(stl, enl + 1):
                atom_num = lines[i][14:20].strip()
                coords = lines[i][36:].strip()
                coord_section += f"{atom_num}    {coords}\n"
            
            # 构建gjf文件内容
            gjf_content = f"%nprocshared={nproc}\n"
            if mem:
                gjf_content += f"%mem={mem}\n"
            gjf_content += f"%chk={name}.chk\n"
            if nosave and link1_method == '':
                gjf_content += "%nosave\n"
            
            # 添加计算关键词
            if basis == '':
                gjf_content += f"# {method} {extra_keywords}\n\n"
            else:
                gjf_content += f"# {method} {basis} {extra_keywords}\n\n"
            gjf_content += f"{name}\n\n"
            gjf_content += coord_section + "\n"
            
            # 如果有Link1部分
            if link1_method:
                gjf_content += "--Link1--\n"
                gjf_content += f"%nprocshared={nproc}\n"
                if mem:
                    gjf_content += f"%mem={mem}\n"
                gjf_content += f"%chk={name}.chk\n"
                if nosave:
                    gjf_content += "%nosave\n"
                
                basis_str = f"/{link1_basis}" if link1_basis else ""
                gjf_content += f"# {link1_method}{basis_str} geom=allcheck\n\n"
            
            # 保存gjf文件
            output_file = os.path.join(self.output_path, f"{name}.gjf")
            with open(output_file, 'w') as f:
                f.write(gjf_content)
            
            success_count += 1
        
        print(f"\nConversion complete! {success_count} files converted.")
        print(f"Output directory: {self.output_path}")
        
        return success_count
    
    def xyz_to_gjf(self, nproc: str = '32', mem: str = '64GB',
                   method: str = 'b3lyp', basis: str = 'def2svp',
                   extra_keywords: str = 'opt freq',
                   charge: int = 0, mult: int = 1,
                   link1_method: str = '',
                   nosave: bool = False) -> int:
        """
        将xyz文件转换为gjf文件
        
        :param nproc: 处理器核心数
        :param mem: 内存大小
        :param method: 计算方法
        :param basis: 基组
        :param extra_keywords: 额外关键词
        :param charge: 电荷
        :param mult: 自旋多重度
        :param link1_method: Link1的计算方法（如果需要）
        :param nosave: 是否添加nosave关键词
        :return: 成功转换的文件数
        """
        # 获取所有xyz文件
        if os.path.isfile(self.input_path):
            xyz_files = [self.input_path]
        else:
            xyz_files = glob.glob(os.path.join(self.input_path, '*.xyz'))
            xyz_files = natsorted(xyz_files, alg=ns.PATH)
        
        if not xyz_files:
            print("No xyz files found!")
            return 0
        
        success_count = 0
        print(f"Found {len(xyz_files)} xyz file(s)")
        
        for xyz_file in tqdm(xyz_files, desc="Converting xyz to gjf"):
            filename = os.path.basename(xyz_file)
            name = filename.replace('.xyz', '')
            
            try:
                with open(xyz_file, 'r') as f:
                    lines = f.readlines()
                
                # 读取xyz文件格式
                if len(lines) < 3:
                    print(f"Warning: {filename} format error")
                    continue
                
                num_atoms = int(lines[0].strip())
                title = lines[1].strip() or name
                
                # 提取坐标
                coord_section = f"{charge}  {mult}\n"
                for i in range(2, 2 + num_atoms):
                    if i < len(lines):
                        coord_section += lines[i]
                
                # 构建gjf文件内容
                gjf_content = f"%nprocshared={nproc}\n"
                if mem:
                    gjf_content += f"%mem={mem}\n"
                gjf_content += f"%chk={name}.chk\n"
                if nosave and link1_method == '':
                    gjf_content += "%nosave\n"
                
                if basis == '':
                    gjf_content += f"# {method} {extra_keywords}\n\n"
                else:
                    gjf_content += f"# {method}/{basis} {extra_keywords}\n\n"
                gjf_content += f"{title}\n\n"
                gjf_content += coord_section + "\n"

                # 如果有Link1部分
                if link1_method:
                    gjf_content += "--Link1--\n"
                    gjf_content += f"%nprocshared={nproc}\n"
                    if mem:
                        gjf_content += f"%mem={mem}\n"
                    gjf_content += f"%chk={name}.chk\n"
                    if nosave:
                        gjf_content += "%nosave\n"

                    gjf_content += f"# {link1_method} geom=allcheck\n\n"
                
                # 保存gjf文件
                output_file = os.path.join(self.output_path, f"{name}.gjf")
                with open(output_file, 'w') as f:
                    f.write(gjf_content)
                
                success_count += 1
                
            except Exception as e:
                print(f"Error converting {filename}: {e}")
        
        print(f"\nConversion complete! {success_count} files converted.")
        print(f"Output directory: {self.output_path}")
        
        return success_count
    
    def gjf_to_xyz(self) -> int:
        """
        将gjf文件转换为xyz文件
        
        :return: 成功转换的文件数
        """
        # 获取所有gjf文件
        if os.path.isfile(self.input_path):
            gjf_files = [self.input_path]
        else:
            gjf_files = glob.glob(os.path.join(self.input_path, '*.gjf'))
            gjf_files = natsorted(gjf_files, alg=ns.PATH)
        
        if not gjf_files:
            print("No gjf files found!")
            return 0
        
        success_count = 0
        print(f"Found {len(gjf_files)} gjf file(s)")
        
        for gjf_file in tqdm(gjf_files, desc="Converting gjf to xyz"):
            filename = os.path.basename(gjf_file)
            name = filename.replace('.gjf', '')
            
            try:
                with open(gjf_file, 'r') as f:
                    lines = f.readlines()
                
                # 查找坐标部分
                coord_start = -1
                for i, line in enumerate(lines):
                    # 跳过链接命令、资源分配和关键词行
                    if line.strip() and not line.startswith('%') and not line.startswith('#'):
                        # 找到标题行后的电荷和自旋行
                        if coord_start < 0:
                            # 检查是否是电荷自旋行
                            parts = line.strip().split()
                            if len(parts) == 2:
                                try:
                                    int(parts[0])
                                    int(parts[1])
                                    coord_start = i + 1
                                    break
                                except:
                                    continue
                
                if coord_start < 0:
                    print(f"Warning: Could not find coordinates in {filename}")
                    continue
                
                # 提取坐标
                coords = []
                for i in range(coord_start, len(lines)):
                    line = lines[i].strip()
                    if not line or line.startswith('--Link1--'):
                        break
                    parts = line.split()
                    if len(parts) >= 4:
                        coords.append(line)
                
                if not coords:
                    print(f"Warning: No coordinates found in {filename}")
                    continue
                
                # 写入xyz文件
                xyz_content = f"{len(coords)}\n{name}\n"
                xyz_content += '\n'.join(coords) + '\n'
                
                output_file = os.path.join(self.output_path, f"{name}.xyz")
                with open(output_file, 'w') as f:
                    f.write(xyz_content)
                
                success_count += 1
                
            except Exception as e:
                print(f"Error converting {filename}: {e}")
        
        print(f"\nConversion complete! {success_count} files converted.")
        print(f"Output directory: {self.output_path}")
        
        return success_count
    
    def _extract_gjf_coordinates(self, gjf_file: str) -> Tuple[List[str], int, int]:
        """
        从gjf文件中提取坐标信息
        
        :param gjf_file: gjf文件路径
        :return: (坐标行列表, 电荷, 多重度)
        """
        try:
            with open(gjf_file, 'r') as f:
                lines = f.readlines()
            
            # 查找坐标部分
            coord_start = -1
            charge, mult = 0, 1
            
            for i, line in enumerate(lines):
                if line.strip() and not line.startswith('%') and not line.startswith('#'):
                    if coord_start < 0:
                        # 检查是否是电荷自旋行
                        parts = line.strip().split()
                        if len(parts) == 2:
                            try:
                                charge = int(parts[0])
                                mult = int(parts[1])
                                coord_start = i + 1
                                break
                            except:
                                continue
            
            if coord_start < 0:
                return [], 0, 1
            
            # 提取坐标
            coords = []
            for i in range(coord_start, len(lines)):
                line = lines[i].strip()
                if not line or line.startswith('--Link1--'):
                    break
                parts = line.split()
                if len(parts) >= 4:
                    coords.append(line)
            
            return coords, charge, mult
            
        except Exception as e:
            print(f"Error extracting coordinates from {gjf_file}: {e}")
            return [], 0, 1
    
    def gjf_to_inp(self, job_type: str = "Opt NumFreq", 
                   functional: str = "wB97M-V", 
                   basis_set: str = "def2-TZVPD",
                   nproc: int = 32,
                   maxcore: int = 20000,
                   extra_keywords: str = "") -> int:
        """
        将Gaussian gjf文件转换为ORCA inp文件
        
        :param job_type: ORCA任务类型，如 "Opt NumFreq"
        :param functional: 泛函，如 "wB97M-V"
        :param basis_set: 基组，如 "def2-TZVPD"
        :param nproc: 处理器核心数
        :param maxcore: 每个核心的最大内存（MB）
        :param extra_keywords: 额外的ORCA关键词
        :return: 成功转换的文件数
        """
        # 获取所有gjf文件
        if os.path.isfile(self.input_path):
            gjf_files = [self.input_path]
        else:
            gjf_files = glob.glob(os.path.join(self.input_path, '*.gjf'))
            gjf_files = natsorted(gjf_files, alg=ns.PATH)
        
        if not gjf_files:
            print("No gjf files found!")
            return 0
        
        success_count = 0
        print(f"Found {len(gjf_files)} gjf file(s)")
        
        for gjf_file in tqdm(gjf_files, desc="Converting gjf to inp"):
            filename = os.path.basename(gjf_file)
            name = filename.replace('.gjf', '')
            
            try:
                coords, charge, mult = self._extract_gjf_coordinates(gjf_file)
                
                if not coords:
                    print(f"Warning: Could not extract coordinates from {filename}")
                    continue
                
                # 构建ORCA输入文件
                inp_content = f"! {job_type} {functional} {basis_set}"
                if extra_keywords:
                    inp_content += f" {extra_keywords}"
                inp_content += "\n\n"
                
                inp_content += f"%maxcore {maxcore}\n"
                inp_content += f"%pal nprocs {nproc} end\n\n"
                inp_content += f"* xyz {charge} {mult}\n"
                
                for coord in coords:
                    parts = coord.split()
                    element = parts[0]
                    x, y, z = parts[1], parts[2], parts[3]
                    inp_content += f" {element}                  {x}    {y}    {z}\n"
                
                inp_content += " *\n"
                
                # 保存inp文件
                output_file = os.path.join(self.output_path, f"{name}.inp")
                with open(output_file, 'w') as f:
                    f.write(inp_content)
                
                success_count += 1
                
            except Exception as e:
                print(f"Error converting {filename}: {e}")
        
        print(f"\nConversion complete! {success_count} files converted.")
        print(f"Output directory: {self.output_path}")
        
        return success_count
    
    def xyz_to_inp(self, job_type: str = "Opt NumFreq", 
                   functional: str = "wB97M-V", 
                   basis_set: str = "def2-TZVPD",
                   nproc: int = 32,
                   maxcore: int = 20000,
                   charge: int = 0,
                   mult: int = 1,
                   extra_keywords: str = "") -> int:
        """
        将xyz文件转换为ORCA inp文件
        
        :param job_type: ORCA任务类型
        :param functional: 泛函
        :param basis_set: 基组
        :param nproc: 处理器核心数
        :param maxcore: 每个核心的最大内存（MB）
        :param charge: 电荷
        :param mult: 自旋多重度
        :param extra_keywords: 额外的ORCA关键词
        :return: 成功转换的文件数
        """
        # 获取所有xyz文件
        if os.path.isfile(self.input_path):
            xyz_files = [self.input_path]
        else:
            xyz_files = glob.glob(os.path.join(self.input_path, '*.xyz'))
            xyz_files = natsorted(xyz_files, alg=ns.PATH)
        
        if not xyz_files:
            print("No xyz files found!")
            return 0
        
        success_count = 0
        print(f"Found {len(xyz_files)} xyz file(s)")
        
        for xyz_file in tqdm(xyz_files, desc="Converting xyz to inp"):
            filename = os.path.basename(xyz_file)
            name = filename.replace('.xyz', '')
            
            try:
                with open(xyz_file, 'r') as f:
                    lines = f.readlines()
                
                # 读取xyz文件格式
                if len(lines) < 3:
                    print(f"Warning: {filename} format error")
                    continue
                
                num_atoms = int(lines[0].strip())
                
                # 构建ORCA输入文件
                inp_content = f"! {job_type} {functional} {basis_set}"
                if extra_keywords:
                    inp_content += f" {extra_keywords}"
                inp_content += "\n\n"
                
                inp_content += f"%maxcore {maxcore}\n"
                inp_content += f"%pal nprocs {nproc} end\n\n"
                inp_content += f"* xyz {charge} {mult}\n"
                
                # 提取并格式化坐标
                for i in range(2, 2 + num_atoms):
                    if i < len(lines):
                        line = lines[i].strip()
                        if line:
                            parts = line.split()
                            if len(parts) >= 4:
                                element = parts[0]
                                x, y, z = parts[1], parts[2], parts[3]
                                inp_content += f" {element}                  {x}    {y}    {z}\n"
                
                inp_content += " *\n"
                
                # 保存inp文件
                output_file = os.path.join(self.output_path, f"{name}.inp")
                with open(output_file, 'w') as f:
                    f.write(inp_content)
                
                success_count += 1
                
            except Exception as e:
                print(f"Error converting {filename}: {e}")
        
        print(f"\nConversion complete! {success_count} files converted.")
        print(f"Output directory: {self.output_path}")
        
        return success_count
    
    def inp_to_xyz(self) -> int:
        """
        将ORCA inp文件转换为xyz文件
        
        :return: 成功转换的文件数
        """
        # 获取所有inp文件
        if os.path.isfile(self.input_path):
            inp_files = [self.input_path]
        else:
            inp_files = glob.glob(os.path.join(self.input_path, '*.inp'))
            inp_files = natsorted(inp_files, alg=ns.PATH)
        
        if not inp_files:
            print("No inp files found!")
            return 0
        
        success_count = 0
        print(f"Found {len(inp_files)} inp file(s)")
        
        for inp_file in tqdm(inp_files, desc="Converting inp to xyz"):
            filename = os.path.basename(inp_file)
            name = filename.replace('.inp', '')
            
            try:
                with open(inp_file, 'r') as f:
                    lines = f.readlines()
                
                # 查找坐标部分
                coord_start = -1
                for i, line in enumerate(lines):
                    if line.strip().startswith('* xyz'):
                        coord_start = i + 1
                        break
                
                if coord_start < 0:
                    print(f"Warning: Could not find coordinates in {filename}")
                    continue
                
                # 提取坐标
                coords = []
                for i in range(coord_start, len(lines)):
                    line = lines[i].strip()
                    if line == '*' or not line:
                        break
                    parts = line.split()
                    if len(parts) >= 4:
                        # 重新格式化坐标行
                        element = parts[0]
                        x, y, z = parts[1], parts[2], parts[3]
                        coords.append(f"{element}    {x}    {y}    {z}")
                
                if not coords:
                    print(f"Warning: No coordinates found in {filename}")
                    continue
                
                # 写入xyz文件
                xyz_content = f"{len(coords)}\n{name}\n"
                xyz_content += '\n'.join(coords) + '\n'
                
                output_file = os.path.join(self.output_path, f"{name}.xyz")
                with open(output_file, 'w') as f:
                    f.write(xyz_content)
                
                success_count += 1
                
            except Exception as e:
                print(f"Error converting {filename}: {e}")
        
        print(f"\nConversion complete! {success_count} files converted.")
        print(f"Output directory: {self.output_path}")
        
        return success_count
    
    def inp_to_gjf(self, nproc: str = '32', mem: str = '64GB',
                   method: str = 'b3lyp', basis: str = 'def2svp',
                   extra_keywords: str = 'opt freq',
                   link1_method: str = '',
                   nosave: bool = False) -> int:
        """
        将ORCA inp文件转换为Gaussian gjf文件
        
        :param nproc: 处理器核心数
        :param mem: 内存大小
        :param method: 计算方法
        :param basis: 基组
        :param extra_keywords: 额外关键词
        :param link1_method: Link1的计算方法（如果需要）
        :param nosave: 是否添加nosave关键词
        :return: 成功转换的文件数
        """
        # 获取所有inp文件
        if os.path.isfile(self.input_path):
            inp_files = [self.input_path]
        else:
            inp_files = glob.glob(os.path.join(self.input_path, '*.inp'))
            inp_files = natsorted(inp_files, alg=ns.PATH)
        
        if not inp_files:
            print("No inp files found!")
            return 0
        
        success_count = 0
        print(f"Found {len(inp_files)} inp file(s)")
        
        for inp_file in tqdm(inp_files, desc="Converting inp to gjf"):
            filename = os.path.basename(inp_file)
            name = filename.replace('.inp', '')
            
            try:
                with open(inp_file, 'r') as f:
                    lines = f.readlines()
                
                # 查找坐标部分和电荷/多重度
                coord_start = -1
                charge, mult = 0, 1
                
                for i, line in enumerate(lines):
                    if line.strip().startswith('* xyz'):
                        parts = line.strip().split()
                        if len(parts) >= 4:
                            try:
                                charge = int(parts[2])
                                mult = int(parts[3])
                            except:
                                pass
                        coord_start = i + 1
                        break
                
                if coord_start < 0:
                    print(f"Warning: Could not find coordinates in {filename}")
                    continue
                
                # 提取坐标
                coords = []
                for i in range(coord_start, len(lines)):
                    line = lines[i].strip()
                    if line == '*' or not line:
                        break
                    parts = line.split()
                    if len(parts) >= 4:
                        element = parts[0]
                        x, y, z = parts[1], parts[2], parts[3]
                        coords.append(f"{element}    {x}    {y}    {z}")
                
                if not coords:
                    print(f"Warning: No coordinates found in {filename}")
                    continue
                
                # 构建gjf文件内容
                gjf_content = f"%nprocshared={nproc}\n"
                if mem:
                    gjf_content += f"%mem={mem}\n"
                gjf_content += f"%chk={name}.chk\n"
                if nosave and link1_method == '':
                    gjf_content += "%nosave\n"
                
                if basis == '':
                    gjf_content += f"# {method} {extra_keywords}\n\n"
                else:
                    gjf_content += f"# {method}/{basis} {extra_keywords}\n\n"
                gjf_content += f"{name}\n\n"
                gjf_content += f"{charge}  {mult}\n"
                gjf_content += '\n'.join(coords) + '\n\n'

                # 如果有Link1部分
                if link1_method:
                    gjf_content += "--Link1--\n"
                    gjf_content += f"%nprocshared={nproc}\n"
                    if mem:
                        gjf_content += f"%mem={mem}\n"
                    gjf_content += f"%chk={name}.chk\n"
                    if nosave:
                        gjf_content += "%nosave\n"

                    gjf_content += f"# {link1_method} geom=allcheck\n\n"
                
                # 保存gjf文件
                output_file = os.path.join(self.output_path, f"{name}.gjf")
                with open(output_file, 'w') as f:
                    f.write(gjf_content)
                
                success_count += 1
                
            except Exception as e:
                print(f"Error converting {filename}: {e}")
        
        print(f"\nConversion complete! {success_count} files converted.")
        print(f"Output directory: {self.output_path}")
        
        return success_count
    
    def _extract_orca_output_coordinates(self, out_file: str) -> Tuple[List[str], int, int]:
        """
        从ORCA输出文件中提取最终优化几何结构
        
        :param out_file: ORCA输出文件路径
        :return: (坐标行列表, 电荷, 多重度)
        """
        try:
            with open(out_file, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            
            # 初始化变量
            coords = []
            charge, mult = 0, 1
            
            # 提取电荷和多重度 - 在文件开头查找
            for i, line in enumerate(lines[:100]):  # 只在前100行查找
                if 'Total Charge' in line and 'Multiplicity' in line:
                    parts = line.split()
                    for j, part in enumerate(parts):
                        if part == 'Charge' and j+1 < len(parts):
                            try:
                                charge = int(parts[j+1])
                            except:
                                pass
                        if part == 'Multiplicity' and j+1 < len(parts):
                            try:
                                mult = int(parts[j+1])
                            except:
                                pass
                    break
            
            # 查找最终几何结构 - 从后往前找最后一个优化结构
            coord_start = -1
            for i in range(len(lines) - 1, -1, -1):
                line = lines[i]
                # 查找最终的笛卡尔坐标
                if ('CARTESIAN COORDINATES (ANGSTROEM)' in line or 
                    'FINAL SINGLE POINT ENERGY' in line or
                    'OPTIMIZATION RUN DONE' in line):
                    
                    # 从当前位置向后查找坐标表格
                    for j in range(i, min(i + 200, len(lines))):
                        if 'CARTESIAN COORDINATES (ANGSTROEM)' in lines[j]:
                            coord_start = j + 2  # 跳过表头
                            break
                    
                    if coord_start > 0:
                        break
            
            # 如果没找到优化后的坐标，查找输入几何结构
            if coord_start < 0:
                for i, line in enumerate(lines):
                    if 'CARTESIAN COORDINATES (ANGSTROEM)' in line:
                        coord_start = i + 2
                        break
            
            if coord_start < 0:
                return [], charge, mult
            
            # 提取坐标数据
            for i in range(coord_start, len(lines)):
                line = lines[i].strip()
                if not line or line.startswith('---') or line.startswith('==='):
                    break
                
                parts = line.split()
                if len(parts) >= 4:
                    try:
                        # ORCA输出格式: 元素符号 x y z
                        element = parts[0]
                        x, y, z = parts[1], parts[2], parts[3]
                        # 验证坐标是否为数字
                        float(x), float(y), float(z)
                        coords.append(f"{element}    {x}    {y}    {z}")
                    except (ValueError, IndexError):
                        # 如果不是坐标行，跳过
                        continue
                else:
                    # 空行或格式不对，结束坐标读取
                    break
            
            return coords, charge, mult
            
        except Exception as e:
            print(f"Error extracting coordinates from {out_file}: {e}")
            return [], 0, 1
    
    def out_to_inp(self, job_type: str = "Opt NumFreq", 
                   functional: str = "wB97M-V", 
                   basis_set: str = "def2-TZVPD",
                   nproc: int = 32,
                   maxcore: int = 20000,
                   extra_keywords: str = "") -> int:
        """
        将ORCA .out文件转换为ORCA .inp文件
        
        :param job_type: ORCA任务类型
        :param functional: 泛函
        :param basis_set: 基组
        :param nproc: 处理器核心数
        :param maxcore: 每个核心的最大内存（MB）
        :param extra_keywords: 额外的ORCA关键词
        :return: 成功转换的文件数
        """
        # 获取所有out文件
        if os.path.isfile(self.input_path):
            out_files = [self.input_path]
        else:
            out_files = glob.glob(os.path.join(self.input_path, '*.out'))
            out_files = natsorted(out_files, alg=ns.PATH)
        
        if not out_files:
            print("No .out files found!")
            return 0
        
        success_count = 0
        print(f"Found {len(out_files)} .out file(s)")
        
        for out_file in tqdm(out_files, desc="Converting .out to .inp"):
            filename = os.path.basename(out_file)
            name = filename.replace('.out', '')
            
            try:
                coords, charge, mult = self._extract_orca_output_coordinates(out_file)
                
                if not coords:
                    print(f"Warning: Could not extract coordinates from {filename}")
                    continue
                
                # 构建ORCA输入文件
                inp_content = f"! {job_type} {functional} {basis_set}"
                if extra_keywords:
                    inp_content += f" {extra_keywords}"
                inp_content += "\n\n"
                
                inp_content += f"%maxcore {maxcore}\n"
                inp_content += f"%pal nprocs {nproc} end\n\n"
                inp_content += f"* xyz {charge} {mult}\n"
                
                for coord in coords:
                    inp_content += f" {coord}\n"
                
                inp_content += " *\n"
                
                # 保存inp文件
                output_file = os.path.join(self.output_path, f"{name}.inp")
                with open(output_file, 'w') as f:
                    f.write(inp_content)
                
                success_count += 1
                
            except Exception as e:
                print(f"Error converting {filename}: {e}")
        
        print(f"\nConversion complete! {success_count} files converted.")
        print(f"Output directory: {self.output_path}")
        
        return success_count

    def out_to_xyz(self) -> int:
        """
        将ORCA .out文件转换为xyz文件
        
        :return: 成功转换的文件数
        """
        # 获取所有out文件
        if os.path.isfile(self.input_path):
            out_files = [self.input_path]
        else:
            out_files = glob.glob(os.path.join(self.input_path, '*.out'))
            out_files = natsorted(out_files, alg=ns.PATH)

        if not out_files:
            print("No .out files found!")
            return 0

        success_count = 0
        print(f"Found {len(out_files)} .out file(s)")

        for out_file in tqdm(out_files, desc="Converting .out to .xyz"):
            filename = os.path.basename(out_file)
            name = filename.replace('.out', '')

            try:
                coords, _, _ = self._extract_orca_output_coordinates(out_file)

                if not coords:
                    print(f"Warning: Could not extract coordinates from {filename}")
                    continue

                # 构建xyz文件内容
                xyz_content = f"{len(coords)}\n{name}\n"
                xyz_content += '\n'.join(coords) + '\n'

                # 保存xyz文件
                output_file = os.path.join(self.output_path, f"{name}.xyz")
                with open(output_file, 'w') as f:
                    f.write(xyz_content)

                success_count += 1

            except Exception as e:
                print(f"Error converting {filename}: {e}")

        print(f"\nConversion complete! {success_count} files converted.")
        print(f"Output directory: {self.output_path}")

        return success_count


def main():
    """
    主函数 - 提供交互式命令行界面
    """
    print("=" * 70)
    print("Gaussian和ORCA文件格式转换工具")
    print("支持log、gjf、xyz、inp格式之间的相互转换")
    print("=" * 70)
    
    # 选择转换类型
    print("\n请选择转换类型:")
    print("Gaussian格式转换:")
    print("  1. log -> xyz")
    print("  2. log -> gjf")
    print("  3. xyz -> gjf")
    print("  4. gjf -> xyz")
    print("\nORCA格式转换:")
    print("  5. gjf -> inp (ORCA)")
    print("  6. xyz -> inp (ORCA)")
    print("  7. inp -> xyz")
    print("  8. inp -> gjf")
    print("  9. out -> inp (ORCA)")
    
    choice = input("\n请输入选项 (1-9): ").strip()
    
    # 获取输入路径
    input_path = input("请输入输入文件或文件夹路径: ").strip()
    if not os.path.exists(input_path):
        print(f"错误: 路径 {input_path} 不存在！")
        return
    
    # 获取输出路径
    output_path = input("请输入输出文件夹路径 (直接回车使用默认路径): ").strip()
    if not output_path:
        output_path = None
    
    # 创建转换器
    converter = GaussianConverter(input_path, output_path)
    
    # 执行转换
    if choice == '1':
        check = input("是否检查正常终止? (y/n, 默认y): ").strip().lower()
        check_termination = check != 'n'
        converter.log_to_xyz(check_termination=check_termination)
    
    elif choice == '2':
        print("\n请设置计算参数 (直接回车使用默认值):")
        nproc = input("处理器核心数 (默认32): ").strip() or '32'
        mem = input("内存大小 (默认64GB): ").strip() or '64GB'
        method = input("计算方法 (默认b3lyp): ").strip() or 'b3lyp'
        basis = input("基组 (默认def2svp): ").strip() or 'def2svp'
        extra = input("额外关键词 (默认opt freq): ").strip() or 'opt freq'
        charge = input("电荷 (默认0): ").strip()
        charge = int(charge) if charge else 0
        mult = input("自旋多重度 (默认1): ").strip()
        mult = int(mult) if mult else 1
        
        converter.log_to_gjf(nproc=nproc, mem=mem, method=method, basis=basis,
                            extra_keywords=extra, charge=charge, mult=mult)
    
    elif choice == '3':
        print("\n请设置计算参数 (直接回车使用默认值):")
        nproc = input("处理器核心数 (默认32): ").strip() or '32'
        mem = input("内存大小 (默认64GB): ").strip() or '64GB'
        method = input("计算方法 (默认b3lyp): ").strip() or 'b3lyp'
        basis = input("基组 (默认def2svp): ").strip() or 'def2svp'
        extra = input("额外关键词 (默认opt freq): ").strip() or 'opt freq'
        charge = input("电荷 (默认0): ").strip()
        charge = int(charge) if charge else 0
        mult = input("自旋多重度 (默认1): ").strip()
        mult = int(mult) if mult else 1
        
        converter.xyz_to_gjf(nproc=nproc, mem=mem, method=method, basis=basis,
                            extra_keywords=extra, charge=charge, mult=mult)
    
    elif choice == '4':
        converter.gjf_to_xyz()
    
    elif choice == '5':
        print("\n请设置ORCA计算参数 (直接回车使用默认值):")
        job_type = input("任务类型 (默认Opt NumFreq): ").strip() or 'Opt NumFreq'
        functional = input("泛函 (默认wB97M-V): ").strip() or 'wB97M-V'
        basis_set = input("基组 (默认def2-TZVPD): ").strip() or 'def2-TZVPD'
        nproc = input("处理器核心数 (默认32): ").strip()
        nproc = int(nproc) if nproc else 32
        maxcore = input("每核心内存/MB (默认20000): ").strip()
        maxcore = int(maxcore) if maxcore else 20000
        extra = input("额外关键词 (可选): ").strip()
        
        converter.gjf_to_inp(job_type=job_type, functional=functional, basis_set=basis_set,
                            nproc=nproc, maxcore=maxcore, extra_keywords=extra)
    
    elif choice == '6':
        print("\n请设置ORCA计算参数 (直接回车使用默认值):")
        job_type = input("任务类型 (默认Opt NumFreq): ").strip() or 'Opt NumFreq'
        functional = input("泛函 (默认wB97M-V): ").strip() or 'wB97M-V'
        basis_set = input("基组 (默认def2-TZVPD): ").strip() or 'def2-TZVPD'
        nproc = input("处理器核心数 (默认32): ").strip()
        nproc = int(nproc) if nproc else 32
        maxcore = input("每核心内存/MB (默认20000): ").strip()
        maxcore = int(maxcore) if maxcore else 20000
        charge = input("电荷 (默认0): ").strip()
        charge = int(charge) if charge else 0
        mult = input("自旋多重度 (默认1): ").strip()
        mult = int(mult) if mult else 1
        extra = input("额外关键词 (可选): ").strip()
        
        converter.xyz_to_inp(job_type=job_type, functional=functional, basis_set=basis_set,
                            nproc=nproc, maxcore=maxcore, charge=charge, mult=mult,
                            extra_keywords=extra)
    
    elif choice == '7':
        converter.inp_to_xyz()
    
    elif choice == '8':
        print("\n请设置Gaussian计算参数 (直接回车使用默认值):")
        nproc = input("处理器核心数 (默认32): ").strip() or '32'
        mem = input("内存大小 (默认64GB): ").strip() or '64GB'
        method = input("计算方法 (默认b3lyp): ").strip() or 'b3lyp'
        basis = input("基组 (默认def2svp): ").strip() or 'def2svp'
        extra = input("额外关键词 (默认opt freq): ").strip() or 'opt freq'
        
        converter.inp_to_gjf(nproc=nproc, mem=mem, method=method, basis=basis,
                            extra_keywords=extra)
    
    elif choice == '9':
        print("\n请设置ORCA计算参数 (直接回车使用默认值):")
        job_type = input("任务类型 (默认Opt NumFreq): ").strip() or 'Opt NumFreq'
        functional = input("泛函 (默认wB97M-V): ").strip() or 'wB97M-V'
        basis_set = input("基组 (默认def2-TZVPD): ").strip() or 'def2-TZVPD'
        nproc = input("处理器核心数 (默认32): ").strip()
        nproc = int(nproc) if nproc else 32
        maxcore = input("每核心内存/MB (默认20000): ").strip()
        maxcore = int(maxcore) if maxcore else 20000
        extra = input("额外关键词 (可选): ").strip()
        
        converter.out_to_inp(job_type=job_type, functional=functional, basis_set=basis_set,
                            nproc=nproc, maxcore=maxcore, extra_keywords=extra)
    
    else:
        print("无效的选项！")


if __name__ == '__main__':
    # 可以直接运行main()函数进行交互式转换
    # 或者直接使用类进行编程式转换
    
    # 示例1: 交互式使用
    # main()
    
    # 示例2: 编程式使用（取消注释以使用）
    """
    # === Gaussian格式转换 ===
    
    # log转xyz
    converter = GaussianConverter('./log_files', './xyz_output')
    converter.log_to_xyz(check_termination=True)
    
    # log转gjf
    converter = GaussianConverter('./log_files', './gjf_output')
    converter.log_to_gjf(nproc='32', method='b3lyp', basis='def2svp', extra_keywords='opt freq')
    
    # xyz转gjf
    converter = GaussianConverter('./xyz_files', './gjf_output')
    converter.xyz_to_gjf(nproc='48', method='wb97xd', basis='def2tzvp', 
                        extra_keywords='opt(ts,calcfc,noeigen) freq', charge=0, mult=1)
    
    # gjf转xyz
    converter = GaussianConverter('./gjf_files', './xyz_output')
    converter.gjf_to_xyz()
    
    # === ORCA格式转换 ===
    
    # gjf转inp (ORCA)
    converter = GaussianConverter('./gjf_files', './orca_inp_output')
    converter.gjf_to_inp(job_type='Opt NumFreq', functional='wB97M-V', 
                        basis_set='def2-TZVPD', nproc=32, maxcore=20000)
    
    # xyz转inp (ORCA)
    converter = GaussianConverter('./xyz_files', './orca_inp_output')
    converter.xyz_to_inp(job_type='Opt', functional='B3LYP', basis_set='def2-SVP',
                        nproc=24, maxcore=20000, charge=0, mult=1)
    
    # inp转xyz
    converter = GaussianConverter('./inp_files', './xyz_output')
    converter.inp_to_xyz()
    
    # inp转gjf
    converter = GaussianConverter('./inp_files', './gjf_output')
    converter.inp_to_gjf(nproc='32', method='b3lyp', basis='def2svp', extra_keywords='opt freq')
    
    # out转inp (ORCA)
    converter = GaussianConverter('./out_files', './orca_inp_output')
    converter.out_to_inp(job_type='Opt NumFreq', functional='wB97M-V', 
                        basis_set='def2-TZVPD', nproc=32, maxcore=20000)
    """

    # converter = GaussianConverter('./test_inputs', './test_inputs/mlip_gjfs')
    # converter.xyz_to_gjf(nproc='1', method="external='./mlpint'", basis='', extra_keywords='opt(calcfc,nomicro,maxcycle=1000)', mem='8GB',
    # link1_method="freq external='./mlpint'", nosave=True)

    # converter = GaussianConverter('./test_inputs', './test_inputs/dft_inps')
    # converter.xyz_to_inp(functional='wB97X-D4', basis_set='def2-TZVP def2/J RIJCOSX TightSCF SlowConv Hirshfeld', job_type='Opt', 
    #                      nproc=32, maxcore=2000, charge=0, mult=1)

    # converter = GaussianConverter('./test_outputs/dft/opt', './test_outputs/dft/freq')
    # converter.out_to_inp(functional='wB97X-D4', basis_set='def2-TZVP def2/J RIJCOSX TightSCF SlowConv', job_type='Freq', 
    #                      nproc=32, maxcore=2000)

    converter = GaussianConverter('./test_outputs/dft/opt', './test_outputs/dft/opt/xyz')
    converter.out_to_xyz()
