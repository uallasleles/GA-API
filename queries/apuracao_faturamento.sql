-- ROTINA WinThor 1464: APURAÇÃO DE FATURAMENTO POR FORNECEDOR
--------------------------------------------------------------------------------
-- Objetivo: Consolidação de Vendas, Devoluções, Metas e Lucratividade
-- Período de Apuração: 17/05/2026 a 13/06/2026
-- Parâmetros: CODFORNEC | CODFILIAL 
-- Filtros Fixos: Usuário PCLIB 1639
--------------------------------------------------------------------------------

SELECT  
    :DTENT_INICIO AS DTENT_INICIO,
    :DTENT_FIM AS DTENT_FIM,
    :codfilial AS CODFILIAL,

    -- Identificação do Fornecedor (Prioriza a tabela de Vendas, senão busca de Devoluções)
    DECODE(VENDAS.CODFORNEC, '', DEVOLUCAO.CODFORNEC, VENDAS.CODFORNEC) AS CODFORNEC,
    DECODE(VENDAS.FORNECEDOR, '', DEVOLUCAO.FORNECEDOR, VENDAS.FORNECEDOR) AS FORNECEDOR, 
    VENDAS.ROTA,
    VENDAS.DESCROTA,
    
    -- Indicadores Financeiros Líquidos (Vendas - Devoluções)
    SUM(NVL(VENDAS.VLREPASSE, 0) - NVL(DEVOLUCAO.VLREPASSE, 0)) AS VLREPASSE,
    SUM(NVL(VENDAS.QTVENDA, 0) - NVL(DEVOLUCAO.QTDEVOLUCAO, 0)) AS QTVENDA,
    SUM(NVL(VENDAS.VLVENDA, 0) - NVL(DEVOLUCAO.VLDEVOLUCAO, 0)) AS VLVENDA,
    SUM(NVL(VENDAS.VLVENDA_SEMST, 0) - NVL(DEVOLUCAO.VLDEVOLUCAO_SEMST, 0)) AS VLVENDA_SEMST,
    
    -- Indicadores Exclusivos de Devolução
    SUM(NVL(DEVOLUCAO.VLDEVOLUCAO, 0)) AS VLDEVOLUCAO,
    SUM(NVL(DEVOLUCAO.VLDEVOLUCAO_SEMST, 0)) AS VLDEVOLUCAO_SEMST,
    
    -- Peso e Preço Médio
    SUM(NVL(VENDAS.TOTPESO, 0) - NVL(DEVOLUCAO.TOTPESO, 0)) AS TOTPESO,
    ROUND((SUM(NVL(VENDAS.VLVENDA, 0)) / DECODE(SUM(NVL(VENDAS.QTVENDA, 0)), 0, 1, SUM(NVL(VENDAS.QTVENDA, 0)))), 2) AS PRECOMEDIO,
    ROUND((SUM(NVL(VENDAS.VLVENDA, 0)) / DECODE(SUM(NVL(VENDAS.QTVENDA, 0)), 0, 1, SUM(NVL(VENDAS.QTVENDA, 0)))), 2) AS PRECOMEDIONF,
    
    -- Positivação, Bonificação e Notas Fiscais
    SUM(DISTINCT(VENDAS.QTCLIPOS)) AS QTCLIPOS, 
    SUM(NVL(VENDAS.VLBONIFIC, 0)) AS VLBONIFIC,
    SUM(DISTINCT(VENDAS.QTNFVENDA)) AS QTNFVENDA, 
    
    -- Mix de Produtos (Ativos vs Vendidos)
    (SELECT COUNT(P.CODPROD) FROM PCPRODUT P WHERE P.CODFORNEC = VENDAS.CODFORNEC AND NVL(P.REVENDA, 'S') = 'S') AS QTMIX,
    SUM(DISTINCT(VENDAS.MIXVENDA)) AS MIXVENDA, 
    
    -- Custos e Quantidades brutas
    SUM(NVL(VLCUSTOFIN, 0) - 0) AS VLCUSTOFIN,
    SUM(NVL(QTVENDIDA, 0)) AS QTVENDIDA,
    SUM(NVL(DEVOLUCAO.QTDEVOLUCAO, 0)) AS QTDEVOLUCAO,
    
    -- Metas Comerciais (trazidas do bloco META)
    NVL(META.VLMETA, 0) AS VLMETA,
    NVL(META.QTMETA, 0) AS QTMETA,
    NVL(META.QTPESOMETA, 0) AS QTPESOMETA,
    NVL(META.MIXPREV, 0) AS MIXPREV,
    NVL(META.CLIPOSPREV, 0) AS CLIPOSPREV,
    
    -- Margem e Lucratividade
    SUM(NVL(VENDAS.VLVENDA, 0) - NVL(DEVOLUCAO.VLDEVOLUCAO, 0) - NVL(VENDAS.VLCUSTOFIN, 0)) AS VLLUCRO,
    SUM(NVL(VENDAS.VLVENDA_SEMST, 0) - NVL(DEVOLUCAO.VLDEVOLUCAO_SEMST, 0) - NVL(VENDAS.VLCUSTOFIN, 0)) AS VLLUCRO_SEMST,
    
    -- Volume e Litragem
    SUM(NVL(VENDAS.VOLUME, 0) - NVL(DEVOLUCAO.VOLUME, 0)) AS VOLUME,
    SUM(NVL(VENDAS.LITRAGEM, 0) - NVL(DEVOLUCAO.LITRAGEM, 0)) AS LITRAGEM,
    SUM(NVL(VENDAS.VLREPASSEBNF, 0) - NVL(DEVOLUCAO.VLREPASSEBNF, 0)) AS VLREPASSEBNF 

