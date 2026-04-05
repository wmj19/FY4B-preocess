# FY-4B 数据处理命令

## 1. 创建 conda 环境

如果当前目录还没有 `conda-env`，先执行：

```bash
conda create -p ./conda-env python=3.11 -y
CONDA_PKGS_DIRS=$PWD/.conda-pkgs conda install -p ./conda-env -c conda-forge satpy h5py matplotlib pytest -y
```

## 2. 将 FY-4B HDF 转成裁剪后的 NPZ

示例：

```bash
./conda-env/bin/python fy4b_to_npz.py \
  sample/FY4B-_AGRI--_N_DISK_1330E_L1-_FDI-_MULT_NOM_20230621080000_20230621081459_4000M_V0001.HDF \
  output/fy4b_crop.npz \
  --bbox 100 20 110 30 \
  --resolution 0.04
```

参数说明：

- `input_file`: 输入的 FY-4B HDF 文件
- `output_file`: 输出的 NPZ 文件
- `--bbox`: 裁剪范围，顺序为 `lon_min lat_min lon_max lat_max`
- `--resolution`: 输出经纬度规则格点分辨率，单位为度

如果只想保留部分通道，例如 `C01 C02 C03`：

```bash
./conda-env/bin/python fy4b_to_npz.py \
  sample/FY4B-_AGRI--_N_DISK_1330E_L1-_FDI-_MULT_NOM_20230621080000_20230621081459_4000M_V0001.HDF \
  output/fy4b_crop_subset.npz \
  --bbox 100 20 110 30 \
  --resolution 0.04 \
  --channels C01 C02 C03
```

## 3. 可视化 NPZ 文件

直接打开交互窗口：

```bash
./conda-env/bin/python view_fy4b_npz.py output/fy4b_crop.npz
```

窗口支持：

- 底部 `Slider` 切换通道索引
- `Previous` / `Next` 按钮切换通道

## 4. 可视化时固定色标范围

如果想让不同通道之间的颜色范围保持一致：

```bash
./conda-env/bin/python view_fy4b_npz.py output/fy4b_crop.npz --vmin 0 --vmax 300
```

## 5. 指定 matplotlib 后端

如果默认窗口打不开，可以尝试：

```bash
./conda-env/bin/python view_fy4b_npz.py output/fy4b_crop.npz --backend TkAgg
```

或者：

```bash
./conda-env/bin/python view_fy4b_npz.py output/fy4b_crop.npz --backend MacOSX
```

## 6. 运行测试

```bash
./conda-env/bin/pytest tests/test_fy4b_to_npz.py tests/test_view_fy4b_npz.py
```

## 7. 批量转换多个日期目录下的 FY-4B HDF

把 `sate_data` 下所有子目录里的 `.HDF` 递归扫描一遍，只转换文件名开始时间为整点或 30 分的文件，并把输出统一平铺到 `output/` 目录：

```bash
./conda-env/bin/python batch_fy4b_to_npz.py \
  sate_data \
  output \
  --bbox 100 20 110 30 \
  --resolution 0.04
```

说明：

- 输入根目录是 `sate_data`
- 输出目录是 `output`
- 输出文件名使用原始文件名中的开始时间，例如 `20230620080000.npz`
- 只会转换 `HH:00:00` 和 `HH:30:00` 的文件
- 如果 `output/20230620080000.npz` 已存在，会直接覆盖

如果只想保留部分通道，例如 `C01 C02 C03`：

```bash
./conda-env/bin/python batch_fy4b_to_npz.py \
  sate_data \
  output \
  --bbox 100 20 110 30 \
  --resolution 0.04 \
  --channels C01 C02 C03
```

如果想指定重采样方法：

```bash
./conda-env/bin/python batch_fy4b_to_npz.py \
  sate_data \
  output \
  --bbox 100 20 110 30 \
  --resolution 0.04 \
  --resampler nearest
```

## 8. 查看批量脚本帮助

```bash
./conda-env/bin/python batch_fy4b_to_npz.py --help
```

## 9. 运行批量转换相关测试

只运行批量转换脚本测试：

```bash
./conda-env/bin/pytest tests/test_batch_fy4b_to_npz.py -v
```

同时检查批量转换和原有单文件转换：

```bash
./conda-env/bin/pytest tests/test_batch_fy4b_to_npz.py tests/test_fy4b_to_npz.py -v
```
