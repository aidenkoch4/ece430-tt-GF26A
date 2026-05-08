/*
 * Copyright (c) 2024 Aiden Koch
 * SPDX-License-Identifier: Apache-2.0
 */

`default_nettype none

module tt_um_aidenkoch4 (
    input  wire [7:0] ui_in,
    output wire [7:0] uo_out,

    input  wire [7:0] uio_in,
    output wire [7:0] uio_out,
    output wire [7:0] uio_oe,

    input  wire       ena,
    input  wire       clk,
    input  wire       rst_n
);

    wire [1:0] mode;
    wire [5:0] value;

    assign mode  = ui_in[7:6];
    assign value = ui_in[5:0];

    wire pwm_r;
    wire pwm_g;
    wire pwm_b;

    rgb_pwm_core core (
        .clk(clk),
        .rst_n(rst_n),
        .mode(mode),
        .value(value),

        .pwm_r(pwm_r),
        .pwm_g(pwm_g),
        .pwm_b(pwm_b)
    );

    assign uo_out[0] = pwm_r;
    assign uo_out[1] = pwm_g;
    assign uo_out[2] = pwm_b;
    assign uo_out[7:3] = 5'b00000;

    assign uio_out = 8'b00000000;
    assign uio_oe  = 8'b00000000;

    wire _unused = &{ena, uio_in};

endmodule
