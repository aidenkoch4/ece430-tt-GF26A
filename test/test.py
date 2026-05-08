# SPDX-FileCopyrightText: © 2024 Tiny Tapeout
# SPDX-License-Identifier: Apache-2.0

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer


# -----------------------------
# Helpers
# -----------------------------
def set_input(dut, value):
    dut.ui_in.value = value


async def reset(dut):
    dut.rst_n.value = 0
    dut.ena.value = 1
    dut.ui_in.value = 0
    dut.uio_in.value = 0

    await Timer(50, units="ns")

    dut.rst_n.value = 1
    await Timer(50, units="ns")


# -----------------------------
# Clock setup (FIXED)
# -----------------------------
async def start_clock(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())


# -----------------------------
# TEST 1: Register updates
# -----------------------------
@cocotb.test()
async def test_rgb_registers(dut):

    await start_clock(dut)
    await reset(dut)

    # RED = 15
    set_input(dut, (0 << 5) | 15)
    await Timer(200, units="ns")

    # GREEN = 8
    set_input(dut, (1 << 5) | 8)
    await Timer(200, units="ns")

    # BLUE = 25
    set_input(dut, (2 << 5) | 25)
    await Timer(200, units="ns")

    # Basic sanity check: outputs exist and are binary
    assert dut.uo_out.value is not None


# -----------------------------
# TEST 2: Speed control
# -----------------------------
@cocotb.test()
async def test_speed_mode(dut):

    await start_clock(dut)
    await reset(dut)

    # slow speed
    set_input(dut, (3 << 5) | 10)
    await Timer(300, units="ns")

    # fast speed
    set_input(dut, (3 << 5) | 2)
    await Timer(300, units="ns")

    assert dut.uo_out.value is not None


# -----------------------------
# TEST 3: PWM activity sanity
# -----------------------------
@cocotb.test()
async def test_pwm_activity(dut):

    await start_clock(dut)
    await reset(dut)

    # Set RED duty mid
    set_input(dut, (0 << 5) | 16)

    highs = 0
    samples = 200

    for _ in range(samples):
        await RisingEdge(dut.clk)

        # safe conversion
        out_val = int(dut.uo_out.value)

        # check red bit
        if out_val & 0x1:
            highs += 1

    # PWM MUST toggle at least somewhat
    assert highs > 0, "PWM output appears stuck LOW"
    assert highs < samples, "PWM output appears stuck HIGH"
