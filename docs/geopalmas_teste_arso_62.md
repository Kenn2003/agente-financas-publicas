# Teste de viabilidade do DXF · ARSO 62

## Resultado

O arquivo `ARSO_62_2017.dxf` foi aberto pelo driver DXF do GDAL 3.12.2. O desenho tem 2.137 entidades e camadas CAD identificadas, incluindo `LOTE` (410 linhas), `QUADRA_INTERNA` (541 linhas) e `MEIO_FIO` (373 entidades). As linhas de `LOTE` e `QUADRA_INTERNA` foram poligonizadas com o algoritmo nativo do QGIS 3.40.15.

O processo gerou 471 polígonos. Todos são polígonos não nulos e válidos segundo GEOS; a área mediana foi 360 unidades². O sistema de referência espacial não veio no DXF. Assim, o teste confirma que a geometria pode ser extraída e explorada, mas não confirma posição geográfica, unidade de medida, topologia cadastral ou correspondência dos polígonos com IDs oficiais.

O DXF contém rótulos em entidades separadas. Um cruzamento espacial do rótulo `NUMERO_LOTE` com as faces geradas associou um texto a 428 polígonos; 43 ficaram sem rótulo. O número de lote não é uma chave única sem o identificador de quadra, e o vínculo ainda requer revisão. A página do Dash colore essas duas classes somente como **qualidade do vínculo CAD**; não representa zoneamento, renda ou outra variável temática. O GDAL também reportou duas entidades de origem com geometria curta/malformada, que não entraram nas camadas de linha usadas para formar as 471 faces.

## Arquivos do teste

- Entrada copiada: `data/raw/geopalmas/02_teste_dxf/ARSO_62_2017.dxf` (os DWGs originais não foram alterados).
- Saídas usadas pela página: `data/processed/geopalmas/ARSO_62_2017/linhas_cad.gpkg`, `rotulos_lote.gpkg`, `areas_rotuladas.gpkg` e `areas_rotuladas.geojson`.
- As primeiras versões intermediárias ficam em `data/processed/geopalmas/teste_arso_62_*`; a página usa o GeoJSON dentro da pasta da subárea.

Os diretórios `data/raw/` e `data/processed/` são ignorados pelo Git. Os dados de teste permanecem locais e não são publicados pelo repositório.

## Conversão em lote e referência cartográfica

O GDAL instalado tem o driver de leitura CAD baseado em libopencad, mas a versão disponível aceita DWG R2000 (`AC1015`). No inventário local, 208 dos 209 DWGs usam cabeçalhos mais novos (`AC1021`, `AC1024` ou `AC1027`) e não abrem diretamente nesse driver. Para converter o conjunto será necessário usar um conversor compatível (por exemplo, ODA File Converter) em lote, ou obter os limites já publicados como vetor no serviço WFS oficial.

O [Geoportal SEPLAN lista o serviço WFS da Base de Referência de Palmas](https://geoportal.to.gov.br/geoserver/base_referencia_palmas/wfs). O [mosaico de ortofotocartas publicado pela Prefeitura](https://geo.palmas.to.gov.br/media/arquivos/8_7_2015_17_53_13.pdf) declara SIRGAS 2000 / UTM zona 22S (EPSG:31982), mas isso não comprova que o DXF local foi produzido nesse CRS. Essas fontes servem para comparar posição e escala; não atribua EPSG:31982 diretamente às coordenadas locais do DXF.

## Reproduzir a conversão

Execute na raiz do projeto. O fluxo requer `ogr2ogr`/GDAL e `qgis_process` com `native:polygonize` e `native:joinattributesbylocation`:

```bash
python3 src/governance/processar_dxf_geopalmas.py \
  data/raw/geopalmas/02_teste_dxf/ARSO_62_2017.dxf
```

O mesmo comando recebe uma pasta de DXFs para processar em lote, por exemplo:

```bash
python3 src/governance/processar_dxf_geopalmas.py \
  data/raw/geopalmas/dxf_convertidos/
```

Cada subárea é processada para `data/processed/geopalmas/<nome-do-dxf>/`. A página carrega a geometria automaticamente quando a subárea correspondente é selecionada.

## Para passar do piloto à cartografia georreferenciada

1. Confirmar com a fonte municipal o CRS e a unidade usados no desenho; não atribuir um CRS só pelo formato ou aparência.
2. Comparar o DXF com uma camada de referência confiável de Palmas e verificar escala, rotação e deslocamento.
3. Identificar quais polígonos representam lotes, quadras e/ou áreas maiores; a poligonização pode criar faces internas que não são a unidade territorial pretendida.
4. Associar os rótulos CAD aos polígonos e conferir uma amostra manualmente.
5. Só então converter as demais subáreas e relacionar os indicadores agregados às chaves territoriais compatíveis.

## Auditoria de continuidade · 26/11/2026

- O serviço WFS da Base de Referência de Palmas continua listado no catálogo oficial da SEPLAN ([serviços geográficos](https://geoportal.to.gov.br/gvsigonline/servicios/)). A tentativa de abrir o `GetCapabilities` neste ambiente não retornou conteúdo; portanto, camadas, atributos, CRS, cobertura e condições de uso não foram confirmados. A listagem do endpoint, sozinha, não valida a aptidão da base para substituir os DWGs.
- Não foi encontrado um executável `ODAFileConverter` no `PATH`. O `qgis_process` e `ogr2ogr` estão instalados, mas isso não converte os DWGs de versões novas que o driver local não lê. Os originais permanecem intactos; nenhum lote foi convertido.
- O inventário local contém o DXF piloto e seus derivados CAD, mas não contém as camadas intermediárias de indicadores referidas na metodologia (`palmas_areas_socioeconomicas_qualificadas.gpkg` e `indicadores_territoriais_qualificados.csv`). Os três PNGs temáticos publicados não são dados vetoriais para colorir as faces CAD. Por isso, não foi criada uma associação visual temática sem chave espacial compatível.
- A seleção da face no protótipo agora acrescenta um contorno claro à geometria escolhida e mantém o detalhe no painel lateral. A cor da base continua representando exclusivamente a presença ou ausência de vínculo do rótulo CAD.

Para concluir a validação cartográfica faltam: acesso legível às capacidades e metadados do WFS (ou uma exportação oficial equivalente), ferramenta compatível para converter os DWGs quando a base municipal não servir, e os produtos vetoriais/atributos temáticos gerados pelo fluxo metodológico. A seleção e a exploração atuais continuam em coordenadas locais, sem validação de posição geográfica ou unidade.
