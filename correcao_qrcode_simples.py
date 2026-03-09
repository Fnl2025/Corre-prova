import json
import re
from pathlib import Path
from datetime import datetime
import math

import cv2
import numpy as np

try:
    import qrcode
except ImportError:
    qrcode = None

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    from reportlab.pdfgen import canvas
except ImportError:
    A4 = None
    mm = None
    canvas = None


BASE_DIR = Path(__file__).resolve().parent
ARQUIVO_CONFIG = BASE_DIR / "prova_config.json"
EXT_IMAGEM = {".png", ".jpg", ".jpeg", ".bmp", ".webp"}
PASTA_RESULTADO = Path(r"C:\Users\wilke\Desktop\codigo-pyton\Gabarito-Prova\resultado")
LOGO_IEMA_CANDIDATOS = [
    PASTA_RESULTADO / "logoiema.png",
    BASE_DIR / "logoiema.png",
    BASE_DIR / "logomarca.png",
]


def normalizar_respostas(texto: str, alternativas_validas: str = "ABCDE") -> str:
    texto = (texto or "").upper().strip()
    return "".join(ch for ch in texto if ch in alternativas_validas)


def limpar_nome_arquivo(texto: str) -> str:
    base = (texto or "").strip().replace(" ", "_")
    base = re.sub(r"[^A-Za-z0-9_-]", "", base)
    return base or "SEM_NOME"


def carregar_config() -> dict:
    if not ARQUIVO_CONFIG.exists():
        raise FileNotFoundError(
            "Arquivo prova_config.json nao encontrado. Rode a opcao 1 primeiro."
        )
    data = json.loads(ARQUIVO_CONFIG.read_text(encoding="utf-8"))
    return validar_config(data)


def carregar_config_para_caminho(caminho: Path) -> dict:
    base = caminho if caminho.is_dir() else caminho.parent
    candidatos = [
        base / "prova_config.json",
        base.parent / "prova_config.json" if base.parent else None,
        base.parent.parent / "prova_config.json" if base.parent and base.parent.parent else None,
    ]
    for cfg_local in candidatos:
        if cfg_local and cfg_local.exists():
            data = json.loads(cfg_local.read_text(encoding="utf-8"))
            return validar_config(data)
    return carregar_config()


def ler_int_positivo(mensagem: str) -> int:
    valor_txt = input(mensagem).strip()
    valor = int(valor_txt)
    if valor <= 0:
        raise ValueError("Informe um numero inteiro maior que zero.")
    return valor


def ler_float_positivo(mensagem: str) -> float:
    valor_txt = input(mensagem).strip().replace(",", ".")
    valor = float(valor_txt)
    if valor <= 0:
        raise ValueError("Informe uma pontuacao maior que zero.")
    return valor


