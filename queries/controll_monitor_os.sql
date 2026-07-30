SELECT 
    M.NUMOS,
    (SELECT COUNT(1)
     FROM pcMovEndPend x
     WHERE x.CODFILIAL = '1'
        AND x.DATA BETWEEN TRUNC(SYSDATE)-1 AND TRUNC(SYSDATE)
        AND NVL(X.NUMPED, 0) = NVL(M.NUMPED, 0) 
        AND x.NUMOS = M.NUMOS) QTDITENS, 
    M.TIPOOS, 
    NVL(M.NUMCAR, 0) NUMCAR, 
    M.CODOPER, 
    NVL(M.NUMPED, 0) NUMPED, 
    S.DESCRICAO, 
    M.NUMTRANSWMS, 
    MAX(NVL(M.NUMPALETE, 0)) NUMPALETE, 
    SUM(M.QT * P.PESOBRUTO) PESO, 
    SUM(M.QT * P.VOLUME) VOLUME,                                                                
    CASE                                                                                                                                                                      
        WHEN m.TIPOOS = 17      THEN SUM(NVL(M.NUMVOL,0))                                                                                                                           
        WHEN m.TIPOOS in (13)   THEN MAX(NVL(M.NUMVOL,0))                                                                                                                     
        WHEN M.TIPOOS = 20      THEN (  SELECT SUM(NUMVOL) 
                                        FROM (
                                            SELECT NUMOS, CODPROD, CODENDERECO, MAX(NVL(NUMVOL, 0)) NUMVOL 
                                            FROM PCMOVENDPEND 
                                            WHERE TIPOOS = 20 AND DTESTORNO IS NULL 
                                            GROUP BY NUMOS, CODPROD, CODENDERECO) 
                                        WHERE NUMOS = M.NUMOS 
                                        GROUP BY NUMOS  )
        WHEN M.TIPOOS = 22      THEN (  SELECT COUNT(1) AS QTVOLUME FROM PCVOLUMEOS WHERE NUMOS = M.NUMOS AND DTESTORNO IS NULL )
                                ELSE (  ROUND(SUM(m.qt)/MAX(p.qtunitcx))  )
    END AS TOTVOL, 
    SUM(
        (
            SELECT 
                CASE 
                    WHEN P1.pesovariavel ='S' AND P1.tipoestoque = 'FR' 
                    THEN (NVL(M.QTPECAS,CEIL( M.QT / DECODE(P1.PESOPECA,0,1,NULL,1,P1.PESOPECA)))) 
                    ELSE 0 
                END                                                                                 
            FROM PCPRODUT P1  
            WHERE P1.CODPROD = M.CODPROD
        )
    ) TOTPECAS,                                                                                                             
    CASE                                                                                                                                                                      
        when to_char(m.dtfimos, 'dd/mm/yyyy HH:MM') IS NOT NULL AND to_char(m.dtestorno, 'dd/mm/yyyy HH:MM') IS NULL AND NVL(M.POSICAO,'P') = 'C'   THEN 'CONCLUÍDA' 
        when NVL(M.POSICAO,'P') = 'A'                                                                                                               THEN 'AGUARDANDO'                                                                                                                
        when MIN(M.DTINICIOOS) IS NOT NULL  AND NVL(M.POSICAO,'P') <> 'C'                                                                           THEN 'INICIADA'                                                                          
        when to_char(m.dtestorno, 'dd/mm/yyyy HH:MM') IS NOT NULL                                                                                   THEN 'ESTORNADA'                                                                                       
        when MIN(M.DTINICIOOS) IS NULL                                                                                                              THEN 'NÃO INICIADA'                                                                                                               
        when MIN(M.DTINICIOOS) IS NOT NULL AND MAX(M.DTFIMSEPARACAO) IS NULL AND M.POSICAO = 'P'                                                    THEN 'EM SEPARAÇÃO'                                                     
        when MIN(M.DTINICIOOS) IS NOT NULL AND to_char(m.dtestorno, 'dd/mm/yyyy HH:MM') IS NOT NULL                                                 THEN 'ESTORNADA DURANTE SEPARAÇÃO'                                                     
        when max(M.DTINICIOCONFERENCIA) IS NOT NULL AND to_char(m.dtfimos, 'dd/mm/yyyy HH:MM') IS NULL AND M.POSICAO = 'P'                          THEN 'EM CONFERÊNCIA'                              
        when max(M.DTINICIOCONFERENCIA) IS NOT NULL AND to_char(m.dtestorno, 'dd/mm/yyyy HH:MM') IS NOT NULL                                        THEN 'ESTORNADA DURANTE CONFERÊNCIA'                                                 
        when to_char(m.dtfimos, 'dd/mm/yyyy HH:MM') IS NULL AND MAX(M.DTFIMSEPARACAO) IS NOT NULL AND M.POSICAO = 'P'                               THEN 'EM ANDAMENTO'                              
    END STATUS, 
    CASE WHEN (COUNT(m.DTINICIOOS) >= 1              AND COUNT(m.DTFIMOS) < COUNT(1)) AND COUNT(1) > 0   THEN 'S' ELSE 'N' END AS EM_SEPARACAO, 
    CASE WHEN (COUNT(m.DTFIMSEPARACAO) = COUNT(1)     OR COUNT(m.DTFIMOS) = COUNT(1)) AND COUNT(1) > 0   THEN 'S' ELSE 'N' END AS SEPARADO, 
    CASE WHEN (COUNT(m.DTINICIOCONFERENCIA) >= 1     AND COUNT(m.DTFIMOS) < COUNT(1)) AND COUNT(1) > 0   THEN 'S' ELSE 'N' END AS EM_CONFERENCIA, 
    CASE WHEN (COUNT(m.DTFIMCONFERENCIA) = COUNT(1)   OR COUNT(m.DTFIMOS) = COUNT(1)) AND COUNT(1) > 0   THEN 'S' ELSE 'N' END AS CONFERIDO, 
    NVL((SELECT MIN(DEPOSITO) 
        FROM PCENDERECO                                                                                                                                                         
        WHERE EXISTS (
            SELECT 1 FROM PCMOVENDPEND 
            WHERE CODENDERECOORIG = PCENDERECO.CODENDERECO 
                AND DATA BETWEEN TRUNC(SYSDATE)-1 AND TRUNC(SYSDATE) 
                AND NUMOS = M.NUMOS)), 1
    ) DEPOSITOORIG,                                                                                                                    
    NVL((SELECT MIN(DEPOSITO)                                                                                                                                                      
        FROM PCENDERECO                                                                                                                                                         
    WHERE EXISTS (SELECT 1                                                                                                                                                   
                    FROM PCMOVENDPEND                                                                                                                                        
                    WHERE CODENDERECO = PCENDERECO.CODENDERECO                                                                                                                
                    AND DATA BETWEEN TRUNC(SYSDATE)-1 AND TRUNC(SYSDATE)
                        AND NUMOS = M.NUMOS)), 1
    ) DEPOSITODEST, 
    CASE                                                                                                                                                                      
        when M.NUMBONUS     > 0  THEN 'B - ' || M.NUMBONUS                                                                                                                   
        when M.NUMCAR       > 0  THEN 'C - ' || M.NUMCAR                                                                                                                     
        when MAX(M.NUMPED)  > 0  THEN 'P - ' || MAX(M.NUMPED)                                                                                                           
        when M.NUMTRANS     > 0  THEN 'T - ' || M.NUMTRANS                                                                                                                   
                                 ELSE 'T - ' || M.CODROTINA                                                                                                                                    
    END MOVIMENT 
