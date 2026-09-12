#!/usr/bin/env python3
"""Aplica o rastreio de substituições no Google Drive (OAuth).

Lê rastreio_substituicoes.csv: linhas `remover` vão para a lixeira e linhas
`adicionar` são enviadas para o mesmo caminho Família/Espécie/CODIGO.jpg.
Também envia/atualiza manifesto_imagens.csv e codigos_descartados.csv na pasta
raiz do Drive (espelho de 10familias/).

O ID da pasta pode vir de --pasta-id ou da chave pasta-id no .env.

Dependências:
  pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib

Credenciais:
  1. Ative a Google Drive API no Google Cloud.
  2. Crie um ID do cliente OAuth (app para computador).
  3. Salve o JSON como credentials.json na raiz do repositório.
  4. Na primeira execução o navegador abre; o token fica em token.json.

O dry-run é o padrão; use --aplicar para alterar o Drive.
"""

import argparse
import csv
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
PASTA_LOCAL = RAIZ / "10familias"
RASTREIO_PADRAO = RAIZ / "rastreio_substituicoes.csv"
ENV_PADRAO = RAIZ / ".env"
CREDENCIAIS_PADRAO = RAIZ / "credentials.json"
TOKEN_PADRAO = RAIZ / "token.json"
ESCOPOS = ["https://www.googleapis.com/auth/drive"]
MIME_PASTA = "application/vnd.google-apps.folder"
MIME_POR_SUFIXO = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".csv": "text/csv",
    ".txt": "text/plain",
}
ARQUIVOS_METADADOS = [
    (PASTA_LOCAL / "manifesto_imagens.csv", "manifesto_imagens.csv"),
    (PASTA_LOCAL / "codigos_descartados.csv", "codigos_descartados.csv"),
]


def ler_env(path=ENV_PADRAO):
    dados = {}
    path = Path(path)
    if not path.exists():
        return dados
    for raw in path.read_text(encoding="utf-8").splitlines():
        linha = raw.strip()
        if not linha or linha.startswith("#") or "=" not in linha:
            continue
        chave, valor = linha.split("=", 1)
        dados[chave.strip()] = valor.strip().strip('"').strip("'")
    return dados


def pasta_id_do_env(env=None):
    env = env if env is not None else ler_env()
    for chave in ("pasta-id", "pasta_id", "PASTA_ID"):
        if env.get(chave):
            return env[chave]
    return ""


def extrair_pasta_id(valor):
    valor = (valor or "").strip()
    m = re.search(r"/folders/([a-zA-Z0-9_-]+)", valor)
    if m:
        return m.group(1)
    m = re.search(r"[?&]id=([a-zA-Z0-9_-]+)", valor)
    if m:
        return m.group(1)
    return valor


def mimetype_arquivo(path):
    return MIME_POR_SUFIXO.get(Path(path).suffix.lower(), "application/octet-stream")


def caminho_local(relativo):
    p = Path(relativo)
    if not p.is_absolute():
        p = (RAIZ / p).resolve()
    return p


def ler_rastreio(path, lote=None):
    with open(path, encoding="utf-8", newline="") as fh:
        linhas = list(csv.DictReader(fh))
    if lote:
        linhas = [r for r in linhas if (r.get("lote") or "").strip() == lote]
    for row in linhas:
        for chave in row:
            row[chave] = (row.get(chave) or "").strip()
    return linhas


def autenticar(credenciais, token):
    try:
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from googleapiclient.discovery import build
    except ImportError as exc:
        raise SystemExit(
            "instale as dependências do Drive:\n"
            "  pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib"
        ) from exc

    if not credenciais.exists():
        raise SystemExit(
            f"credentials.json não encontrado em {credenciais}\n"
            "baixe a credencial OAuth (app para computador) e salve nesse caminho"
        )

    creds = None
    if token.exists():
        creds = Credentials.from_authorized_user_file(str(token), ESCOPOS)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(str(credenciais), ESCOPOS)
            creds = flow.run_local_server(port=0)
        token.write_text(creds.to_json(), encoding="utf-8")
    return build("drive", "v3", credentials=creds)


def _listar_filhos(service, pasta_id):
    itens = []
    page_token = None
    while True:
        resp = (
            service.files()
            .list(
                q=f"'{pasta_id}' in parents and trashed = false",
                fields="nextPageToken, files(id, name, mimeType)",
                pageSize=1000,
                pageToken=page_token,
                supportsAllDrives=True,
                includeItemsFromAllDrives=True,
            )
            .execute()
        )
        itens.extend(resp.get("files", []))
        page_token = resp.get("nextPageToken")
        if not page_token:
            break
    return itens


