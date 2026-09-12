#!/usr/bin/env python3
"""Baixa N imagens de exsicata por espécie a partir do buscador do speciesLink.

Prioriza registros identificados pelos taxonomistas listados em familias.txt.
Não exige chave da API: usa a galeria pública e o endpoint osd-dezoomify.
"""

import argparse
import csv
import re
import time
from pathlib import Path

import requests

SEARCH_URL = "https://specieslink.net/search/index"
DEZOOMIFY_URL = "https://specieslink.net/search/util/osd-dezoomify"
DEFAULT_FAMILIAS = Path(__file__).resolve().parents[1] / "familias.txt"
DESCARTADOS_PADRAO = Path(__file__).resolve().parents[1] / "10familias" / "codigos_descartados.csv"
SUFIXO_VISTA = re.compile(r"_(?:[ev]\d*|nd\d*|\d+)$", re.IGNORECASE)


def parse_familias(path):
    blocos = []
    familia = None
    taxonomistas = []
    especies = []

    cabecalho = re.compile(
        r"^([A-ZÁÉÍÓÚÂÊÔÃÕ][A-Za-zÀ-ÿ\-]+)\s*\((?:taxonomista:\s*)?(.+)\)$"
    )

    def fechar():
        if familia and especies:
            blocos.append(
                {
                    "familia": familia,
                    "taxonomistas": taxonomistas,
                    "especies": list(especies),
                }
            )

    with open(path, encoding="utf-8") as fh:
        for raw in fh:
            linha = raw.strip()
            if not linha:
                continue
            m = cabecalho.match(linha)
            if m:
                fechar()
                familia = m.group(1)
                taxonomistas = [t.strip() for t in m.group(2).split(",") if t.strip()]
                especies = []
                continue
            if familia and re.match(r"^[A-Z][a-z]+ [a-z\-]+$", linha):
                especies.append(linha)
    fechar()
    return blocos


def session():
    s = requests.Session()
    s.headers.update(
        {
            "User-Agent": "HerbCoRe/1.0 (download de exsicatas para pesquisa)",
            "Referer": "https://specieslink.net/search/",
        }
    )
    s.get("https://specieslink.net/search/", timeout=30)
    return s


def buscar_imagens(s, familia, especie, identifiedby=None, from_offset=0):
    data = {
        "action": "images",
        "family": familia,
        "scientificname": especie,
        "flags": "photo",
        "from": str(from_offset),
        "recs_order_by": "random_order",
    }
    if identifiedby:
        data["identifiedby"] = identifiedby
    html = s.post(SEARCH_URL, data=data, timeout=90).text
    itens = []
    m = re.search(r"imgs_array\s*=\s*\[([^\]]+)\]", html)
    if not m:
        return itens
    for raw in re.findall(r"'([^']+)'", m.group(1)):
        if ":" not in raw:
            continue
        path, width, height = raw.split(":")
        codigo = path.rstrip("/").split("/")[-1]
        itens.append(
            {
                "path": path,
                "width": width,
                "height": height,
                "codigo": codigo,
            }
        )
    return itens


def prefixo_barcode(codigo):
    return SUFIXO_VISTA.sub("", codigo) if codigo else codigo


def ler_codigos_descartados(path=None):
    path = Path(path or DESCARTADOS_PADRAO)
    if not path.exists() or path.stat().st_size == 0:
        return set(), set()
    with open(path, encoding="utf-8", newline="") as fh:
        codigos = {
            (row.get("codigo") or "").strip()
            for row in csv.DictReader(fh)
            if (row.get("codigo") or "").strip()
        }
    prefixos = {prefixo_barcode(c) for c in codigos}
    return codigos, prefixos


def coletar(s, familia, especie, taxonomistas, limite, excluir_codigos=None, excluir_prefixos=None):
    vistos = set(excluir_codigos or ())
    prefixos = set(excluir_prefixos or ())
    escolhidos = []
    tentativas = list(taxonomistas) + [None]
    for ident in tentativas:
        if len(escolhidos) >= limite:
            break
        for item in buscar_imagens(s, familia, especie, ident):
            codigo = item["codigo"]
            pref = prefixo_barcode(codigo)
            if codigo in vistos or pref in prefixos:
                continue
            vistos.add(codigo)
            prefixos.add(pref)
            item["identifiedby"] = ident or ""
            escolhidos.append(item)
            if len(escolhidos) >= limite:
                break
        time.sleep(0.4)
    return escolhidos


