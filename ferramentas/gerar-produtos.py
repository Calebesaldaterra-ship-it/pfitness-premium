#!/usr/bin/env python3
"""
Gera as paginas por produto de premium.pfitness.com.br.

Fonte unica de verdade: o array PRODUTOS_BASE dentro do index.html.
Nada e digitado duas vezes — rodou o script, as 42 paginas saem iguais ao catalogo.

Para cada produto escreve:
  p/<ID>/index.html   pagina com Open Graph (e ela que faz o WhatsApp mostrar o card)
  p/img/<ID>.jpg      foto hospedada no nosso dominio (a CDN do fornecedor bloqueia robo)
  p/og/<ID>.jpg       card 1200x630 com foto + nome + preco + codigo

Uso:  python3 ferramentas/gerar-produtos.py
"""
import json, os, re, sys, urllib.request, io

RAIZ  = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE  = "https://premium.pfitness.com.br"
ZAP   = "5534991298865"
UA    = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/126 Safari/537.36"
INK, PAPER, GOLD, MUTED = "#0e0d0c", "#f6f2ec", "#c9a227", "#b3aa9d"

def produtos():
    s = open(os.path.join(RAIZ, "index.html"), encoding="utf-8").read()
    tag = "const PRODUTOS_BASE = "
    i = s.index(tag); j = s.index("\n];", i)
    return json.loads(s[i+len(tag):j+2])

def brl(v):  return ("R$ %.2f" % v).replace(".", ",")
def sku(p):  return p.get("sku") or p["id"]

def baixar(url, destino):
    if os.path.exists(destino) and os.path.getsize(destino) > 2000:
        return True
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        dados = urllib.request.urlopen(req, timeout=30).read()
        from PIL import Image
        im = Image.open(io.BytesIO(dados)).convert("RGB")
        im.thumbnail((1200, 1200), Image.LANCZOS)
        im.save(destino, "JPEG", quality=86, optimize=True)
        return True
    except Exception as e:
        print("   ! foto falhou (%s): %s" % (os.path.basename(destino), e))
        return False

def fonte(nome, tam, **eixos):
    from PIL import ImageFont
    for caminho in (os.path.join(RAIZ, "ferramentas", "fontes", nome + ".ttf"),):
        if os.path.exists(caminho):
            f = ImageFont.truetype(caminho, tam)
            try:
                vals = [eixos.get(a["name"].decode().lower().replace(" ", ""), a["default"])
                        for a in f.get_variation_axes()]
                f.set_variation_by_axes(vals)
            except Exception:
                pass
            return f
    return ImageFont.load_default()

def card_og(p, foto, destino):
    """1200x630: foto a esquerda, dados a direita. E a miniatura que aparece no chat."""
    from PIL import Image, ImageDraw
    L, A, COL = 1200, 630, 630
    c = Image.new("RGB", (L, A), INK)
    try:
        im = Image.open(foto).convert("RGB")
        r = max(COL/im.width, A/im.height)
        im = im.resize((round(im.width*r), round(im.height*r)), Image.LANCZOS)
        x = (im.width-COL)//2
        y = max(0, min(im.height-A, round(im.height*0.30 - A/2)))
        c.paste(im.crop((x, y, x+COL, y+A)), (0, 0))
    except Exception:
        pass
    d = ImageDraw.Draw(c)
    px = COL + 54

    def espacado(xy, txt, f, cor, esp=4):
        x, y = xy
        for ch in txt:
            d.text((x, y), ch, font=f, fill=cor); x += d.textlength(ch, font=f) + esp

    espacado((px, 92), (p.get("c") or "").upper(), fonte("Inter", 20, weight=600), GOLD, 4)

    f_nome = fonte("Fraunces", 44, weight=500, opticalsize=144)
    linha, linhas = "", []
    for palavra in p["n"].split():
        teste = (linha + " " + palavra).strip()
        if d.textlength(teste, font=f_nome) > (L - px - 54) and linha:
            linhas.append(linha); linha = palavra
        else:
            linha = teste
    linhas.append(linha)
    yy = 138
    for ln in linhas[:3]:
        d.text((px, yy), ln, font=f_nome, fill=PAPER); yy += 56

    d.text((px, yy + 26), brl(p["p"]), font=fonte("Fraunces", 86, weight=700, opticalsize=144), fill=GOLD)
    d.text((px, yy + 132), "ou 3x de %s sem juros" % brl(p["p"]/3),
           font=fonte("Inter", 21, weight=400), fill=MUTED)
    espacado((px, yy + 176), "CÓDIGO " + sku(p), fonte("Inter", 20, weight=600), PAPER, 4)
    d.line((px, A-96, px+300, A-96), fill=GOLD, width=2)
    espacado((px, A-72), "PONTO FITNESS PREMIUM", fonte("Inter", 19, weight=600), PAPER, 5)
    c.save(destino, "JPEG", quality=88, optimize=True)

