--! @title eFuse ROM controller
--! @file efuse_ctrl.vhd
--! @author anarky (anarky@maltsystem.com)
--! @version 0.1a
--! @date 2022-11-19
--!
--! @copyright  Copyright (c) 2022 by MALT System
--!              Apache License 2.0
--! @details eFuse ROM controller with wishbone interface. 
--! Data mask is not supported. Configurable bank structure.
library ieee;
    use ieee.std_logic_1164.all;
    use ieee.numeric_std.all;
    use ieee.std_logic_unsigned.all;



entity efuse_ctrl is
    generic (
        DEPTH       : integer := 11; --! pow2 depth in words
        WDT         : integer := 8;  --! word width
        BANK        : integer := 7;  --! pow2 bank amount (max)
        BANK_NUM    : integer := 72  --! actual bank ammount
    );
    port (
        wb_rst_i : in std_logic; --! active high reset
        wb_clk_i : in std_logic; --! clock

        -- Wishbone secondary
        wb_adr_i : in std_logic_vector(DEPTH - 1 downto 0); --! address
        wb_dat_o : out std_logic_vector(WDT - 1 downto 0); --! read data
        wb_dat_i : in std_logic_vector(WDT - 1 downto 0); --! write data
        wb_we_i : in std_logic; --! active hihg WE
        wb_sel_i : in std_logic_vector(WDT/8 - 1 downto 0); --! not connected
        wb_stb_i : in std_logic; --! WB stb signal
        wb_cyc_i : in std_logic; --! WB cyc signal
        wb_ack_o : out std_logic --! WB ack signal
    );
end  efuse_ctrl;

architecture rtl of efuse_ctrl is
constant C_WRITE_TIME : integer := 500; --! Program data hold time in clocks (should be increased to 100)
constant C_PRESET_TIME : integer := 10; --! Preset cycle time in clocks
constant C_SENSE_TIME : integer := 10; --! Sense sycle time in clocks

component efuse_rom
    generic (
      DATA_WDT : integer;
      ADDR_WDT : integer;
      BA_WDT : integer; 
      BANK_NUM  : integer
    );
      port (
      nPRESET : in std_logic;
      SENSE : in std_logic;
      PROG_ENA : in std_logic_vector(DATA_WDT - 1 downto 0);
      DO : out std_logic_vector(DATA_WDT - 1 downto 0);
      ADDR : in std_logic_vector(ADDR_WDT - 1 downto 0)
    );
end component;
  
type state_type is (idle, prog, preset_pulse, sense_pulse, latch_data, latch_data_out);

type v_type is record
    wb_dat_o : std_logic_vector(WDT - 1 downto 0);
    wb_ack_o : std_logic;
    nPRESET : std_logic;
    SENSE : std_logic;
    PROG_ENA : std_logic_vector(WDT - 1 downto 0);
    ADDR : std_logic_vector(DEPTH - 1 downto 0);
    state : state_type;
    timer : integer range 0 to C_PRESET_TIME + C_WRITE_TIME + C_SENSE_TIME;
end record;
signal r, rin : v_type;
signal DO : std_logic_vector(WDT - 1 downto 0);
signal iPROG_ENA : std_logic_vector(WDT - 1 downto 0);
signal inPRESET : std_logic;
signal iSENSE : std_logic;
begin

wb_dat_o <= r.wb_dat_o;
wb_ack_o <= r.wb_ack_o;

-- additional defence while reset is active --
iPROG_ENA <= r.PROG_ENA and (not wb_rst_i);
iSENSE <= r.SENSE and (not wb_rst_i);
inPRESET <= r.nPRESET and (not wb_rst_i);

SYNC : process(wb_clk_i, wb_rst_i)

begin
    if wb_rst_i  = '1' then
        r.state <= idle;
        r.PROG_ENA <= (others =>  '0'); 
        r.wb_ack_o <= '0';
        r.wb_dat_o <= (others => '0');
        r.ADDR <= (others => '0');
        r.SENSE <= '0';
        r.nPRESET <= '1';
        r.timer <= 0;
    else
        if rising_edge(wb_clk_i) then
            r <= rin;
        end if;
    end if;    
end process;

ASYNC : process(all)
    variable v : v_type;
begin
    v := r;
    case r.state is
        when idle =>
            v.PROG_ENA := (others => '0');
            v.wb_ack_o := '0';
            if wb_stb_i = '1' then
                v.ADDR := wb_adr_i;
                if wb_we_i = '1' then
                    v.state := latch_data;
                    v.wb_ack_o := '1';
                else
                    v.state := preset_pulse;
                end if;
            end if;
        when latch_data => 
            v.PROG_ENA := wb_dat_i;
            v.wb_ack_o := '0';
            v.state := prog;
        when prog =>
            if r.timer < C_WRITE_TIME then
                v.timer := r.timer + 1;
            else
                v.timer := 0;
                v.state := idle;
                v.PROG_ENA := (others =>  '0'); 
            end if;
        when preset_pulse =>
            v.nPRESET := '0';
            v.wb_ack_o := '0';
            if r.timer = C_PRESET_TIME then
                v.timer := 0;
                v.state := sense_pulse;
                v.nPRESET := '1';
            else
                v.timer := r.timer + 1;
            end if;
        when sense_pulse =>
            v.SENSE := '1';
            v.wb_ack_o := '0';
            if r.timer = C_SENSE_TIME then
                v.timer := 0;
                v.state := latch_data_out;
                v.SENSE := '0';
                v.wb_dat_o := DO;
                v.wb_ack_o := '1';
            else
                v.timer := r.timer + 1;
            end if;
        when latch_data_out =>
		    v.wb_ack_o := '0';
		    v.state := idle;
			
    end case;
    rin <= v;

end process;

efuse_rom_inst : efuse_rom
    generic map (
      ADDR_WDT  => DEPTH,
      DATA_WDT  => WDT,
      BA_WDT    => BANK,
      BANK_NUM  => BANK_NUM
    )
    port map (
      nPRESET => inPRESET,
      SENSE => iSENSE,
      PROG_ENA => iPROG_ENA,
      DO => DO,
      ADDR => r.ADDR
    );

end architecture;
