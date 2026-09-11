# Páginas de produto — como funciona

Cada produto do catálogo tem uma página própria, e é ela que faz o WhatsApp
mostrar o card com a foto quando o link é enviado numa conversa.

```
p/P001/index.html   página com as tags Open Graph (o WhatsApp lê daqui)
p/img/P001.jpg      foto do produto no nosso domínio
p/og/P001.jpg       card 1200x630 (foto + nome + preço + código)
```

## Regenerar depois de mexer nos produtos

O catálogo mora no `index.html`, no array `PRODUTOS_BASE`. Mudou preço, nome ou
foto? Rode:

```bash
python3 ferramentas/gerar-produtos.py
```

O script relê o `index.html`, baixa as fotos que faltam e reescreve as 42
páginas. Nada é digitado duas vezes.

## Por que a foto fica hospedada aqui

A CDN do fornecedor (`arquivos-cdn.facilzap.app.br`) responde **403** para robô
sem navegador — o rastreador do WhatsApp não conseguiria ler a imagem e o card
apareceria sem foto. Por isso a foto é copiada para `p/img/`.

## Limite do WhatsApp

`wa.me` só aceita **texto**. Não existe forma de anexar imagem por link.
O card visual na conversa vem do preview de link (Open Graph) — por isso a
mensagem sempre leva a URL do produto.

Para mandar um card de produto de verdade (catálogo nativo) seria preciso a
**WhatsApp Cloud API** com o número conectado e o catálogo sincronizado. Hoje
o projeto não tem Cloud API, e o perfil do WhatsApp nem está conectado à Página.
