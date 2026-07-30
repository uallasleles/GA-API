/* =====================================================================
   ROTINA 410 - ACERTOS DE CARGA / CAIXA
   ABA 1 - NOTAS FISCAIS / ROMANEIO
   =====================================================================
   Objetivo:
     Listar os títulos financeiros (PCPREST) vinculados a um carregamento
     (NUMCAR) que ainda estão pendentes de acerto/baixa, trazendo dados
     do cliente, da nota fiscal de saída, da forma de cobrança e diversos
     indicadores complementares (TEF, cartão, boleto, protesto, NF-e etc).

   Parâmetros (bind variables):
     - :NUMCAR    -> número do carregamento
     - :CODFILIAL -> filial do título

   Padrão de junção: ANSI SQL (INNER JOIN / LEFT JOIN), substituindo
   os outer joins implícitos do Oracle (notação "(+)") do script original.
   ===================================================================== */

SELECT
    -----------------------------------------------------------------
    -- Identificação do título / carregamento
    -----------------------------------------------------------------
    PCPREST.NUMCAR,                       -- Número do carregamento
    PCPREST.CODFILIAL,                    -- Filial do título
    PCPREST.DUPLIC,                       -- Número da duplicata
    PCPREST.PREST,                        -- Número da prestação/parcela
    PCPREST.STATUS,                       -- Situação do título
    PCPREST.CODCLI,                       -- Código do cliente

    -- Valor líquido do título (valor original menos eventual estorno)
    (NVL(PCPREST.VALOR, 0) - NVL(PCPREST.VALORESTORNO, 0)) VALOR,

    PCPREST.DTVENC,                       -- Data de vencimento

    -----------------------------------------------------------------
    -- Nome do cliente
    -- Para os códigos de cliente "genéricos" de consumidor (1 e 2),
    -- prioriza o nome informado na venda ao consumidor
    -- (PCVENDACONSUM.CLIENTE); senão usa o cadastro PCCLIENT.
    -----------------------------------------------------------------
    DECODE(PCPREST.CODCLI,
            1, NVL(PCVENDACONSUM.CLIENTE, PCCLIENT.CLIENTE),
            2, NVL(PCVENDACONSUM.CLIENTE, PCCLIENT.CLIENTE),
            PCCLIENT.CLIENTE) CLIENTE,

    -----------------------------------------------------------------
    -- Vendedores / rota / forma de pagamento
    -----------------------------------------------------------------
    PCPREST.CODUSUR,                       -- Código do vendedor (usuário de rota)
    PCPREST.COMPENSACAOBCO,                -- Indicador de compensação bancária
    PCPREST.CODCOB,                        -- Código da forma de cobrança
    PCPREST.DTDESD,                        -- Data do desdobramento
    PCPREST.NUMCHEQUE,                     -- Número do cheque
    PCPREST.DTLANCCH,                      -- Data de lançamento do cheque
    PCPREST.CODFUNCDESD,                   -- Funcionário que desdobrou
    PCPREST.NUMTRANSVENDA,                 -- Número da transação de venda
    PCPREST.NUMBANCO,                      -- Número do banco (cheque)
    PCPREST.NUMAGENCIA,                    -- Número da agência (cheque)
    PCCLIENT.CGCENT,                       -- CNPJ/CPF do cliente
    PCCLIENT.ACEITACHTERCEIROS,            -- Cliente aceita cheque de terceiros?
    PCPREST.DTULTALTER,                    -- Data da última alteração
    PCPREST.DTCXMOT,                       -- Data do caixa do motorista
    PCPREST.CODFUNCCXMOT,                  -- Funcionário responsável pelo caixa do motorista

    -- Data de vencimento original (antes de eventual renegociação)
    NVL(PCPREST.DTVENCORIG, PCPREST.DTVENC) DTVENCORIG,

    PCPREST.CODFUNCULTALTER,               -- Funcionário da última alteração
    PCPREST.VPAGO,                         -- Valor pago
    PCPREST.DTPAG,                         -- Data do pagamento
    PCPREST.DTEMISSAO,                     -- Data de emissão do título

    -- Data de emissão original (antes de eventual renegociação)
    NVL(PCPREST.DTEMISSAOORIG, PCPREST.DTEMISSAO) AS DTEMISSAOORIG,

    PCPREST.CODBARRA,                      -- Código de barras do boleto
    PCPREST.CODFUNCVALE,                   -- Funcionário que deu vale
    PCPREST.CODHISTVALE,                   -- Histórico do vale
    PCPREST.VLTXBOLETO,                    -- Valor da taxa de boleto

    NVL(PCPREST.VALORDESC, 0) AS VALORDESC, -- Valor de desconto concedido

    PCPREST.TXPERM,                        -- Taxa de permanência (juros)
    PCPREST.VALORLIQCOM,                   -- Valor líquido de comissão
    PCPREST.PERCOM,                        -- Percentual de comissão
    PCPREST.CODFILIALNF,                   -- Filial da nota fiscal
    PCPREST.DVAGENCIA,                     -- Dígito verificador da agência
    PCPREST.DVCHEQUE,                      -- Dígito verificador do cheque
    PCPREST.NUMCONTACORRENTE,              -- Número da conta corrente
    PCPREST.DVCONTA,                       -- Dígito verificador da conta
    PCPREST.BOLETO,                        -- Indicador de boleto
    PCPREST.OPERACAO,                      -- Tipo de operação do título
    PCPREST.CODCOBORIG,                    -- Forma de cobrança original (antes de troca)
    PCPREST.OBSFINANC,                     -- Observação financeira

    PCNFSAID.NUMPED,                       -- Número do pedido (da NF de saída)
    PCNFSAID.DTFAT,

    PCPREST.ROTDESD,                       -- Rota do desdobramento
    
    -- Fechamento
    -----------------------------------------------------------------
    PCPREST.DTFECHA,                       -- Data de fechamento (acerto)
    PCPREST.MINUTOFECHA,                   -- Minuto do fechamento/acerto
    PCPREST.HORAFECHA,                     -- Hora do fechamento/acerto
    PCPREST.CODFUNCFECHA,                  -- Funcionário que fechou/acertou

    PCPREST.CODUSUR2,                      -- Vendedor 2 (rateio de comissão)
    PCPREST.CODUSUR3,                      -- Vendedor 3 (rateio de comissão)
    PCPREST.DVCOB,                         -- Dígito verificador da cobrança
    PCPREST.DTCXMOTHHMMSS,                 -- Hora do caixa do motorista (HHMMSS)

    -----------------------------------------------------------------
    -- Dados da forma de cobrança (PCCOB) vinculada ao título
    -----------------------------------------------------------------
    PCCOB.AUTENTICARACERTOCX402,           -- Exige autenticação no acerto (rotina 402)?
    PCCOB.COBRANCAEMTRANSITO,              -- Cobrança em trânsito?
    NVL(PCCOB.CARTAO, 'N') CARTAO,         -- É forma de pagamento em cartão?
    NVL(PCCOB.TIPOOPERACAOTEF, 'N') TIPOOPERACAOTEF,  -- Tipo de operação TEF
    PCCOB.CODCLICC,                        -- Código do cliente de cartão de crédito

    -- Código da forma de cobrança usada para compensação em CC
    -- (apenas valida que o CODCOBCC referenciado existe em PCCOB)
    (SELECT CODCOB
        FROM PCCOB C
        WHERE C.CODCOB = PCCOB.CODCOBCC) CODCOBCC,

    NVL(PCCOB.BAIXACXBANCO, 'N') BAIXACXBANCO,   -- Baixa automática via caixa/banco?
    NVL(PCCOB.CODMOEDA, '') CODMOEDA,            -- Moeda da cobrança

    -- Mesmos indicadores, porém referentes à forma de cobrança ORIGINAL
    -- (antes de uma eventual troca de forma de pagamento)
    NVL(CORIG.CARTAO, 'N') CARTAOORIG,
    NVL(CORIG.TIPOOPERACAOTEF, 'N') TIPOOPERACAOTEFORIG,
    CORIG.CODCLICC CODCLICCORIG,
    NVL(CORIG.CODCOBCC, '') CODCOBCCORIG,

    PCPREST.QTPARCELASPOS,                 -- Quantidade de parcelas pós-datadas
    PCPREST.DTRECEBIMENTOPREVISTO,         -- Data prevista de recebimento

    NVL(PCPREST.TXPERMPREVISTO, 0) TXPERMPREVISTO,       -- Taxa de permanência prevista
    NVL(PCPREST.TXPERMPREVREAL, 0) TXPERMPREVREAL,       -- Taxa de permanência prevista x real

    PCCARREG.LANCARDESPDESCFINAUTOMATIC,   -- Carregamento lança desp./desconto financeiro automaticamente?

    PCPREST.CODFUNCCHECKOUT,               -- Funcionário do checkout (se já passou por checkout)
    PCPREST.NUMCHECKOUT,                   -- Número do checkout
    PCPREST.CODFUNCVEND,                   -- Funcionário que já fez o "vendor" do título
    PCPREST.CODUSUR4,                      -- Vendedor 4 (rateio de comissão)
    PCPREST.DTPAGCOMISSAO,                 -- Data de pagamento de comissão (vendedor 1)
    PCPREST.DTPAGCOMISSAO2,                -- Data de pagamento de comissão (vendedor 2)
    PCPREST.DTPAGCOMISSAO3,                -- Data de pagamento de comissão (vendedor 3)
    PCPREST.DTPAGCOMISSAO4,                -- Data de pagamento de comissão (vendedor 4)
    PCPREST.PERCOM2,                       -- Percentual de comissão (vendedor 2)
    PCPREST.PERCOM3,                       -- Percentual de comissão (vendedor 3)
    PCPREST.PERCOM4,                       -- Percentual de comissão (vendedor 4)

    NVL(PCCLIENT.BLOQUEIO, 'N') AS BLOQUEIO,-- Cliente bloqueado?

    PCPREST.ROTINALANC,                    -- Rotina que originou o lançamento do título
    NVL(PCPREST.DADOSECF, 'M') AS DADOSECF,-- Origem dos dados (ECF, manual etc.)
    PCPREST.NSUTEF,                        -- NSU da transação TEF
    PCPREST.PRESTTEF,                      -- Indicador de prestação via TEF
    PCPREST.CODADMCARTAO,                  -- Código da administradora de cartão

    NVL(PCCOB.BOLETO, 'N') AS cBOLETOCOB,  -- Forma de cobrança gera boleto?
    PCCOB.NIVELVENDA cNIVELVENDA,          -- Nível de venda exigido pela cobrança
    PCCOB.CARTAO cCOBRCARTAO,              -- Forma de cobrança é cartão (alias da PCCOB)

    -----------------------------------------------------------------
    -- Código do emitente (vendedor/operador) do pedido de origem
    -- Se o título não tem emitente gravado diretamente, busca o
    -- emitente do pedido (PCPEDC) vinculado à transação de venda.
    -----------------------------------------------------------------
    (CASE
        WHEN (PCPREST.CODEMITENTEPEDIDO IS NULL) THEN
        (NVL((SELECT PCPEDC.CODEMITENTE
                FROM PCPEDC
                WHERE PCPEDC.NUMTRANSVENDA = PCNFSAID.NUMTRANSVENDA
                    AND ROWNUM = 1), 0))
        ELSE
        (PCPREST.CODEMITENTEPEDIDO)
    END) AS CODEMITENTE,

    -----------------------------------------------------------------
    NVL(PCPREST.BLOQDESDEMITENTEDIF, 'S') BLOQDESDEMITENTEDIF,
    -- Bloqueia desdobramento quando o emitente do desdobramento
    -- é diferente do emitente original do título?

    -----------------------------------------------------------------
    -- Indica se a comissão do emitente/operador deve ser rateada.
    -- Mesma lógica de fallback do CODEMITENTE acima: se não há
    -- emitente gravado no título, busca via PCPEDC; senão usa
    -- diretamente o emitente gravado no título (PCEMPR.MATRICULA).
    -----------------------------------------------------------------
    NVL((CASE
            WHEN (PCPREST.CODEMITENTEPEDIDO IS NULL) THEN
            (SELECT DISTINCT PCEMPR.USARATEIOCOMISSAOOPERADOR
                FROM PCEMPR, PCPEDC
                WHERE PCPEDC.NUMTRANSVENDA = PCNFSAID.NUMTRANSVENDA
                AND PCPEDC.CODEMITENTE = PCEMPR.MATRICULA
                AND ROWNUM = 1)
            ELSE
            (SELECT DISTINCT PCEMPR.USARATEIOCOMISSAOOPERADOR USA
                FROM PCEMPR
                WHERE PCPREST.CODEMITENTEPEDIDO = PCEMPR.MATRICULA
                AND ROWNUM = 1)
        END), 'N') USARATEIOCOMISSAOOPERADOR,

    -----------------------------------------------------------------
    PCPREST.DTCANCEL,                      -- Data de cancelamento do título
    PCPREST.DTESTORNO,                     -- Data de estorno
    PCCOB.COBRANCA,                        -- Descrição/tipo da cobrança
    PCCOB.CODMOEDA,                        -- Moeda (novamente, sem NVL aqui)
    PCCARREG.OBSACERTO,                    -- Observação de acerto do carregamento
    PCPREST.DTVENCVALE,                    -- Data de vencimento do vale
    PCPREST.OBS,                           -- Observação do título
    PCPREST.DTABERTURACONTA,               -- Data de abertura da conta (cheque)
    PCPREST.CGCCPFCH,                      -- CNPJ/CPF do emitente do cheque
    PCPREST.OBS2,                          -- Observação 2
    PCPREST.CODMOTORISTA,                  -- Código do motorista do carregamento
    PCPREST.CODSUPERVISOR,                 -- Código do supervisor
    PCPREST.DTDEVOL,                       -- Data de devolução
    PCPREST.VLDEVOL,                       -- Valor devolvido
    PCPREST.NOSSONUMBCO,                   -- Nosso número bancário
    PCPREST.CODBANCOCM,                    -- Código do banco da carta de cobrança
    PCPREST.CODOCORRBAIXA,                 -- Código de ocorrência da baixa
    PCPREST.ROWID,                         -- ROWID do título (útil para updates pontuais)
    PCPREST.DTCRIACAO,                     -- Data de criação do registro
    PCPREST.SOMATXBOLETO,                  -- Soma a taxa de boleto ao valor do título?
    PCPREST.VALORDESCORIG,                 -- Valor de desconto original
    PCPREST.CODEMITENTEPEDIDO,             -- Emitente gravado diretamente no título
    PCPREST.PARCELAMENTOTEF,               -- Quantidade de parcelas (TEF)
    PCPREST.CODAUTORIZACAOTEF,             -- Código de autorização TEF
    PCPREST.NUMASSOCDNI,                   -- Número de associação ao DNI (negativação)

    NVL(PCCOB.TXJUROS, 0) TXJUROS,         -- Taxa de juros da forma de cobrança

    -----------------------------------------------------------------
    -- Indicadores calculados de atraso
    -----------------------------------------------------------------
    (TRUNC(SYSDATE) - PCPREST.DTVENC) DIASATRASO,   -- Dias de atraso (hoje - vencimento)

    (CASE
        WHEN NVL(PCCOB.TXJUROS, 0) <> 0 THEN (NVL(PCCOB.TXJUROS, 0) / 30)
        ELSE 0
    END) TXJUROSDIA,                      -- Taxa de juros proporcional ao dia (mensal / 30)

    -----------------------------------------------------------------
    PCPREST.NUMDIASPRAZOPROTESTO,          -- Prazo (em dias) para protesto
    PCPREST.CODEPTO,                       -- Código do departamento
    PCPREST.HORADESD,                      -- Hora do desdobramento
    PCPREST.MINUTODESD,                    -- Minuto do desdobramento
    PCPREST.NUMBORDERO,                    -- Número do borderô
    PCPREST.CODFUNCBORDERO,                -- Funcionário que gerou o borderô
    PCPREST.CODPORTADOR,                   -- Código do portador (banco/carteira)
    PCPREST.NUMTRANS,                      -- Número da transação do título

    NVL(PCPREST.PERDESC, 0) AS PERDESC,                  -- Percentual de desconto
    NVL(PCPREST.VLRDESPBANCARIAS, 0) VLRDESPBANCARIAS,   -- Despesas bancárias
    NVL(PCPREST.VLRDESPCARTORAIS, 0) VLRDESPCARTORAIS,   -- Despesas cartorárias (protesto)

    PCPREST.CODAGENTECOBRANCA,             -- Código do agente de cobrança
    PCPREST.CODFUNCDNICLI,                 -- Funcionário que associou o cliente ao DNI

    NVL(PCPREST.VLROUTROSACRESC, 0) VLROUTROSACRESC,     -- Outros acréscimos

    PCPREST.NUMTRANSVENDAST,               -- Transação de venda ST (substituição tributária), se houver
    PCPREST.LINHADIG,                      -- Linha digitável do boleto

    PCCOB.PERMITEALTCOBDESD,               -- Forma de cobrança permite alterar no desdobramento?
    PCCOB.DEPOSITOBANCARIO,                -- Forma de cobrança é depósito bancário?

    PCPREST.CHEQUETERCEIRO,                -- Cheque de terceiro?
    NVL(PCPREST.CARTORIO, 'N') CARTORIO,   -- Título está em cartório?
    NVL(PCPREST.PROTESTO, 'N') PROTESTO,   -- Título está protestado?
    PCPREST.TIPOPORTADOR,                  -- Tipo do portador do título

    -- Indica se o título é um título de Substituição Tributária (ST):
    -- 'S' quando NUMTRANSVENDAST está preenchido, 'N' caso contrário
    DECODE(NVL(PCPREST.NUMTRANSVENDAST, 0), 0, 'N', 'S') TITULOST,

    PCPREST.DTBAIXA,                       -- Data da baixa do título
    PCPREST.DTBORDERO,                     -- Data de inclusão no borderô
    PCPREST.DTASSOCIADNICLI,               -- Data de associação ao DNI do cliente

    0 AS QTD,                              -- Coluna auxiliar (quantidade), usada na UI da rotina

    PCNFSAID.NUMSEQ,                       -- Número sequencial da NF de saída
    PCPREST.PERMITEESTORNO,                -- Título permite estorno?

    -----------------------------------------------------------------
    -- Dados fiscais da nota / filial
    -----------------------------------------------------------------
    PCNFSAID.SITUACAONFE,                  -- Situação da NF-e (autorizada, cancelada etc.)
    NVL(PCFILIAL.CONTROLENFEPORSERIE, 'N') CONTROLENFEPORSERIE,  -- Filial controla numeração de NF-e por série?
    NVL(PCNFSAID.ESPECIE, 'N') ESPECIE,    -- Espécie do documento fiscal
    PCNFSAID.SERIE,                        -- Série da nota fiscal
    PCNFSAID.CONDVENDA,                    -- Condição de venda

    -----------------------------------------------------------------
    -- Dados de cartão / vendor / cessão de crédito
    -----------------------------------------------------------------
    PCPREST.NOSSONUMBCO2,                  -- Nosso número bancário (segunda via/linha)
    PCPREST.NUMTRANSENTDEVCLI,             -- Transação de entrada por devolução de cliente vinculada
    PCPREST.NSUHOST,                       -- NSU do host da adquirente
    PCPREST.NUMCARTAO,                     -- Número do cartão (mascarado)

    -- Data da transação no cartão; se não houver, usa a emissão do título
    NVL(PCPREST.DTTRANSACAOCC, PCPREST.DTEMISSAO) AS DTTRANSACAOCC,

    PCPREST.NUMTRANSVENDOR,                -- Número da transação de "vendor" (cessão a terceiro)
    PCPREST.DTFECHAVENDOR,                 -- Data de fechamento do vendor
    PCPREST.DTVENDOR,                      -- Data do vendor

    NVL(PCCOB.COBSUPPLIERCARD, 'N') AS COBSUPPLIERCARD,   -- Forma de cobrança é cartão fornecedor (supplier card)?

    PCPREST.CODPROFISSIONAL,               -- Código do profissional vinculado (ex.: representante autônomo)
    PCPREST.PASTAARQUIVOBOLETO,            -- Caminho/pasta do arquivo do boleto gerado
    PCPREST.DTPROCESSAMENTO,                -- Data de processamento do título
    PCPREST.PERCOMLIQ,                     -- Percentual de comissão líquida
    PCPREST.CODCOBSEFAZ,                   -- Código da forma de cobrança informado à SEFAZ
    PCPREST.TIPOOPERACAOTEF,               -- Tipo de operação TEF (direto do título)

    NVL(PCCOB.CARTEIRADIGITAL, 'N') CARTEIRADIGITAL,      -- Forma de cobrança é carteira digital?

    PCPREST.CODINSTDOACAOTEF,              -- Código da instituição doadora (TEF)
    PCPREST.DTMOVIMENTOCX,                 -- Data do movimento de caixa

    'N' SELECIONADO                        -- Flag de seleção da linha na tela (controle de UI, sempre inicia 'N')

