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


def buscar_imagens(s, familia, especie, identifiedby=None):
    data = {
        "action": "images",
        "family": familia,
        "scientificname": especie,
        "flags": "photo",
        "from": "0",
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


def coletar(s, familia, especie, taxonomistas, limite):
    vistos = set()
    escolhidos = []
    tentativas = list(taxonomistas) + [None]
    for ident in tentativas:
        if len(escolhidos) >= limite:
            break
        for item in buscar_imagens(s, familia, especie, ident):
            if item["codigo"] in vistos:
                continue
            vistos.add(item["codigo"])
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
                itens = coletar(s, familia, especie, bloco["taxonomistas"], args.por_especie)
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
