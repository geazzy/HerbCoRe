#!/usr/bin/env python3
"""Remove imagens não-exsicata, vistas duplicadas, duplicatas de coleta ou
sem coletor/número e baixa substitutas no speciesLink.

Mantém família, espécie e taxonomista. Não reutiliza códigos já presentes no
manifesto, no rastreio de remoções, nem outras vistas do mesmo espécime.
Substitutas com largura ou altura menor que 1024 px são recusadas.
Com --substituir-sem-chave ou --substituir-duplicatas-coleta, só aceita
folha com chave_coleta inédita e só apaga a antiga se houver substituta.
"""

import argparse
import csv
import re
import sys
import time
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

from PIL import Image, UnidentifiedImageError

sys.path.insert(0, str(Path(__file__).resolve().parent))

from baixar_imagens_especies import baixar, buscar_imagens, parse_familias, session, slug
from enriquecer_manifesto import consultar_lote, marcar_duplicatas

RAIZ = Path(__file__).resolve().parents[1]
PASTA_LOCAL = RAIZ / "10familias"
MANIFESTO_PADRAO = PASTA_LOCAL / "manifesto_imagens.csv"
RASTREIO_PADRAO = RAIZ / "rastreio_substituicoes.csv"
RASTREIO_IMAGENS_PADRAO = RAIZ / "rastreio_imagens.csv"
CODIGOS_DESCARTADOS_PADRAO = PASTA_LOCAL / "codigos_descartados.csv"
FAMILIAS_PADRAO = RAIZ / "familias.txt"
LIMIAR_RESOLUCAO = 1024
FATOR_CANDIDATOS = 4
FATOR_CANDIDATOS_CHAVE = 8
LOTE_METADADOS = 20
PAUSA_METADADOS = 0.15
CAMPOS = ["familia", "especie", "taxonomista", "codigo", "arquivo", "resolucao", "exsicata?"]
CAMPOS_RASTREIO = [
    "lote",
    "data",
    "acao",
    "motivo",
    "familia",
    "especie",
    "taxonomista",
    "codigo",
    "arquivo_local",
    "arquivo_online",
    "codigo_relacionado",
    "arquivo_local_relacionado",
    "arquivo_online_relacionado",
]
CAMPOS_DESCARTADOS = ["codigo", "familia", "especie", "taxonomista", "motivo", "fonte"]
SUFIXO_VISTA = re.compile(r"_(?:[ev]\d*|nd\d*|\d+)$", re.IGNORECASE)
MAX_PAGINAS = 25


def prefixo_barcode(codigo):
    return SUFIXO_VISTA.sub("", codigo) if codigo else codigo


def dims_galeria(item):
    try:
        largura = int(item.get("width") or 0)
        altura = int(item.get("height") or 0)
    except (TypeError, ValueError):
        return None
    if largura <= 0 or altura <= 0:
        return None
    return largura, altura


def parece_foto_campo(dims):
    """Fotos de planta viva, não prancha de herbário.

    Cobre o padrão MO em retrato (~2000x3008) e paisagens de câmera
    (ex.: 2048x1536). Scans de prancha em paisagem costumam ter o maior
    lado bem acima de 3000 px.
    """
    if not dims:
        return False
    largura, altura = dims
    menor, maior = min(dims), max(dims)
    if 1900 <= menor <= 2100 and maior <= 3200:
        return True
    if largura > altura and maior <= 3000:
        return True
    return False


def galeria_ok(item, limiar=LIMIAR_RESOLUCAO):
    dims = dims_galeria(item)
    if not dims:
        return True
    largura, altura = dims
    if not (largura >= limiar and altura >= limiar):
        return False
    return not parece_foto_campo(dims)


def medir_arquivo(path):
    try:
        with Image.open(path) as img:
            return img.size
    except (UnidentifiedImageError, OSError):
        return None


def resolucao_ok(dims, limiar=LIMIAR_RESOLUCAO):
    if not dims:
        return False
    largura, altura = dims
    return largura >= limiar and altura >= limiar


def rotulo_resolucao(dims):
    if not dims:
        return "ilegível"
    return f"{dims[0]}x{dims[1]}"


def unir_excluidos(*paths):
    codigos = set()
    prefixos = set()
    vistos = set()
    for path in paths:
        if not path:
            continue
        p = Path(path)
        chave = str(p.resolve()) if p.exists() else str(p)
        if chave in vistos:
            continue
        vistos.add(chave)
        extra_c, extra_p = excluidos_do_rastreio(ler_rastreio(p))
        codigos |= extra_c
        prefixos |= extra_p
    return codigos, prefixos


def registros_da_lista(linhas, path):
    with open(path, encoding="utf-8", newline="") as fh:
        pedidos = []
        vistos = set()
        for row in csv.DictReader(fh):
            codigo = (row.get("codigo") or "").strip()
            if not codigo or codigo in vistos:
                continue
            vistos.add(codigo)
            pedidos.append(codigo)
    por_codigo = {r["codigo"]: r for r in linhas if r.get("codigo")}
    encontrados = []
    ausentes = []
    for codigo in pedidos:
        row = por_codigo.get(codigo)
        if row:
            encontrados.append(row)
        else:
            ausentes.append(codigo)
    return encontrados, ausentes


def eh_false(valor):
    return (valor or "").strip().upper() == "FALSE"


def eh_true(valor):
    return (valor or "").strip().upper() == "TRUE"


def eh_pendente(valor):
    return (valor or "").strip().upper() == "PENDENTE"


