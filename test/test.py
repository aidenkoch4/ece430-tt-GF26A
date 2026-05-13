# SPDX-FileCopyrightText: © 2024 Tiny Tapeout
# SPDX-License-Identifier: Apache-2.0

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer


# =========================================================
# Helper Functions
# =========================================================

def set_input(dut, sel, value):
    """
    ui_in[7:6] = mode
    ui_in[5:0] = value
    """

    packed = ((sel & 0x3) << 6) | (value & 0x3F)

    dut.ui_in.value = packed

    dut._log.info(
        f"SET_INPUT mode={sel:02b} "
        f"value={value:06b} "
        f"packed={packed:08b}"
    )


async def reset(dut):

    dut.rst_n.value = 0
    dut.ena.value = 1
    dut.ui_in.value = 0
    dut.uio_in.value = 0

    await Timer(200, unit="ns")

    dut.rst_n.value = 1

    await Timer(200, unit="ns")


async def sample_highs(dut, bitmask, cycles):

    highs = 0

    for _ in range(cycles):

        await RisingEdge(dut.clk)

        value = int(dut.uo_out.value)

        if value & bitmask:
            highs += 1

    return highs


async def count_toggles(dut, bitmask, cycles):

    toggles = 0

    previous = int(dut.uo_out.value) & bitmask

    for _ in range(cycles):

        await RisingEdge(dut.clk)

        current = int(dut.uo_out.value) & bitmask

        if current != previous:
            toggles += 1

        previous = current

    return toggles


# =========================================================
# Main Comprehensive RGB PWM Test
# =========================================================

