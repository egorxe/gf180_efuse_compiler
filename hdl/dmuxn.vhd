library ieee;
    use ieee.std_logic_1164.all;
    use ieee.numeric_std.all;
    use ieee.std_logic_unsigned.all;

entity dmuxn is
    generic(
        SEL_WDT     : integer := 4;
        OUT_NUM     : integer := 16
    );
    port (
        data_in     : in std_logic;
        data_out    : out std_logic_vector(OUT_NUM - 1 downto 0);
        sel         : in std_logic_vector(SEL_WDT - 1 downto 0)
    );
end dmuxn;

architecture rtl of dmuxn is

begin
    DMX : process(data_in, sel)
    begin
        data_out <= (others => '0');
        for i in 0 to OUT_NUM - 1 loop
            if i = sel then
                data_out(i) <= data_in;
            end if;
        end loop;
    end process;
end rtl;
