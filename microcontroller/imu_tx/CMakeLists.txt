#
# Copyright (c) 2018 Nordic Semiconductor
#
# SPDX-License-Identifier: LicenseRef-Nordic-5-Clause
#
cmake_minimum_required(VERSION 3.20.0)

find_package(Zephyr REQUIRED HINTS $ENV{ZEPHYR_BASE})

if(NOT DEFINED TRANSMITTER_PIPE)
  set(TRANSMITTER_PIPE 1 CACHE STRING "ESB transmitter pipe (0..7)")
endif()

if(TARGET app)
  target_compile_definitions(app PRIVATE TRANSMITTER_PIPE=${TRANSMITTER_PIPE})
endif()

project(imu_tx)

FILE(GLOB app_sources src/*.c)
# NORDIC SDK APP START
target_sources(app PRIVATE ${app_sources})
# NORDIC SDK APP END
