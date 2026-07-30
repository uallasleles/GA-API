WITH 

CTE_CARREGAMENTOS AS (

    SELECT DISTINCT
        JSON_ARRAYAGG(
            JSON_OBJECT(
                'NUMCAR' VALUE C.NUMCAR,
                'ORIGEM' VALUE t2.ORIGEM,
                'DESTINO' VALUE C.DESTINO,

                'EM_SEPARACAO' VALUE CASE 
                    WHEN (COUNT(m.DTINICIOOS) >= 1 AND COUNT(m.DTFIMOS) < COUNT(1)) AND COUNT(1) > 0 
                    THEN 'S' 
                    ELSE 'N' 
                END,
                'SEPARADO' VALUE CASE 
                    WHEN (COUNT(m.DTFIMSEPARACAO) = COUNT(1) OR COUNT(m.DTFIMOS) = COUNT(1)) AND COUNT(1) > 0 
                    THEN 'S' 
                    ELSE 'N' 
                END,
                'EM_CONFERENCIA' VALUE CASE 
                    WHEN (COUNT(m.DTINICIOCONFERENCIA) >= 1 AND COUNT(m.DTFIMOS) < COUNT(1)) AND COUNT(1) > 0 
                    THEN 'S' 
                    ELSE 'N' 
                END,
                'CONFERIDO' VALUE CASE 
                    WHEN (COUNT(m.DTFIMCONFERENCIA) = COUNT(1)OR COUNT(m.DTFIMOS) = COUNT(1)) AND COUNT(1) > 0 
                    THEN 'S' 
                    ELSE 'N' 
                END,
                'DTSAIDA' VALUE c.DTSAIDA,
                'DATAMON' VALUE c.DATAMON,
                'HORAMON' VALUE c.HORAMON,
                'MINUTOMON' VALUE c.MINUTOMON,
                'DTFECHA' VALUE c.DTFECHA,
                'CODMOTORISTA' VALUE c.CODMOTORISTA,
                'MOTORISTA' VALUE e1.NOME,
                'CODVEICULO' VALUE c.CODVEICULO,
                'TOTPESO' VALUE c.TOTPESO,
                'TOTVOLUME' VALUE c.TOTVOLUME,
                'VLTOTAL' VALUE c.VLTOTAL,
                'CODROTAPRINC' VALUE c.CODROTAPRINC,
                'CODROTA' VALUE r.CODROTA,
                'ROTA' VALUE r.DESCRICAO,
                'NUMNOTAS' VALUE c.NUMNOTAS,
                'QTITENS' VALUE c.QTITENS,
                'OBSFATUR' VALUE c.OBSFATUR,
                'TIPOCARGA' VALUE c.TIPOCARGA,
                'OBSDESTINO' VALUE c.OBSDESTINO,
                'CARGASECUNDARIA' VALUE c.CARGASECUNDARIA,
                'SITUACAO' VALUE r.SITUACAO,
                'KMROTA' VALUE r.KMROTA,
                'VLMINCARREG' VALUE r.VLMINCARREG,
                'PRAZOPREVENT' VALUE r.PRAZOPREVENT,
                'TIPOCOMISSAO' VALUE r.TIPOCOMISSAO,
                'VLDIARIA' VALUE r.VLDIARIA,
                'NUMDIARIA' VALUE r.NUMDIARIA,
                'RASTREADA' VALUE r.RASTREADA,
                'DIASENTREGA' VALUE r.DIASENTREGA,
                'QT_PALETES' VALUE COALESCE(MAX(m.NUMPALETE), 0),
                'QT_ENTREGAS' VALUE COUNT(DISTINCT p.CODCLI),
                'TIPOOS_LIST' VALUE LISTAGG(DISTINCT m.TIPOOS, ', ')
            ) RETURNING CLOB
        ) AS JSON_DOCUMENT

    FROM CHOCOSUL.PCCARREG c
        INNER JOIN CHOCOSUL.PCROTAEXP r   ON r.CODROTA = c.CODROTAPRINC
        INNER JOIN CHOCOSUL.PCPEDC p      ON p.NUMCAR = c.NUMCAR
        LEFT JOIN CHOCOSUL.PCEMPR e1      ON c.CODMOTORISTA = e1.MATRICULA
        LEFT JOIN CHOCOSUL.PCMOVENDPEND m ON c.NUMCAR = m.NUMCAR
        LEFT JOIN CHOCOSUL.PCTIPOOS o     ON m.TIPOOS = o.CODIGO
        INNER JOIN (
            SELECT DISTINCT
                c.NUMCAR
                ,CASE 
                    WHEN p.CODFILIAL IN (1, 2)    THEN 'EUNÁPOLIS' 
                    WHEN p.CODFILIAL IN (12, 13)  THEN 'ITABUNA'
                ELSE 'OUTRA'
                END AS ORIGEM
            FROM CHOCOSUL.PCCARREG c
                INNER JOIN CHOCOSUL.PCPEDC p        ON p.NUMCAR = c.NUMCAR
                LEFT JOIN CHOCOSUL.PCMOVENDPEND m   ON c.NUMCAR = m.NUMCAR
            WHERE 1=1
                AND C.NUMCAR LIKE NVL(:NUMCAR, C.NUMCAR)
                AND NVL(c.DATAMON, c.DTSAIDA) >= TRUNC(SYSDATE) - NVL(:NUM_DIAS, 30)
                AND m.DTESTORNO IS NULL
            GROUP BY c.NUMCAR, p.CODFILIAL
        ) t2 ON t2.NUMCAR = C.NUMCAR
    WHERE 1=1
        -- AND C.NUMCAR LIKE NVL(:NUMCAR, C.NUMCAR)
        -- AND NVL(C.DATAMON, C.DTSAIDA) >= TRUNC(SYSDATE) - NVL(:NUM_DIAS, 7)
        -- AND m.DTESTORNO IS NULL
    GROUP BY 
        C.NUMCAR
        ,t2.ORIGEM
        ,c.DTSAIDA
        ,c.DATAMON
        ,c.HORAMON
        ,c.MINUTOMON
        ,c.DESTINO
        ,c.DTFECHA
        ,c.CODMOTORISTA
        ,e1.NOME
        ,c.CODVEICULO
        ,c.TOTPESO
        ,c.TOTVOLUME
        ,c.VLTOTAL
        ,c.CODROTAPRINC
        ,r.CODROTA
        ,r.DESCRICAO
        ,c.NUMNOTAS
        ,c.QTITENS
        ,c.OBSFATUR
        ,c.TIPOCARGA
        ,c.OBSDESTINO
        ,c.CARGASECUNDARIA
        ,r.SITUACAO
        ,r.KMROTA
        ,r.VLMINCARREG
        ,r.PRAZOPREVENT
        ,r.TIPOCOMISSAO
        ,r.VLDIARIA
        ,r.NUMDIARIA
        ,r.RASTREADA
        ,r.DIASENTREGA
    ORDER BY c.NUMCAR
)

SELECT JSON_DOCUMENT FROM CTE_CARREGAMENTOS
