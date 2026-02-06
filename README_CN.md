# Gaussian和ORCA文件格式转换工具

一个强大且全面的Python工具，用于计算化学文件格式之间的相互转换，支持Gaussian (log, gjf)、ORCA (inp) 和 xyz 格式。

## 功能特性

### Gaussian格式转换
- ✅ **log → xyz**: 从Gaussian计算结果提取结构
- ✅ **log → gjf**: 从计算结果创建新的输入文件
- ✅ **xyz → gjf**: 从结构文件创建Gaussian输入文件
- ✅ **gjf → xyz**: 从输入文件提取结构

### ORCA格式转换
- ✅ **gjf → inp**: 将Gaussian输入文件转换为ORCA输入文件
- ✅ **xyz → inp**: 从结构文件创建ORCA输入文件
- ✅ **inp → xyz**: 从ORCA输入文件提取结构
- ✅ **inp → gjf**: 将ORCA输入文件转换为Gaussian输入文件

### 通用特性
- ✅ 支持批量转换
- ✅ 自动检查计算是否正常终止（log文件）
- ✅ 生成成功/失败文件列表
- ✅ 面向对象设计，易于集成到其他项目
- ✅ 进度条显示，友好的用户体验
- ✅ 灵活的参数配置

## 依赖项

```bash
pip install tqdm natsort
```

## 使用方法

### 方法1: 交互式命令行

直接运行脚本，按照提示操作：

```bash
python gaussian_converter.py
```

程序会引导你：
1. 选择转换类型（8种转换方式）
2. 输入源文件/文件夹路径
3. 输入输出路径（可选）
4. 根据转换类型设置相关参数

### 方法2: 编程式调用

在你的Python脚本中导入并使用：

## Gaussian格式转换示例

### 示例1: log → xyz

```python
from gaussian_converter import GaussianConverter

# 创建转换器
converter = GaussianConverter(
    input_path='./log_files',      # log文件所在文件夹
    output_path='./xyz_output'     # 输出文件夹
)

# 执行转换
success, success_files, error_files = converter.log_to_xyz(
    check_termination=True,         # 检查是否正常终止
    save_success_list=True          # 保存成功/失败文件列表
)

print(f"成功: {success}, 失败: {len(error_files)}")
```

### 示例2: log → gjf

```python
from gaussian_converter import GaussianConverter

converter = GaussianConverter('./log_files', './gjf_output')

converter.log_to_gjf(
    nproc='32',                     # 处理器核心数
    mem='64GB',                     # 内存
    method='b3lyp',                 # 计算方法
    basis='def2svp',                # 基组
    extra_keywords='opt freq',      # 额外关键词
    charge=0,                       # 电荷
    mult=1,                         # 自旋多重度
    nosave=False                    # 是否添加nosave
)
```

### 示例3: xyz → gjf (用于过渡态计算)

```python
from gaussian_converter import GaussianConverter

converter = GaussianConverter('./xyz_files', './ts_gjf_output')

converter.xyz_to_gjf(
    nproc='48',
    mem='128GB',
    method='wb97xd',
    basis='def2tzvp',
    extra_keywords='opt(ts,calcfc,noeigen) freq',
    charge=0,
    mult=1
)
```

### 示例4: gjf → xyz

```python
from gaussian_converter import GaussianConverter

converter = GaussianConverter('./gjf_files', './xyz_output')
converter.gjf_to_xyz()
```

## ORCA格式转换示例

### 示例5: gjf → inp (Gaussian到ORCA)

```python
from gaussian_converter import GaussianConverter

# 批量将Gaussian的gjf文件转换为ORCA的inp文件
converter = GaussianConverter('./gjf_files', './orca_inp_output')

converter.gjf_to_inp(
    job_type='Opt NumFreq',         # ORCA任务类型
    functional='wB97M-V',           # 泛函
    basis_set='def2-TZVPD',         # 基组
    nproc=32,                       # 处理器核心数
    maxcore=20000,                  # 每核心最大内存(MB)
    extra_keywords=''               # 额外ORCA关键词
)
```

**输出的ORCA inp文件示例：**
```
! Opt NumFreq wB97M-V def2-TZVPD

%maxcore 20000
%pal nprocs 32 end

* xyz 0 1
 C                  -0.123     0.456    -0.789
 H                   0.890     0.123     0.456
 ...
 *
```

### 示例6: xyz → inp (创建ORCA输入文件)

```python
from gaussian_converter import GaussianConverter

converter = GaussianConverter('./xyz_files', './orca_inp_output')

converter.xyz_to_inp(
    job_type='Opt',                 # 只做优化
    functional='B3LYP',
    basis_set='def2-SVP',
    nproc=24,
    maxcore=20000,
    charge=0,
    mult=1,
    extra_keywords='def2/J RIJCOSX'  # 使用RIJCOSX近似
)
```

