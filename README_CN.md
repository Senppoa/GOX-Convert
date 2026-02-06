# GOX-Convert

**GOX-Convert** 是一个用于计算化学领域的文件格式转换工具，支持 Gaussian 和 ORCA 量子化学计算软件之间的文件格式相互转换。

## 功能简介

本工具支持以下文件格式之间的相互转换：

- **Gaussian 格式**: `.log` (输出文件), `.gjf` (输入文件)
- **ORCA 格式**: `.inp` (输入文件)
- **通用格式**: `.xyz` (分子结构文件)

## 支持的原子

工具内置了常见原子的原子序数到元素符号的映射，包括：
- 主族元素：H, He, Li, Be, B, C, N, O, F, Ne, Na, Mg, Al, Si, P, S, Cl, Ar, K, Ca
- 过渡金属：Fe, Co, Ni, Cu, Zn, Zr, Rh, Pd, Ag, Ir, Pt, Au
- 卤素和其他：Br, I

## 主要功能

### 1. log 转 xyz

从 Gaussian 的 log 输出文件中提取最终优化后的分子结构，保存为 xyz 格式。

**特性：**
- 自动检查计算是否正常终止 (Normal termination)
- 从后向前查找标准坐标 (Standard orientation)，确保获取最终结构
- 支持批量处理整个文件夹
- 可生成成功/失败文件列表

### 2. log 转 gjf

将 Gaussian 的 log 文件转换为新的 gjf 输入文件，用于后续计算。

**特性：**
- 自动提取电荷和自旋多重度
- 支持自定义计算方法、基组、关键词
- 支持 Link1 多步计算
- 可添加 nosave 关键词

### 3. xyz 转 gjf

将 xyz 结构文件转换为 Gaussian 输入文件。

**特性：**
- 自动读取原子数量和标题
- 支持自定义计算参数
- 批量处理多个文件

### 4. gjf 转 xyz

从 Gaussian 输入文件中提取分子坐标，保存为 xyz 格式。

**特性：**
- 自动识别坐标部分
- 正确处理电荷和自旋多重度行
- 支持 Link1 分隔符

### 5. gjf 转 inp

将 Gaussian 输入文件转换为 ORCA 输入文件。

**特性：**
- 支持自定义泛函和基组
- 可设置并行核心数和内存
- 支持额外的 ORCA 关键词

### 6. xyz 转 inp

将 xyz 结构文件直接转换为 ORCA 输入文件。

**特性：**
- 保持分子结构信息
- 支持完整的 ORCA 计算参数设置

### 7. inp 转 gjf

将 ORCA 输入文件转换为 Gaussian 输入文件。

**特性：**
- 解析 ORCA 坐标部分
- 转换为 Gaussian 格式

### 8. log 转 inp

直接将 Gaussian log 文件转换为 ORCA 输入文件。

**特性：**
- 提取最终优化结构
- 生成 ORCA 格式的输入文件

## 安装要求

### 依赖包

```bash
pip install tqdm natsort
```

### Python 版本

- Python 3.6 或更高版本

## 使用方法

### 作为模块导入使用

```python
from gaussian_orca_converter import GaussianConverter

# 初始化转换器
converter = GaussianConverter(input_path="path/to/input", output_path="path/to/output")

# log 转 xyz
converter.log_to_xyz(check_termination=True, save_success_list=True)

# log 转 gjf
converter.log_to_gjf(
    nproc='32',
    mem='64GB',
    method='b3lyp',
    basis='def2svp',
    extra_keywords='opt freq',
    charge=0,
    mult=1
)

# xyz 转 gjf
converter.xyz_to_gjf(
    nproc='32',
    mem='64GB',
    method='b3lyp',
    basis='def2svp',
    extra_keywords='opt freq',
    charge=0,
    mult=1
)

# gjf 转 xyz
converter.gjf_to_xyz()

# gjf 转 inp
converter.gjf_to_inp(
    job_type="Opt NumFreq",
    functional="wB97M-V",
    basis_set="def2-TZVPD",
    nproc=32,
    maxcore=20000
)

# xyz 转 inp
converter.xyz_to_inp(
    job_type="Opt NumFreq",
    functional="wB97M-V",
    basis_set="def2-TZVPD",
    nproc=32,
    maxcore=20000
)

# inp 转 gjf
converter.inp_to_gjf(
    nproc='32',
    mem='64GB',
    method='b3lyp',
    basis='def2svp',
    extra_keywords='opt freq'
)

# log 转 inp
converter.log_to_inp(
    job_type="Opt NumFreq",
    functional="wB97M-V",
    basis_set="def2-TZVPD",
    nproc=32,
    maxcore=20000
)
```