def indexar_arvore(service, raiz_id):
    pastas = {"": raiz_id}
    arquivos = {}
    fila = [("", raiz_id)]
    while fila:
        prefixo, pasta_id = fila.pop(0)
        for item in _listar_filhos(service, pasta_id):
            rel = f"{prefixo}/{item['name']}" if prefixo else item["name"]
            if item["mimeType"] == MIME_PASTA:
                pastas[rel] = item["id"]
                fila.append((rel, item["id"]))
            else:
                arquivos[rel] = item
    return pastas, arquivos


def garantir_pasta(service, pastas, rel_dir, aplicar):
    if not rel_dir:
        return pastas[""]
    atual = ""
    parent_id = pastas[""]
    for parte in Path(rel_dir).parts:
        prox = f"{atual}/{parte}" if atual else parte
        if prox not in pastas:
            if not aplicar:
                pastas[prox] = f"dry-run:{prox}"
            else:
                criado = (
                    service.files()
                    .create(
                        body={
                            "name": parte,
                            "mimeType": MIME_PASTA,
                            "parents": [parent_id],
                        },
                        fields="id",
                        supportsAllDrives=True,
                    )
                    .execute()
                )
                pastas[prox] = criado["id"]
                print(f"  pasta criada: {prox}", flush=True)
        parent_id = pastas[prox]
        atual = prox
    return parent_id


def enviar(service, local, pasta_id, nome):
    from googleapiclient.http import MediaFileUpload

    media = MediaFileUpload(str(local), mimetype=mimetype_arquivo(local), resumable=True)
    criado = (
        service.files()
        .create(
            body={"name": nome, "parents": [pasta_id]},
            media_body=media,
            fields="id",
            supportsAllDrives=True,
        )
        .execute()
    )
    return criado["id"]


def atualizar_conteudo(service, local, file_id):
    from googleapiclient.http import MediaFileUpload

    media = MediaFileUpload(str(local), mimetype=mimetype_arquivo(local), resumable=True)
    service.files().update(
        fileId=file_id,
        media_body=media,
        supportsAllDrives=True,
    ).execute()
    return file_id


def lixeira(service, file_id):
    service.files().update(
        fileId=file_id,
        body={"trashed": True},
        supportsAllDrives=True,
    ).execute()


def imprimir_resumo(
    apagados, enviados, atualizados, ja_sync, ausentes_drive, ausentes_local, aplicar
):
    modo = "aplicado" if aplicar else "dry-run"
    print(f"\n=== resumo ({modo}) ===", flush=True)
    print(f"apagados: {apagados}", flush=True)
    print(f"enviados: {enviados}", flush=True)
    print(f"atualizados: {atualizados}", flush=True)
    print(f"já sincronizados: {ja_sync}", flush=True)
    print(f"ausentes no Drive (remoção): {ausentes_drive}", flush=True)
    print(f"ausentes no disco (envio): {ausentes_local}", flush=True)


def sincronizar_metadados(service, arquivos, pastas, aplicar):
    enviados = 0
    atualizados = 0
    ausentes_local = 0
    print("\n=== metadados ===", flush=True)
    for local, online in ARQUIVOS_METADADOS:
        if not local.exists() or local.stat().st_size < 1:
            ausentes_local += 1
            print(f"  ausente no disco {local}", flush=True)
            continue
        item = arquivos.get(online)
        if item is None:
            if aplicar:
                file_id = enviar(service, local, pastas[""], Path(online).name)
                arquivos[online] = {"id": file_id, "name": Path(online).name}
                print(f"  enviado {online}", flush=True)
            else:
                print(f"  [dry-run] enviar {local} -> {online}", flush=True)
            enviados += 1
            continue
        if aplicar:
            atualizar_conteudo(service, local, item["id"])
            print(f"  atualizado {online}", flush=True)
        else:
            print(f"  [dry-run] atualizar {local} -> {online}", flush=True)
        atualizados += 1
    return enviados, atualizados, ausentes_local


