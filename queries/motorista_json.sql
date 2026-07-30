SELECT
    JSON_OBJECT(
        'Country' VALUE 'Brazil',
        'NationalId' VALUE NVL(CPF, ''),
        'DriverLicenseNumber' VALUE NVL(CNH, ''),
        'Address' VALUE JSON_OBJECT(
            'Street' VALUE NVL(ENDERECO, ''),
            'Number' VALUE '', -- Campo Número não encontrado na tabela, preenchido com string vazia
            'Complement' VALUE '',
            'Neighborhood' VALUE NVL(BAIRRO, ''),
            'ZipCode' VALUE NVL(CEP, '')
        ),
        /* Corrigido: Removido o ARRAYAGG interno ou tratado como objeto único por linha */
        'Phones' VALUE JSON_ARRAY(
            JSON_OBJECT(
                'AreaCode' VALUE NVL(DDDTEL, 0),
                'Number' VALUE NVL(CELULAR, 0),
                'Preferential' VALUE 'true',
                'TypeId' VALUE 'CELL'
            )
        ),
        'DriverPersonalInformation' VALUE JSON_OBJECT(
            'BirthDate' VALUE TO_CHAR(DTNASC, 'YYYY-MM-DD"T"HH24:MI:SS"Z"'),
            'Name' VALUE REPLACE(REPLACE(NOME, 'WMS - ', ''), ' - ', ' '),
            'Gender' VALUE (CASE WHEN SEXO = 'M' THEN 'Male' WHEN SEXO = 'F' THEN 'Female' ELSE 'Uninformed' END)
        )
	) AS JSON_DOCUMENT
FROM 
    CHOCOSUL.PCEMPR
WHERE 1=1
    AND	PCEMPR.ROWID = NVL(:row_id, PCEMPR.ROWID)
    AND PCEMPR.CPF = NVL(:national_id, PCEMPR.CPF)
    AND PCEMPR.MATRICULA = NVL(:enrollment, PCEMPR.MATRICULA)
    -- AND PCEMPR.SITUACAO = 'A'
    AND PCEMPR.CPF IS NOT NULL
    AND PCEMPR.CNH IS NOT NULL
    -- AND CODSETOR IN (SELECT CODSETORMOTORISTA FROM PCCONSUM)