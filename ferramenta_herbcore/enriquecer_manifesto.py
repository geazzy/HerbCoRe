#!/usr/bin/env python3
"""Consulta o speciesLink e grava metadados das exsicatas no manifesto.

Para cada código, busca o registro público e acrescenta coletor, número,
local, data etc. Também gera chave_coleta (primeiro coletor normalizado +
número) para marcar duplicatas da mesma coleta no acervo.
"""

from __future__ import annotations

import argparse
import csv
import html as htmlmod
import re
import sys
import time
import unicodedata
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from baixar_imagens_especies import SEARCH_URL, prefixo_barcode, session

RAIZ = Path(__file__).resolve().parents[1]
MANIFESTO_PADRAO = RAIZ / "10familias" / "manifesto_imagens.csv"

CAMPOS_BASE = [
    "familia",
    "especie",
    "taxonomista",
    "codigo",
    "arquivo",
    "resolucao",
    "exsicata?",
]
CAMPOS_META = [
    "barcode",
    "herbario",
    "instituicao",
    "numero_catalogo",
    "nome_cientifico",
    "autor",
    "determinador",
    "coletor",
    "primeiro_coletor",
    "primeiro_coletor_norm",
    "numero_coletor",
    "chave_coleta",
    "duplicata_acervo",
    "n_duplicatas_acervo",
    "duplicatas_codigos",
    "ano_coleta",
    "mes_coleta",
    "dia_coleta",
    "pais",
    "estado",
    "municipio",
    "localidade",
    "latitude",
    "longitude",
    "altitude",
    "notas",
    "tipo",
    "url_registro",
    "status_metadados",
]
CAMPOS = CAMPOS_BASE + CAMPOS_META

SEM_NUMERO = re.compile(
    r"^(s\.?\s*/?\s*n\.?|sn|sine\s*numero|sem\s*n[uú]mero|s/n[oº°]?)$",
    re.IGNORECASE,
)
SPLIT_COLETORES = re.compile(
    r"\s*[;|&]\s*|\s+(?:e|and|et|with|com)\s+",
    re.IGNORECASE,
)
TAG_TH = re.compile(
    r"<th class='tag'>([^<]+)</th>\s*<td>(.*?)</td>",
    re.IGNORECASE | re.DOTALL,
)
REC_URL = re.compile(r"https://specieslink\.net/rec/\d+/\d+")
REC_ID = re.compile(r"showFullRecord\('([^']+)'\)")


def sem_acento(texto):
    nfkd = unicodedata.normalize("NFKD", texto or "")
    return "".join(ch for ch in nfkd if not unicodedata.combining(ch))


def texto_celula(raw):
    limpo = re.sub(r"<[^>]+>", " ", raw or "")
    limpo = htmlmod.unescape(limpo)
    return re.sub(r"\s+", " ", limpo).strip()


def primeiro_coletor(coletor):
    texto = (coletor or "").strip()
    if not texto:
        return ""
    partes = [p.strip() for p in SPLIT_COLETORES.split(texto) if p.strip()]
    return partes[0] if partes else texto


def normalizar_coletor(nome):
    base = sem_acento(nome or "").upper()
    return re.sub(r"[^A-Z0-9]+", "", base)


def normalizar_numero(numero):
    texto = (numero or "").strip()
    if not texto or SEM_NUMERO.match(texto):
        return ""
    return re.sub(r"[^A-Z0-9]+", "", sem_acento(texto).upper())


def chave_coleta(coletor, numero):
    pessoa = normalizar_coletor(primeiro_coletor(coletor))
    nro = normalizar_numero(numero)
    if not pessoa or not nro:
        return ""
    return f"{pessoa}{nro}"


def parse_full_record(html):
    campos = {}
    for m in TAG_TH.finditer(html):
        chave = texto_celula(m.group(1)).lower()
        if not chave or chave in campos:
            continue
        campos[chave] = texto_celula(m.group(2))
    url = REC_URL.search(html)
    campos["url_registro"] = url.group(0) if url else ""
    return campos


