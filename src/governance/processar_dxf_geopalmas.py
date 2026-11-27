"""Converte DXF de loteamento em polígonos e associa rótulos de lote.

Requer ogr2ogr (GDAL) e qgis_process com native:polygonize e
native:joinattributesbylocation. Nenhum CRS é atribuído automaticamente.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


RAIZ = Path(__file__).resolve().parents[2]
SAIDA = RAIZ / "data" / "processed" / "geopalmas"
PADRAO_CHAVE = re.compile(r"^[A-Za-z0-9_-]+$")


def _executar(comando: list[str], *, env: dict[str, str] | None = None) -> str:
    processo = subprocess.run(
        comando,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
    )
    return processo.stdout + processo.stderr


def processar(arquivo_dxf: Path, destino: Path = SAIDA) -> dict[str, int | str]:
    arquivo_dxf = arquivo_dxf.expanduser().resolve()
    if not arquivo_dxf.is_file() or arquivo_dxf.suffix.lower() != ".dxf":
        raise ValueError(f"Entrada não encontrada ou não é DXF: {arquivo_dxf}")
    chave = arquivo_dxf.stem
    if not PADRAO_CHAVE.fullmatch(chave):
        raise ValueError(f"Nome da subárea contém caracteres não suportados: {chave}")
    for ferramenta in ("ogr2ogr", "ogrinfo", "qgis_process"):
        if shutil.which(ferramenta) is None:
            raise RuntimeError(f"Ferramenta necessária não encontrada no PATH: {ferramenta}")

    pasta_saida = destino / chave
    pasta_saida.mkdir(parents=True, exist_ok=True)
    linhas_final = pasta_saida / "linhas_cad.gpkg"
    rotulos_final = pasta_saida / "rotulos_lote.gpkg"
    poligonos_final = pasta_saida / "areas_rotuladas.gpkg"
    geojson_final = pasta_saida / "areas_rotuladas.geojson"

    with tempfile.TemporaryDirectory(prefix="geopalmas-", dir=pasta_saida) as temp:
        tmp = Path(temp)
        linhas = tmp / "linhas.gpkg"
        rotulos = tmp / "rotulos.gpkg"
        poligonos = tmp / "areas.gpkg"
        rotulados = tmp / "areas_rotuladas.gpkg"

        _executar([
            "ogr2ogr", "-f", "GPKG", str(linhas), str(arquivo_dxf), "entities",
            "-where", "Layer IN ('LOTE','QUADRA_INTERNA')",
            "-nln", "linhas_cad", "-nlt", "PROMOTE_TO_MULTI",
            "-lco", "SPATIAL_INDEX=YES",
        ])
        _executar([
            "ogr2ogr", "-f", "GPKG", str(rotulos), str(arquivo_dxf), "entities",
            "-where", "Layer='NUMERO_LOTE' AND Text IS NOT NULL",
            "-nln", "rotulos_lote", "-nlt", "POINT", "-lco", "SPATIAL_INDEX=YES",
        ])

        ambiente = os.environ.copy()
        ambiente["QT_QPA_PLATFORM"] = "offscreen"
        _executar([
            "qgis_process", "run", "native:polygonize", "--",
            f"INPUT={linhas}|layername=linhas_cad", "KEEP_FIELDS=1", f"OUTPUT={poligonos}",
        ], env=ambiente)
        _executar([
            "qgis_process", "run", "native:joinattributesbylocation", "--",
            f"INPUT={poligonos}|layername=areas", "PREDICATE=1",
            f"JOIN={rotulos}|layername=rotulos_lote", "JOIN_FIELDS=Text",
            "METHOD=1", "DISCARD_NONMATCHING=0", "PREFIX=lote_", f"OUTPUT={rotulados}",
        ], env=ambiente)
        _executar(["ogr2ogr", "-f", "GeoJSON", str(tmp / "areas.geojson"), str(rotulados), "-nln", "areas"])

        dados = json.loads((tmp / "areas.geojson").read_text(encoding="utf-8"))
        faces = dados.get("features", [])
        rotuladas = sum(bool(str((face.get("properties") or {}).get("lote_Text") or "").strip()) for face in faces)
        if not faces:
            raise RuntimeError("A conversão não gerou polígonos; confira as camadas CAD de linha.")

        # Publica cada derivado completo antes de trocar os arquivos finais.
        shutil.copy2(linhas, linhas_final)
        shutil.copy2(rotulos, rotulos_final)
        shutil.copy2(rotulados, poligonos_final)
        shutil.copy2(tmp / "areas.geojson", geojson_final)

    return {
        "subarea": chave,
        "faces": len(faces),
        "faces_com_rotulo": rotuladas,
        "faces_sem_rotulo": len(faces) - rotuladas,
        "crs": "não informado; nenhuma reprojeção aplicada",
        "geojson": str(geojson_final),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("entrada", type=Path, help="Um arquivo .dxf ou pasta contendo .dxf")
    args = parser.parse_args()
    entrada = args.entrada.expanduser()
    arquivos = sorted(entrada.glob("*.dxf")) if entrada.is_dir() else [entrada]
    if not arquivos:
        parser.error(f"Nenhum DXF encontrado em {entrada}")
    erros = 0
    for arquivo in arquivos:
        try:
            resultado = processar(arquivo)
            print(
                f"{resultado['subarea']}: {resultado['faces']} faces; "
                f"{resultado['faces_com_rotulo']} com rótulo; "
                f"{resultado['faces_sem_rotulo']} sem rótulo; CRS {resultado['crs']}"
            )
        except (OSError, ValueError, RuntimeError, subprocess.CalledProcessError) as erro:
            erros += 1
            print(f"ERRO {arquivo.name}: {erro}", file=sys.stderr)
    return 1 if erros else 0


if __name__ == "__main__":
    raise SystemExit(main())