def arquivo_relativo(familia, especie, codigo):
    pasta = Path("10familias") / slug(familia) / slug(especie)
    return f"./{pasta.as_posix()}/{codigo}.jpg"


def arquivo_online(familia, especie, codigo):
    """Caminho no Drive (espelho de 10familias: Família/Espécie/CODIGO.jpg)."""
    if not codigo:
        return ""
    pasta = Path(slug(familia)) / slug(especie)
    return f"{pasta.as_posix()}/{codigo}.jpg"


def caminhos_rastreio(familia, especie, codigo):
    if not codigo:
        return "", ""
    return arquivo_relativo(familia, especie, codigo), arquivo_online(familia, especie, codigo)


def ler_manifesto(path):
    with open(path, encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        linhas = []
        for row in reader:
            if not (row.get("familia") or "").strip() or not (row.get("especie") or "").strip():
                continue
            linhas.append({k: (v or "").strip() for k, v in row.items()})
    return linhas


def caminho_arquivo(relativo):
    p = Path(relativo)
    if not p.is_absolute():
        p = (RAIZ / p).resolve()
    return p


def ler_rastreio(path):
    path = Path(path)
    if not path.exists() or path.stat().st_size == 0:
        return []
    with open(path, encoding="utf-8", newline="") as fh:
        return [{k: (v or "").strip() for k, v in row.items()} for row in csv.DictReader(fh)]


def append_rastreio(path, rows):
    if not rows:
        return
    path = Path(path)
    existe = path.exists() and path.stat().st_size > 0
    with open(path, "a", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=CAMPOS_RASTREIO)
        if not existe:
            writer.writeheader()
        for row in rows:
            writer.writerow({campo: row.get(campo, "") for campo in CAMPOS_RASTREIO})


def ler_lista_codigos(path):
    """Lê códigos de um CSV (coluna codigo) ou de um txt (um código por linha)."""
    path = Path(path)
    if not path.exists() or path.stat().st_size == 0:
        return []
    with open(path, encoding="utf-8", newline="") as fh:
        inicio = fh.read(4096)
        fh.seek(0)
        cabecalho = inicio.splitlines()[0] if inicio else ""
        if path.suffix.lower() == ".csv" or "codigo" in cabecalho.split(","):
            return [
                (row.get("codigo") or "").strip()
                for row in csv.DictReader(fh)
                if (row.get("codigo") or "").strip()
            ]
        return [ln.strip() for ln in fh if ln.strip() and not ln.startswith("#")]


def incorporar_excluidos(codigos, prefixos, path):
    extras = ler_lista_codigos(path)
    codigos.update(extras)
    prefixos.update(prefixo_barcode(c) for c in extras)
    return extras


def append_descartados(path, ops, fonte=""):
    """Acrescenta códigos recém-removidos à lista permanente de exclusão."""
    if not ops:
        return
    path = Path(path)
    existentes = set(ler_lista_codigos(path))
    novos = []
    for op in ops:
        if (op.get("acao") or "").strip() != "remover":
            continue
        codigo = (op.get("codigo") or "").strip()
        if not codigo or codigo in existentes:
            continue
        existentes.add(codigo)
        novos.append(
            {
                "codigo": codigo,
                "familia": op.get("familia", ""),
                "especie": op.get("especie", ""),
                "taxonomista": op.get("taxonomista", ""),
                "motivo": op.get("motivo", ""),
                "fonte": fonte or op.get("lote", ""),
            }
        )
    if not novos:
        return
    existe = path.exists() and path.stat().st_size > 0
    with open(path, "a", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=CAMPOS_DESCARTADOS)
        if not existe:
            writer.writeheader()
        for row in novos:
            writer.writerow(row)


def excluidos_do_rastreio(rows):
    codigos = set()
    prefixos = set()
    for row in rows:
        if (row.get("acao") or "").strip() != "remover":
            continue
        codigo = (row.get("codigo") or "").strip()
        if not codigo:
            continue
        codigos.add(codigo)
        prefixos.add(prefixo_barcode(codigo))
    return codigos, prefixos


def conjuntos_exclusao(linhas, extra_codigos, extra_prefixos=None):
    codigos = {r["codigo"] for r in linhas if r.get("codigo")}
    codigos |= set(extra_codigos or ())
    prefixos = {prefixo_barcode(c) for c in codigos}
    prefixos |= set(extra_prefixos or ())
    return codigos, prefixos


def mapa_especialistas(path):
    if not path or not Path(path).exists():
        return {}
    return {b["familia"]: list(b["taxonomistas"]) for b in parse_familias(path)}


def taxonomista_autorizado(taxonomista, autorizados):
    t = (taxonomista or "").strip()
    return bool(t) and t in autorizados


def registros_taxonomista_nao_listado(linhas, especialistas):
    remover = []
    for row in linhas:
        autorizados = especialistas.get(row.get("familia") or "", [])
        if not autorizados:
            continue
        if not taxonomista_autorizado(row.get("taxonomista"), autorizados):
            remover.append(row)
    return remover


def taxonomista_especie(linhas, familia, especie):
    taxs = [
        r["taxonomista"]
        for r in linhas
        if r.get("familia") == familia and r.get("especie") == especie and r.get("taxonomista")
    ]
    return Counter(taxs).most_common(1)[0][0] if taxs else ""


def especialistas_da_familia(familia, especialistas, linhas_ref, especie=None):
    autorizados = list(especialistas.get(familia) or [])
    if autorizados:
        return autorizados
    if especie:
        tax = taxonomista_especie(linhas_ref, familia, especie)
        return [tax] if tax else []
    return []


def chave_ordenacao_vista(row):
    codigo = row.get("codigo") or ""
    exs = (row.get("exsicata?") or "").strip().upper()
    rank_exs = 0 if exs == "TRUE" else 1 if exs == "PENDENTE" else 2
    tem_sufixo = 0 if codigo == prefixo_barcode(codigo) else 1
    m = SUFIXO_VISTA.search(codigo)
    digits = re.sub(r"\D", "", m.group(0)) if m else ""
    num = int(digits) if digits else 0
    return (rank_exs, tem_sufixo, num, codigo)


def vistas_duplicadas_a_remover(linhas):
    grupos = defaultdict(list)
    for row in linhas:
        codigo = row.get("codigo") or ""
        if not codigo:
            continue
        grupos[prefixo_barcode(codigo)].append(row)
    remover = []
    for rs in grupos.values():
        if len(rs) < 2:
            continue
        ordenados = sorted(rs, key=chave_ordenacao_vista)
        remover.extend(ordenados[1:])
    return remover


def parse_resolucao(valor):
    texto = (valor or "").strip().lower()
    if "x" not in texto:
        return None
    largura, altura = texto.split("x", 1)
    try:
        return int(largura), int(altura)
    except ValueError:
        return None


def chave_manter_duplicata(row):
    """Menor tupla = melhor: maior área, depois TRUE > PENDENTE, depois codigo."""
    dims = parse_resolucao(row.get("resolucao"))
    area = dims[0] * dims[1] if dims else -1
    exs = (row.get("exsicata?") or "").strip().upper()
    rank_exs = 0 if exs == "TRUE" else 1 if exs == "PENDENTE" else 2
    return (-area, rank_exs, row.get("codigo") or "")


def linhas_sem_chave(linhas):
    return [r for r in linhas if not (r.get("chave_coleta") or "").strip()]


def chaves_do_acervo(linhas):
    return {
        (r.get("chave_coleta") or "").strip()
        for r in linhas
        if (r.get("chave_coleta") or "").strip()
    }


def duplicatas_a_remover(linhas):
    """Por chave_coleta com mais de um herbário, mantém a melhor folha."""
    grupos = defaultdict(list)
    for row in linhas:
        chave = (row.get("chave_coleta") or "").strip()
        if not chave:
            continue
        grupos[chave].append(row)
    remover = []
    for rs in grupos.values():
        prefixos = {prefixo_barcode(r.get("codigo") or "") for r in rs if r.get("codigo")}
        if len(prefixos) <= 1:
            continue
        ordenados = sorted(rs, key=chave_manter_duplicata)
        remover.extend(ordenados[1:])
    return remover


def meta_do_item(encontrados, codigo):
    pref = prefixo_barcode(codigo or "").upper()
    if pref and pref in encontrados:
        return encontrados[pref]
    codigo_u = (codigo or "").upper()
    if codigo_u in encontrados:
        return encontrados[codigo_u]
    return None


def filtrar_candidatos_com_chave(s, candidatos, chaves_ocupadas, pausa=PAUSA_METADADOS):
    """Mantém candidatos com chave_coleta inédita e anexa metadados do speciesLink."""
    if not candidatos:
        return []
    ocupadas = set(chaves_ocupadas)
    barcodes = []
    vistos = set()
    for item in candidatos:
        pref = prefixo_barcode(item.get("codigo") or "")
        if not pref or pref.upper() in vistos:
            continue
        vistos.add(pref.upper())
        barcodes.append(pref)

    encontrados = {}
    for i in range(0, len(barcodes), LOTE_METADADOS):
        bloco = barcodes[i : i + LOTE_METADADOS]
        print(
            f"  consultando metadados {i + 1}-{i + len(bloco)}/{len(barcodes)}",
            flush=True,
        )
        try:
            achados = consultar_lote(s, bloco, pausa)
        except Exception as exc:
            print(f"  erro metadados: {exc}", flush=True)
            achados = {}
        encontrados.update(achados)

    aceitos = []
    for item in candidatos:
        codigo = item.get("codigo") or ""
        meta = meta_do_item(encontrados, codigo)
        if not meta:
            print(f"  [sem registro] {codigo}", flush=True)
            continue
        chave = (meta.get("chave_coleta") or "").strip()
        if not chave:
            print(f"  [sem chave] {codigo}", flush=True)
            continue
        if chave in ocupadas:
            print(f"  [chave no acervo] {codigo} {chave}", flush=True)
            continue
        novo = dict(item)
        novo["meta"] = meta
        aceitos.append(novo)
        ocupadas.add(chave)
    print(f"  candidatos com chave inédita: {len(aceitos)}/{len(candidatos)}", flush=True)
    return aceitos


def enriquecer_linhas(s, linhas, pausa=PAUSA_METADADOS):
    """Completa metadados faltantes e remarca duplicata_acervo."""
    pendentes = []
    vistos = set()
    for row in linhas:
        pref = prefixo_barcode(row.get("codigo") or "")
        if not pref or pref.upper() in vistos:
            continue
        if (row.get("status_metadados") or "") == "ok" and (row.get("chave_coleta") or "").strip():
            continue
        vistos.add(pref.upper())
        pendentes.append(pref)

    cache = {}
    for i in range(0, len(pendentes), LOTE_METADADOS):
        bloco = pendentes[i : i + LOTE_METADADOS]
        print(
            f"enriquecendo {i + 1}-{i + len(bloco)}/{len(pendentes)}",
            flush=True,
        )
        try:
            cache.update(consultar_lote(s, bloco, pausa))
        except Exception as exc:
            print(f"  erro ao enriquecer: {exc}", flush=True)
    for row in linhas:
        if (row.get("status_metadados") or "") == "ok" and (row.get("chave_coleta") or "").strip():
            continue
        meta = meta_do_item(cache, row.get("codigo") or "")
        if meta:
            row.update(meta)
    marcar_duplicatas(linhas)
    return linhas


def problemas_duplicados(linhas):
    problemas = []
    por_codigo = defaultdict(list)
    por_prefixo = defaultdict(list)
    for i, row in enumerate(linhas):
        codigo = row.get("codigo") or ""
        if not codigo:
            problemas.append(f"linha sem código (espécie {row.get('especie')})")
            continue
        por_codigo[codigo].append(i)
        por_prefixo[prefixo_barcode(codigo)].append(row)
    for codigo, idxs in por_codigo.items():
        if len(idxs) > 1:
            problemas.append(f"código repetido: {codigo} ({len(idxs)}x)")
    for pref, rs in por_prefixo.items():
        if len(rs) > 1:
            codigos = ", ".join(r["codigo"] for r in rs)
            problemas.append(f"prefixo repetido: {pref} -> {codigos}")
    return problemas


def _paginas_imagens(s, familia, especie, taxonomista):
    vistos = []
    vistos_codigos = set()
    offset = 0
    for _ in range(MAX_PAGINAS):
        itens = buscar_imagens(s, familia, especie, taxonomista, from_offset=offset)
        if not itens:
            break
        novos_na_pagina = 0
        for item in itens:
            codigo = item["codigo"]
            if codigo in vistos_codigos:
                continue
            vistos_codigos.add(codigo)
            novos_na_pagina += 1
            item["identifiedby"] = taxonomista
            vistos.append(item)
        if novos_na_pagina == 0:
            break
        offset += len(itens)
        time.sleep(0.4)
    return vistos


def coletar_substitutas(
    s,
    familia,
    especie,
    taxonomista,
    quantidade,
    excluir_codigos,
    excluir_prefixos,
    limiar=LIMIAR_RESOLUCAO,
):
    """Só aceita códigos cujo barcode (prefixo) ainda não está no acervo/rastreio."""
    itens = _paginas_imagens(s, familia, especie, taxonomista)
    escolhidos = []
    vistos_cod = set()
    vistos_pref = set()
    for item in itens:
        codigo = item["codigo"]
        pref = prefixo_barcode(codigo)
        if codigo in excluir_codigos or codigo in vistos_cod:
            continue
        if pref in excluir_prefixos or pref in vistos_pref:
            continue
        if not galeria_ok(item, limiar):
            continue
        escolhidos.append(item)
        vistos_cod.add(codigo)
        vistos_pref.add(pref)
        if len(escolhidos) >= quantidade:
            break
    return escolhidos


def coletar_por_especialistas(
    s,
    familia,
    especie,
    taxonomistas,
    quantidade,
    excluir_codigos,
    excluir_prefixos,
    limiar=LIMIAR_RESOLUCAO,
):
    escolhidos = []
    vistos_cod = set(excluir_codigos)
    vistos_pref = set(excluir_prefixos)
    for tax in taxonomistas:
        if len(escolhidos) >= quantidade:
            break
        falta = quantidade - len(escolhidos)
        print(f"  buscando com {tax} (faltam {falta})", flush=True)
        lote = coletar_substitutas(
            s, familia, especie, tax, falta, vistos_cod, vistos_pref, limiar=limiar
        )
        for item in lote:
            escolhidos.append(item)
            vistos_cod.add(item["codigo"])
            vistos_pref.add(prefixo_barcode(item["codigo"]))
    return escolhidos


def campos_manifesto(linhas):
    campos = list(CAMPOS)
    vistos = set(campos)
    for row in linhas:
        for chave in row:
            if chave not in vistos:
                campos.append(chave)
                vistos.add(chave)
    return campos


def escrever_manifesto(path, linhas):
    tmp = path.with_suffix(path.suffix + ".tmp")
    campos = campos_manifesto(linhas)
    with open(tmp, "w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=campos, extrasaction="ignore")
        writer.writeheader()
        for row in linhas:
            writer.writerow({campo: row.get(campo, "") for campo in campos})
    tmp.replace(path)


def baixar_lote(
    s,
    familia,
    especie,
    taxonomista,
    candidatos,
    codigos_acervo,
    prefixos_acervo,
    alvo=None,
    limiar=LIMIAR_RESOLUCAO,
    chaves_acervo=None,
    exigir_chave=False,
):
    novas = []
    chaves_acervo = chaves_acervo if chaves_acervo is not None else set()
    for item in candidatos:
        if alvo is not None and len(novas) >= alvo:
            break
        codigo = item["codigo"]
        pref = prefixo_barcode(codigo)
        if codigo in codigos_acervo or pref in prefixos_acervo:
            print(f"  [recusado] {codigo} (código ou prefixo já no acervo)", flush=True)
            continue
        meta = item.get("meta") or {}
        chave = (meta.get("chave_coleta") or "").strip()
        if exigir_chave:
            if not chave:
                print(f"  [recusado] {codigo} (sem chave de coleta)", flush=True)
                continue
            if chave in chaves_acervo:
                print(f"  [recusado] {codigo} (chave {chave} já no acervo)", flush=True)
                continue
        rel = arquivo_relativo(familia, especie, codigo)
        destino = caminho_arquivo(rel)
        ident = item.get("identifiedby") or taxonomista
        status = baixar(s, item, destino)
        if status not in ("ok", "existe"):
            print(f"  [{status}] {codigo} ({ident})", flush=True)
            time.sleep(0.25)
            continue
        dims = medir_arquivo(destino)
        campo = parece_foto_campo(dims)
        if not resolucao_ok(dims, limiar) or campo:
            motivo = "campo" if campo else "baixa"
            print(f"  [{motivo}] {codigo} {rotulo_resolucao(dims)}", flush=True)
            if destino.exists():
                destino.unlink()
            time.sleep(0.25)
            continue
        resolucao = rotulo_resolucao(dims)
        print(f"  [{status}] {codigo} ({ident}) {resolucao}", flush=True)
        nova = {
            "familia": familia,
            "especie": especie,
            "taxonomista": ident,
            "codigo": codigo,
            "arquivo": rel,
            "resolucao": resolucao,
            "exsicata?": "PENDENTE",
        }
        if meta:
            nova.update(meta)
            nova["familia"] = familia
            nova["especie"] = especie
            nova["taxonomista"] = ident
            nova["codigo"] = codigo
            nova["arquivo"] = rel
            nova["resolucao"] = resolucao
            nova["exsicata?"] = "PENDENTE"
        novas.append(nova)
        codigos_acervo.add(codigo)
        prefixos_acervo.add(pref)
        if chave:
            chaves_acervo.add(chave)
        time.sleep(0.25)
    return novas


def imprimir_resumo(apagadas, remover, novas, falhas, manifesto, total):
    print("\n=== resumo ===", flush=True)
    if remover is not None:
        print(f"imagens apagadas: {len(apagadas)}/{len(remover)}", flush=True)
    print(f"substitutas baixadas: {len(novas)}", flush=True)
    print(f"linhas no manifesto: {total}", flush=True)
    if novas:
        print("novas (PENDENTE):", flush=True)
        for row in novas:
            print(
                f"  {row['familia']} | {row['especie']} | {row['codigo']}"
                + (f" | {row['resolucao']}" if row.get("resolucao") else ""),
                flush=True,
            )
    if falhas:
        print("espécies sem substituta suficiente:", flush=True)
        for f in falhas:
            print(
                f"  {f['familia']} | {f['especie']} | {f['taxonomista']}: "
                f"{f['obtidas']}/{f['pedidas']}",
                flush=True,
            )
    else:
        print("todas as espécies receberam o número pedido de substitutas.", flush=True)
    print(f"manifesto: {manifesto}", flush=True)


def completar_ate(
    s, linhas, alvo, extra_excluidos=None, extra_prefixos=None, especialistas=None
):
    por_esp = defaultdict(list)
    for row in linhas:
        por_esp[(row["familia"], row["especie"])].append(row)

    extra_excluidos = extra_excluidos or set()
    extra_prefixos = extra_prefixos or set()
    especialistas = especialistas or {}
    codigos_acervo, prefixos_acervo = conjuntos_exclusao(linhas, extra_excluidos, extra_prefixos)
    novas = []
    falhas = []
    for (familia, especie), rows in sorted(por_esp.items()):
        falta = alvo - len(rows)
        if falta <= 0:
            continue
        taxonomistas = especialistas_da_familia(familia, especialistas, rows, especie)
        rotulo = ", ".join(taxonomistas) if taxonomistas else ""
        if not taxonomistas:
            falhas.append(
                {
                    "familia": familia,
                    "especie": especie,
                    "taxonomista": "",
                    "pedidas": falta,
                    "obtidas": 0,
                }
            )
            continue
        print(
            f"\n=== completar {familia} | {especie} | {rotulo} | {falta} ===",
            flush=True,
        )
        candidatos = coletar_por_especialistas(
            s,
            familia,
            especie,
            taxonomistas,
            falta * FATOR_CANDIDATOS,
            codigos_acervo,
            prefixos_acervo,
            limiar=LIMIAR_RESOLUCAO,
        )
        baixadas = baixar_lote(
            s,
            familia,
            especie,
            taxonomistas[0],
            candidatos,
            codigos_acervo,
            prefixos_acervo,
            alvo=falta,
            limiar=LIMIAR_RESOLUCAO,
        )
        novas.extend(baixadas)
        if len(baixadas) < falta:
            falhas.append(
                {
                    "familia": familia,
                    "especie": especie,
                    "taxonomista": rotulo,
                    "pedidas": falta,
                    "obtidas": len(baixadas),
                }
            )
            print(f"  faltaram {falta - len(baixadas)} substituta(s)", flush=True)
    return novas, falhas


def _linha_rastreio(lote, data, acao, motivo, row, relacionado=None):
    familia = (row or {}).get("familia", "")
    especie = (row or {}).get("especie", "")
    codigo = (row or {}).get("codigo", "")
    local, online = caminhos_rastreio(familia, especie, codigo)
    rel = relacionado or {}
    rel_local, rel_online = caminhos_rastreio(
        rel.get("familia") or familia,
        rel.get("especie") or especie,
        rel.get("codigo", ""),
    )
    return {
        "lote": lote,
        "data": data,
        "acao": acao,
        "motivo": motivo,
        "familia": familia,
        "especie": especie,
        "taxonomista": (row or {}).get("taxonomista", ""),
        "codigo": codigo,
        "arquivo_local": local,
        "arquivo_online": online,
        "codigo_relacionado": rel.get("codigo", ""),
        "arquivo_local_relacionado": rel_local,
        "arquivo_online_relacionado": rel_online,
    }


def montar_pares_rastreio(lote, motivo_remover, removidas, baixadas, data):
    ops = []
    n = max(len(removidas), len(baixadas))
    for i in range(n):
        old = removidas[i] if i < len(removidas) else None
        new = baixadas[i] if i < len(baixadas) else None
        if old:
            ops.append(_linha_rastreio(lote, data, "remover", motivo_remover, old, new))
        if new:
            ops.append(_linha_rastreio(lote, data, "adicionar", "substituta", new, old))
    return ops


def emparelhar(rows, baixadas, somente_pares):
    if not somente_pares:
        return rows, baixadas
    n = min(len(rows), len(baixadas))
    return rows[:n], baixadas[:n]


def remocoes_emparelhadas(pares, somente_pares=True):
    remover = []
    for rows, subst in pares:
        rows_ok, _ = emparelhar(rows, subst, somente_pares)
        remover.extend(rows_ok)
    return remover


def apagar_arquivos(remover):
    apagadas = []
    print("\n=== apagando imagens ===", flush=True)
    for row in remover:
        destino = caminho_arquivo(row["arquivo"])
        if destino.exists():
            destino.unlink()
            apagadas.append(row["codigo"])
            print(f"  apagado {row['arquivo']}", flush=True)
        else:
            print(f"  ausente {row['arquivo']}", flush=True)
    return apagadas


def substituir_grupos(
    s,
    grupos,
    linhas_ref,
    extra_excluidos,
    extra_prefixos,
    especialistas=None,
    limiar=LIMIAR_RESOLUCAO,
    exigir_chave=False,
    chaves_ocupadas=None,
):
    """grupos: (familia, especie, taxonomista) -> lista de linhas a trocar."""
    especialistas = especialistas or {}
    if chaves_ocupadas is None:
        chaves_ocupadas = chaves_do_acervo(linhas_ref) if exigir_chave else set()
    codigos_acervo, prefixos_acervo = conjuntos_exclusao(
        linhas_ref, extra_excluidos, extra_prefixos
    )
    novas = []
    falhas = []
    pares = []
    fator = FATOR_CANDIDATOS_CHAVE if exigir_chave else FATOR_CANDIDATOS
    for (familia, especie, taxonomista), rows in grupos.items():
        n = len(rows)
        taxonomistas = especialistas_da_familia(
            familia, especialistas, linhas_ref, especie
        )
        if not taxonomistas:
            taxonomistas = [taxonomista] if taxonomista else []
        rotulo = ", ".join(t for t in taxonomistas if t)
        print(
            f"\n=== {familia} | {especie} | {rotulo} | {n} substituta(s) ===",
            flush=True,
        )
        candidatos = coletar_por_especialistas(
            s,
            familia,
            especie,
            taxonomistas,
            n * fator,
            codigos_acervo,
            prefixos_acervo,
            limiar=limiar,
        )
        if exigir_chave:
            candidatos = filtrar_candidatos_com_chave(s, candidatos, chaves_ocupadas)
        baixadas = baixar_lote(
            s,
            familia,
            especie,
            taxonomistas[0] if taxonomistas else "",
            candidatos,
            codigos_acervo,
            prefixos_acervo,
            alvo=n,
            limiar=limiar,
            chaves_acervo=chaves_ocupadas,
            exigir_chave=exigir_chave,
        )
        novas.extend(baixadas)
        pares.append((rows, baixadas))
        if len(baixadas) < n:
            falhas.append(
                {
                    "familia": familia,
                    "especie": especie,
                    "taxonomista": rotulo,
                    "pedidas": n,
                    "obtidas": len(baixadas),
                }
            )
            print(f"  faltaram {n - len(baixadas)} substituta(s)", flush=True)
    return novas, falhas, pares


def validar_ou_abortar(linhas, contexto):
    problemas = problemas_duplicados(linhas)
    if not problemas:
        return
    print(f"\nERRO: manifesto inválido ({contexto}):", flush=True)
    for p in problemas:
        print(f"  {p}", flush=True)
    raise SystemExit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Substitui imagens não-exsicata, vistas duplicadas, duplicatas de coleta ou sem coletor/número no speciesLink"
    )
    parser.add_argument("--manifesto", default=str(MANIFESTO_PADRAO))
    parser.add_argument("--rastreio", default=None)
    parser.add_argument("--familias", default=str(FAMILIAS_PADRAO))
    parser.add_argument(
        "--lista",
        help="CSV com códigos a substituir (ex: imagens_resolucao_menor_1024.csv)",
    )
    parser.add_argument(
        "--limiar",
        type=int,
        default=LIMIAR_RESOLUCAO,
        help="recusa substitutas com largura ou altura menor que este valor (padrão: 1024)",
    )
    parser.add_argument(
        "--completar",
        type=int,
        metavar="N",
        help="completa espécies com menos de N imagens (especialistas de familias.txt)",
    )
    parser.add_argument(
        "--substituir-vistas-duplicadas",
        action="store_true",
        help="remove vistas extras do mesmo barcode e baixa substitutas",
    )
    parser.add_argument(
        "--substituir-taxonomista-nao-listado",
        action="store_true",
        help="remove imagens cujo taxonomista não está em familias.txt e baixa substitutas",
    )
    parser.add_argument(
        "--substituir-sem-chave",
        action="store_true",
        help="troca imagens sem coletor/número (s.n.) por folhas com chave_coleta; só remove se houver substituta",
    )
    parser.add_argument(
        "--substituir-duplicatas-coleta",
        action="store_true",
        help="descarta extras da mesma coleta (mantém a de maior resolução) e baixa outra coleta; só remove se houver substituta",
    )
    parser.add_argument(
        "--codigos-excluidos",
        help="arquivo extra com códigos a não baixar (CSV com coluna codigo, ou um código por linha)",
    )
    args = parser.parse_args()

    manifesto = Path(args.manifesto)
    if not manifesto.is_absolute():
        manifesto = (Path.cwd() / manifesto).resolve()
    if not manifesto.exists():
        raise SystemExit(f"manifesto não encontrado: {manifesto}")

    if args.rastreio:
        rastreio_path = Path(args.rastreio)
    else:
        rastreio_path = RASTREIO_IMAGENS_PADRAO if args.lista else RASTREIO_PADRAO
    if not rastreio_path.is_absolute():
        rastreio_path = (Path.cwd() / rastreio_path).resolve()

    extra_excluidos, extra_prefixos = unir_excluidos(
        RASTREIO_PADRAO, RASTREIO_IMAGENS_PADRAO, rastreio_path
    )
    for path_exc in (CODIGOS_DESCARTADOS_PADRAO, args.codigos_excluidos):
        if not path_exc:
            continue
        p = Path(path_exc)
        if not p.is_absolute():
            p = (Path.cwd() / p).resolve()
        if not p.exists():
            continue
        n = len(incorporar_excluidos(extra_excluidos, extra_prefixos, p))
        print(f"códigos descartados: {n} de {p.name}", flush=True)

    especialistas = mapa_especialistas(args.familias)
    limiar = args.limiar
    linhas = ler_manifesto(manifesto)

    s = None
    novas = []
    falhas = []
    apagadas = []
    ops_rastreio = []
    hoje = date.today().isoformat()
    linhas_ref = linhas
    chaves_ocupadas = chaves_do_acervo(linhas)

    def processar(remover, lote, motivo, somente_pares=False, exigir_chave=False):
        nonlocal s, novas, falhas
        if not remover:
            return [], [], []
        grupos = defaultdict(list)
        for row in remover:
            tax = row.get("taxonomista") or taxonomista_especie(
                linhas_ref, row["familia"], row["especie"]
            )
            grupos[(row["familia"], row["especie"], tax)].append(row)
        if s is None:
            s = session()
        baixadas, falhas_g, pares = substituir_grupos(
            s,
            grupos,
            linhas_ref,
            extra_excluidos,
            extra_prefixos,
            especialistas,
            limiar=limiar,
            exigir_chave=exigir_chave,
            chaves_ocupadas=chaves_ocupadas,
        )
        novas.extend(baixadas)
        falhas.extend(falhas_g)
        ops = []
        for rows, subst in pares:
            rows_ok, subst_ok = emparelhar(rows, subst, somente_pares)
            ops.extend(montar_pares_rastreio(lote, motivo, rows_ok, subst_ok, hoje))
            extra_excluidos.update(r["codigo"] for r in rows_ok if r.get("codigo"))
            extra_prefixos.update(prefixo_barcode(r["codigo"]) for r in rows_ok if r.get("codigo"))
            extra_excluidos.update(r["codigo"] for r in subst_ok if r.get("codigo"))
            extra_prefixos.update(
                prefixo_barcode(r["codigo"]) for r in subst_ok if r.get("codigo")
            )
        return ops, baixadas, pares

    if args.lista:
        lista_path = Path(args.lista)
        if not lista_path.is_absolute():
            lista_path = (Path.cwd() / lista_path).resolve()
        if not lista_path.exists():
            raise SystemExit(f"lista não encontrada: {lista_path}")
        remover_lista, ausentes = registros_da_lista(linhas, lista_path)
        if ausentes:
            print(
                f"aviso: {len(ausentes)} código(s) da lista não estão no manifesto",
                flush=True,
            )
            for codigo in ausentes:
                print(f"  {codigo}", flush=True)
        print(f"baixa resolução a substituir: {len(remover_lista)}", flush=True)
        pares_lista = []
        if remover_lista:
            ops, _, pares_lista = processar(
                remover_lista,
                "baixa_resolucao",
                "resolucao_menor_1024",
                somente_pares=True,
            )
            ops_rastreio.extend(ops)
        remover = []
        for rows, subst in pares_lista:
            rows_ok, _ = emparelhar(rows, subst, True)
            remover.extend(rows_ok)
        codigos_removidos = {r["codigo"] for r in remover}
        manter = [r for r in linhas if r["codigo"] not in codigos_removidos]
        final = manter + novas
    else:
        manter = [
            r
            for r in linhas
            if eh_true(r.get("exsicata?")) or eh_pendente(r.get("exsicata?"))
        ]
        remover_false = [r for r in linhas if eh_false(r.get("exsicata?"))]
        conhecidos = {(id(r)) for r in manter} | {(id(r)) for r in remover_false}
        outros = [r for r in linhas if id(r) not in conhecidos]
        if outros:
            print(
                f"aviso: {len(outros)} linha(s) ignorada(s) (exsicata? não é TRUE/FALSE/PENDENTE)",
                flush=True,
            )

        remover_vistas = []
        if args.substituir_vistas_duplicadas:
            remover_vistas = vistas_duplicadas_a_remover(manter)
            codigos_vista = {r["codigo"] for r in remover_vistas}
            manter = [r for r in manter if r["codigo"] not in codigos_vista]

        remover_tax = []
        if args.substituir_taxonomista_nao_listado:
            if not especialistas:
                raise SystemExit("familias.txt não encontrado ou sem taxonomistas")
            remover_tax = registros_taxonomista_nao_listado(manter, especialistas)
            codigos_tax = {r["codigo"] for r in remover_tax}
            manter = [r for r in manter if r["codigo"] not in codigos_tax]

        remover_sem_chave = linhas_sem_chave(manter) if args.substituir_sem_chave else []

        print(f"exsicatas/pendentes mantidas: {len(manter)}", flush=True)
        print(f"não-exsicatas a substituir: {len(remover_false)}", flush=True)
        print(f"vistas duplicadas a substituir: {len(remover_vistas)}", flush=True)
        print(f"taxonomista não listado a substituir: {len(remover_tax)}", flush=True)
        print(f"sem chave de coleta a substituir: {len(remover_sem_chave)}", flush=True)
        if args.substituir_duplicatas_coleta:
            print(
                f"duplicatas de coleta (antes da troca s.n.): {len(duplicatas_a_remover(manter))}",
                flush=True,
            )

        remover = []
        if remover_false and not args.substituir_sem_chave and not args.substituir_duplicatas_coleta:
            ops, _, pares_ne = processar(
                remover_false,
                "nao_exsicata",
                "nao_exsicata",
                somente_pares=True,
                exigir_chave=True,
            )
            ops_rastreio.extend(ops)
            rem_ne = remocoes_emparelhadas(pares_ne, True)
            remover.extend(rem_ne)
            rem_cod = {r["codigo"] for r in rem_ne}
            for r in remover_false:
                if r["codigo"] not in rem_cod:
                    manter.append(r)
        elif remover_false:
            print(
                f"aviso: {len(remover_false)} não-exsicata(s) ignorada(s) neste lote",
                flush=True,
            )
        if remover_vistas:
            ops, _, _ = processar(remover_vistas, "vistas_duplicadas", "vista_duplicada")
            ops_rastreio.extend(ops)
            remover.extend(remover_vistas)
        if remover_tax:
            ops, _, _ = processar(
                remover_tax, "taxonomista_nao_listado", "taxonomista_nao_listado"
            )
            ops_rastreio.extend(ops)
            remover.extend(remover_tax)

        if remover_sem_chave:
            ops, _, pares_sc = processar(
                remover_sem_chave,
                "sem_chave_coleta",
                "coletor_ou_numero_ausente",
                somente_pares=True,
                exigir_chave=True,
            )
            ops_rastreio.extend(ops)
            rem_sc = remocoes_emparelhadas(pares_sc, True)
            remover.extend(rem_sc)
            rem_cod = {r["codigo"] for r in rem_sc}
            manter = [r for r in manter if r["codigo"] not in rem_cod]

        if args.substituir_duplicatas_coleta:
            remover_dups = duplicatas_a_remover(manter + novas)
            print(f"duplicatas de coleta a substituir: {len(remover_dups)}", flush=True)
            if remover_dups:
                ops, _, pares_d = processar(
                    remover_dups,
                    "duplicata_coleta",
                    "duplicata_coleta",
                    somente_pares=True,
                    exigir_chave=True,
                )
                ops_rastreio.extend(ops)
                rem_d = remocoes_emparelhadas(pares_d, True)
                remover.extend(rem_d)
                rem_cod = {r["codigo"] for r in rem_d}
                manter = [r for r in manter if r["codigo"] not in rem_cod]
                novas = [r for r in novas if r["codigo"] not in rem_cod]

        final = manter + novas

    validar_ou_abortar(final, "após substituição")

    extras_completar = []
    if args.completar:
        if s is None:
            s = session()
        extras_completar, falhas_c = completar_ate(
            s,
            final,
            args.completar,
            extra_excluidos=extra_excluidos,
            extra_prefixos=extra_prefixos,
            especialistas=especialistas,
        )
        final = final + extras_completar
        novas = novas + extras_completar
        falhas = falhas + falhas_c
        if args.lista:
            lote_c = "baixa_resolucao"
        elif args.substituir_duplicatas_coleta:
            lote_c = "duplicata_coleta"
        elif args.substituir_sem_chave:
            lote_c = "sem_chave_coleta"
        elif args.substituir_taxonomista_nao_listado:
            lote_c = "taxonomista_nao_listado"
        elif args.substituir_vistas_duplicadas:
            lote_c = "vistas_duplicadas"
        else:
            lote_c = "completar"
        ops_rastreio.extend(
            montar_pares_rastreio(
                lote_c,
                "substituta",
                [],
                extras_completar,
                hoje,
            )
        )

    validar_ou_abortar(final, "manifesto final")

    if remover:
        apagadas = apagar_arquivos(remover)

    if remover or novas:
        if novas:
            if s is None:
                s = session()
            print("\n=== metadados e duplicatas ===", flush=True)
            enriquecer_linhas(s, final)
        escrever_manifesto(manifesto, final)
        append_rastreio(rastreio_path, ops_rastreio)
        append_descartados(CODIGOS_DESCARTADOS_PADRAO, ops_rastreio, fonte=rastreio_path.name)
        print(f"rastreio: {rastreio_path}", flush=True)
        print(f"descartados: {CODIGOS_DESCARTADOS_PADRAO}", flush=True)
    elif not remover:
        print("nada a substituir.", flush=True)

    imprimir_resumo(apagadas, remover if remover else None, novas, falhas, manifesto, len(final))


if __name__ == "__main__":
    main()
