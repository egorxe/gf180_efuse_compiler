library ieee;
    use ieee.std_logic_1164.all;
    use ieee.numeric_std.all;
    use ieee.std_logic_unsigned.all;


entity efuse_rom is
    generic (
      DATA_WDT  : integer := 8;
      ADDR_WDT  : integer := 10;
      BA_WDT    : integer := 3; 
      BANK_NUM  : integer := 8 
    );
    port (
        -- interface
        nPRESET : in std_logic;
        SENSE : in std_logic;
        PROG_ENA : in std_logic_vector(DATA_WDT - 1 downto 0);
        DO : out std_logic_vector(DATA_WDT - 1 downto 0);
        ADDR : in std_logic_vector(ADDR_WDT - 1 downto 0)      
    );
end efuse_rom;

architecture rtl of efuse_rom is
--~ constant BANK_NUM : integer := 2**BA_WDT;
type addr_array_type is array (BANK_NUM - 1 downto 0) of std_logic_vector(ADDR_WDT - BA_WDT - 1 downto 0);
type addr_array_col_type is array (ADDR_WDT - BA_WDT - 1 downto 0) of std_logic_vector(BANK_NUM - 1 downto 0);
type data_array_type is array (BANK_NUM - 1 downto 0) of std_logic_vector(DATA_WDT - 1 downto 0);
signal data_array : data_array_type;
signal data_out_array : data_array_type;
signal addr_array : addr_array_type;
signal addr_array_col : addr_array_col_type;
signal iSENSE : std_logic_vector(BANK_NUM - 1 downto 0);
signal inPRESET : std_logic_vector(BANK_NUM - 1 downto 0);
signal prog_sel : std_logic_vector(BANK_NUM - 1 downto 0);
component efuse_bank
    generic (
        DATA_WDT : integer;
        ADDR_WDT : integer
    );
        port (
        nPRESET : in std_logic;
        SENSE : in std_logic;
        PROG_ENA : in std_logic_vector(DATA_WDT - 1 downto 0);
        DO : out std_logic_vector(DATA_WDT - 1 downto 0);
        ADDR : in std_logic_vector(ADDR_WDT - 1 downto 0)
    );
end component;
      
component dmuxn
    generic(
        SEL_WDT     : integer := 4;
        OUT_NUM     : integer := 16
    );
    port (
        data_in     : in std_logic;
        data_out    : out std_logic_vector(OUT_NUM - 1 downto 0);
        sel         : in std_logic_vector(SEL_WDT - 1 downto 0)
    );
end component;

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

begin

assert (BANK_NUM <= 2**BA_WDT);

gen_efuse_banks : for i in 0 to BANK_NUM - 1 generate
begin
	data_array(i) <= PROG_ENA and prog_sel(i);
    efuse_bank_inst : efuse_bank
        generic map (
            DATA_WDT => DATA_WDT,
            ADDR_WDT => ADDR_WDT - BA_WDT
        )
        port map (
            nPRESET => nPRESET,
            SENSE => SENSE,
            PROG_ENA => data_array(i),
            DO => data_out_array(i),
            ADDR => addr_array(i)
        );
end generate;

gen_bank_dmuxes : for i in 0 to ADDR_WDT - BA_WDT - 1 generate
begin
    muxn_inst : dmuxn
        generic map (
            SEL_WDT => BA_WDT,
            OUT_NUM => BANK_NUM
        )
        port map (
            data_in => ADDR(i),
            data_out => addr_array_col(i),
            sel => ADDR(ADDR_WDT - 1 downto ADDR_WDT - BA_WDT)
        );
end generate;

sense_dmux_inst : dmuxn
	generic map (
		SEL_WDT => BA_WDT,
        OUT_NUM => BANK_NUM
	)
	port map (
		data_in => SENSE,
		data_out => iSENSE,
		sel => ADDR(ADDR_WDT - 1 downto ADDR_WDT - BA_WDT)
	);
	
preset_dmux_inst : dmuxn
	generic map (
		SEL_WDT => BA_WDT,
        OUT_NUM => BANK_NUM
	)
	port map (
		data_in => nPRESET,
		data_out => inPRESET,
		sel => ADDR(ADDR_WDT - 1 downto ADDR_WDT - BA_WDT)
	);

comm_addr_buses : process(addr_array_col)
begin
    for i in 0 to BANK_NUM - 1 loop
        for j in 0 to ADDR_WDT - BA_WDT - 1 loop
            addr_array(i)(j) <= addr_array_col(j)(i);
        end loop;
    end loop;
end process;



prog_bank_sel_inst : addr_sel
    generic map (
      ADDR_WDT  => BA_WDT,
      NUM       => BANK_NUM
    )
    port map (
      addr_i => ADDR(ADDR_WDT - 1 downto ADDR_WDT - BA_WDT),
      sel => prog_sel
    );
    
DO <= data_out_array(to_integer(unsigned(ADDR(ADDR_WDT - 1 downto ADDR_WDT - BA_WDT))));

end rtl;