-----------------------------------------------------------------
-- FROM / JOIN em padrão ANSI
-- (joins obrigatórios primeiro; LEFT JOIN para os relacionamentos
--  que no script original eram outer join "(+)")
-----------------------------------------------------------------
FROM PCPREST
INNER JOIN PCFILIAL
    ON PCPREST.CODFILIAL = PCFILIAL.CODIGO
INNER JOIN PCCLIENT
    ON PCPREST.CODCLI = PCCLIENT.CODCLI
INNER JOIN PCCOB
    ON PCPREST.CODCOB = PCCOB.CODCOB
INNER JOIN PCCARREG
    ON PCPREST.NUMCAR = PCCARREG.NUMCAR
LEFT JOIN PCNFSAID
    ON PCPREST.NUMTRANSVENDA = PCNFSAID.NUMTRANSVENDA          -- Nem todo título tem NF (ex.: vale/cheque pré)
LEFT JOIN PCVENDACONSUM
    ON PCNFSAID.NUMPED = PCVENDACONSUM.NUMPED                  -- Só existe se for venda ao consumidor
LEFT JOIN PCCOB CORIG
    ON PCPREST.CODCOBORIG = CORIG.CODCOB                       -- Só existe se houve troca de forma de cobrança

WHERE 1=1
    AND PCPREST.DTCANCEL IS NULL                             -- Exclui títulos cancelados

    -----------------------------------------------------------------
    -- Filtros de parâmetro (bind variables)
    -----------------------------------------------------------------
    AND PCPREST.NUMCAR    = :NUMCAR
    AND PCPREST.CODFILIAL = NVL(:CODFILIAL, PCPREST.CODFILIAL)

    -----------------------------------------------------------------
    -- Considera apenas títulos ainda não processados em outras telas
    -----------------------------------------------------------------
    AND NVL(PCPREST.CODFUNCCHECKOUT, 0) = 0    -- Ainda não passou pelo checkout
    AND NVL(PCPREST.NUMCHECKOUT, 0)     = 0
    AND NVL(PCPREST.CODFUNCVEND, 0)     = 0    -- Ainda não foi "vendorizado" (cessão a terceiro)

    -----------------------------------------------------------------
    -- Exclui vendas do tipo Transferência (TR) originadas pelas
    -- rotinas 1419/1420 (provavelmente transferência entre filiais/depósitos,
    -- que não geram título de cliente neste contexto)
    -----------------------------------------------------------------
    AND NOT ((NVL(PCNFSAID.TIPOVENDA, 'X') = 'TR')
            AND ((NVL(PCNFSAID.ROTINACAD, 'X') LIKE '%1419%')
            OR (NVL(PCNFSAID.ROTINACAD, 'X') LIKE '%1420%')))

    -----------------------------------------------------------------
    -- Exclui formas de cobrança que não representam título "em aberto"
    -- de fato: DESD (desdobrado), CANC (cancelado), ESTR (estornado),
    -- CRED (crédito)
    -----------------------------------------------------------------
    AND PCPREST.CODCOB NOT IN ('DESD', 'CANC', 'ESTR', 'CRED')

    -----------------------------------------------------------------
    -- Considera apenas títulos ainda não pagos e ainda não fechados
    -- no acerto de carga/caixa
    -----------------------------------------------------------------
    -- AND PCPREST.DTPAG   IS NULL
    -- AND PCPREST.DTFECHA IS NULL

    -- :NUMCAR 	= 174773
    -- :CODFILIAL = 1





    /*
        Quando um título financeiro (como uma duplicata, nota ou boleto) ainda não foi "vendorizado", significa que a operação de vendor (ou vendor finance) não foi efetivada pelo banco ou pela instituição financeira parceira da sua empresa.Isso gera algumas consequências diretas no fluxo financeiro:Sem antecipação: A empresa vendedora ainda não recebeu o repasse antecipado do valor.Cobrança pendente: A responsabilidade pelo pagamento permanece temporariamente com o comprador original até que o banco assuma o crédito.Processo travado: Geralmente, há alguma pendência de aprovação de crédito, divergência de documentos (como a Nota Fiscal Eletrônica) ou falha na integração via API Financeira entre o ERP da sua empresa e o sistema bancário SPB.Para que eu possa te ajudar a resolver isso, me informe:Qual sistema de gestão (ERP) ou banco vocês estão utilizando?Essa transação é para antecipação de recebíveis ou financiamento de cadeia de fornecedores?O status da Nota Fiscal já foi aprovado na Secretaria da Fazenda (Sefaz)?
    */