WITH CTE_FORNECEDOR AS (

    SELECT DISTINCT
        JSON_OBJECT(
            'Email' VALUE NVL(PCFORNEC.EMAIL, ''),
            'Phones' VALUE (
                -- Subconsulta para processar a lógica do telefone
                SELECT 
                    JSON_ARRAY(
                        JSON_OBJECT(
                            'AreaCode' VALUE NVL(REGEXP_SUBSTR(RAW_PHONE, '\((\d{2,3})\)', 1, 1, NULL, 1), '73'),
                            'Number' VALUE CLEAN_NUMBER,
                            'Preferential' VALUE 'true',
                            'TypeId' VALUE CASE 
                                            WHEN LENGTH(CLEAN_NUMBER) = 9 AND SUBSTR(CLEAN_NUMBER, 1, 1) = '9' THEN 'Cell'
                                            WHEN LENGTH(CLEAN_NUMBER) = 8 AND SUBSTR(CLEAN_NUMBER, 1, 1) BETWEEN '2' AND '5' THEN 'Fixed'
                                            ELSE 'FIXED' -- Fallback para casos fora do padrão
                                          END -- ['Fixed', 'Cell', 'Residential', 'Message']
                        )
                    )
                FROM (
                    SELECT 
                        -- Pega o primeiro telefone disponível das 3 colunas
                        NVL(NVL(PCFORNEC.TELEFONECOM, PCFORNEC.SUP_CELULAR), PCFORNEC.TELFAB) AS RAW_PHONE,
                        -- Limpa o número: remove o DDD entre parênteses e tudo que não for dígito
                        REGEXP_REPLACE(
                            REGEXP_REPLACE(NVL(NVL(PCFORNEC.TELEFONECOM, PCFORNEC.SUP_CELULAR), PCFORNEC.TELFAB), '\(\d{2,3}\)', ''),
                            '[^0-9]', ''
                        ) AS CLEAN_NUMBER
                    FROM DUAL
                )
            ),
            'BrazilianSettings' VALUE JSON_OBJECT(
                'RNTRC' VALUE NVL((SELECT LPAD(PCVEICUL.CODIGORNTRC, 9, '0') FROM PCVEICUL WHERE PCVEICUL.CODFORNEC = PCFORNEC.CODFORNEC AND ROWNUM = 1), ''),
                'HiredPessoaFisica' VALUE JSON_OBJECT(
                    'INSS' VALUE NVL(REPLACE(REPLACE(REPLACE(PCFORNEC.INSS, '-', ''), '.', ''), '/', ''), ''),
                    'RG' VALUE NVL(REPLACE(REPLACE(REPLACE(PCFORNEC.RG, '-', ''), '.', ''), '/', ''), '')
                ),
                'HiredPessoaJuridica' VALUE JSON_OBJECT(
                    'InscricaoEstadual' VALUE NVL(REPLACE(REPLACE(REPLACE(PCFORNEC.IE, '-', ''), '.', ''), '/', ''), ''),
                    'InscricaoMunicipal' VALUE NVL(REPLACE(REPLACE(REPLACE(PCFORNEC.INSCMUNICIP, '-', ''), '.', ''), '/', ''), ''),
                    'NomeFantasia' VALUE NVL(PCFORNEC.FANTASIA, ''),
                    'OptanteSimplesNacional' VALUE (CASE WHEN PCFORNEC.SIMPLESNACIONAL = 'S' THEN 'true' ELSE 'false' END) FORMAT JSON
                )
            ), 
            'Address' VALUE JSON_OBJECT(
                'Street' VALUE NVL(PCFORNEC.ENDER, ''),
                'Number' VALUE NVL(PCFORNEC.NUMEROEND, ''),
                'Complement' VALUE NVL(PCFORNEC.COMPLEMENTOEND, ''),
                'Neighborhood' VALUE NVL(PCFORNEC.BAIRRO, ''),
                'ZipCode' VALUE NVL(REPLACE(PCFORNEC.CEP, '-', ''), '')
            ),
            'CompanyInformation' VALUE JSON_OBJECT(
                'CompanyName' VALUE NVL(PCFORNEC.FORNECEDOR, '')
            ),
            'HiredPersonalInformation' VALUE JSON_OBJECT(
                'Name' VALUE NVL(PCFORNEC.CONTATOCOM, 'Uninformed'), 
                'BirthDate' VALUE TO_CHAR(NVL(PCFORNEC.COM_DTANIVERSARIO, TO_DATE('1900-01-01', 'YYYY-MM-DD')), 'YYYY-MM-DD"T"HH24:MI:SS"Z"'),
                'LegalDependents' VALUE 0, 
                'Gender' VALUE 'Uninformed' -- ['Uninformed', 'Male', 'Female']
            )
            --'FuelVoucherPercentage' VALUE '0.01'
        ) AS HIRED_DOCUMENT
    FROM PCFORNEC
    LEFT JOIN PCVEICUL ON PCVEICUL.CODFORNEC = PCFORNEC.CODFORNEC
    WHERE 1=1
        AND PCFORNEC.ROWID = NVL(:row_id, PCFORNEC.ROWID) 
        AND PCFORNEC.CGCAUX = NVL(:national_id, PCFORNEC.CGCAUX)
        AND PCFORNEC.CODFORNEC = NVL(:hired_id, PCFORNEC.CODFORNEC)
)

SELECT 
    HIRED_DOCUMENT AS JSON_DOCUMENT
FROM CTE_FORNECEDOR