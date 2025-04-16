@echo off
echo 🔁 Derrubando containers Docker...
docker-compose down --volumes

echo 🟢 Tudo pronto! Pressione qualquer tecla para sair.
pause >nul
