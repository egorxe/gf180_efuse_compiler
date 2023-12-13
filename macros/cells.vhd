library ieee;
    use ieee.std_logic_1164.all;
    
entity tech_buf is
    port (
        I : in std_logic;
        Z : out std_logic
    );
end tech_buf;

architecture rtl of tech_buf is

begin
    Z <= I;
end rtl;

library ieee;
    use ieee.std_logic_1164.all;
    
entity tech_inv is
    port (
        I : in std_logic;
        ZN : out std_logic
    );
end tech_inv;

architecture rtl of tech_inv is

begin
    ZN <= not I;
end rtl;