FROM  
    ----------------------------------------------------------------------------
    -- SUBQUERY 1: COMPILADO DE VENDAS (FATURAMENTO BRUTO)
    ----------------------------------------------------------------------------
    (
        SELECT 
            CODFORNEC,
            0 AS ROTA,
            '' AS DESCROTA,
            FORNECEDOR,
            SUM(NVL(QTVENDA, 0)) AS QTVENDA,
            SUM(NVL(VLVENDA, 0) + NVL(VALORST, 0) + NVL(VALORIPI, 0)) AS VLVENDA,
            SUM(NVL(VLVENDA_SEMST, 0)) AS VLVENDA_SEMST,
            SUM(NVL(TOTPESO, 0)) AS TOTPESO,
            COUNT(DISTINCT(QTCLIPOS)) AS QTCLIPOS, 
            SUM(NVL(VLBONIFIC, 0)) AS VLBONIFIC,
            COUNT(DISTINCT(QTNUMTRANSVENDA)) AS QTNFVENDA, 
            COUNT(DISTINCT(CODPROD)) AS MIXVENDA, 
            COUNT(DISTINCT(CODPROD)) AS TOTMIX, 
            SUM(NVL(VLCUSTOFIN, 0)) AS VLCUSTOFIN,
            SUM(NVL(QTVENDIDA, 0)) AS QTVENDIDA,
            SUM(NVL(VOLUME, 0)) AS VOLUME,
            SUM(NVL(VLREPASSE, 0)) AS VLREPASSE,
            SUM(LITRAGEM) AS LITRAGEM, 
            SUM(NVL(VLREPASSEBNF, 0)) AS VLREPASSEBNF 
        FROM (  
            SELECT 
                PCNFSAID.CODCLI, 
                PCATIVI.RAMO,    
                PCMOV.CODPROD, 
                PCATIVI.CODATIV, 
                PCNFSAID.CODUSUR,     
                PCNFSAID.NUMTRANSVENDA, 
                NVL(PCNFSAID.CODSUPERVISOR, PCSUPERV.CODSUPERVISOR) AS CODSUPERVISOR, 
                PCNFSAID.CODFILIAL, 
                PCPRODUT.CODAUXILIAR, 
                PCCLIENT.CLIENTE,
                PCFORNEC.CODFORNECPRINC,
                PCFORNEC.FORNECEDOR,
                PCFORNEC.CODFORNEC,
                PCUSUARI.NOME, 
                PCSUPERV.NOME AS SUPERV, 
                PCPRODUT.CODEPTO, 
                PCPRODUT.CODSEC, 
                PCDEPTO.DESCRICAO AS DEPARTAMENTO, 
                PCSECAO.DESCRICAO AS SECAO, 
                PCNFSAID.CODPRACA, 
                PCPRACA.PRACA, 
                PCPRODUT.CODMARCA, 
                PCPRODUT.QTUNIT, 
                PCMARCA.MARCA, 
                PCCLIENT.ESTENT, 
                PCCLIENT.MUNICENT,
                PCCLIENT.CODCIDADE,
                PCCIDADE.NOMECIDADE,
                NVL(PCCLIENT.CODCLIPRINC, PCCLIENT.CODCLI) AS CODCLIPRINC, 
                ROUND((NVL(PCPRODUT.VOLUME, 0) * NVL(PCMOV.QT, 0)), 2) AS VOLUME, 
                (NVL(PCPRODUT.LITRAGEM, 0) * NVL(PCMOV.QT, 0)) AS LITRAGEM, 
                PCPRODUT.DESCRICAO,
                PCPRODUT.EMBALAGEM,
                PCPRODUT.UNIDADE,
                PCPRODUT.CODFAB,
                PCNFSAID.CODPLPAG,
                PCNFSAID.NUMPED,
                PCNFSAID.CODCOB,
                PCCLIENT.CODPLPAG AS CODPLANOCLI,
                PCPLPAG.DESCRICAO AS DESCRICAOPCPLPAG,
                PCPLPAG.NUMDIAS, 
                0 AS QTMETA,
                0 AS QTPESOMETA,
                0 AS MIXPREV,
                0 AS CLIPOSPREV,
                
                -- Cálculo de Repasse de Bonificação
                ROUND((DECODE(PCMOV.CODOPER, 'SB', PCMOV.QTCONT, 0)) * NVL(PCMOV.VLREPASSE, 0), 2) AS VLREPASSEBNF,              
                
                -- Cálculo de IPI e ST
                ROUND((NVL(PCMOV.QT, 0) * DECODE(PCNFSAID.CONDVENDA, 5,0, 6,0, 11,0, 12,0, DECODE(PCMOV.CODOPER, 'SB', 0, NVL(PCMOV.VLIPI, 0)))), 2) AS VALORIPI,
                ROUND(NVL(PCMOV.QT, 0) * DECODE(PCNFSAID.CONDVENDA, 5,0, 6,0, 11,0, 12,0, DECODE(PCMOV.CODOPER, 'SB', 0, (NVL(PCMOV.ST, 0) + NVL(PCMOVCOMPLE.VLSTTRANSFCD, 0)))), 2) AS VALORST,
                
                -- Quantidade Comercializada (Filtra operações válidas de venda: S, SM, ST, SB)
                ((DECODE(PCMOV.CODOPER, 'S', (NVL(DECODE(PCNFSAID.CONDVENDA, 7, PCMOV.QTCONT, PCMOV.QT), 0)), 
                                        'SM', (NVL(DECODE(PCNFSAID.CONDVENDA, 7, PCMOV.QTCONT, PCMOV.QT), 0)), 
                                        'ST', (NVL(DECODE(PCNFSAID.CONDVENDA, 7, PCMOV.QTCONT, PCMOV.QT), 0)), 
                                        'SB', (NVL(DECODE(PCNFSAID.CONDVENDA, 7, PCMOV.QTCONT, PCMOV.QT), 0)), 0))) AS QTVENDA, 
                
                -- Custo Financeiro Total da Venda
                ((DECODE(PCMOV.CODOPER, 'S', (NVL(DECODE(PCNFSAID.CONDVENDA, 7, PCMOV.QTCONT, PCMOV.QT), 0)), 
                                        'ST', (NVL(DECODE(PCNFSAID.CONDVENDA, 7, PCMOV.QTCONT, PCMOV.QT), 0)), 
                                        'SM', (NVL(DECODE(PCNFSAID.CONDVENDA, 7, PCMOV.QTCONT, PCMOV.QT), 0)), 
                                        'SB', (NVL(DECODE(PCNFSAID.CONDVENDA, 7, PCMOV.QTCONT, PCMOV.QT), 0)), 0)) * NVL(PCMOV.CUSTOFIN, 0)) AS VLCUSTOFIN,  
                
                -- Cálculo Complexo do Valor de Venda Líquido (Tratando Subtotais, Fretes, IPI e ST)
                CASE 
                    WHEN NVL(PCMOVCOMPLE.VLSUBTOTITEM, 0) <> 0 THEN  
                        DECODE(NVL(PCMOV.TIPOITEM, 'N'), 'I', 0, NVL(PCMOVCOMPLE.VLSUBTOTITEM, 0) + (DECODE(NVL(PCMOV.TIPOITEM, 'N'), 'I', NVL(PCMOV.QTCONT, 0), 0) * NVL(PCMOV.VLFRETE, 0))) - 
                        (ROUND((NVL(PCMOV.QT, 0) * DECODE(PCNFSAID.CONDVENDA, 5,0, 6,0, 11,0, 12,0, DECODE(PCMOV.CODOPER, 'SB', 0, NVL(PCMOV.VLIPI, 0)))), 2)) -  
                        (ROUND(NVL(PCMOV.QT, 0) * DECODE(PCNFSAID.CONDVENDA, 5,0, 6,0, 11,0, 12,0, DECODE(PCMOV.CODOPER, 'SB', 0, NVL(PCMOV.ST, 0))), 2)) 
                    ELSE                                                
                        ROUND((((DECODE(PCMOV.CODOPER, 'S', (NVL(DECODE(PCNFSAID.CONDVENDA, 7, PCMOV.QTCONT, PCMOV.QT), 0)), 
                                                       'ST', (NVL(DECODE(PCNFSAID.CONDVENDA, 7, PCMOV.QTCONT, PCMOV.QT), 0)), 
                                                       'SM', (NVL(DECODE(PCNFSAID.CONDVENDA, 7, PCMOV.QTCONT, PCMOV.QT), 0)), 0)) * (NVL(DECODE(PCNFSAID.CONDVENDA, 7, 
                                    (NVL(PUNITCONT, 0) - NVL(PCMOV.VLIPI, 0) - (NVL(PCMOV.ST, 0) + NVL(PCMOVCOMPLE.VLSTTRANSFCD, 0))) + NVL(PCMOV.VLFRETE, 0) + NVL(PCMOV.VLOUTRASDESP, 0) + NVL(PCMOV.VLFRETE_RATEIO, 0) + DECODE(PCMOV.TIPOITEM, 'C', (SELECT NVL((SUM(M.QTCONT * NVL(M.VLOUTROS, 0)) / PCMOV.QT), 0) FROM PCMOV M WHERE M.NUMTRANSVENDA = PCMOV.NUMTRANSVENDA AND M.TIPOITEM = 'I' AND CODPRODPRINC = PCMOV.CODPROD), 'I', NVL(PCMOV.VLOUTROS, 0), DECODE(NVL(PCNFSAID.SOMAREPASSEOUTRASDESPNF, 'N'), 'N', NVL(PCMOV.VLOUTROS, 0), 'S', NVL((NVL(PCMOV.VLOUTROS, 0) - NVL(PCMOV.VLREPASSE, 0)), 0))),
                                    (NVL(PCMOV.PUNIT, 0) - NVL(PCMOV.VLIPI, 0) - (NVL(PCMOV.ST, 0) + NVL(PCMOVCOMPLE.VLSTTRANSFCD, 0))) + NVL(PCMOV.VLFRETE, 0) + NVL(PCMOV.VLOUTRASDESP, 0) + NVL(PCMOV.VLFRETE_RATEIO, 0) + DECODE(PCMOV.TIPOITEM, 'C', (SELECT NVL((SUM(M.QTCONT * NVL(M.VLOUTROS, 0)) / PCMOV.QT), 0) FROM PCMOV M WHERE M.NUMTRANSVENDA = PCMOV.NUMTRANSVENDA AND M.TIPOITEM = 'I' AND CODPRODPRINC = PCMOV.CODPROD), 'I', NVL(PCMOV.VLOUTROS, 0), DECODE(NVL(PCNFSAID.SOMAREPASSEOUTRASDESPNF, 'N'), 'N', NVL(PCMOV.VLOUTROS, 0), 'S', NVL((NVL(PCMOV.VLOUTROS, 0) - NVL(PCMOV.VLREPASSE, 0)), 0)))
                               ), 0)))), 2) 
                END AS VLVENDA,                                                 
                                                                                
                -- Faturamento Sem Substituição Tributária (ST)
                (((DECODE(PCMOV.CODOPER, 'S', (NVL(DECODE(PCNFSAID.CONDVENDA, 7, PCMOV.QTCONT, PCMOV.QT), 0)), 
                                        'ST', (NVL(DECODE(PCNFSAID.CONDVENDA, 7, PCMOV.QTCONT, PCMOV.QT), 0)), 
                                        'SM', (NVL(DECODE(PCNFSAID.CONDVENDA, 7, PCMOV.QTCONT, PCMOV.QT), 0)), 0)) * (NVL(DECODE(PCNFSAID.CONDVENDA, 7, PCMOV.PUNITCONT, NVL(PCMOV.PUNIT, 0) + NVL(PCMOV.VLFRETE, 0) + NVL(PCMOV.VLOUTRASDESP, 0) + NVL(PCMOV.VLFRETE_RATEIO, 0) + DECODE(PCMOV.TIPOITEM, 'C', (SELECT (SUM(M.QTCONT * NVL(M.VLOUTROS, 0)) / PCMOV.QT) FROM PCMOV M WHERE M.NUMTRANSVENDA = PCMOV.NUMTRANSVENDA AND M.TIPOITEM = 'I' AND CODPRODPRINC = PCMOV.CODPROD), 'I', NVL(PCMOV.VLOUTROS, 0), DECODE(NVL(PCNFSAID.SOMAREPASSEOUTRASDESPNF, 'N'), 'N', NVL(PCMOV.VLOUTROS, 0), 'S', NVL((NVL(PCMOV.VLOUTROS, 0) - NVL(PCMOV.VLREPASSE, 0)), 0))) - (NVL(PCMOV.ST, 0) + NVL(PCMOVCOMPLE.VLSTTRANSFCD, 0))), 0)))) AS VLVENDA_SEMST,                                              
                
                -- Valores de Bonificação por Condição de Venda
                ROUND((NVL(PCMOV.QT, 0) * (DECODE(PCNFSAID.CONDVENDA, 5, DECODE(PCMOV.PBONIFIC, NULL, PCMOV.PTABELA, PCMOV.PBONIFIC), 6, DECODE(PCMOV.PBONIFIC, NULL, PCMOV.PTABELA, PCMOV.PBONIFIC), 11, DECODE(PCMOV.PBONIFIC, NULL, PCMOV.PTABELA, PCMOV.PBONIFIC), 1, NVL(PCMOV.PBONIFIC, 0), 14, NVL(PCMOV.PBONIFIC, 0), 12, DECODE(PCMOV.PBONIFIC, NULL, PCMOV.PTABELA, PCMOV.PBONIFIC), 0))), 2) AS VLBONIFIC,
                
                ((DECODE(PCMOV.CODOPER, 'S', (NVL(DECODE(PCNFSAID.CONDVENDA, 7, PCMOV.QTCONT, PCMOV.QT), 0)), 'ST', (NVL(DECODE(PCNFSAID.CONDVENDA, 7, PCMOV.QTCONT, PCMOV.QT), 0)), 'SM', (NVL(DECODE(PCNFSAID.CONDVENDA, 7, PCMOV.QTCONT, PCMOV.QT), 0)), 0))) AS QTVENDIDA,
                ROUND((NVL(PCPRODUT.PESOBRUTO, PCMOV.PESOBRUTO) * NVL(PCMOV.QT, 0)), 2) AS TOTPESO,
                ROUND(PCMOV.QT * (PCMOV.PTABELA + NVL(PCMOV.VLFRETE, 0) + NVL(PCMOV.VLOUTRASDESP, 0) + NVL(PCMOV.VLFRETE_RATEIO, 0) + NVL(PCMOV.VLOUTROS, 0)), 2) AS VLTABELA,
                PCMOV.CODCLI AS QTCLIPOS,
                PCNFSAID.NUMTRANSVENDA AS QTNUMTRANSVENDA, 
                PCMOV.CODPROD AS QTMIX, 
                PCGERENTE.NOMEGERENTE,
                DECODE(PCNFSAID.CODGERENTE, NULL, PCSUPERV.CODGERENTE, PCNFSAID.CODGERENTE) AS CODGERENTE, 
                PCPRACA.ROTA,
                PCROTAEXP.DESCRICAO AS DESCROTA,
                (NVL(PCMOV.VLREPASSE, 0) * DECODE(PCNFSAID.CONDVENDA, 5,0, 6,0, 11,0, 12,0, DECODE(PCMOV.CODOPER, 'SB', 0, NVL(PCMOV.QT, 0)))) AS VLREPASSE
            FROM 
                PCNFSAID, PCPRODUT, PCMOV, PCCLIENT, PCUSUARI, PCSUPERV, PCPLPAG, 
                PCFORNEC, PCATIVI, PCPRACA, PCDEPTO, PCSECAO, PCPEDC, PCGERENTE, 
                PCCIDADE, PCMARCA, PCROTAEXP, PCMOVCOMPLE
            WHERE 
                PCMOV.NUMTRANSVENDA = PCNFSAID.NUMTRANSVENDA
                AND PCMOV.CODFILIAL = PCNFSAID.CODFILIAL 
                
                -- Filtros Críticos de Data, Fornecedor e Filial
                AND PCMOV.DTMOV BETWEEN TO_DATE(:DTENT_INICIO, 'DD/MM/YYYY') AND TO_DATE(:DTENT_FIM, 'DD/MM/YYYY') 
                AND PCNFSAID.DTSAIDA BETWEEN TO_DATE(:DTENT_INICIO, 'DD/MM/YYYY') AND TO_DATE(:DTENT_FIM, 'DD/MM/YYYY') 
                AND PCPRODUT.CODFORNEC IN (:codfornec)
                AND PCMOV.CODFILIAL IN (:codfilial)
                AND PCNFSAID.CODFILIAL IN (:codfilial)
                
                -- Joins de Relacionamento das Tabelas
                AND PCMOV.CODPROD = PCPRODUT.CODPROD
                AND PCNFSAID.CODPRACA = PCPRACA.CODPRACA(+)
                AND PCATIVI.CODATIV(+) = PCCLIENT.CODATV1
                AND PCMOV.CODCLI = PCCLIENT.CODCLI
                AND PCFORNEC.CODFORNEC = PCPRODUT.CODFORNEC
                AND PCNFSAID.CODUSUR = PCUSUARI.CODUSUR 
                AND PCPRACA.ROTA = PCROTAEXP.CODROTA(+)
                AND PCMOV.NUMTRANSITEM = PCMOVCOMPLE.NUMTRANSITEM(+)
                AND PCPRODUT.CODMARCA = PCMARCA.CODMARCA(+)
                AND PCCLIENT.CODCIDADE = PCCIDADE.CODCIDADE(+)
                AND PCNFSAID.CODPLPAG = PCPLPAG.CODPLPAG
                AND PCNFSAID.NUMPED = PCPEDC.NUMPED(+)
                AND PCPRODUT.CODEPTO = PCDEPTO.CODEPTO(+)
                AND PCPRODUT.CODSEC = PCSECAO.CODSEC(+)
                
                -- Filtros de Controle Operacional (Exclui Devoluções/Remessas e Status Inválidos)
                AND PCMOV.CODOPER <> 'SR' 
                AND NVL(PCNFSAID.TIPOVENDA, 'X') NOT IN ('SR', 'DF')
                AND PCMOV.CODOPER <> 'SO' 
                AND NVL(PCNFSAID.CODSUPERVISOR, PCSUPERV.CODSUPERVISOR) = PCSUPERV.CODSUPERVISOR
                AND NVL(PCNFSAID.CODGERENTE, PCSUPERV.CODGERENTE) = PCGERENTE.CODGERENTE 
                AND PCNFSAID.CODFISCAL NOT IN (522, 622, 722, 532, 632, 732)
                AND PCNFSAID.CONDVENDA NOT IN (4, 8, 10, 13, 20, 98, 99)
                AND PCNFSAID.DTCANCEL IS NULL
                
                -- Validação de Permissões de Usuário (Módulo PCLIB do WinThor)
                AND (NVL(PCNFSAID.CODSUPERVISOR, PCSUPERV.CODSUPERVISOR) IN (SELECT CODIGON FROM PCLIB WHERE CODFUNC IN (1639) AND CODTABELA = 7)) 
                AND (PCPRODUT.CODFORNEC IN (SELECT CODIGON FROM PCLIB WHERE CODFUNC IN (1639) AND CODTABELA = 3)) 
                AND (PCPRODUT.CODEPTO IN (SELECT CODIGON FROM PCLIB WHERE CODFUNC IN (1639) AND CODTABELA = 2)) 
        )
        GROUP BY 
            CODFORNEC, 0, '', FORNECEDOR
    ) VENDAS,
    
    ----------------------------------------------------------------------------
    -- SUBQUERY 2: METAS COMERCIAIS (PCMETA)
    ----------------------------------------------------------------------------
    (
        SELECT 
            CODFORNEC, 
            SUM(NVL(VLMETA, 0)) AS VLMETA,
            SUM(NVL(QTMETA, 0)) AS QTMETA,
            SUM(NVL(QTPESOMETA, 0)) AS QTPESOMETA,
            SUM(NVL(MIXPREV, 0)) AS MIXPREV,
            SUM(NVL(CLIPOSPREV, 0)) AS CLIPOSPREV
        FROM (
            SELECT 
                NVL(PCMETA.VLVENDAPREV, 0) AS VLMETA,
                NVL(PCMETA.QTVENDAPREV, 0) AS QTMETA,
                NVL(PCMETA.QTPESOPREV, 0) AS QTPESOMETA,
                NVL(PCMETA.MIXPREV, 0) AS MIXPREV,
                NVL(PCMETA.CLIPOSPREV, 0) AS CLIPOSPREV,
                PCFORNEC.CODFORNEC
            FROM 
                PCMETA, PCUSUARI, PCSUPERV, PCPRODUT, PCDEPTO, PCSECAO, PCFORNEC, PCTEMP_SELECIONADOS
            WHERE 
                PCMETA.CODUSUR = PCUSUARI.CODUSUR
                AND PCUSUARI.CODSUPERVISOR = PCSUPERV.CODSUPERVISOR
                AND PCUSUARI.CODSUPERVISOR NOT IN ('9999')
                AND PCMETA.TIPOMETA = 'P' -- Meta por Produto
                AND PCPRODUT.CODPROD = PCMETA.CODIGO
                AND PCPRODUT.CODEPTO = PCDEPTO.CODEPTO(+)
                AND PCPRODUT.CODSEC = PCSECAO.CODSEC(+)
                AND PCPRODUT.CODFORNEC = PCFORNEC.CODFORNEC(+)
                
                -- Filtros de Período da Meta e Filial
                AND PCMETA.DATA BETWEEN TO_DATE('01/05/2026', 'DD/MM/YYYY') AND TO_DATE(:DTENT_FIM, 'DD/MM/YYYY') 
                AND NVL(PCMETA.CODFILIAL, ' ') IN (:codfilial)
                AND PCPRODUT.CODFORNEC = PCTEMP_SELECIONADOS.NUMERO
                
                -- Segurança / Permissões (PCLIB)
                AND (PCFORNEC.CODFORNEC IN (SELECT CODIGON FROM PCLIB WHERE CODFUNC IN (1639) AND CODTABELA = 3)) 
                AND (PCDEPTO.CODEPTO IN (SELECT CODIGON FROM PCLIB WHERE CODFUNC IN (1639) AND CODTABELA = 2)) 
                AND (PCUSUARI.CODSUPERVISOR IN (SELECT CODIGON FROM PCLIB WHERE CODFUNC IN (1639) AND CODTABELA = 7)) 
        )
        GROUP BY 
            CODFORNEC
    ) META,
     
    ----------------------------------------------------------------------------
    -- SUBQUERY 3: DEVOLUÇÕES DE CLIENTES (PCNFENT / PCMOV / PCESTCOM)
    ----------------------------------------------------------------------------
    ( 
        SELECT 
            CODFORNEC,
            FORNECEDOR,
            0 AS ROTA,
            '' AS DESCROTA,
            SUM(NVL(QTDEVOLUCAO, 0)) AS QTDEVOLUCAO,
            SUM(NVL(VLDEVOLUCAO, 0)) AS VLDEVOLUCAO,
            SUM(NVL(VLDEVOLUCAO_SEMST, 0)) AS VLDEVOLUCAO_SEMST,
            SUM(NVL(TOTPESO, 0)) AS TOTPESO,
            SUM(NVL(VOLUME, 0)) AS VOLUME,
            COUNT(DISTINCT(CODPROD)) AS MIXVENDA, 
            SUM(NVL(VLBONIFIC, 0)) AS VLBONIFIC, 
            SUM(NVL(VLREPASSEBNF, 0)) AS VLREPASSEBNF, 
            SUM(NVL(VLREPASSE, 0)) AS VLREPASSE,
            SUM(NVL(LITRAGEM, 0)) AS LITRAGEM 
        FROM (
            SELECT 
                PCFORNEC.CODFORNEC, 
                PCFORNEC.FORNECEDOR, 
                PCMOV.CODPROD,
                (NVL(PCMOV.QT, 0)) AS QTDEVOLUCAO,
                (NVL(PCPRODUT.LITRAGEM, 0) * NVL(PCMOV.QT, 0)) AS LITRAGEM,                      
                (NVL(PCPRODUT.VOLUME, 0) * NVL(PCMOV.QT, 0)) AS VOLUME,                          
                (NVL(PCPRODUT.PESOBRUTO, PCMOV.PESOBRUTO) * NVL(PCMOV.QT, 0)) AS TOTPESO,
                
                -- Valores Líquidos de Repasse em Devoluções
                ROUND(DECODE(PCNFSAID.CONDVENDA, 5,0, DECODE(NVL(PCMOVCOMPLE.BONIFIC, 'N'), 'N', NVL(PCMOV.QT, 0), 0)) * NVL(PCMOV.VLREPASSE, 0), 2) AS VLREPASSE,                                
                ROUND(DECODE(PCNFSAID.CONDVENDA, 5, NVL(PCMOV.QT, 0), DECODE(NVL(PCMOVCOMPLE.BONIFIC, 'N'), 'N', 0, NVL(PCMOV.QT, 0), 0)) * NVL(PCMOV.VLREPASSE, 0), 2) AS VLREPASSEBNF,                             
                
                -- Cálculo do Valor Financeiro de Devolução Entrada
                CASE 
                    WHEN NVL(PCMOVCOMPLE.VLSUBTOTITEM, 0) <> 0 THEN  
                        NVL(PCMOVCOMPLE.VLSUBTOTITEM, 0) -                  
                        (ROUND((NVL(PCMOV.QT, 0) * DECODE(PCNFSAID.CONDVENDA, 5,0, 6,0, 11,0, 12,0, DECODE(PCMOV.CODOPER, 'SB', 0, NVL(PCMOV.VLIPI, 0)))), 2)) -  
                        (ROUND(NVL(PCMOV.QT, 0) * DECODE(PCNFSAID.CONDVENDA, 5,0, 6,0, 11,0, 12,0, DECODE(PCMOV.CODOPER, 'SB', 0, NVL(PCMOV.ST, 0))), 2)) 
                    ELSE                                                
                        ROUND((DECODE(PCNFSAID.CONDVENDA, 5, 0, DECODE(NVL(PCMOVCOMPLE.BONIFIC, 'N'), 'N', NVL(PCMOV.QT, 0), 0)) * DECODE(PCNFSAID.CONDVENDA, 5,0, 6,0, 11,0, (DECODE(PCMOV.PUNIT, 0, PCMOV.PUNITCONT, NULL, PCMOV.PUNITCONT, PCMOV.PUNIT) + NVL(PCMOV.VLFRETE, 0) + NVL(PCMOV.VLOUTRASDESP, 0) + NVL(PCMOV.VLFRETE_RATEIO, 0) - (DECODE(NVL(PCNFSAID.SOMAREPASSEOUTRASDESPNF, 'N'), 'N', (DECODE(NVL(PCMOV.VLOUTROS, 0), 0, NVL(PCMOV.VLREPASSE, 0), 0)), 'S', (NVL(PCMOV.VLREPASSE, 0)))) + NVL(PCMOV.VLOUTROS, 0)))), 2) 
                END AS VLDEVOLUCAO,                          
                
                -- Devoluções sem ST
                (NVL(PCMOV.QT, 0) * DECODE(PCNFSAID.CONDVENDA, 5, 0, 6, 0, 11, 0, (DECODE(PCMOV.PUNIT, 0, PCMOV.PUNITCONT, NULL, PCMOV.PUNITCONT, PCMOV.PUNIT) + NVL(PCMOV.VLOUTROS, 0) - (NVL(PCMOV.ST, 0) + NVL(PCMOVCOMPLE.VLSTTRANSFCD, 0)) + NVL(PCMOV.VLFRETE, 0)))) AS VLDEVOLUCAO_SEMST,        
                
                -- Bonificação e Tabelas
                ROUND((NVL(PCMOV.QT, 0) * DECODE(PCNFSAID.CONDVENDA, 5, DECODE(PCMOV.PBONIFIC, NULL, PCMOV.PTABELA, PCMOV.PBONIFIC), 6, DECODE(PCMOV.PBONIFIC, NULL, PCMOV.PTABELA, PCMOV.PBONIFIC), 1, NVL(PCMOV.PBONIFIC, 0), 14, NVL(PCMOV.PBONIFIC, 0), 11, DECODE(PCMOV.PBONIFIC, NULL, PCMOV.PTABELA, PCMOV.PBONIFIC), 12, DECODE(PCMOV.PBONIFIC, NULL, PCMOV.PTABELA, PCMOV.PBONIFIC), 0)), 2) AS VLBONIFIC
            FROM 
                PCNFENT, PCESTCOM, PCEMPR, PCNFSAID, PCMOV, PCPRODUT, PCCLIENT, PCFORNEC, PCPRACA, PCTABDEV, PCTABDEV PCTABDEV2, 
                PCDEPTO, PCSECAO, PCUSUARI, PCPLPAG, PCSUPERV, PCATIVI, PCPEDC, PCCIDADE, PCMARCA, PCGERENTE, PCMOVCOMPLE, PCROTAEXP,
                
                -- Subquery específica para tratar vendas futuras e condições especiais de TV8
                (
                    SELECT DISTINCT 
                        CASE                                          
                            WHEN PED.CONDVENDA = 7 THEN (SELECT DISTINCT P1.NUMPED FROM PCPEDC P1, PCESTCOM E1 WHERE E1.NUMTRANSENT = ESTC.NUMTRANSENT AND P1.NUMTRANSVENDA = E1.NUMTRANSVENDA AND P1.NUMPEDENTFUT = PED.NUMPED AND P1.CONDVENDA = 8)                           
                            WHEN PED.CONDVENDA = 8 THEN (SELECT DISTINCT P2.NUMPED FROM PCPEDC P2, PCESTCOM E2 WHERE E2.NUMTRANSENT = ESTC.NUMTRANSENT AND P2.NUMTRANSVENDA = E2.NUMTRANSVENDA AND P2.NUMPED = PED.NUMPEDENTFUT AND P2.CONDVENDA = 7)                           
                        END AS TEMVENDATV8,                                       
                        PED.NUMTRANSVENDA, ESTC.NUMTRANSENT                                       
                    FROM PCPEDC PED, PCESTCOM ESTC                              
                    WHERE PED.NUMTRANSVENDA(+) = ESTC.NUMTRANSVENDA
                      AND PED.DATA BETWEEN TO_DATE(:DTENT_INICIO, 'DD/MM/YYYY') AND TO_DATE(:DTENT_FIM, 'DD/MM/YYYY') 
                ) TEMVENDATV8 
            WHERE 
                PCNFENT.NUMTRANSENT = PCESTCOM.NUMTRANSENT
                AND PCESTCOM.NUMTRANSENT = PCMOV.NUMTRANSENT
                AND PCPRODUT.CODPROD = PCMOV.CODPROD
                AND PCFORNEC.CODFORNEC = PCPRODUT.CODFORNEC
                AND PCNFENT.CODFORNEC = PCCLIENT.CODCLI
                AND PCESTCOM.NUMTRANSVENDA = PCNFSAID.NUMTRANSVENDA(+)
                
                -- Filtros Críticos de Data, Fornecedor e Filial para Devolução
                AND PCNFENT.DTENT BETWEEN TO_DATE(:DTENT_INICIO, 'DD/MM/YYYY') AND TO_DATE(:DTENT_FIM, 'DD/MM/YYYY') 
                AND PCMOV.DTMOV BETWEEN TO_DATE(:DTENT_INICIO, 'DD/MM/YYYY') AND TO_DATE(:DTENT_FIM, 'DD/MM/YYYY') 
                AND PCPRODUT.CODFORNEC IN (:codfornec)
                AND PCMOV.CODFILIAL IN (:codfilial)
                AND PCNFENT.CODFILIAL IN (:codfilial)
                
                -- Demais Joins da Devolução
                AND PCCLIENT.CODPRACA = PCPRACA.CODPRACA
                AND PCNFSAID.NUMPED = PCPEDC.NUMPED(+)
                AND PCNFENT.CODDEVOL = PCTABDEV.CODDEVOL(+)
                AND PCMOV.CODDEVOL = PCTABDEV2.CODDEVOL(+)
                AND PCPRODUT.CODEPTO = PCDEPTO.CODEPTO(+)
                AND PCPRACA.ROTA = PCROTAEXP.CODROTA(+)
                AND PCNFENT.CODUSURDEVOL = PCUSUARI.CODUSUR(+)
                AND NVL(PCNFSAID.CODSUPERVISOR, PCUSUARI.CODSUPERVISOR) = PCSUPERV.CODSUPERVISOR
                AND PCPRODUT.CODSEC = PCSECAO.CODSEC(+)
                AND PCCLIENT.CODATV1 = PCATIVI.CODATIV(+)
                AND PCNFENT.CODFUNCLANC = PCEMPR.MATRICULA(+)
                AND PCCLIENT.CODCIDADE = PCCIDADE.CODCIDADE(+)
                AND NVL(PCNFSAID.CODPLPAG, PCCLIENT.CODPLPAG) = PCPLPAG.CODPLPAG
                AND PCPRODUT.CODMARCA = PCMARCA.CODMARCA(+)
                AND PCMOV.NUMTRANSITEM = PCMOVCOMPLE.NUMTRANSITEM(+)
                AND DECODE(PCNFSAID.CODGERENTE, NULL, PCSUPERV.CODGERENTE, PCNFSAID.CODGERENTE) = PCGERENTE.CODGERENTE
                AND TEMVENDATV8.NUMTRANSENT(+) = PCNFENT.NUMTRANSENT 
                
                -- Filtros de Validação do Tipo de Devolução (Tipos comerciais válidos 6, 7 e T)
                AND PCNFENT.TIPODESCARGA IN ('6', '7', 'T')
                AND NVL(PCNFENT.CODFISCAL, 0) IN (131, 132, 231, 232, 199, 299)
                AND PCMOV.CODOPER = 'ED' 
                AND PCMOV.DTCANCEL IS NULL
                AND NVL(PCNFENT.TIPOMOVGARANTIA, -1) = -1
                AND NVL(PCNFENT.OBS, 'X') <> 'NF CANCELADA'
                AND NVL(PCNFSAID.CONDVENDA, 0) NOT IN (4, 8, 10, 13, 20, 98, 99)
                
                -- Segurança / Permissões (PCLIB)
                AND (PCUSUARI.CODSUPERVISOR IN (SELECT CODIGON FROM PCLIB WHERE CODFUNC IN (1639) AND CODTABELA = 7)) 
                AND (PCPRODUT.CODFORNEC IN (SELECT CODIGON FROM PCLIB WHERE CODFUNC IN (1639) AND CODTABELA = 3)) 
                AND (PCPRODUT.CODEPTO IN (SELECT CODIGON FROM PCLIB WHERE CODFUNC IN (1639) AND CODTABELA = 2)) 
        )
        GROUP BY 
            CODFORNEC, 0, '', FORNECEDOR
    ) DEVOLUCAO,
    
    PCFORNEC

