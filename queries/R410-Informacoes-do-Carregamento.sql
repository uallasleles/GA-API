-- INFORMAÇÕES DO CARREGAMENTO
SELECT 
	-- ------------------------------
    -- Dados do Veículo
	-- ------------------------------
	C.NUMCAR, 
    C.CODMOTORISTA, 
    E.NOME AS MOTORISTA,
    C.CODVEICULO, 
    V.PLACA, 
	-- ------------------------------
	-- Datas/Horários de Movimentação
	-- ------------------------------
    C.DTSAIDA, 			-- Saída
    C.DTSAIDAVEICULO,
    C.DTFECHA, 			-- Fechamento
    C.HORAFECHA, 
    C.MINUTOFECHA, 
    C.SEGUNDOSFECHA, 
    C.DTRETORNO, 		-- Retorno
    C.KMINICIAL, 		-- Kilometragem
    C.KMFINAL,
	-- ------------------------------
    -- Dados Financeiros do Caixa
	-- ------------------------------
	C.CODCAIXA, 
    C.DTCAIXA, 
    C.PERCOM, 
    C.TRANSFERENCIA, 
    C.VLVALERETENCAO, 
    C.LANCARDESPDESCFINAUTOMATIC
FROM CHOCOSUL.PCCARREG C
	LEFT JOIN CHOCOSUL.PCVEICUL V ON C.CODVEICULO = V.CODVEICULO
	LEFT JOIN CHOCOSUL.PCEMPR E   ON C.CODMOTORISTA = E.MATRICULA
WHERE C.NUMCAR = :NUMCAR