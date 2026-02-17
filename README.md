# GF180MCU eFuse array compiler

This repository contains an eFuse array compiler for the GF180MCU technology. [Original compiler](https://github.com/egorxe/gf180_efuse_compiler/commit/444cecf080246598029439b6df1605e37e3599de) was used to do a tapeout during the Open MPW GFMPW-0 run, but recently compiler was rewritten from scratch to increase density and automate the flow. Current version of the compiler is much more usable, but still not verified in silicon and should be treated as experimental.

## Compiler features

eFuse compiler provides:

* Generation of synchronous nonvolatile eFuse memory array for the GF180MCU process.
* GDS and other files necessary for integration into any GF180MCU-based chip design.
* Configurable word width and memory depth. Currently only 16, 32 and 64 word depths are supported.
* eFuse memory density up to 10 kbits/mm^2 (without digital wrapper).
* Support for the open source GF180MCU PDK.
* Digital wrapper with Wishbone interface to eFuse memory.

## Requirements

To generate and verify an eFuse array a Linux system is required with the following tools present in the PATH:
1. Python 3.8+ with klayout package (0.29+, could be installed with pip).
2. KLayout 0.29+ (for DRC & LVS).
3. magic (any version compatible with GF180MCU PDK for the circuit extraction).
4. Xyce (7.9+).
5. LibreLane version with GF180MCU support, environment from [wafer.space project template](https://github.com/wafer-space/gf180mcu-project-template) is recommended.

Additionally the open source GF180MCU PDK should be installed and environmental variable PDK_ROOT should be set to it's location and variable PDK to specific PDK variant (for example gf180mcuD). The recommended way to install the PDK is the [ciel tool](https://github.com/fossi-foundation/ciel). 

Alternatively it's possible to use a ready made environment with all required tools and PDK preinstalled like the [IIC-OSIC-TOOLS](https://github.com/iic-jku/IIC-OSIC-TOOLS) container (does not contain suitable LibreLane yet, digital wrapper generation will not work) or [wafer.space project template environment](https://github.com/wafer-space/gf180mcu-project-template) (Xyce is not included).

## How to run

A flow script for eFuse generation and verification efuse.py is located in the repository root. It requires two parameters: eFuse memory depth in words and single word width, all other options are described in script help message. Runtime files will be produced in temporary runs directory and resulting files will be copied to macros directory.

For example to generate a minimal possible array with 16 1-bit eFuse words run:

```
./efuse.py 16 1
```

To generate 64x64 array skipping Xyce verification run:

```
./efuse.py --xyce_netlist=none 64 64
```

## Examples

Files for several precompiled configurations are provided in the releases. Here are some GDS screenshots.

![efuse_array_16x1](docs/efuse_array_16x1.png?raw=true)

Minimal eFuse array with 16 1-bit words.

![efuse_array_64x8](docs/efuse_array_64x8.png?raw=true)

Larger eFuse array with 64 8-bit words.

## TODO

* Improve a sense amplifier to reduce read currents.
* Add a digital wrapper with SPI interface.
* Improve aspect ratios for large arrays.
* Implement async eFuse.
* Add block integration documentation.
