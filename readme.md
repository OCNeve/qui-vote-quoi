# Startup
_le projet dépend de `python 3.12` et de `docker`_

## Infrastructure
Lancer les contenaires
```bash
docker-compose up -d
```
Une fois les contenaires en cours d'execution, vous pouvez consulter pgadmin
```bash
http://localhost:15432/
```
## Projet
### Windows (batch/powershell)
```bash
python -m pip install poetry
```
```bash
python -m poetry install
```

### Unix (bash/zsh)

```bash
python3 -m pip3 install poetry
```
```bash
python3 -m poetry install
```
