# Studio3D – Loja 3D com Checkout via WhatsApp

Projeto Django focado em venda de itens impressos em 3D com catálogo, carrinho em sessão e checkout simplificado via link `wa.me`.

## O que vem pronto
- Catálogo com produtos, tags e variações (cores via hex).
- Carrinho em `request.session`, sem necessidade de login.
- Checkout gera mensagem de pedido formatada para WhatsApp.
- Painel admin com inlines para gerenciar produtos e imagens.

## Como rodar em outra máquina
1) Clone o repo e crie o venv
```bash
python -m venv venv
venv\Scripts\activate  # Windows
```

2) Instale dependências mínimas
```bash
pip install django pillow python-dotenv
```

3) Crie o arquivo .env na raiz
```env
SECRET_KEY=django-insecure-mude-esta-chave
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
WHATSAPP_PHONE=55DDDNUMERO
```
Valores:
- `SECRET_KEY`: gere uma chave única para produção.
- `DEBUG`: use `False` em produção.
- `ALLOWED_HOSTS`: lista separada por vírgula.
- `WHATSAPP_PHONE`: número internacional sem `+`, DDI+DDD+número.

4) Migre o banco (SQLite por padrão)
```bash
python manage.py migrate
```

5) Crie um admin
```bash
python manage.py createsuperuser
```

6) Suba o servidor
```bash
python manage.py runserver
```
App em http://127.0.0.1:8000/ e admin em /admin/.

## Dicas rápidas de produção
- Ajuste `DEBUG=False`, configure `ALLOWED_HOSTS` e `CSRF_TRUSTED_ORIGINS` conforme o domínio.
- Troque para PostgreSQL se precisar de persistência real; mantenha `DATABASES` via env ou `dj-database-url` (não incluído).
- Rode `python manage.py collectstatic` e use storage estático apropriado se o host não persistir disco.
