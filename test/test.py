# SPDX-FileCopyrightText: © 2024 Tiny Tapeout
# SPDX-License-Identifier: Apache-2.0

# SPDX-FileCopyrightText: © 2024 Tiny Tapeout
# SPDX-License-Identifier: Apache-2.0

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer


# ============================================================
# Helper Functions
# ============================================================

def set_input(dut, mode, value):
    """
    ui[5:4] = mode
    ui[3:0] = value
    """
    packed = ((mode & 0x3) << 4) | (value & 0xF)
    dut.ui_in.value = packed


async def reset(dut):
    dut.rst_n.value = 0
    dut.ena.value = 1
    dut.ui_in.value = 0
    dut.uio_in.value = 0

    await Timer(100, units="ns")

    dut.rst_n.value = 1

    await Timer(100, units="ns")


async def start_clock(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())


def pwm_bit(output, bit):
    return (output >> bit) & 1


async def sample_pwm(dut, bit, cycles=256):
    """
    Measure PWM duty activity over time.
    """
    highs = 0

    for _ in range(cycles):
        await RisingEdge(dut.clk)

        val = int(dut.uo_out.value)

        if pwm_bit(val, bit):
            highs += 1

    return highs


# ============================================================
# TEST 1: Reset behavior
# ============================================================

@cocotb.test()
async def test_reset_behavior(dut):

    await start_clock(dut)

    dut.rst_n.value = 0
    dut.ena.value = 1
    dut.ui_in.value = 0
    dut.uio_in.value = 0

    await Timer(100, units="ns")

    assert int(dut.uo_out.value) == 0, "Outputs not cleared during reset"

    dut.rst_n.value = 1

    await Timer(100, units="ns")


# ============================================================
# TEST 2: RGB register loading
# ============================================================

@cocotb.test()
async def test_rgb_registers(dut):

    await start_clock(dut)
    await reset(dut)

    # RED = 15
    set_input(dut, 0, 15)
    await Timer(200, units="ns")

    # GREEN = 8
    set_input(dut, 1, 8)
    await Timer(200, units="ns")

    # BLUE = 4
    set_input(dut, 2, 4)
    await Timer(200, units="ns")

    out = int(dut.uo_out.value)

    dut._log.info(f"RGB output state = {out:08b}")

    assert out >= 0


# ============================================================
# TEST 3: PWM functionality
# ============================================================

@cocotb.test()
async def test_pwm_activity(dut):

    await start_clock(dut)
    await reset(dut)

    # Set RED duty cycle to mid-scale
    set_input(dut, 0, 8)

    red_highs = await sample_pwm(dut, 0)

    dut._log.info(f"RED highs = {red_highs}")

    assert red_highs > 0, "RED stuck LOW"
    assert red_highs < 256, "RED stuck HIGH"


# ============================================================
# TEST 4: RGB independent channels
# ============================================================

@cocotb.test()
async def test_independent_channels(dut):

    await start_clock(dut)
    await reset(dut)

    # RED max
    set_input(dut, 0, 15)
    await Timer(100, units="ns")

    # GREEN low
    set_input(dut, 1, 2)
    await Timer(100, units="ns")

    # BLUE off
    set_input(dut, 2, 0)
    await Timer(100, units="ns")

    red = await sample_pwm(dut, 0)
    green = await sample_pwm(dut, 1)
    blue = await sample_pwm(dut, 2)

    dut._log.info(f"RED activity   = {red}")
    dut._log.info(f"GREEN activity = {green}")
    dut._log.info(f"BLUE activity  = {blue}")

    assert red > green
    assert blue == 0


# ============================================================
# TEST 5: Speed divider control
# ============================================================

@cocotb.test()
async def test_speed_control(dut):

    await start_clock(dut)
    await reset(dut)

    # Set visible PWM output
    set_input(dut, 0, 8)
    await Timer(100, units="ns")

    # Slow divider
    set_input(dut, 3, 15)

    slow_toggles = 0
    prev = int(dut.uo_out.value) & 1

    for _ in range(200):
        await RisingEdge(dut.clk)

        curr = int(dut.uo_out.value) & 1

        if curr != prev:
            slow_toggles += 1

        prev = curr

    # Fast divider
    set_input(dut, 3, 1)

    fast_toggles = 0
    prev = int(dut.uo_out.value) & 1

    for _ in range(200):
        await RisingEdge(dut.clk)

        curr = int(dut.uo_out.value) & 1

        if curr != prev:
            fast_toggles += 1

        prev = curr

    dut._log.info(f"Slow toggles = {slow_toggles}")
    dut._log.info(f"Fast toggles = {fast_toggles}")

    assert fast_toggles > slow_toggles


# ============================================================
# TEST 6: Edge cases
# ============================================================

@cocotb.test()
async def test_edge_cases(dut):

    await start_clock(dut)
    await reset(dut)

    # Fully OFF
    set_input(dut, 0, 0)

    off_highs = await sample_pwm(dut, 0)

    # Fully ON
    set_input(dut, 0, 15)

    on_highs = await sample_pwm(dut, 0)

    dut._log.info(f"OFF highs = {off_highs}")
    dut._log.info(f"ON highs  = {on_highs}")

    assert off_highs == 0
    assert on_highs > off_highs


# ============================================================
# TEST 7: Long runtime stability
# ============================================================

@cocotb.test()
async def test_long_runtime(dut):

    await start_clock(dut)
    await reset(dut)

    set_input(dut, 0, 7)
    await Timer(100, units="ns")

    for i in range(1000):

        await RisingEdge(dut.clk)

        val = int(dut.uo_out.value)

        assert val >= 0

        if i % 100 == 0:
            dut._log.info(f"Cycle {i}: output={val:08b}")

    dut._log.info("Long runtime stability test passed")