def metadados_de_campos(campos, status="ok"):
    coletor = campos.get("collector") or ""
    numero = campos.get("collectornumber") or ""
    primeiro = primeiro_coletor(coletor)
    return {
        "barcode": campos.get("barcode") or "",
        "herbario": campos.get("collectioncode") or "",
        "instituicao": campos.get("institutioncode") or "",
        "numero_catalogo": campos.get("catalognumber") or "",
        "nome_cientifico": campos.get("scientificname") or "",
        "autor": campos.get("scientificnameauthor") or "",
        "determinador": campos.get("identifiedby") or "",
        "coletor": coletor,
        "primeiro_coletor": primeiro,
        "primeiro_coletor_norm": normalizar_coletor(primeiro),
        "numero_coletor": numero,
        "chave_coleta": chave_coleta(coletor, numero),
        "ano_coleta": campos.get("yearcollected") or "",
        "mes_coleta": campos.get("monthcollected") or "",
        "dia_coleta": campos.get("daycollected") or "",
        "pais": campos.get("country") or "",
        "estado": campos.get("stateprovince") or "",
        "municipio": campos.get("county") or "",
        "localidade": campos.get("locality") or "",
        "latitude": campos.get("latitude") or "",
        "longitude": campos.get("longitude") or "",
        "altitude": campos.get("minimumelevation") or "",
        "notas": campos.get("notes") or "",
        "tipo": campos.get("typestatus") or "",
        "url_registro": campos.get("url_registro") or "",
        "status_metadados": status,
    }


def vazio_meta(status):
    return metadados_de_campos({}, status=status)


def get_com_retry(fazer, tentativas=3):
    ultimo = None
    for i in range(tentativas):
        try:
            return fazer()
        except Exception as exc:
            ultimo = exc
            time.sleep(1.5 * (i + 1))
    raise ultimo


def buscar_rec_ids(s, barcodes):
    html = get_com_retry(
        lambda: s.post(
            SEARCH_URL,
            data={
                "action": "records",
                "barcode": ",".join(barcodes),
                "from": "0",
                "recs_order_by": "sp_token",
            },
            timeout=90,
        ).text
    )
    return REC_ID.findall(html)


def buscar_full_record(s, rec_id):
    html = get_com_retry(
        lambda: s.post(
            SEARCH_URL,
            data={"action": "full-record", "rec_id": rec_id},
            timeout=90,
        ).text
    )
    return parse_full_record(html)


def consultar_lote(s, barcodes, pausa):
    encontrados = {}
    if not barcodes:
        return encontrados
    rec_ids = buscar_rec_ids(s, barcodes)
    time.sleep(pausa)
    for rec_id in rec_ids:
        campos = buscar_full_record(s, rec_id)
        barcode = (campos.get("barcode") or "").strip()
        if barcode:
            meta = metadados_de_campos(campos)
            for token in re.split(r"[\s,;]+", barcode):
                token = token.strip()
                if not token:
                    continue
                encontrados[token.upper()] = meta
                pref = prefixo_barcode(token).upper()
                if pref:
                    encontrados[pref] = meta
        time.sleep(pausa)
    faltando = [b for b in barcodes if b.upper() not in encontrados]
    for barcode in faltando:
        rec_ids = buscar_rec_ids(s, [barcode])
        time.sleep(pausa)
        for rec_id in rec_ids:
            campos = buscar_full_record(s, rec_id)
            codigo = (campos.get("barcode") or "").strip()
            meta = metadados_de_campos(campos)
            encontrados[barcode.upper()] = meta
            if codigo:
                for token in re.split(r"[\s,;]+", codigo):
                    token = token.strip()
                    if not token:
                        continue
                    encontrados[token.upper()] = meta
                    pref = prefixo_barcode(token).upper()
                    if pref:
                        encontrados[pref] = meta
            time.sleep(pausa)
    return encontrados


def marcar_duplicatas(linhas):
    grupos = defaultdict(list)
    for i, row in enumerate(linhas):
        chave = (row.get("chave_coleta") or "").strip()
        if not chave:
            continue
        grupos[chave].append(i)

    for row in linhas:
        row["duplicata_acervo"] = ""
        row["n_duplicatas_acervo"] = ""
        row["duplicatas_codigos"] = ""

    for chave, idxs in grupos.items():
        prefixos = []
        vistos = set()
        for i in idxs:
            pref = prefixo_barcode(linhas[i].get("codigo") or "")
            if pref and pref not in vistos:
                vistos.add(pref)
                prefixos.append(pref)
        n = len(vistos)
        if n <= 1:
            for i in idxs:
                linhas[i]["duplicata_acervo"] = "FALSE"
                linhas[i]["n_duplicatas_acervo"] = "1"
                linhas[i]["duplicatas_codigos"] = ""
            continue
        for i in idxs:
            codigo = linhas[i].get("codigo") or ""
            pref = prefixo_barcode(codigo)
            outros = [p for p in prefixos if p != pref]
            linhas[i]["duplicata_acervo"] = "TRUE"
            linhas[i]["n_duplicatas_acervo"] = str(n)
            linhas[i]["duplicatas_codigos"] = "|".join(outros)
    return grupos


