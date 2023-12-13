--! @title eFuse array model
--! @file efuse_array.vhd
--! @author anarky 
--! @version 0.1a
--! @date 2022-11-19
--!
--! @copyright  Apache License 2.0
--! @details eFuse array model for gf180mcu.
--!

library ieee;
    use ieee.std_logic_1164.all;
    use ieee.numeric_std.all;
    use ieee.std_logic_unsigned.all;
    use ieee.std_logic_textio.all;
library std;
    use std.textio.all;

--! Timing diagram:
--! { signal: [
--!   {                                                                              node: ".EF.P....Q"           },
--!   { name: "nPRESET",         wave: "1...0.1.....",                                node: "....G.H"           },
--!   { name: "SENSE",          wave: "0......1.0.." ,                               node: '......KL.N'},
--!   { name: "COL_PROG",       wave: "2222........", data: "0 WORD_A WORD_B 0"    , node: ".AB"           },
--!   { name: "SEL",            wave: "x22x2.....x.", data: "LINE_A LINE_B LINE_A" },
--!   { name: "DO",             wave: "x.......2..x", data: "WORD_A" },
--!   {                                                                              node: ".CD.I.JM.O"           },
--! ],
--! edge: ['A-C', 'B-D', 'C<->D C_T_write', 'A-E', 'B-F', 'E<->F write cycle', 'G-I', 'H-J', 'I<->J C_T_preset', 'L-M', 'J<->M C_T_gap', 'N-O', 'M<->O C_T_read', 'P<->Q read cycle', 'G-P', 'N-Q'],
--! config: { hscale: 2 }}

entity efuse_array is
    generic (
        DEPTH : integer := 16; --! depth in words
        WDT : integer := 8     --! word width in bits
    );
    port (
        -- interface
        nPRESET : in std_logic; --! active low preset pulse
        SENSE : in std_logic; --! active high sense pulse
        COL_PROG : in std_logic_vector(WDT - 1 downto 0); --! active high bit prog ena 
        DO : out std_logic_vector(WDT - 1 downto 0); --! read data out
        \LINE\ : in std_logic_vector(DEPTH - 1 downto 0) --! line select input

        -- PWR pins
        --VSS : inout std_logic; --! ground connection
        --VDD  : inout std_logic --! power connection
    );
end efuse_array;

architecture rtl of efuse_array is
constant C_T_read : time := 1 ns; --! time from sense edge to valid output data
constant C_T_preset : time := 1 ns; --! minimal preset pulse time
constant C_T_write : time := 1 ns; --! minimal write data hold time
constant C_T_gap : time := 1 ns; --! minimal gap between nPRESET and SENSE pulses

constant C_DEBUG_LEVEL : integer := 2;
type efuse_arry_type is array (DEPTH - 1 downto 0) of std_logic_vector(WDT - 1 downto 0);
signal efuse_array : efuse_arry_type := (others => (others => '0'));
impure function printstring (msg : string; dbgl : integer) return integer is
    variable msg_buf : line;
begin
    if dbgl <= C_DEBUG_LEVEL then
		report msg;
        --write(msg_buf, msg);
        --writeline(output, msg_buf);
    end if;
end function;

function get_pin_int (sel : in std_logic_vector) return integer is
variable bit_num : integer;
begin
    for i in 0 to sel'length-1 loop
        if sel(i) = '1' then
            bit_num := i;
        end if;
    end loop;
    return bit_num;
end function;


begin

MODEL : process
variable preset_latch : std_logic := '0';
begin
    if nPRESET = '0' and preset_latch = '0' then
        preset_latch := '1';
        wait for C_T_preset;
        --report("Got nPRESET");
    elsif SENSE = '1' and preset_latch = '1' then
        preset_latch := '0';
        wait for C_T_read;
        DO <= efuse_array(get_pin_int(\LINE\));
        --report("Read operation. Addr = " & TO_HSTRING(ADDR) & ", data = " & TO_HSTRING(efuse_array(to_integer(unsigned(ADDR)))));
    elsif and(COL_PROG) = '0' then
		for i in 0 to WDT - 1 loop
			if (efuse_array(get_pin_int(\LINE\))(i) = '0') and ((not COL_PROG(i)) = '1') then
				efuse_array(get_pin_int(\LINE\))(i) <= '1';
			end if;
		end loop;
		wait for C_T_write;
        --report("Program operation. Addr = " & TO_HSTRING(ADDR) & ", data = " & TO_HSTRING(COL_PROG));
    else
		wait for 1 ns;
    end if;
end process;

assert not(nPRESET = '0' and SENSE = '1') report "Error! Wrong nPRESET and SENSE position!" severity failure;
assert not(SENSE = '1' and (and(COL_PROG) = '0')) report "Error! Programming while data read!" severity failure;

--VDD <= 'Z';
--VSS <= 'Z';

--~ POWERCHECK : process 
--~ begin
	--~ wait for 10 ns;
	--~ if VDD /= '1' then
		--~ report "Error! No VDD connection!" severity failure;
	--~ end if;
	--~ if VSS /= '0' then
		--~ report "Error! No VSS connection!" severity failure;
	--~ end if;	
--~ end process;

end architecture;