### 批量处理

当输入路径为文件夹时，工具会自动处理该文件夹中所有匹配的文件：

```python
# 批量转换整个文件夹的 log 文件
converter = GaussianConverter(input_path="./log_files", output_path="./xyz_files")
converter.log_to_xyz()
```

## 参数说明

### 通用参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `input_path` | str | 必填 | 输入文件或文件夹路径 |
| `output_path` | str | None | 输出文件夹路径，默认为 `converted_files` |

### log_to_xyz 参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `check_termination` | bool | True | 是否检查正常终止 |
| `save_success_list` | bool | True | 是否保存成功/失败文件列表 |

### log_to_gjf / xyz_to_gjf / inp_to_gjf 参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `nproc` | str | '32' | 处理器核心数 |
| `mem` | str | '64GB' | 内存大小 |
| `method` | str | 'b3lyp' | 计算方法/泛函 |
| `basis` | str | 'def2svp' | 基组 |
| `extra_keywords` | str | 'opt freq' | 额外关键词 |
| `link1_method` | str | '' | Link1 的计算方法 |
| `link1_basis` | str | '' | Link1 的基组 |
| `charge` | int | 0 | 电荷 |
| `mult` | int | 1 | 自旋多重度 |
| `nosave` | bool | False | 是否添加 nosave 关键词 |

### gjf_to_inp / xyz_to_inp / log_to_inp 参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `job_type` | str | "Opt NumFreq" | ORCA 任务类型 |
| `functional` | str | "wB97M-V" | 泛函 |
| `basis_set` | str | "def2-TZVPD" | 基组 |
| `nproc` | int | 32 | 处理器核心数 |
| `maxcore` | int | 20000 | 每个核心的最大内存 (MB) |
| `extra_keywords` | str | "" | 额外的 ORCA 关键词 |

## 输出文件

转换完成后，工具会输出以下信息：

1. **转换后的文件**: 保存在指定的输出目录中
2. **success_files.txt**: 成功转换的文件列表 (仅在 `save_success_list=True` 时生成)
3. **error_files.txt**: 转换失败的文件列表 (仅在 `save_success_list=True` 时生成)

## 注意事项

1. **文件编码**: 工具使用 UTF-8 编码读取和写入文件
2. **坐标提取**: log 文件转换时，工具会从后向前查找标准坐标，确保获取最终优化结构
3. **批量处理**: 使用 `tqdm` 显示进度条，`natsort` 进行自然排序
4. **错误处理**: 工具会捕获异常并继续处理其他文件，不会中断批量转换

## 示例

### 示例 1: 提取优化后的结构

```python
from gaussian_orca_converter import GaussianConverter

# 从 log 文件提取最终结构
converter = GaussianConverter("molecule.log", "./output")
converter.log_to_xyz(check_termination=True)
```

### 示例 2: 批量生成 ORCA 输入文件

```python
from gaussian_orca_converter import GaussianConverter

# 将 xyz 文件批量转换为 ORCA 输入文件
converter = GaussianConverter("./xyz_structures", "./orca_inputs")
converter.xyz_to_inp(
    job_type="Opt Freq",
    functional="B3LYP",
    basis_set="def2-SVP",
    nproc=16,
    maxcore=4000
)
```

### 示例 3: 创建多步计算输入文件

```python
from gaussian_orca_converter import GaussianConverter

# 创建包含 Link1 的 Gaussian 输入文件
converter = GaussianConverter("molecule.log", "./output")
converter.log_to_gjf(
    method='b3lyp',
    basis='def2svp',
    extra_keywords='opt',
    link1_method='wB97M-V',
    link1_basis='def2tzvpd',
    extra_keywords_link1='freq'
)
```

## 许可证

本项目为开源项目，可自由使用和修改。

## 作者信息

请联系tkun@mail.dlut.edu.cn 进行问题反馈或建议。

## 更新日志

- **2025-10-20**: 初始版本发布，支持基本的文件格式转换功能