def main():
    parser = argparse.ArgumentParser(
        description="Aplica rastreio_substituicoes.csv no Google Drive"
    )
    parser.add_argument(
        "--pasta-id",
        default="",
        help="ID ou link da pasta raiz no Drive; se omitido, lê pasta-id do .env",
    )
    parser.add_argument("--rastreio", default=str(RASTREIO_PADRAO))
    parser.add_argument("--lote", help="restringe à coluna lote (ex: nao_exsicata)")
    parser.add_argument(
        "--aplicar",
        action="store_true",
        help="executa as alterações; sem esta flag só lista o que seria feito",
    )
    parser.add_argument("--credenciais", default=str(CREDENCIAIS_PADRAO))
    parser.add_argument("--token", default=str(TOKEN_PADRAO))
    args = parser.parse_args()

    pasta_id = extrair_pasta_id(args.pasta_id or pasta_id_do_env())
    if not pasta_id:
        raise SystemExit("informe --pasta-id ou defina pasta-id no .env")

    rastreio = Path(args.rastreio)
    if not rastreio.is_absolute():
        rastreio = (Path.cwd() / rastreio).resolve()
    if rastreio.exists():
        linhas = ler_rastreio(rastreio, args.lote)
    else:
        linhas = []
        print(f"aviso: rastreio não encontrado: {rastreio}", flush=True)
    if args.lote and not linhas:
        raise SystemExit(f"nenhuma linha com lote={args.lote}")

    remover = [r for r in linhas if r.get("acao") == "remover"]
    adicionar = [r for r in linhas if r.get("acao") == "adicionar"]
    outras = [r for r in linhas if r.get("acao") not in ("remover", "adicionar")]
    if outras:
        print(
            f"aviso: {len(outras)} linha(s) ignorada(s) (acao não é remover/adicionar)",
            flush=True,
        )

    print(f"pasta Drive: {pasta_id}", flush=True)
    print(f"rastreio: {rastreio}", flush=True)
    print(f"remover: {len(remover)} | adicionar: {len(adicionar)}", flush=True)
    if not args.aplicar:
        print("modo dry-run (use --aplicar para alterar o Drive)", flush=True)

    service = autenticar(Path(args.credenciais), Path(args.token))
    print("indexando árvore do Drive...", flush=True)
    pastas, arquivos = indexar_arvore(service, pasta_id)
    print(f"pastas: {len(pastas) - 1} | arquivos: {len(arquivos)}", flush=True)

    apagados = 0
    enviados = 0
    atualizados = 0
    ja_sync = 0
    ausentes_drive = 0
    ausentes_local = 0

    print("\n=== remoções ===", flush=True)
    vistos_remover = set()
    for row in remover:
        online = row.get("arquivo_online")
        if not online or online in vistos_remover:
            continue
        vistos_remover.add(online)
        item = arquivos.get(online)
        if item is None:
            ausentes_drive += 1
            print(f"  ausente {online}", flush=True)
            continue
        if args.aplicar:
            lixeira(service, item["id"])
            arquivos.pop(online, None)
            print(f"  lixeira {online}", flush=True)
        else:
            print(f"  [dry-run] lixeira {online}", flush=True)
        apagados += 1

    print("\n=== envios ===", flush=True)
    vistos_adicionar = set()
    for row in adicionar:
        online = row.get("arquivo_online")
        local_rel = row.get("arquivo_local")
        if not online or online in vistos_adicionar:
            continue
        vistos_adicionar.add(online)
        if online in arquivos:
            ja_sync += 1
            print(f"  já existe {online}", flush=True)
            continue
        local = caminho_local(local_rel)
        if not local.exists() or local.stat().st_size < 1:
            ausentes_local += 1
            print(f"  ausente no disco {local_rel}", flush=True)
            continue
        dest_dir = str(Path(online).parent).replace("\\", "/")
        if dest_dir == ".":
            dest_dir = ""
        pasta_dest = garantir_pasta(service, pastas, dest_dir, args.aplicar)
        if args.aplicar:
            file_id = enviar(service, local, pasta_dest, Path(online).name)
            arquivos[online] = {"id": file_id, "name": Path(online).name}
            print(f"  enviado {online}", flush=True)
        else:
            print(f"  [dry-run] enviar {local_rel} -> {online}", flush=True)
        enviados += 1

    env_meta, at_meta, aus_meta = sincronizar_metadados(
        service, arquivos, pastas, args.aplicar
    )
    enviados += env_meta
    atualizados += at_meta
    ausentes_local += aus_meta

    imprimir_resumo(
        apagados,
        enviados,
        atualizados,
        ja_sync,
        ausentes_drive,
        ausentes_local,
        args.aplicar,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