FROM PCMOVENDPEND M,                                                                                                                                                           
    PCTIPOOS S,                                                                                                                                                               
    PCPRODUT P                                                                                                                                                                
WHERE M.CODPROD = P.CODPROD                                                                                                                                                     
    AND M.TIPOOS = S.CODIGO                                                                                                                                                       
    AND M.NUMOS > 0                                                                                                                                                               
    AND M.CODFILIAL = NVL(:CODFILIAL , M.CODFILIAL)                                                                                                                                               
    --AND M.TIPOOS in (10,13,16,17,18,41,50,59,60,61,97,98) 
    AND M.TIPOOS in (10,13,16,17) 
    AND M.DTESTORNO  IS NULL 
    AND m.data between TRUNC(SYSDATE)-2 AND TRUNC(SYSDATE)
    AND M.NUMCAR = NVL(:NUMCAR, M.NUMCAR)                              
GROUP BY 
    M.NUMOS, 
    M.NUMCAR,                                                                 
    M.CODOPER,                                                                            
    M.TIPOOS,                                                                             
    to_char(m.dtfimos, 'dd/mm/yyyy HH:MM'),                                             
    M.NUMBONUS,                                                                           
    M.NUMTRANSWMS,                                                                        
    M.NUMCAR,                                                                             
    M.NUMPED,                                                                             
    M.CODROTINA,                                                                          
    M.NUMTRANS,                                                                           
    S.DESCRICAO,
    M.POSICAO,                                                                            
    to_char(m.dtestorno, 'dd/mm/yyyy HH:MM')                                            
ORDER BY TIPOOS, M.NUMOS