def ler_manifesto(path):
    with open(path, encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        originais = list(reader.fieldnames or CAMPOS_BASE)
        linhas = [{k: (v or "").strip() for k, v in row.items()} for row in reader]
    return originais, linhas


def campos_saida(originais):
    campos = list(originais or CAMPOS_BASE)
    for extra in CAMPOS_META:
        if extra not in campos:
            campos.append(extra)
    return campos


def escrever_manifesto(path, campos, linhas):
    tmp = path.with_suffix(path.suffix + ".tmp")
    with open(tmp, "w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=campos, extrasaction="ignore")
        writer.writeheader()
        for row in linhas:
            writer.writerow({campo: row.get(campo, "") for campo in campos})
    tmp.replace(path)


def aplicar_cache(linhas, cache):
    for row in linhas:
        pref = prefixo_barcode(row.get("codigo") or "").upper()
        meta = cache.get(pref)
        if not meta:
            continue
        row.update(meta)
        if not row.get("barcode"):
            row["barcode"] = prefixo_barcode(row.get("codigo") or "")


def enriquecer(manifesto, forcar=False, lote=20, pausa=0.15, limite=None):
    originais, linhas = ler_manifesto(manifesto)
    campos = campos_saida(originais)

    pendentes = []
    vistos = set()
    for row in linhas:
        codigo = (row.get("codigo") or "").strip()
        pref = prefixo_barcode(codigo)
        if not pref or pref in vistos:
            continue
        if not forcar and (row.get("status_metadados") or "") == "ok":
            continue
        vistos.add(pref)
        pendentes.append(pref)
    if limite:
        pendentes = pendentes[:limite]

    print(
        f"{len(linhas)} linha(s); {len(pendentes)} barcode(s) a consultar",
        flush=True,
    )

    cache = {}
    if not forcar:
        for row in linhas:
            if (row.get("status_metadados") or "") != "ok":
                continue
            pref = prefixo_barcode(row.get("codigo") or "").upper()
            if pref and pref not in cache:
                cache[pref] = {campo: row.get(campo, "") for campo in CAMPOS_META}

    s = session() if pendentes else None
    ok = falha = 0
    for i in range(0, len(pendentes), lote):
        bloco = pendentes[i : i + lote]
        print(
            f"consultando {i + 1}-{i + len(bloco)}/{len(pendentes)}",
            flush=True,
        )
        try:
            achados = consultar_lote(s, bloco, pausa)
        except Exception as exc:
            print(f"  erro no lote: {exc}", flush=True)
            achados = {}
        for pref in bloco:
            chave = pref.upper()
            if chave in achados:
                cache[chave] = achados[chave]
                ok += 1
            else:
                cache[chave] = vazio_meta("nao_encontrado")
                falha += 1
                print(f"  não encontrado: {pref}", flush=True)
        aplicar_cache(linhas, cache)
        escrever_manifesto(manifesto, campos, linhas)

    aplicar_cache(linhas, cache)
    marcar_duplicatas(linhas)
    escrever_manifesto(manifesto, campos, linhas)

    com_chave = sum(1 for r in linhas if r.get("chave_coleta"))
    n_dup = sum(1 for r in linhas if r.get("duplicata_acervo") == "TRUE")
    grupos_dup = {
        r.get("chave_coleta")
        for r in linhas
        if r.get("duplicata_acervo") == "TRUE" and r.get("chave_coleta")
    }
    print(f"metadados ok: {ok}", flush=True)
    print(f"não encontrados neste lote: {falha}", flush=True)
    print(f"com chave de coleta: {com_chave}/{len(linhas)}", flush=True)
    print(
        f"duplicatas no acervo: {n_dup} exsicata(s) em {len(grupos_dup)} coleta(s)",
        flush=True,
    )
    print(f"manifesto: {manifesto}", flush=True)
    return linhas


def main():
    parser = argparse.ArgumentParser(
        description="Acrescenta metadados do speciesLink e marca duplicatas no manifesto"
    )
    parser.add_argument("--manifesto", default=str(MANIFESTO_PADRAO))
    parser.add_argument("--forcar", action="store_true", help="consulta de novo mesmo se já houver metadados")
    parser.add_argument("--lote", type=int, default=20)
    parser.add_argument("--pausa", type=float, default=0.15)
    parser.add_argument("--limite", type=int, help="processa só as N primeiras linhas (teste)")
    args = parser.parse_args()

    manifesto = Path(args.manifesto)
    if not manifesto.is_absolute():
        manifesto = (Path.cwd() / manifesto).resolve()
    if not manifesto.exists():
        raise SystemExit(f"manifesto não encontrado: {manifesto}")

    enriquecer(
        manifesto,
        forcar=args.forcar,
        lote=args.lote,
        pausa=args.pausa,
        limite=args.limite,
    )


if __name__ == "__main__":
    main()