### 示例7: inp → xyz (从ORCA提取结构)

```python
from gaussian_converter import GaussianConverter

converter = GaussianConverter('./inp_files', './xyz_output')
converter.inp_to_xyz()
```

### 示例8: inp → gjf (ORCA到Gaussian)

```python
from gaussian_converter import GaussianConverter

# 将ORCA的inp文件转换为Gaussian的gjf文件
converter = GaussianConverter('./inp_files', './gjf_output')

converter.inp_to_gjf(
    nproc='32',
    mem='64GB',
    method='b3lyp',
    basis='def2svp',
    extra_keywords='opt freq'
)
```

## 实际应用场景

### 场景1: XTB → DFT 工作流

从XTB优化结果创建DFT计算输入：

```python
# 第1步: 从XTB log提取结构
converter1 = GaussianConverter('./xtb_logs', './xtb_xyz')
converter1.log_to_xyz(check_termination=True)

# 第2步: 创建Gaussian DFT输入文件
converter2 = GaussianConverter('./xtb_xyz', './dft_gjf')
converter2.xyz_to_gjf(
    method='wb97xd',
    basis='def2svp',
    extra_keywords='opt freq'
)
```

### 场景2: Gaussian → ORCA 迁移

将现有的Gaussian计算迁移到ORCA：

```python
# 直接从gjf创建ORCA输入
converter = GaussianConverter('./gaussian_inputs', './orca_inputs')
converter.gjf_to_inp(
    job_type='Opt NumFreq',
    functional='wB97M-V',
    basis_set='def2-TZVPD',
    nproc=32
)
```

### 场景3: 批量IRC计算准备

从过渡态结果批量创建IRC计算输入：

```python
# 先从过渡态log提取结构
converter1 = GaussianConverter('./ts_logs', './ts_xyz')
converter1.log_to_xyz(check_termination=True)

# 创建IRC gjf文件
converter2 = GaussianConverter('./ts_xyz', './irc_gjf')
converter2.xyz_to_gjf(
    nproc='32',
    method='wb97xd',
    basis='def2svp',
    extra_keywords='IRC(calcfc,maxpoints=100)'
)
```

### 场景4: 跨平台计算

在不同的计算程序间切换：

```python
# ORCA优化 → Gaussian单点能计算
converter1 = GaussianConverter('./orca_opt_inp', './structures')
converter1.inp_to_xyz()

converter2 = GaussianConverter('./structures', './gaussian_sp')
converter2.xyz_to_gjf(
    method='ccsd(t)',
    basis='def2tzvpp',
    extra_keywords='sp'
)
```

## 类方法详细说明

### GaussianConverter类

#### 初始化参数

```python
GaussianConverter(input_path, output_path=None)
```

- `input_path` (str): 输入文件或文件夹路径
- `output_path` (str, 可选): 输出文件夹路径，默认为 `./converted_files`

#### Gaussian格式转换方法

##### `log_to_xyz(check_termination=True, save_success_list=True)`

将Gaussian log文件转换为xyz文件。

**返回:** `(success_count, success_files, error_files)`

##### `log_to_gjf(...)`

将log文件转换为gjf文件。

**参数:**
- `nproc` (str): 处理器核心数，默认'32'
- `mem` (str): 内存大小，默认'64GB'
- `method` (str): 计算方法，默认'b3lyp'
- `basis` (str): 基组，默认'def2svp'
- `extra_keywords` (str): 额外关键词，默认'opt freq'
- `link1_method` (str): Link1的计算方法
- `link1_basis` (str): Link1的基组
- `charge` (int): 电荷，默认0
- `mult` (int): 自旋多重度，默认1
- `nosave` (bool): 是否添加nosave

**返回:** `int` - 成功转换的文件数

##### `xyz_to_gjf(...)`

将xyz文件转换为gjf文件。参数与 `log_to_gjf` 类似（不包括link1相关）。

##### `gjf_to_xyz()`

将gjf文件转换为xyz文件。

#### ORCA格式转换方法

##### `gjf_to_inp(...)`

将Gaussian gjf文件转换为ORCA inp文件。

**参数:**
- `job_type` (str): ORCA任务类型，默认"Opt NumFreq"
- `functional` (str): 泛函，默认"wB97M-V"
- `basis_set` (str): 基组，默认"def2-TZVPD"
- `nproc` (int): 处理器核心数，默认32
- `maxcore` (int): 每核心最大内存(MB)，默认20000
- `extra_keywords` (str): 额外ORCA关键词

