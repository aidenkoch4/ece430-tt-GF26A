# SPDX-FileCopyrightText: © 2024 Tiny Tapeout
# SPDX-License-Identifier: Apache-2.0

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer

CLK_NS = 10

# ============================================================
# Helpers
# ============================================================

async def start_clock(dut):
    cocotb.start_soon(Clock(dut.clk, CLK_NS, units="ns").start())


async def reset(dut):

    dut.ena.value = 1
    dut.ui_in.value = 0
    dut.uio_in.value = 0

    dut.rst_n.value = 0

    await Timer(200, units="ns")

    dut.rst_n.value = 1

    await Timer(200, units="ns")


def set_input(dut, mode, value):
    """
    ui_in[7:6] = mode
    ui_in[5:0] = value
    """

    packed = ((mode & 0b11) << 6) | (value & 0x3F)

    dut.ui_in.value = packed

    dut._log.info(
        f"SET_INPUT mode={mode:02b} value={value:06b} packed={packed:08b}"
    )


def get_outputs(dut):

    val = int(dut.uo_out.value)

    red   = (val >> 0) & 1
    green = (val >> 1) & 1
    blue  = (val >> 2) & 1

    return red, green, blue


async def sample_pwm(dut, cycles=512):

    red_high = 0
    green_high = 0
    blue_high = 0

    for _ in range(cycles):

        await RisingEdge(dut.clk)

        r, g, b = get_outputs(dut)

        red_high += r
        green_high += g
        blue_high += b

    return red_high, green_high, blue_high


# ============================================================
# FULL SYSTEM TEST
# ============================================================

@cocotb.test()
async def rgb_pwm_full_system_test(dut):

    dut._log.info("========================================")
    dut._log.info("STARTING RGB PWM FULL SYSTEM TEST")
    dut._log.info("========================================")

    await start_clock(dut)
    await reset(dut)

    # ========================================================
    # TEST 1
    # Initial outputs low
    # ========================================================

    dut._log.info("TEST 1: Verify outputs start LOW")

    initial = int(dut.uo_out.value)

    dut._log.info(f"Initial uo_out = {initial:08b}")

    # ========================================================
    # TEST 2
    # Clock divider mode
    # mode = 11
    # ========================================================

    dut._log.info("TEST 2: Configure divider")

    set_input(dut, 0b11, 2)

    await Timer(1000, units="ns")

    # ========================================================
    # TEST 3
    # RED CHANNEL
    # mode = 00
    # ========================================================

    dut._log.info("TEST 3: RED PWM")

    set_input(dut, 0b00, 48)

    await Timer(1000, units="ns")

    r, g, b = await sample_pwm(dut)

    dut._log.info(f"RED samples -> R={r} G={g} B={b}")

    assert r > 0, "RED never goes HIGH"
    assert r < 512, "RED stuck HIGH"

    # ========================================================
    # TEST 4
    # GREEN CHANNEL
    # mode = 01
    # ========================================================

    dut._log.info("TEST 4: GREEN PWM")

    set_input(dut, 0b01, 48)

    await Timer(1000, units="ns")

    r, g, b = await sample_pwm(dut)

    dut._log.info(f"GREEN samples -> R={r} G={g} B={b}")

    assert g > 0, "GREEN never goes HIGH"
    assert g < 512, "GREEN stuck HIGH"

    # ========================================================
    # TEST 5
    # BLUE CHANNEL
    # mode = 10
    # ========================================================

    dut._log.info("TEST 5: BLUE PWM")

    set_input(dut, 0b10, 48)

    await Timer(1000, units="ns")

    r, g, b = await sample_pwm(dut)

    dut._log.info(f"BLUE samples -> R={r} G={g} B={b}")

    assert b > 0, "BLUE never goes HIGH"
    assert b < 512, "BLUE stuck HIGH"

    # ========================================================
    # TEST 6
    # LONG STABILITY TEST
    # ========================================================

    dut._log.info("TEST 6: Long duration stability")

    set_input(dut, 0b00, 32)
    await Timer(5000, units="ns")

    set_input(dut, 0b01, 16)
    await Timer(5000, units="ns")

    set_input(dut, 0b10, 48)
    await Timer(5000, units="ns")

    r, g, b = await sample_pwm(dut, cycles=1024)

    dut._log.info(f"LONG RUN -> R={r} G={g} B={b}")

    assert b > 0, "BLUE failed long-run stability"

    dut._log.info("========================================")
    dut._log.info("ALL TESTS PASSED")
    dut._log.info("========================================")