@cocotb.test()
async def rgb_pwm_full_system_test(dut):

    # -----------------------------------------------------
    # Start clock
    # -----------------------------------------------------

    cocotb.start_soon(
        Clock(dut.clk, 10, unit="ns").start()
    )

    await reset(dut)

    dut._log.info("========================================")
    dut._log.info("STARTING RGB PWM FULL SYSTEM TEST")
    dut._log.info("========================================")

    # =====================================================
    # TEST 1
    # Verify outputs start LOW after reset
    # =====================================================

    dut._log.info("TEST 1: Verify outputs start LOW")

    initial_output = int(dut.uo_out.value)

    dut._log.info(
        f"Initial uo_out = {initial_output:08b}"
    )

    assert (initial_output & 0x1) == 0, \
        "RED not LOW after reset"

    assert (initial_output & 0x2) == 0, \
        "GREEN not LOW after reset"

    assert (initial_output & 0x4) == 0, \
        "BLUE not LOW after reset"

    # =====================================================
    # TEST 2
    # Configure divider
    # =====================================================

    dut._log.info("TEST 2: Configure clock divider")

    set_input(dut, 3, 2)

    await Timer(1000, unit="ns")

    divider_value = int(
        dut.user_project.core.clk_div.value
    )

    dut._log.info(
        f"Clock divider loaded = {divider_value}"
    )

    assert divider_value == 2

    # =====================================================
    # TEST 3
    # RED channel only
    # =====================================================

    dut._log.info("TEST 3: RED channel")

    set_input(dut, 0, 48)

    await Timer(5000, unit="ns")

    red_highs = await sample_highs(
        dut,
        0x1,
        20000
    )

    green_highs = await sample_highs(
        dut,
        0x2,
        20000
    )

    blue_highs = await sample_highs(
        dut,
        0x4,
        20000
    )

    dut._log.info(f"RED highs   = {red_highs}")
    dut._log.info(f"GREEN highs = {green_highs}")
    dut._log.info(f"BLUE highs  = {blue_highs}")

    assert red_highs > 0, \
        "RED never activated"

    assert green_highs == 0, \
        "GREEN should still be OFF"

    assert blue_highs == 0, \
        "BLUE should still be OFF"

    # =====================================================
    # TEST 4
    # GREEN channel enable
    # =====================================================

    dut._log.info("TEST 4: GREEN channel")

    set_input(dut, 1, 24)

    await Timer(5000, unit="ns")

    red_highs = await sample_highs(
        dut,
        0x1,
        20000
    )

    green_highs = await sample_highs(
        dut,
        0x2,
        20000
    )

    blue_highs = await sample_highs(
        dut,
        0x4,
        20000
    )

    dut._log.info(f"RED highs   = {red_highs}")
    dut._log.info(f"GREEN highs = {green_highs}")
    dut._log.info(f"BLUE highs  = {blue_highs}")

    assert red_highs > green_highs, \
        "RED should be brighter than GREEN"

    assert green_highs > 0, \
        "GREEN never activated"

    assert blue_highs == 0, \
        "BLUE should still be OFF"

    # =====================================================
    # TEST 5
    # BLUE channel enable
    # =====================================================

    dut._log.info("TEST 5: BLUE channel")

    set_input(dut, 2, 8)

    await Timer(5000, unit="ns")

    red_highs = await sample_highs(
        dut,
        0x1,
        20000
    )

    green_highs = await sample_highs(
        dut,
        0x2,
        20000
    )

    blue_highs = await sample_highs(
        dut,
        0x4,
        20000
    )

    dut._log.info(f"RED highs   = {red_highs}")
    dut._log.info(f"GREEN highs = {green_highs}")
    dut._log.info(f"BLUE highs  = {blue_highs}")

    assert red_highs > green_highs > blue_highs

    assert red_highs > 0
    assert green_highs > 0
    assert blue_highs > 0

    # =====================================================
    # TEST 6
    # Toggle verification
    # =====================================================

    dut._log.info("TEST 6: PWM toggle verification")

    red_toggles = await count_toggles(
        dut,
        0x1,
        50000
    )

    green_toggles = await count_toggles(
        dut,
        0x2,
        50000
    )

    blue_toggles = await count_toggles(
        dut,
        0x4,
        50000
    )

    dut._log.info(
        f"RED toggles   = {red_toggles}"
    )

    dut._log.info(
        f"GREEN toggles = {green_toggles}"
    )

    dut._log.info(
        f"BLUE toggles  = {blue_toggles}"
    )

    assert red_toggles > 10, \
        "RED not toggling"

    assert green_toggles > 10, \
        "GREEN not toggling"

    assert blue_toggles > 10, \
        "BLUE not toggling"

    # =====================================================
    # TEST 7
    # Divider speed comparison
    # =====================================================

    dut._log.info("TEST 7: Clock divider speed comparison")

    # Slow divider
    set_input(dut, 3, 20)

    await Timer(10000, unit="ns")

    slow_toggles = await count_toggles(
        dut,
        0x1,
        50000
    )

    dut._log.info(
        f"Slow divider toggles = {slow_toggles}"
    )

    # Fast divider
    set_input(dut, 3, 1)

    await Timer(10000, unit="ns")

    fast_toggles = await count_toggles(
        dut,
        0x1,
        50000
    )

    dut._log.info(
        f"Fast divider toggles = {fast_toggles}"
    )

    assert fast_toggles > slow_toggles, \
        "Clock divider not affecting PWM speed"

    # =====================================================
    # TEST 8
    # Long runtime stability
    # =====================================================

    dut._log.info("TEST 8: Long runtime stability")

    for cycle in range(100000):

        await RisingEdge(dut.clk)

        output = int(dut.uo_out.value)

        assert output >= 0

        if cycle % 10000 == 0:

            pwm_counter = int(
                dut.user_project.core.pwm_counter.value
            )

            divider_counter = int(
                dut.user_project.core.div_counter.value
            )

            duty_r = int(
                dut.user_project.core.duty_r.value
            )

            duty_g = int(
                dut.user_project.core.duty_g.value
            )

            duty_b = int(
                dut.user_project.core.duty_b.value
            )

            dut._log.info(
                f"CYCLE={cycle} "
                f"OUT={output:08b} "
                f"PWMCTR={pwm_counter} "
                f"DIVCTR={divider_counter} "
                f"R={duty_r} "
                f"G={duty_g} "
                f"B={duty_b}"
            )

    dut._log.info("========================================")
    dut._log.info("ALL TESTS PASSED")
    dut._log.info("========================================")