**返回:** `int` - 成功转换的文件数

##### `xyz_to_inp(...)`

将xyz文件转换为ORCA inp文件。

**参数:** 与 `gjf_to_inp` 类似，额外需要 `charge` 和 `mult`

##### `inp_to_xyz()`

将ORCA inp文件转换为xyz文件。

##### `inp_to_gjf(...)`

将ORCA inp文件转换为Gaussian gjf文件。

**参数:** 与 `log_to_gjf` 类似

## 输出说明

### log_to_xyz

输出文件夹包含：
- `*.xyz`: 转换后的xyz文件
- `success_files.txt`: 成功转换的文件列表
- `error_files.txt`: 失败的文件列表

### 其他转换

输出文件夹包含相应格式的转换文件，以及转换统计信息。

## 支持的原子类型

脚本内置了常见原子的序数到符号的映射，包括：
- **主族元素**: H, He, Li, Be, B, C, N, O, F, Ne, Na, Mg, Al, Si, P, S, Cl, Ar
- **过渡金属**: K, Ca, Fe, Co, Ni, Cu, Zn, Rh, Pd, Ag, Zr, Ir, Pt, Au
- **卤素**: F, Cl, Br, I

如需添加其他元素，可修改类中的 `ATOM_SYMBOL_MAP` 字典。

## 常用ORCA任务类型

### 优化和频率
- `Opt`: 几何优化
- `Freq`: 频率计算
- `NumFreq`: 数值频率计算
- `Opt Freq`: 优化+频率
- `Opt NumFreq`: 优化+数值频率

### 过渡态搜索
- `OptTS`: 过渡态优化
- `OptTS NumFreq`: 过渡态优化+数值频率

### 单点能
- `SP`: 单点能计算

### 常用泛函和基组组合

#### 常用泛函
- `B3LYP`: 经典杂化泛函
- `wB97M-V`: 考虑色散的meta-GGA泛函
- `wB97X-D3`: 带D3色散校正
- `PBE0`: 另一个流行的杂化泛函
- `CCSD(T)`: 高精度后HF方法

#### 常用基组
- `def2-SVP`: 小基组，快速计算
- `def2-TZVP`: 三zeta基组
- `def2-TZVPD`: 带弥散函数的三zeta基组
- `cc-pVDZ`, `cc-pVTZ`: 相关一致基组

#### 辅助基组和加速
- `def2/J`: RIJCOSX的辅助基组
- `RIJCOSX`: 分辨率恒等近似，加速混合泛函计算
- `strongSCF`: 更稳定的SCF收敛

## 常见问题

### Q1: 转换时提示"Could not extract coordinates"？

**A:** 检查输入文件格式是否正确，特别是：
- gjf文件是否有电荷和自旋多重度行
- xyz文件第一行是否为原子数
- inp文件是否有 `* xyz` 关键字

### Q2: ORCA inp文件的内存设置怎么理解？

**A:** `maxcore` 是每个核心的最大内存（单位MB）。总内存 = maxcore × nprocs / 1024 GB

例如：`maxcore=20000`, `nprocs=32` → 总内存 ≈ 625 GB

### Q3: 如何添加更复杂的ORCA关键词？

**A:** 使用 `extra_keywords` 参数：

```python
converter.xyz_to_inp(
    extra_keywords='def2/J RIJCOSX strongSCF'
)
```

### Q4: 转换后的文件编码问题？

**A:** 所有文件默认使用UTF-8编码。如遇到问题，检查原文件编码。

### Q5: 批量转换时如何跳过已存在的文件？

**A:** 当前版本会覆盖已存在的文件。如需跳过，可以先检查输出目录或手动实现：

```python
import os
from gaussian_converter import GaussianConverter

input_files = ['file1.xyz', 'file2.xyz']
for f in input_files:
    output_file = f.replace('.xyz', '.gjf')
    if not os.path.exists(output_file):
        converter = GaussianConverter(f, './output')
        converter.xyz_to_gjf()
```

## 注意事项

1. **编码问题**: log文件使用UTF-8编码读取
2. **路径分隔符**: Windows系统建议使用原始字符串 `r'path'` 或正斜杠 `/`
3. **内存设置**: 根据实际计算体系大小合理设置
4. **检查输出**: 转换后建议检查生成的文件
5. **电荷和多重度**: gjf→inp转换会自动提取，xyz→inp需要手动指定

## 更新日志

- **2025-10-20**: 初始版本，整合Gaussian和ORCA转换功能
  - 支持8种格式转换
  - 批量处理
  - 交互式和编程式两种使用方式

## 许可证

本工具整合自多个原始脚本，保留原作者信息。

## 贡献

欢迎提交问题和改进建议！

