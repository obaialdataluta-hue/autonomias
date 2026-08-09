#!/usr/bin/env python3
"""
Cria e semeia a planilha do projeto ESTRANGEIRIZAÇÃO.

Cria um Google Sheet novo (aba de resultados + RAW_TEXT + ESTADO + DESTINATARIOS
+ LISTAS + CODEBOOK), semeia os vocabulários controlados (LISTAS) e o glossário
(CODEBOOK), e compartilha a planilha com um e-mail (default: freddymu@gmail.com).

Uso:
    python seed_estrangeirizacao.py [--share you@example.com] [--title "..."]
    python seed_estrangeirizacao.py --spreadsheet-id <ID>   # só semeia (planilha já existe)

Imprime o SPREADSHEET_ID ao final — use-o em OBAIAL_SPREADSHEET_ID / template.yaml.
Requer a Drive API habilitada no projeto GCP para criar/compartilhar; se falhar,
o script instrui a criar a planilha manualmente e compartilhar com a service account.
"""
import argparse
import sys

from googleapiclient.discovery import build
from google.oauth2 import service_account

import obAIAL_pipeline_merged as P
import profiles

TABS_HEADERS = {
    profiles.PROFILE_ESTRANGEIRIZACAO.sheet_name_default: profiles.ESTRA_COLUNAS,
    "RAW_TEXT": profiles.ESTRA_RAW_TEXT_HEADERS,
    "ESTADO": ["CHAVE", "VALOR"],
    "DESTINATARIOS": ["EMAIL", "NOME", "ATIVO"],
}


def _creds(scopes):
    sa = P.load_secret_json(P.SHEETS_SA_SECRET_ID)
    return service_account.Credentials.from_service_account_info(sa, scopes=scopes), sa


def _listas_rows():
    names = list(profiles.ESTRA_LISTAS.keys())
    maxlen = max(len(v) for v in profiles.ESTRA_LISTAS.values())
    rows = [names]
    for i in range(maxlen):
        rows.append([
            profiles.ESTRA_LISTAS[n][i] if i < len(profiles.ESTRA_LISTAS[n]) else ""
            for n in names
        ])
    return rows


def _codebook_rows():
    return [["TERMO", "DEFINICAO"]] + [[k, v] for k, v in profiles.ESTRA_GLOSSARIO.items()]


def seed(sheets, spreadsheet_id):
    """Escreve headers + LISTAS + CODEBOOK nas abas (idempotente)."""
    data = []
    for tab, header in TABS_HEADERS.items():
        data.append({"range": f"{tab}!A1", "values": [header]})
    data.append({"range": "LISTAS!A1", "values": _listas_rows()})
    data.append({"range": "CODEBOOK!A1", "values": _codebook_rows()})
    sheets.spreadsheets().values().batchUpdate(
        spreadsheetId=spreadsheet_id,
        body={"valueInputOption": "RAW", "data": data},
    ).execute()
    print(f"  Semeado: {list(TABS_HEADERS.keys())} + LISTAS + CODEBOOK")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--share", default="freddymu@gmail.com")
    ap.add_argument("--title", default="DATALUTA — Estrangeirização (ObAIAL)")
    ap.add_argument("--spreadsheet-id", default=None,
                    help="Se informado, apenas semeia uma planilha já existente.")
    args = ap.parse_args()

    all_tabs = list(TABS_HEADERS.keys()) + ["LISTAS", "CODEBOOK"]

    if args.spreadsheet_id:
        creds, _ = _creds(["https://www.googleapis.com/auth/spreadsheets"])
        sheets = build("sheets", "v4", credentials=creds)
        # garante que as abas existem
        meta = sheets.spreadsheets().get(spreadsheetId=args.spreadsheet_id).execute()
        existentes = {s["properties"]["title"] for s in meta.get("sheets", [])}
        reqs = [{"addSheet": {"properties": {"title": t}}}
                for t in all_tabs if t not in existentes]
        if reqs:
            sheets.spreadsheets().batchUpdate(
                spreadsheetId=args.spreadsheet_id, body={"requests": reqs}
            ).execute()
        seed(sheets, args.spreadsheet_id)
        print(f"\nSPREADSHEET_ID={args.spreadsheet_id}")
        return

    # cria a planilha (precisa de escopo drive p/ compartilhar depois)
    creds, sa = _creds([
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ])
    sheets = build("sheets", "v4", credentials=creds)
    body = {
        "properties": {"title": args.title},
        "sheets": [{"properties": {"title": t}} for t in all_tabs],
    }
    ss = sheets.spreadsheets().create(body=body, fields="spreadsheetId").execute()
    sid = ss["spreadsheetId"]
    print(f"Planilha criada: {sid}")
    seed(sheets, sid)

    # compartilha com o usuário
    try:
        drive = build("drive", "v3", credentials=creds)
        drive.permissions().create(
            fileId=sid, sendNotificationEmail=True,
            body={"type": "user", "role": "writer", "emailAddress": args.share},
        ).execute()
        print(f"  Compartilhado (writer) com {args.share}")
    except Exception as e:  # noqa: BLE001
        print(f"  ⚠ Não consegui compartilhar via Drive API ({e}).")
        print(f"    A planilha pertence à service account: {sa.get('client_email')}")
        print(f"    Compartilhe manualmente OU rode com --share depois de habilitar a Drive API.")

    print(f"\n✅ SPREADSHEET_ID={sid}")
    print("   Configure OBAIAL_SPREADSHEET_ID (template.yaml / env) com esse ID.")


if __name__ == "__main__":
    sys.exit(main())
