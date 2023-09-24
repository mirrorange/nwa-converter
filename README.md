## NWA / NWK / OVK 格式转换工具 (NWA / NWK / OVK Converter)

这是一个用于将 NWA / NWK / OVK 格式的音频转换为 WAV / OGG 格式的工具。

This is a tool for converting NWA / NWK / OVK format audio to WAV / OGG format.

### 使用方法 (Usage)

#### 从可执行文件运行 (Run from executable file)

你可以到 Release 页面下载已经打包好的可执行文件。

You can download the packaged executable file from the Release page.

使用 Nuitka 打包的可执行文件大小约为 10 MB，但速度远远不如 pypy。

The size of the executable file packaged with Nuitka is about 10 MB, but the speed is far less than pypy.

包含完整 pypy 环境的可执行文件大小约为 100 MB，但速度比 Nuitka 快 5 倍左右。

The size of the executable file containing the complete pypy environment is about 100 MB, but the speed is about 5 times faster than Nuitka.

```bash
nwaconverter [-h] [-o OUTPUT] path
```

#### 从源代码运行 (Run from source code)

程序不需要安装任何依赖库，可以直接使用 Python 3 运行。

The program does not need to install any dependent libraries, and can be run directly with Python 3.

```bash
python main.py [-h] [-o OUTPUT] path
```

如果不指定输出目录，则默认输出到当前目录。

If the output directory is not specified, the default output is to the current directory.

#### 使用 pypy 运行 (Run with pypy)

由于 pypy 能提供 5 倍左右的性能提升，建议使用 pypy 运行。

Since pypy can provide about 5 times performance improvement, it is recommended to use pypy to run.

```bash
pypy main.py [-h] [-o OUTPUT] path
```

### 其它 (Others)

本项目是 [rs-nwa](https://github.com/hasenbanck/rs-nwa) 的 Python 移植版本。

This project is a Python port of [rs-nwa](https://github.com/hasenbanck/rs-nwa).