def baixar(s, item, destino):
    destino.parent.mkdir(parents=True, exist_ok=True)
    if destino.exists() and destino.stat().st_size > 1000:
        return "existe"
    params = {
        "imagecode": item["codigo"],
        "path": item["path"],
        "width": item["width"],
        "height": item["height"],
    }
    for tentativa in range(3):
        try:
            r = s.get(DEZOOMIFY_URL, params=params, timeout=120)
            if r.status_code == 200 and r.content[:2] == b"\xff\xd8":
                destino.write_bytes(r.content)
                return "ok"
        except requests.RequestException:
            pass
        time.sleep(1.5 * (tentativa + 1))
    return "erro"


def slug(nome):
    return re.sub(r"[^\w\-]+", "_", nome, flags=re.UNICODE).strip("_")


def main():
    parser = argparse.ArgumentParser(
        description="Baixa N imagens por espécie listada em familias.txt"
    )
    parser.add_argument("--arquivo", default=str(DEFAULT_FAMILIAS))
    parser.add_argument("--familia", help="restringe a uma família (ex: Lauraceae)")
    parser.add_argument("--exceto", action="append", default=[], help="família a pular (pode repetir)")
    parser.add_argument("--por-especie", type=int, default=20)
    parser.add_argument("--saida", default=str(Path(__file__).resolve().parents[1] / "imagens-saida"))
    args = parser.parse_args()

    blocos = parse_familias(args.arquivo)
    if args.familia:
        blocos = [b for b in blocos if b["familia"].lower() == args.familia.lower()]
    if args.exceto:
        pular = {n.lower() for n in args.exceto}
        blocos = [b for b in blocos if b["familia"].lower() not in pular]
    if not blocos:
        raise SystemExit("nenhuma família encontrada no arquivo")

    s = session()
    excluir_codigos, excluir_prefixos = ler_codigos_descartados()
    if excluir_codigos:
        print(f"excluindo {len(excluir_codigos)} código(s) já descartado(s)", flush=True)
    saida = Path(args.saida)
    manifesto = saida / "manifesto_imagens.csv"
    saida.mkdir(parents=True, exist_ok=True)
    novo_manifesto = not manifesto.exists()
    with open(manifesto, "a", newline="", encoding="utf-8") as csv_fh:
        writer = csv.DictWriter(
            csv_fh,
            fieldnames=["familia", "especie", "taxonomista", "codigo", "arquivo", "status"],
        )
        if novo_manifesto:
            writer.writeheader()

        for bloco in blocos:
            familia = bloco["familia"]
            print(f"\n=== {familia} | taxonomistas: {', '.join(bloco['taxonomistas'])} ===", flush=True)
            for especie in bloco["especies"]:
                itens = coletar(
                    s,
                    familia,
                    especie,
                    bloco["taxonomistas"],
                    args.por_especie,
                    excluir_codigos=excluir_codigos,
                    excluir_prefixos=excluir_prefixos,
                )
                pasta = saida / slug(familia) / slug(especie)
                print(f"{especie}: {len(itens)} url(s)", flush=True)
                for item in itens:
                    destino = pasta / f"{item['codigo']}.jpg"
                    status = baixar(s, item, destino)
                    print(f"  [{status}] {item['codigo']} ({item['identifiedby'] or 'sem filtro'})", flush=True)
                    writer.writerow(
                        {
                            "familia": familia,
                            "especie": especie,
                            "taxonomista": item["identifiedby"],
                            "codigo": item["codigo"],
                            "arquivo": str(destino),
                            "status": status,
                        }
                    )
                    csv_fh.flush()
                    time.sleep(0.25)

    print(f"\nconcluído. imagens em {saida}", flush=True)
    print(f"manifesto: {manifesto}", flush=True)


if __name__ == "__main__":
    main()
