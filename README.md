# FY-4B Data Process

基于 `Satpy` 的 FY-4B AGRI L1 数据处理脚本集合，用于将原始 `.HDF` 文件裁剪并重采样到规则经纬度网格，保存为 `.npz` 文件，并提供简单的可视化与批量处理能力。

## 功能概览

- 将单个 FY-4B AGRI L1 `.HDF` 文件转换为裁剪后的 `.npz`
- 支持按经纬度范围 `bbox` 裁剪
- 支持指定输出规则网格分辨率
- 支持选择部分通道输出
- 支持批量递归扫描目录并按时间规则过滤转换
- 支持交互式查看 `.npz` 中的多通道数据
- 提供 `pytest` 测试用例

## 目录结构

```text
.
├── batch_fy4b_to_npz.py      # 批量转换脚本
├── fy4b_to_npz.py            # 单文件转换脚本
├── view_fy4b_npz.py          # NPZ 可视化脚本
├── environment.yml           # Conda 环境定义
├── COMMANDS.md               # 常用命令备忘
├── tests/                    # 测试用例
├── sample/                   # 示例 FY-4B HDF 数据
└── output/                   # 示例输出目录
```

## 环境准备

推荐使用 Conda：

```bash
conda env create -f environment.yml
conda activate fy4b-satpy
```

如果你希望沿用当前目录本地环境，也可以按 [COMMANDS.md](/Users/si14san1er/Code/GX_QPE_DATA/data_process/COMMANDS.md) 中的方式创建 `./conda-env`。

## 快速开始

### 1. 单文件转换

```bash
python fy4b_to_npz.py \
  sample/FY4B-_AGRI--_N_DISK_1330E_L1-_FDI-_MULT_NOM_20230621080000_20230621081459_4000M_V0001.HDF \
  output/fy4b_crop.npz \
  --bbox 100 20 110 30 \
  --resolution 0.04
```

常用参数：

- `input_file`：输入 FY-4B HDF 文件
- `output_file`：输出 NPZ 文件
- `--bbox`：裁剪范围，格式为 `lon_min lat_min lon_max lat_max`
- `--resolution`：输出规则经纬网分辨率，单位为度
- `--channels`：可选，指定输出通道，例如 `C01 C02 C03`
- `--resampler`：可选，重采样方法，默认 `nearest`

### 2. 批量转换

批量脚本会递归扫描目录下所有 `.HDF` 文件，只处理文件名开始时间为整点或半点的数据，输出文件名为对应开始时间。

```bash
python batch_fy4b_to_npz.py \
  sate_data \
  output \
  --bbox 100 20 110 30 \
  --resolution 0.04
```

示例输出文件名：

```text
output/20230620080000.npz
output/20230621103000.npz
```

### 3. 查看 NPZ 数据

```bash
python view_fy4b_npz.py output/fy4b_crop.npz
```

可选参数：

- `--cmap`：matplotlib 色标，默认 `viridis`
- `--vmin` / `--vmax`：固定颜色范围
- `--backend`：指定 matplotlib 后端，例如 `TkAgg`、`MacOSX`

交互界面支持：

- 滑块切换通道
- `Previous` / `Next` 按钮切换通道

## NPZ 输出内容

转换后的 `.npz` 文件包含以下主要字段：

- `data`：形状为 `(channels, lat, lon)` 的三维数组
- `channels`：通道名称列表
- `lat`：纬度坐标
- `lon`：经度坐标
- `bbox`：裁剪范围
- `resolution_deg`：输出分辨率
- `source_file`：原始输入文件路径
- `reader` / `resampler`：读取器与重采样方法
- `platform_name` / `sensor`：传感器元数据
- `start_time` / `end_time`：观测起止时间

## 运行测试

运行全部测试：

```bash
pytest tests -v
```

如果只想执行某一类测试：

```bash
pytest tests/test_fy4b_to_npz.py -v
pytest tests/test_batch_fy4b_to_npz.py -v
pytest tests/test_view_fy4b_npz.py -v
```

## 提交建议

建议提交以下内容：

- 源码脚本
- `tests/`
- `environment.yml`
- `README.md`
- `COMMANDS.md`

建议不要提交：

- 本地 Conda 环境目录
- 包缓存
- Python 缓存文件
- 运行生成的 `.npz` 输出

## 说明

- 当前测试默认依赖 `sample/` 目录中的示例 FY-4B 文件。
- 如果你后续不打算提交示例数据，可以同时调整测试数据策略或将测试改为 mock 数据驱动。
