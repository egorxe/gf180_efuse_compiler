library ieee;
    use ieee.std_logic_1164.all;
    use ieee.numeric_std.all;
    use ieee.std_logic_unsigned.all;


entity efuse_bank is
    generic (
      DATA_WDT : integer := 8;
      ADDR_WDT : integer := 7  
    );
    port (
        -- interface
        nPRESET : in std_logic;
        SENSE : in std_logic;
        PROG_ENA : in std_logic_vector(DATA_WDT - 1 downto 0);
        DO : out std_logic_vector(DATA_WDT - 1 downto 0);
        ADDR : in std_logic_vector(ADDR_WDT - 1 downto 0)     
    );
end efuse_bank;

architecture rtl of efuse_bank is
component efuse_array
    port (
        nPRESET : in std_logic;
        SENSE : in std_logic;
        COL_PROG : in std_logic_vector(DATA_WDT - 1 downto 0);
        DO : out std_logic_vector(DATA_WDT - 1 downto 0);
        \LINE\ : in std_logic_vector(2**ADDR_WDT - 1 downto 0)
    );
end component;
-- component efuse_array
    -- port (
        -- nPRESET : in std_logic;
        -- SENSE : in std_logic;
        -- COL_PROG : in std_logic_vector(DATA_WDT - 1 downto 0);
        -- DO : out std_logic_vector(8 - 1 downto 0);
        -- \LINE\ : in std_logic_vector(2**ADDR_WDT - 1 downto 0)
    -- );
-- end component;

component addr_sel
    generic(
        ADDR_WDT     : integer := 4;
        NUM          : integer := 16
    );
    port (
        addr_i      : in std_logic_vector(ADDR_WDT - 1 downto 0);
        sel         : out std_logic_vector(NUM - 1 downto 0)
    );
end component;

component tech_buf
    port (
        I   : in  std_logic;
        Z   : out std_logic
    );
end component;
  
signal SEL : std_logic_vector(2**ADDR_WDT - 1 downto 0);    

signal nPRESET_buf, SENSE_buf : std_logic;
  
begin

-- Buffers needed to ensure necessary drive strength
sense_buf_cell : tech_buf
    port map (
        I  => SENSE,
        Z  => SENSE_buf
    );

npreset_buf_cell : tech_buf
    port map (
        I  => nPRESET,
        Z  => nPRESET_buf
    );


efuse_array_inst : efuse_array
    port map (
      nPRESET => nPRESET,
      SENSE => SENSE,
      COL_PROG => not PROG_ENA, -- #WARNING! pMOS FETs on prog lines!
      DO => DO,
      \LINE\ => SEL
    );
      
addr_sel_inst : addr_sel
    generic map (
      ADDR_WDT  => ADDR_WDT,
      NUM       => 2**ADDR_WDT
    )
    port map (
      addr_i => ADDR,
      sel => SEL
    );
  

end rtl;
