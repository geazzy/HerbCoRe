#!/usr/bin/env python3
"""Lê manifesto_imagens.csv e grava a resolução (largura x altura) de cada imagem."""

import argparse
import csv
import sys
from pathlib import Path

from PIL import Image, UnidentifiedImageError

RAIZ = Path(__file__).resolve().parents[1]
MANIFESTO_PADRAO = RAIZ / "10familias" / "manifesto_imagens.csv"
LISTA_BAIXAS_PADRAO = RAIZ / "imagens_resolucao_menor_1024.csv"
CAMPO_RESOLUCAO = "resolucao"
CAMPOS_BASE = ["familia", "especie", "taxonomista", "codigo", "arquivo", "exsicata?"]
LIMIAR_PADRAO = 1024


def caminho_arquivo(relativo, raiz):
    p = Path(relativo)
    if not p.is_absolute():
        p = (raiz / p).resolve()
    return p


def resolucao_imagem(path):
    with Image.open(path) as img:
        largura, altura = img.size
    return f"{largura}x{altura}"


def parse_resolucao(valor):
    texto = (valor or "").strip().lower()
    if "x" not in texto:
        return None
    largura, altura = texto.split("x", 1)
    try:
        return int(largura), int(altura)
    except ValueError:
        return None


def resolucao_baixa(row, limiar):
    dims = parse_resolucao(row.get(CAMPO_RESOLUCAO))
    if not dims:
        return False
    largura, altura = dims
    return largura < limiar or altura < limiar


def escrever_lista_baixas(linhas, campos, saida, limiar):
    baixas = [row for row in linhas if resolucao_baixa(row, limiar)]
    with open(saida, "w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=campos, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(baixas)
    return baixas


def ler_manifesto(manifesto):
    with open(manifesto, encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        originais = list(reader.fieldnames or CAMPOS_BASE)
        linhas = list(reader)
    return originais, linhas


def campos_saida(originais):
    campos = list(originais or CAMPOS_BASE)
    if CAMPO_RESOLUCAO in campos:
        return campos
    if "arquivo" in campos:
        i = campos.index("arquivo") + 1
        return campos[:i] + [CAMPO_RESOLUCAO] + campos[i:]
    return campos + [CAMPO_RESOLUCAO]


def atualizar_manifesto(manifesto, raiz):
    originais, linhas = ler_manifesto(manifesto)
    campos = campos_saida(originais)
    ok = 0
    falhas = []

    for i, row in enumerate(linhas, start=2):
        relativo = (row.get("arquivo") or "").strip()
        if not relativo:
            row[CAMPO_RESOLUCAO] = ""
            falhas.append((i, relativo or "(sem arquivo)", "caminho vazio"))
            continue
        path = caminho_arquivo(relativo, raiz)
        if not path.exists():
            row[CAMPO_RESOLUCAO] = ""
            falhas.append((i, relativo, "arquivo não encontrado"))
            continue
        try:
            row[CAMPO_RESOLUCAO] = resolucao_imagem(path)
            ok += 1
        except (UnidentifiedImageError, OSError) as exc:
            row[CAMPO_RESOLUCAO] = ""
            falhas.append((i, relativo, str(exc)))

    with open(manifesto, "w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=campos, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(linhas)

    return linhas, campos, ok, falhas


def main():
    parser = argparse.ArgumentParser(
        description="Grava a resolução de cada imagem em manifesto_imagens.csv"
    )
    parser.add_argument(
        "--manifesto",
        default=str(MANIFESTO_PADRAO),
        help="CSV do manifesto (padrão: manifesto_imagens.csv na raiz)",
    )
    parser.add_argument(
        "--raiz",
        default=str(RAIZ),
        help="pasta usada para resolver caminhos relativos do manifesto",
    )
    parser.add_argument(
        "--lista-baixas",
        default=str(LISTA_BAIXAS_PADRAO),
        help="CSV só com imagens abaixo do limiar (padrão: imagens_resolucao_menor_1024.csv)",
    )
    parser.add_argument(
        "--limiar",
        type=int,
        default=LIMIAR_PADRAO,
        help="lista imagens com largura ou altura menor que este valor (padrão: 1024)",
    )
    parser.add_argument(
        "--somente-lista",
        action="store_true",
        help="não relê as imagens; só gera a lista das resoluções baixas",
    )
    args = parser.parse_args()

    manifesto = Path(args.manifesto)
    if not manifesto.exists():
        raise SystemExit(f"manifesto não encontrado: {manifesto}")

    if args.somente_lista:
        originais, linhas = ler_manifesto(manifesto)
        campos = campos_saida(originais)
    else:
        linhas, campos, ok, falhas = atualizar_manifesto(manifesto, Path(args.raiz))
        print(f"resoluções gravadas: {ok}", flush=True)
        if falhas:
            print(f"falhas: {len(falhas)}", flush=True)
            for linha, arquivo, motivo in falhas:
                print(f"  linha {linha}: {arquivo} ({motivo})", flush=True)
            sys.exit(1)
        print(f"manifesto: {manifesto}", flush=True)

    lista_baixas = Path(args.lista_baixas)
    baixas = escrever_lista_baixas(linhas, campos, lista_baixas, args.limiar)
    print(
        f"resoluções < {args.limiar}px (largura ou altura): {len(baixas)}",
        flush=True,
    )
    print(f"lista: {lista_baixas}", flush=True)


if __name__ == "__main__":
    main()
