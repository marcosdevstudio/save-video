# SaveVideo

Aplicação em Python para pesquisar e baixar vídeos e áudios de YouTube, Instagram e TikTok usando `yt-dlp`. Inclui um site responsivo e uma interface de terminal.

## Requisitos

- Python 3.10+
- FFmpeg instalado no sistema
- Acesso à internet

## Instalação

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Abrir o site localmente

```bash
python app.py
```

Depois acesse `http://127.0.0.1:5000` no navegador.

No Windows, também é possível usar o servidor Waitress:

```powershell
waitress-serve --listen=0.0.0.0:5000 app:app
```

Ou dê duplo clique em `run_web.bat`.

Para rodar em produção em serviços como Render ou Railway, use o comando:

```bash
gunicorn app:app
```

## Publicar gratuitamente no Render

1. Crie um repositório no GitHub e envie este projeto.
2. Acesse `render.com` e entre com sua conta GitHub.
3. Clique em `New +` e escolha `Blueprint`.
4. Selecione o repositório do SaveVideo.
5. Confirme o serviço gratuito definido em `render.yaml`.
6. Aguarde o build do Docker e abra a URL `onrender.com` criada.

O `Dockerfile` já instala FFmpeg e inicia o Gunicorn na porta fornecida pelo Render. No plano gratuito, o serviço pode entrar em repouso quando não houver acesso e demorar alguns segundos para acordar.

O projeto já inclui `Procfile` e `runtime.txt` para facilitar a publicação. O servidor de hospedagem também precisa ter FFmpeg instalado, porque ele é usado para juntar áudio e vídeo e converter MP3.

O site valida URLs apenas de YouTube, Instagram e TikTok, limita requisições por endereço IP e processa downloads em jobs assíncronos para evitar timeout em arquivos maiores. Os arquivos temporários são removidos depois do envio ou após 30 minutos.

Antes de publicar:

- mantenha o modo debug desligado em produção
- instale FFmpeg no servidor
- revise os textos de `Termos` e `Privacidade` para o seu projeto
- baixe somente conteúdo para o qual você tenha autorização

## Uso

```bash
python savevideo.py "https://www.youtube.com/watch?v=EXEMPLO"
python savevideo.py "https://www.instagram.com/reel/EXEMPLO/"
python savevideo.py "https://www.tiktok.com/@usuario/video/1234567890"
```

### Opções úteis

```bash
python savevideo.py "https://youtu.be/EXEMPLO" --output-dir videos
python savevideo.py "https://www.youtube.com/playlist?list=EXEMPLO" --no-playlist
python savevideo.py "https://www.youtube.com/watch?v=EXEMPLO" --audio-only
python savevideo.py "https://www.youtube.com/watch?v=EXEMPLO" --no-watermark
```

## Observação sobre marca d'água

A remoção de marca d'água depende do site, do vídeo e da forma como o conteúdo é disponibilizado. O `yt-dlp` pode tentar baixar variantes sem marca quando elas existem, mas não existe uma solução universal que funcione para todos os vídeos de todos os serviços.

Para melhores resultados:

- use `--no-watermark` quando houver uma versão limpa disponível
- teste a URL em 1 ou 2 vídeos diferentes
- em alguns casos, cookies ou login podem ser necessários para acessar conteúdo restrito
- o FFmpeg continua sendo obrigatório para conversão de áudio em MP3