--------------------------------------------------------------------------------
-- JOINS E FILTROS DA SUBQUERY PRINCIPAL (CONSOLIDAÇÃO FINAL)
--------------------------------------------------------------------------------
WHERE 
    PCFORNEC.CODFORNEC = VENDAS.CODFORNEC(+)
    AND PCFORNEC.CODFORNEC = DEVOLUCAO.CODFORNEC(+)
    AND PCFORNEC.CODFORNEC = META.CODFORNEC(+)
    
    -- Restringe o relatório final apenas ao fornecedor desejado
    AND PCFORNEC.CODFORNEC IN (:codfornec)
    
    -- Filtro de segurança para ocultar linhas totalmente zeradas
    AND (
        (NVL(VENDAS.QTVENDA, 0) <> 0) 
        OR (NVL(DEVOLUCAO.QTDEVOLUCAO, 0) <> 0) 
        OR (NVL(DEVOLUCAO.VLDEVOLUCAO, 0) <> 0) 
        OR (NVL(VENDAS.TOTPESO, 0) <> 0) 
        OR (NVL(VENDAS.VLVENDA, 0) <> 0) 
        OR (NVL(VENDAS.CODFORNEC, 0) <> 0) 
        OR (NVL(VENDAS.VLBONIFIC, 0) <> 0) 
        OR (NVL(VENDAS.QTCLIPOS, 0) <> 0)
    ) 

GROUP BY 
    VENDAS.CODFORNEC,
    VENDAS.FORNECEDOR,
    DEVOLUCAO.FORNECEDOR,
    DEVOLUCAO.CODFORNEC,
    VENDAS.ROTA,
    VENDAS.DESCROTA,
    NVL(META.VLMETA, 0),
    NVL(META.QTMETA, 0),
    NVL(META.QTPESOMETA, 0),
    NVL(META.MIXPREV, 0),
    NVL(META.CLIPOSPREV, 0)

-- Ordena trazendo os fornecedores/rotas com maior faturamento primeiro
ORDER BY 
    VLVENDA DESC