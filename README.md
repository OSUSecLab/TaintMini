# TaintMini

TaintMini is a framework for detecting flows of sensitive data in Mini-Programs with static taint analysis. It is a novel universal data flow graph approach that captures data flows within
and across mini-programs.

<p align="center"><img src="figure/taint-mini.svg" alt="taintmini" width="800"></p>

We implemented TaintMini based on `pdg_js` (from [DoubleX](https://github.com/Aurore54F/DoubleX) by [Aurore Fass](https://aurore54f.github.io/) *et al*.). For more implementation details, please refer to our [paper](https://chaowang.dev/publications/icse23.pdf) and the [DoubleX paper](https://swag.cispa.saarland/papers/fass2021doublex.pdf).

## Table of contents

- [TaintMini](#taintmini)
  - [Table of contents](#table-of-contents)
  - [Prerequisites](#prerequisites)
    - [Environment](#environment)
    - [Dependencies](#dependencies)
    - [Pre-processing](#pre-processing)
  - [Usage](#usage)
  - [Config](#config)
  - [Examples](#examples)
    - [Single MiniProgram](#single-miniprogram)
    - [Multiple MiniPrograms](#multiple-miniprograms)
  - [Citation](#citation)
  - [License](#license)

## Prerequisites

### Environment

For optimal performance, we recommend allocating at least 4 cores and 16 GiB of memory to run the tool. 
Additionally, for best IO performance during analysis, we recommend using SSDs rather than hard disk drives, due to the large number of small files (less than one page size) that Mini-Programs typically have.
As a reference, we used 16 vCPUs of Intel Xeon Silver 4314, 128 GiB of 3200 MHz DDR4 memory, and 2 TiB of NVMe SSD (700 KIOPS) as the host for building and validating our artifact evaluation submission.

### Dependencies

Install Node.js dependencies for `pdg_js` first.

```bash
# make sure node.js and npm is installed
node --version && cd pdg_js && npm i
```

Install requirements for python.

```bash
# install requirements
pip install -r requirements.txt
```

### Pre-processing

TaintMini operates on unpacked WeChat Mini-Programs, necessitating the use of a WeChat Mini-Program unpacking tool in advance.
Please note that we are unable to provide such a tool directly due to potential legal implications.
We recommend seeking it out on external websites.

## Usage

```
usage: mini-taint [-h] -i path [-o path] [-c path] [-j number] [-b]

optional arguments:
  -h, --help            show this help message and exit
  -i path, --input path
                        path of input mini program(s). Single mini program directory or index files will both be fine.
  -o path, --output path
                        path of output results. The output file will be stored outside of the mini program directories.
  -c path, --config path
                        path of config file. See default config file for example. Leave the field empty to include all results.
  -j number, --jobs number
                        number of workers.
  -b, --bench           enable benchmark data log. Default: False
```

Results will be written to the directory provided by the `-o/--output` flag.
Result files are named `$(basename <directory>)-result.csv`,
along with `$(basename <directory>)-bench.csv` if `-b/--bench` option is present.

## Config

The `config.json` is a JSON formatted file, which includes two fields: `sources` and `sinks`:

- `sources` is an array, indicating the source APIs that need to be included. Please note there is a special value named `[double_binding]` which indicates the data flows from `WXML`.
- `sinks` is an array, indicating the sink APIs that need to be included.

For examples, please refer to the `config.json` file.

## Examples

### Single MiniProgram

Analyze a single MiniProgram; Include all sources and sinks; Enable multi-processing (all available CPU cores); No benchmark required.

```bash
python main.py -i /path/to/miniprogram -o ./results -j $(nproc)
```

### Multiple MiniPrograms

Analyze multiple MiniPrograms; Include all sources and sinks; Enable multi-processing (all available CPU cores); Benchmarks required.

```bash
# generate index
find /path/to/miniprograms -maxdepth 1 -type d -name "wx*" > index.txt
# start analysis
python main.py -i ./index.txt -o ./results -j $(nproc) -b
```

## Citation

If you find TaintMini useful, please consider citing our paper and DoubleX:

```plaintext
@inproceedings{wang2023taintmini,
  title={TAINTMINI: Detecting Flow of Sensitive Data in Mini-Programs with Static Taint Analysis},
  author={Wang, Chao and Ko, Ronny and Zhang, Yue and Yang, Yuqing and Lin, Zhiqiang},
  booktitle={Proceedings of the 45th International Conference on Software Engineering},
  year={2023}
}

@inproceedings{fass2021doublex,
author="Aurore Fass and Doli{\`e}re Francis Som{\'e} and Michael Backes and Ben Stock",
title="{\textsc{DoubleX}: Statically Detecting Vulnerable Data Flows in Browser Extensions at Scale}",
booktitle="ACM CCS",
year="2021"
}
```

## License

This project is licensed under the terms of the AGPLV3 license.

* **pdg_js** is credit to [**DoubleX**](https://github.com/Aurore54F/DoubleX/)


