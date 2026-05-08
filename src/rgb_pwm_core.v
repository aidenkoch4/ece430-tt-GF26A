// Aiden Koch
// 5/5/2026
// Version 1

module rgb_pwm_core (
    input  wire       clk,
    input  wire       rst_n,
    input  wire [1:0] mode,
    input  wire [5:0] value,

    output wire       pwm_r,
    output wire       pwm_g,
    output wire       pwm_b
);

    reg [5:0] duty_r;
    reg [5:0] duty_g;
    reg [5:0] duty_b;

    reg [5:0] clk_div;

    reg [5:0] div_counter;
    reg       slow_clk;

    reg [5:0] pwm_counter;

    // ----------------------------
    // Register writes
    // ----------------------------
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            duty_r <= 0;
            duty_g <= 0;
            duty_b <= 0;
            clk_div <= 1;
        end else begin
            case (mode)
                2'b00: duty_r <= value;
                2'b01: duty_g <= value;
                2'b10: duty_b <= value;
                2'b11: clk_div <= value;
            endcase
        end
    end

    // ----------------------------
    // Clock divider
    // ----------------------------
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            div_counter <= 0;
            slow_clk <= 0;
        end else begin
            if (div_counter >= clk_div) begin
                div_counter <= 0;
                slow_clk <= ~slow_clk;
            end else begin
                div_counter <= div_counter + 1;
            end
        end
    end

    // ----------------------------
    // PWM counter
    // ----------------------------
    always @(posedge slow_clk or negedge rst_n) begin
        if (!rst_n)
            pwm_counter <= 0;
        else
            pwm_counter <= pwm_counter + 1;
    end

    // ----------------------------
    // PWM outputs
    // ----------------------------
    assign pwm_r = (pwm_counter < duty_r);
    assign pwm_g = (pwm_counter < duty_g);
    assign pwm_b = (pwm_counter < duty_b);

endmodule
