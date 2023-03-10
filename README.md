# GF180MCU eFuse array compiler

This repository contains eFuse array with Wishbone interface compiler for GF180 Open MPW. Was used in [Ophelia FPGA](https://github.com/egorxe/ophelia_fpga_openmpw) taped out on GFMPW-0. 

Compiler uses small eFuse memory PCell for KLayout and generates eFuse array with Wishbone read/write interface using GHDL, Yosys and OpenLane. Compiler is semi-automatic for now and requires some manual work to generate and characterize required array geometry.

## Directories

* **docs** - Hopefully one day documentation will reside here
* **hw** - VHDL sources for Wishbone array wrapper, behavioral models and testbenches
* **macros** - Output from KLayout goes here to be used during OpenLane step
* **openlane** - OpenLane scripts to generate Wishbone array wrapper macro
* **klayout** - KLayout eFuse PCells
* **scripts** - Useful scripts used during implementation & characterization
* **xyce** - Some (very unrefined) Xyce analog simulation tests for eFuse array components

## Requirements

To generate eFuse array following tools are required: KLayout, OpenLane, GHDL plugin for Yosys. For characterization Xyce simulator is required. Hopefully this repository will be expanded with more instructions and automated scripts in the future.

## Example

![9kbyte_efuse](docs/9kbyte_efuse.png?raw=true)

9 kByte eFuse array with Wishbone compiled from 72 16x8 eFuse blocks for GFMPW-0 (OpenROAD density view).