def salvar_config(config: dict) -> None:
    ARQUIVO_CONFIG.write_text(
        json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def validar_config(config: dict) -> dict:
    prova_id = str(config.get("prova_id") or "").strip()
    qtd_questoes = int(config.get("qtd_questoes") or 0)
    gabarito = normalizar_respostas(str(config.get("gabarito") or ""))
    ponto = float(config.get("ponto_por_questao") or 0)

    if not prova_id:
        raise ValueError("Configuracao invalida: campo 'prova_id' vazio.")
    if qtd_questoes <= 0:
        raise ValueError("Configuracao invalida: 'qtd_questoes' deve ser maior que zero.")
    if ponto <= 0:
        raise ValueError("Configuracao invalida: 'ponto_por_questao' deve ser maior que zero.")
    if len(gabarito) != qtd_questoes:
        raise ValueError(
            f"Configuracao invalida: gabarito com {len(gabarito)} respostas para {qtd_questoes} questoes."
        )

    return {
        "prova_id": prova_id,
        "qtd_questoes": qtd_questoes,
        "gabarito": gabarito,
        "ponto_por_questao": ponto,
    }


def resolver_logo_iema() -> Path | None:
    for p in LOGO_IEMA_CANDIDATOS:
        if p.exists():
            return p
    return None


def salvar_relatorio_pdf_resultado(resultados: list[dict], destino_pdf: Path) -> None:
    if canvas is None or A4 is None:
        raise RuntimeError("Pacote 'reportlab' nao instalado. Instale com: pip install reportlab")

    c = canvas.Canvas(str(destino_pdf), pagesize=A4)
    largura, altura = A4
    y = altura - 20 * mm

    logo = resolver_logo_iema()
    if logo:
        c.drawImage(str(logo), 15 * mm, y - 10 * mm, width=24 * mm, height=24 * mm, preserveAspectRatio=True, mask="auto")

    c.setFont("Helvetica-Bold", 20)
    c.drawCentredString(largura / 2, y, "RESULTADO")
    y -= 18 * mm

    c.setFont("Helvetica-Bold", 10)
    c.drawString(15 * mm, y, "Arquivo")
    c.drawString(70 * mm, y, "Aluno")
    c.drawString(110 * mm, y, "Turma/Serie")
    c.drawString(145 * mm, y, "Acertos")
    c.drawString(170 * mm, y, "Nota")
    y -= 5 * mm
    c.line(15 * mm, y, 195 * mm, y)
    y -= 4 * mm

    c.setFont("Helvetica", 9)
    for r in resultados:
        if y < 18 * mm:
            c.showPage()
            y = altura - 20 * mm
            c.setFont("Helvetica-Bold", 20)
            c.drawCentredString(largura / 2, y, "RESULTADO")
            y -= 14 * mm
            c.setFont("Helvetica", 9)

        arquivo = str(r.get("arquivo", ""))[:25]
        aluno = str(r.get("nome_aluno", ""))[:18]
        turma = str(r.get("turma", ""))[:8]
        serie = str(r.get("serie", ""))[:8]
        turma_serie = f"{turma}/{serie}".strip("/")
        status = r.get("status", "")
        if status == "ok":
            acertos = f"{r.get('acertos','')}/{r.get('qtd_questoes','')}"
            nota = f"{r.get('nota','')}/{r.get('nota_maxima','')}"
        else:
            acertos = "-"
            nota = "ERRO"

        c.drawString(15 * mm, y, arquivo)
        c.drawString(70 * mm, y, aluno)
        c.drawString(110 * mm, y, turma_serie)
        c.drawString(145 * mm, y, acertos)
        c.drawString(170 * mm, y, nota)
        y -= 5 * mm

    c.save()


def gerar_qr_oficial(config: dict) -> Path:
    if qrcode is None:
        raise RuntimeError(
            "Pacote 'qrcode' nao instalado. Instale com: pip install qrcode[pil]"
        )
    payload = {
        "tipo": "gabarito_oficial",
        "prova_id": config["prova_id"],
        "qtd_questoes": config["qtd_questoes"],
        "gabarito": config["gabarito"],
        "ponto_por_questao": config["ponto_por_questao"],
    }
    img = qrcode.make(json.dumps(payload, ensure_ascii=False))
    prova_id = limpar_nome_arquivo(str(config["prova_id"]))
    destino = Path(f"qr_oficial_{prova_id}.png")
    img.save(destino)
    return destino


def gerar_qr_aluno(config: dict, aluno_id: str, respostas: str = "") -> Path:
    if qrcode is None:
        raise RuntimeError(
            "Pacote 'qrcode' nao instalado. Instale com: pip install qrcode[pil]"
        )
    payload = {
        "tipo": "respostas_aluno",
        "aluno": aluno_id,
        "prova": config["prova_id"],
        "respostas": normalizar_respostas(respostas),
    }
    img = qrcode.make(json.dumps(payload, ensure_ascii=False))
    prova_id = limpar_nome_arquivo(str(config["prova_id"]))
    aluno = limpar_nome_arquivo(aluno_id)
    destino = Path(f"qr_aluno_{prova_id}_{aluno}.png")
    img.save(destino)
    return destino


def gerar_folha_aluno_pdf(
    config: dict,
    aluno_id: str,
    nome_aluno: str,
    qr_oficial_path: Path,
    respostas_aluno: str = "",
) -> Path:
    if canvas is None or A4 is None:
        raise RuntimeError(
            "Pacote 'reportlab' nao instalado. Instale com: pip install reportlab"
        )

    qtd = int(config["qtd_questoes"])
    prova_id = limpar_nome_arquivo(str(config["prova_id"]))
    aluno = limpar_nome_arquivo(aluno_id)
    nome = limpar_nome_arquivo(nome_aluno)
    respostas_aluno = normalizar_respostas(respostas_aluno)[:qtd]
    destino = Path(f"folha_respostas_{prova_id}_{aluno}_{nome}.pdf")
    if not qr_oficial_path.exists():
        raise FileNotFoundError(f"QR oficial nao encontrado: {qr_oficial_path}")

    c = canvas.Canvas(str(destino), pagesize=A4)
    largura, altura = A4

    c.setFont("Helvetica-Bold", 14)
    c.drawString(20 * mm, altura - 20 * mm, "Folha de Respostas")
    c.setFont("Helvetica", 10)
    c.drawString(20 * mm, altura - 28 * mm, f"Prova: {prova_id}")
    c.drawString(20 * mm, altura - 34 * mm, f"Aluno ID: {aluno_id}")
    c.drawString(20 * mm, altura - 40 * mm, f"Nome: {nome_aluno or '____________________________'}")

    c.drawImage(str(qr_oficial_path), largura - 55 * mm, altura - 50 * mm, width=32 * mm, height=32 * mm)
    c.setFont("Helvetica", 8)
    c.drawString(largura - 60 * mm, altura - 54 * mm, "QR oficial")

    c.setFont("Helvetica-Bold", 10)
    c.drawString(20 * mm, altura - 50 * mm, "Gabarito do aluno (em branco):")

    letras = "ABCDE"
    linhas_por_coluna = 24
    espaco_linha = 9 * mm
    x_base = [20 * mm, 105 * mm]
    y_inicio = altura - 62 * mm

    for i in range(qtd):
        coluna = (i // linhas_por_coluna) % 2
        bloco = i // (linhas_por_coluna * 2)
        linha = i % linhas_por_coluna

        x = x_base[coluna]
        y = y_inicio - (linha * espaco_linha) - (bloco * (linhas_por_coluna * espaco_linha + 10 * mm))
        if y < 20 * mm:
            c.showPage()
            c.setFont("Helvetica-Bold", 10)
            c.drawString(20 * mm, altura - 20 * mm, f"Folha de Respostas - continuacao ({aluno_id})")
            y_inicio = altura - 30 * mm
            y = y_inicio

        c.setFont("Helvetica", 9)
        c.drawString(x, y, f"{i + 1:02d}")
        resposta_marcada = respostas_aluno[i] if i < len(respostas_aluno) else ""
        for j, letra in enumerate(letras):
            cx = x + 12 * mm + (j * 10 * mm)
            cy = y + 1.7 * mm
            c.circle(cx, cy, 2.8 * mm)
            c.drawString(cx + 3.6 * mm, y, letra)
            if resposta_marcada == letra:
                c.setFillColorRGB(0.1, 0.2, 0.9)
                c.circle(cx, cy, 1.7 * mm, stroke=0, fill=1)
                c.setFillColorRGB(0, 0, 0)

    c.save()
    return destino


def extrair_dados_qr(payload: str) -> dict:
    payload = (payload or "").strip()
    if not payload:
        raise ValueError("QR vazio.")

    # JSON esperado para aluno:
    # {"tipo":"respostas_aluno","aluno":"123","prova":"MAT1","respostas":"ABCDE"}
    if payload.startswith("{") and payload.endswith("}"):
        data = json.loads(payload)
        tipo = str(data.get("tipo") or "").strip().lower()
        if tipo == "gabarito_oficial":
            raise ValueError(
                "Este QR e o oficial da prova. Para corrigir, use o QR do aluno (com respostas)."
            )
        respostas = normalizar_respostas(str(data.get("respostas") or ""))
        if not respostas:
            raise ValueError("QR do aluno sem respostas.")
        return {
            "aluno_id": str(data.get("aluno") or data.get("aluno_id") or "").strip(),
            "prova_id": str(data.get("prova") or data.get("prova_id") or "").strip(),
            "respostas": respostas,
        }

    # Texto: ALUNO=123;PROVA=MAT1;RESPOSTAS=ABCDE
    pares = re.findall(r"([A-Za-z_]+)\s*=\s*([^;|]+)", payload)
    if pares:
        d = {k.lower().strip(): v.strip() for k, v in pares}
        respostas = normalizar_respostas(d.get("respostas") or "")
        if not respostas:
            raise ValueError("QR do aluno sem respostas.")
        return {
            "aluno_id": d.get("aluno") or d.get("aluno_id") or "",
            "prova_id": d.get("prova") or d.get("prova_id") or "",
            "respostas": respostas,
        }

    # Fallback: 123|MAT1|ABCDE
    partes = [x.strip() for x in payload.split("|")]
    if len(partes) >= 3:
        respostas = normalizar_respostas(partes[2])
        if not respostas:
            raise ValueError("QR do aluno sem respostas.")
        return {
            "aluno_id": partes[0],
            "prova_id": partes[1],
            "respostas": respostas,
        }

    raise ValueError("Formato de QR nao reconhecido.")


def ler_qr_de_imagem(caminho_imagem: Path) -> str:
    img = cv2.imread(str(caminho_imagem))
    if img is None:
        raise FileNotFoundError(f"Nao foi possivel abrir: {caminho_imagem}")

    detector = cv2.QRCodeDetector()

    # Tentativa 1: imagem original
    payload, _, _ = detector.detectAndDecode(img)
    payload = (payload or "").strip()
    if payload:
        return payload

    # Tentativa 2: escala de cinza
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    payload, _, _ = detector.detectAndDecode(gray)
    payload = (payload or "").strip()
    if payload:
        return payload

    # Tentativa 3: binarizacao adaptativa (ajuda em screenshot/foto lavada)
    bw = cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 41, 5
    )
    payload, _, _ = detector.detectAndDecode(bw)
    payload = (payload or "").strip()
    if payload:
        return payload

    # Tentativa 4: ampliar imagem
    up = cv2.resize(gray, None, fx=2.0, fy=2.0, interpolation=cv2.INTER_CUBIC)
    payload, _, _ = detector.detectAndDecode(up)
    payload = (payload or "").strip()
    if payload:
        return payload

    raise ValueError("Nao foi encontrado QR na imagem.")


def listar_imagens(caminho: Path) -> list[Path]:
    ignorar_prefixos = ("qr_", "gabarito_", "resultado_correcao_", "logoiema")

    def valido(p: Path) -> bool:
        if not p.is_file() or p.suffix.lower() not in EXT_IMAGEM:
            return False
        nome = p.name.lower()
        return not nome.startswith(ignorar_prefixos)

    if caminho.is_file():
        return [caminho] if valido(caminho) else []
    if caminho.is_dir():
        return sorted([p for p in caminho.rglob("*") if valido(p)])
    return []


def config_por_qr_oficial(payload: str) -> dict | None:
    texto = (payload or "").strip()
    if not (texto.startswith("{") and texto.endswith("}")):
        return None
    data = json.loads(texto)
    tipo = str(data.get("tipo") or "").strip().lower()
    if tipo != "gabarito_oficial":
        return None
    data_cfg = {
        "prova_id": str(data.get("prova_id") or "").strip(),
        "qtd_questoes": int(data.get("qtd_questoes") or 0),
        "gabarito": normalizar_respostas(str(data.get("gabarito") or "")),
        "ponto_por_questao": float(data.get("ponto_por_questao") or 0),
    }
    try:
        return validar_config(data_cfg)
    except Exception:
        return None


def inferir_aluno_id_por_nome(caminho: Path) -> str:
    m = re.search(r"folha_respostas_[^_]+_([^_]+)", caminho.stem, re.IGNORECASE)
    if m:
        return m.group(1)
    return "NAO_INFORMADO"


def extrair_respostas_marcadas_da_folha(caminho_imagem: Path, qtd_questoes: int) -> str:
    img = cv2.imread(str(caminho_imagem))
    if img is None:
        raise FileNotFoundError(f"Nao foi possivel abrir: {caminho_imagem}")

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    respostas_circulos = extrair_respostas_por_circulos(gray, qtd_questoes)
    if respostas_circulos and set(respostas_circulos) != {"-"}:
        return respostas_circulos

    # Tenta localizar a pagina branca em screenshots/fotos.
    _, th = cv2.threshold(gray, 235, 255, cv2.THRESH_BINARY)
    contours, _ = cv2.findContours(th, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    page = gray
    if contours:
        c = max(contours, key=cv2.contourArea)
        x, y, w, h = cv2.boundingRect(c)
        if w > 200 and h > 200:
            page = gray[y : y + h, x : x + w]

    h_img, w_img = page.shape
    if h_img <= 0 or w_img <= 0:
        raise ValueError("Nao foi possivel detectar a area da folha.")

    # Coordenadas da folha gerada (A4 em points no ReportLab).
    a4_w_pt = 595.2756
    a4_h_pt = 841.8898
    sx = w_img / a4_w_pt
    sy = h_img / a4_h_pt

    mm_pt = 2.83464567
    letras = "ABCDE"
    linhas_por_coluna = 24
    espaco_linha = 9 * mm_pt
    x_base = [20 * mm_pt, 105 * mm_pt]
    y_inicio = a4_h_pt - 62 * mm_pt

    respostas = []
    for i in range(qtd_questoes):
        coluna = (i // linhas_por_coluna) % 2
        bloco = i // (linhas_por_coluna * 2)
        linha = i % linhas_por_coluna
        x = x_base[coluna]
        y = y_inicio - (linha * espaco_linha) - (bloco * (linhas_por_coluna * espaco_linha + 10 * mm_pt))

        intensidades = []
        for j in range(5):
            cx_pt = x + 12 * mm_pt + (j * 10 * mm_pt)
            cy_pt = y + 1.7 * mm_pt

            cx = int(cx_pt * sx)
            cy = int(cy_pt * sy)
            r = max(3, int(1.6 * mm_pt * min(sx, sy)))

            y0 = max(0, cy - r)
            y1 = min(h_img, cy + r + 1)
            x0 = max(0, cx - r)
            x1 = min(w_img, cx + r + 1)
            roi = page[y0:y1, x0:x1]
            if roi.size == 0:
                intensidades.append(255.0)
                continue

            yy, xx = np.ogrid[: roi.shape[0], : roi.shape[1]]
            mask = (xx - (cx - x0)) ** 2 + (yy - (cy - y0)) ** 2 <= r * r
            vals = roi[mask]
            media = float(vals.mean()) if vals.size else 255.0
            intensidades.append(media)

        idx_min = int(np.argmin(intensidades))
        min_val = intensidades[idx_min]
        sorted_vals = sorted(intensidades)
        segundo = sorted_vals[1] if len(sorted_vals) > 1 else 255.0

        # Marca como preenchido apenas se houver contraste suficiente.
        if min_val < 170 and (segundo - min_val) > 8:
            respostas.append(letras[idx_min])
        else:
            respostas.append("-")

    return "".join(respostas)


def extrair_respostas_por_circulos(gray: np.ndarray, qtd_questoes: int) -> str | None:
    h, w = gray.shape[:2]
    min_dim = min(h, w)
    # Threshold fixo funciona melhor para bolhas pretas da folha gerada.
    th = cv2.threshold(gray, 140, 255, cv2.THRESH_BINARY_INV)[1]
    contours, _ = cv2.findContours(th, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    candidatos: list[tuple[int, int, int, int]] = []
    for c in contours:
        area = cv2.contourArea(c)
        if area < 80:
            continue
        x, y, ww, hh = cv2.boundingRect(c)
        if not (int(min_dim * 0.03) <= ww <= int(min_dim * 0.10)):
            continue
        if not (int(min_dim * 0.03) <= hh <= int(min_dim * 0.10)):
            continue
        if x < int(w * 0.05) or x > int(w * 0.60):
            continue
        if y < int(h * 0.30) or y > int(h * 0.98):
            continue
        ratio = ww / max(hh, 1)
        if ratio < 0.75 or ratio > 1.3:
            continue
        peri = cv2.arcLength(c, True)
        if peri <= 0:
            continue
        circularidade = 4.0 * math.pi * area / (peri * peri)
        if circularidade < 0.55:
            continue
        candidatos.append((x, y, ww, hh))

    if len(candidatos) < 10:
        return None

    candidatos.sort(key=lambda t: t[1])
    linhas: list[list[tuple[int, int, int, int]]] = []
    tol_y = max(10, int(min_dim * 0.02))
    for bolha in candidatos:
        if not linhas:
            linhas.append([bolha])
            continue
        y_med = int(np.median([p[1] for p in linhas[-1]]))
        if abs(bolha[1] - y_med) <= tol_y:
            linhas[-1].append(bolha)
        else:
            linhas.append([bolha])

    linhas_validas: list[list[tuple[int, int, int, int]]] = []
    for linha in linhas:
        linha = sorted(linha, key=lambda t: t[0])
        if len(linha) >= 5:
            linhas_validas.append(linha[:5])
    if len(linhas_validas) < min(3, qtd_questoes):
        return None

    letras = "ABCDE"
    respostas: list[str] = []
    for i in range(min(qtd_questoes, len(linhas_validas))):
        linha = linhas_validas[i]
        intens = []
        for x, y, ww, hh in linha:
            cx = x + ww // 2
            cy = y + hh // 2
            rr = max(4, int(min(ww, hh) * 0.30))

            y0 = max(0, cy - rr)
            y1 = min(h, cy + rr + 1)
            x0 = max(0, cx - rr)
            x1 = min(w, cx + rr + 1)
            roi = gray[y0:y1, x0:x1]
            if roi.size == 0:
                intens.append(255.0)
                continue
            yy, xx = np.ogrid[: roi.shape[0], : roi.shape[1]]
            mask = (xx - (cx - x0)) ** 2 + (yy - (cy - y0)) ** 2 <= rr * rr
            vals = roi[mask]
            intens.append(float(vals.mean()) if vals.size else 255.0)

        idx_min = int(np.argmin(intens))
        minimo = intens[idx_min]
        media = float(np.mean(intens))
        segundo = sorted(intens)[1] if len(intens) > 1 else 255.0
        if minimo < 220 and (media - minimo) > 18 and (segundo - minimo) > 12:
            respostas.append(letras[idx_min])
        else:
            respostas.append("-")

    if len(respostas) < qtd_questoes:
        respostas.extend("-" for _ in range(qtd_questoes - len(respostas)))
    return "".join(respostas[:qtd_questoes])


def ler_qr_da_camera(indice_camera: int = 0) -> str:
    cap = cv2.VideoCapture(indice_camera)
    if not cap.isOpened():
        raise RuntimeError(
            f"Nao foi possivel abrir camera indice {indice_camera}. "
            "Se for celular (DroidCam/IP Webcam), confirme o indice."
        )

    detector = cv2.QRCodeDetector()
    print("Aponte para o QR do aluno. Pressione Q para cancelar.")
    while True:
        ok, frame = cap.read()
        if not ok:
            continue

        payload, points, _ = detector.detectAndDecode(frame)
        if points is not None and len(points) > 0:
            pts = points[0].astype(int)
            for i in range(4):
                p1 = tuple(pts[i])
                p2 = tuple(pts[(i + 1) % 4])
                cv2.line(frame, p1, p2, (0, 255, 0), 2)

        cv2.imshow("Leitura QR - pressione Q para sair", frame)
        tecla = cv2.waitKey(1) & 0xFF

        payload = (payload or "").strip()
        if payload:
            cap.release()
            cv2.destroyAllWindows()
            return payload
        if tecla == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()
    raise RuntimeError("Leitura cancelada.")


def corrigir(config: dict, dados_aluno: dict) -> dict:
    config = validar_config(config)
    gabarito = normalizar_respostas(config["gabarito"])
    respostas_raw = str(dados_aluno["respostas"] or "").upper().strip()
    qtd = int(config["qtd_questoes"])
    ponto = float(config["ponto_por_questao"])
    prova_id_config = str(config["prova_id"]).strip()
    prova_id_aluno = str(dados_aluno.get("prova_id") or "").strip()

    if prova_id_aluno and prova_id_aluno != prova_id_config:
        raise ValueError(
            f"Prova divergente: QR do aluno={prova_id_aluno} e sistema={prova_id_config}."
        )

    gabarito = gabarito[:qtd]
    respostas_raw = respostas_raw[:qtd]

    acertos = 0
    for i in range(len(gabarito)):
        resp = respostas_raw[i] if i < len(respostas_raw) else ""
        if resp == gabarito[i]:
            acertos += 1

    nota = round(acertos * ponto, 2)
    nota_maxima = round(qtd * ponto, 2)

    return {
        "aluno_id": dados_aluno["aluno_id"] or "NAO_INFORMADO",
        "prova_id": dados_aluno["prova_id"] or "NAO_INFORMADO",
        "acertos": acertos,
        "qtd_questoes": qtd,
        "nota": nota,
        "nota_maxima": nota_maxima,
    }


def opcao_configurar_prova() -> None:
    print("\n=== Configurar prova ===")
    try:
        prova_id = input("ID da prova (ex: MAT1): ").strip() or "PROVA"
        qtd_questoes = ler_int_positivo("Quantidade de questoes: ")
        gabarito = normalizar_respostas(
            input("Alternativas corretas em sequencia (ex: ABCDEABCDE): ")
        )
        ponto = ler_float_positivo("Pontuacao por questao certa (ex: 0.5 ou 1): ")

        config = validar_config(
            {
                "prova_id": prova_id,
                "qtd_questoes": qtd_questoes,
                "gabarito": gabarito[:qtd_questoes],
                "ponto_por_questao": ponto,
            }
        )
        salvar_config(config)
        caminho_qr = gerar_qr_oficial(config)

        print(f"\nConfiguracao salva em: {ARQUIVO_CONFIG}")
        print(f"QR oficial gerado: {caminho_qr}")
        print("Use esse QR no cabecalho da prova (referencia da avaliacao).")
    except Exception as exc:
        print(f"Erro na opcao 1: {exc}")


def opcao_corrigir_camera() -> None:
    print("\n=== Correcao por camera ===")
    try:
        config = carregar_config()
        indice = input("Indice da camera [0]: ").strip()
        indice_camera = int(indice) if indice else 0

        payload = ler_qr_da_camera(indice_camera=indice_camera)
        dados = extrair_dados_qr(payload)
        resultado = corrigir(config, dados)

        print("\n=== Resultado ===")
        print(f"Aluno: {resultado['aluno_id']}")
        print(f"Prova: {resultado['prova_id']}")
        print(f"Acertos: {resultado['acertos']}/{resultado['qtd_questoes']}")
        print(f"Nota: {resultado['nota']} / {resultado['nota_maxima']}")
    except Exception as exc:
        print(f"Erro na opcao 2: {exc}")
        print("Dica: use QR do aluno com respostas e camera ativa.")


def opcao_corrigir_imagem() -> None:
    print("\n=== Correcao por imagem (pasta resultado) ===")
    try:
        PASTA_RESULTADO.mkdir(parents=True, exist_ok=True)
        caminho = PASTA_RESULTADO
        imagens = listar_imagens(caminho)
        if not imagens:
            raise ValueError(
                f"Nenhuma imagem encontrada em: {caminho}\n"
                "Coloque as imagens da prova nessa pasta e tente novamente."
            )
        config_base = carregar_config_para_caminho(caminho)

        processadas = 0
        erros = 0
        resultados = []
        for arq in imagens:
            try:
                print(f"\n--- Dados do aluno para: {arq.name} ---")
                nome_aluno = input("Nome do aluno: ").strip()
                turma = input("Turma: ").strip()
                serie = input("Serie: ").strip()

                payload = ""
                try:
                    payload = ler_qr_de_imagem(arq)
                except Exception:
                    payload = ""

                # Fluxo A: QR do aluno contem respostas.
                if payload:
                    try:
                        config = config_base
                        dados = extrair_dados_qr(payload)
                        resultado = corrigir(config, dados)
                        print(f"\n[{arq.name}]")
                        print(f"Aluno: {resultado['aluno_id']}")
                        print(f"Prova: {resultado['prova_id']}")
                        print(f"Acertos: {resultado['acertos']}/{resultado['qtd_questoes']}")
                        print(f"Nota: {resultado['nota']} / {resultado['nota_maxima']}")
                        processadas += 1
                        resultados.append(
                            {
                                "arquivo": arq.name,
                                "status": "ok",
                                "aluno_id": resultado["aluno_id"],
                                "nome_aluno": nome_aluno,
                                "turma": turma,
                                "serie": serie,
                                "prova_id": resultado["prova_id"],
                                "acertos": resultado["acertos"],
                                "qtd_questoes": resultado["qtd_questoes"],
                                "nota": resultado["nota"],
                                "nota_maxima": resultado["nota_maxima"],
                                "respostas_lidas": dados.get("respostas", ""),
                                "erro": "",
                            }
                        )
                        continue
                    except Exception:
                        pass

                # Evita tentar OMR em imagem que e apenas QR.
                nome_l = arq.name.lower()
                if nome_l.startswith("qr_") or nome_l.startswith("gabarito_"):
                    raise ValueError("Imagem contem apenas QR; use foto/scan da folha de respostas.")

                # Fluxo B: QR oficial + leitura das bolhas.
                config_oficial = config_por_qr_oficial(payload) if payload else None
                if not config_oficial:
                    # Fallback sem QR: usa config local, util para pasta com imagens sem QR legivel.
                    config_oficial = config_base

                if int(config_oficial["qtd_questoes"]) <= 0 or not normalizar_respostas(str(config_oficial["gabarito"])):
                    raise ValueError("Configuracao invalida (faltando gabarito/qtd_questoes).")

                respostas_marcadas = extrair_respostas_marcadas_da_folha(
                    arq, int(config_oficial["qtd_questoes"])
                )
                if not respostas_marcadas or set(respostas_marcadas) <= {"-"}:
                    raise ValueError("Nao foi possivel ler as marcacoes da folha.")
                dados = {
                    "aluno_id": inferir_aluno_id_por_nome(arq),
                    "prova_id": str(config_oficial["prova_id"]),
                    "respostas": respostas_marcadas,
                }
                resultado = corrigir(config_oficial, dados)
                print(f"\n[{arq.name}]")
                print(f"Aluno: {resultado['aluno_id']}")
                print(f"Prova: {resultado['prova_id']}")
                print(f"Respostas lidas: {respostas_marcadas}")
                print(f"Acertos: {resultado['acertos']}/{resultado['qtd_questoes']}")
                print(f"Nota: {resultado['nota']} / {resultado['nota_maxima']}")
                processadas += 1
                resultados.append(
                    {
                        "arquivo": arq.name,
                        "status": "ok",
                        "aluno_id": resultado["aluno_id"],
                        "nome_aluno": nome_aluno,
                        "turma": turma,
                        "serie": serie,
                        "prova_id": resultado["prova_id"],
                        "acertos": resultado["acertos"],
                        "qtd_questoes": resultado["qtd_questoes"],
                        "nota": resultado["nota"],
                        "nota_maxima": resultado["nota_maxima"],
                        "respostas_lidas": respostas_marcadas,
                        "erro": "",
                    }
                )
            except Exception as exc_arq:
                erros += 1
                print(f"\n[{arq.name}] ERRO: {exc_arq}")
                resultados.append(
                    {
                        "arquivo": arq.name,
                        "status": "erro",
                        "aluno_id": "",
                        "nome_aluno": nome_aluno,
                        "turma": turma,
                        "serie": serie,
                        "prova_id": "",
                        "acertos": "",
                        "qtd_questoes": "",
                        "nota": "",
                        "nota_maxima": "",
                        "respostas_lidas": "",
                        "erro": str(exc_arq),
                    }
                )

        print(f"\nResumo: processadas={processadas} | erros={erros} | total={len(imagens)}")
        if resultados:
            pdf_saida = caminho / f"resultado_correcao_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            try:
                salvar_relatorio_pdf_resultado(resultados, pdf_saida)
                print(f"Relatorio PDF salvo em: {pdf_saida}")
            except Exception as exc_pdf:
                print(f"Aviso: nao foi possivel salvar PDF de resultado: {exc_pdf}")
    except Exception as exc:
        print(f"Erro na opcao 3: {exc}")
        print("Dica: use a pasta 'resultado' para colocar as imagens a corrigir.")


def opcao_gerar_folha_aluno() -> None:
    print("\n=== Gerar gabarito + QR oficial ===")
    try:
        config = carregar_config()
        aluno_id = input("Aluno ID (obrigatorio): ").strip()
        if not aluno_id:
            raise ValueError("Aluno ID e obrigatorio.")
        nome_aluno = input("Nome do aluno (opcional): ").strip()

        qr_oficial = gerar_qr_oficial(config)
        pdf_folha = gerar_folha_aluno_pdf(
            config,
            aluno_id=aluno_id,
            nome_aluno=nome_aluno,
            qr_oficial_path=qr_oficial,
            respostas_aluno="",
        )

        print("\nArquivos gerados:")
        print(f"- QR oficial: {qr_oficial}")
        print(f"- Folha PDF: {pdf_folha}")
        print("Menu 4 apenas gera os arquivos. A correcao fica no menu 2 ou 3.")
    except Exception as exc:
        print(f"Erro na opcao 4: {exc}")


def main() -> None:
    while True:
        print("\nSistema simples de correcao por QR (estilo Gradepen)")
        print("1 - Configurar prova + gerar QR oficial")
        print("2 - Corrigir aluno lendo QR pela camera")
        print("3 - Corrigir aluno por foto/imagem")
        print("4 - Gerar gabarito + QR oficial")
        print("5 - Sair")
        op = input("Escolha: ").strip()

        if op == "1":
            opcao_configurar_prova()
        elif op == "2":
            opcao_corrigir_camera()
        elif op == "3":
            opcao_corrigir_imagem()
        elif op == "4":
            opcao_gerar_folha_aluno()
        elif op == "5":
            print("Encerrando sistema.")
            break
        else:
            print("Opcao invalida.")


if __name__ == "__main__":
    main()