def resumo(p, limite=190):
    """Descricao curta e limpa para o preview do WhatsApp."""
    t = re.sub(r"\s+", " ", (p.get("d") or "")).strip()
    t = re.sub(r"[🔥✨💫💖🧺🧼✅•]", "", t).strip(" -·")
    return (t[:limite].rsplit(" ", 1)[0] + "…") if len(t) > limite else t

def pagina(p):
    img_og = "%s/p/og/%s.jpg" % (SITE, p["id"])
    url    = "%s/p/%s/" % (SITE, p["id"])
    titulo = "%s — %s" % (p["n"], brl(p["p"]))
    desc   = resumo(p)
    msg    = ("Olá! 👋 Gostei deste produto e gostaria de saber mais informações.\n\n"
              "🛍️ Produto: %s\n💰 Valor: %s\n🔖 Código: %s\n\n📸 %s\n\n"
              "Gostaria de saber as cores e tamanhos disponíveis." % (p["n"], brl(p["p"]), sku(p), url))
    dados = {"id": p["id"], "sku": sku(p), "nome": p["n"], "preco": p["p"], "precoTxt": brl(p["p"]),
             "categoria": p.get("c", ""), "url": url,
             "imagem": "%s/p/img/%s.jpg" % (SITE, p["id"]), "og": img_og, "zap": ZAP}
    troca = {
        "__ID__": p["id"], "__TITULO__": html_escape(titulo), "__DESC__": html_escape(desc),
        "__URL__": url, "__OG__": img_og, "__NOME__": html_escape(p["n"]),
        "__PRECO__": brl(p["p"]), "__PARC__": brl(p["p"]/3), "__SKU__": sku(p),
        "__CAT__": html_escape(p.get("c", "")), "__PRECO_NUM__": "%.2f" % p["p"],
        "__IMG__": "%s/p/img/%s.jpg" % (SITE, p["id"]),
        "__DESCRICAO__": html_escape(p.get("d", "")),
        "__MSG_JSON__": json.dumps(msg, ensure_ascii=False),
        "__DADOS_JSON__": json.dumps(dados, ensure_ascii=False),
        "__SITE__": SITE, "__ZAP__": ZAP,
    }
    saida = TPL
    for k, v in troca.items():
        saida = saida.replace(k, str(v))
    return saida

def html_escape(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))

TPL = open(os.path.join(RAIZ, "ferramentas", "modelo-produto.html"), encoding="utf-8").read()

def main():
    ps = produtos()
    for d in ("p/img", "p/og"):
        os.makedirs(os.path.join(RAIZ, d), exist_ok=True)
    ok = 0
    for p in ps:
        foto = os.path.join(RAIZ, "p/img", p["id"] + ".jpg")
        origem = next((u for u in (p.get("g") or []) if isinstance(u, str) and u.startswith("http")), None)
        tem_foto = baixar(origem, foto) if origem else False
        if tem_foto:
            try: card_og(p, foto, os.path.join(RAIZ, "p/og", p["id"] + ".jpg"))
            except Exception as e: print("   ! card og falhou:", p["id"], e)
        destino = os.path.join(RAIZ, "p", p["id"])
        os.makedirs(destino, exist_ok=True)
        open(os.path.join(destino, "index.html"), "w", encoding="utf-8").write(pagina(p))
        ok += 1
    print("paginas geradas: %d" % ok)

if __name__ == "__main__":
    main()
