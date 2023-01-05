library ieee;
    use ieee.std_logic_1164.all;
    use ieee.numeric_std.all;
    use ieee.std_logic_unsigned.all;

entity addr_sel is
    generic(
        ADDR_WDT     : integer := 4;
        NUM          : integer := 16
    );
    port (
        addr_i      : in std_logic_vector(ADDR_WDT - 1 downto 0);
        sel         : out std_logic_vector(NUM - 1 downto 0)
    );
end addr_sel;

architecture rtl of addr_sel is

begin
    DMX : process(addr_i)
    begin
        sel <= (others => '0');
        sel(to_integer(unsigned(addr_i))) <= '1';
        --~ for i in 0 to 2**ADDR_WDT - 1 loop
            --~ if i = sel then
                --~ sel(i) <= '1';
            --~ end if;            
        --~ end loop;
    end process;
end rtl;
