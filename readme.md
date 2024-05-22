# A propos
_voici un diagram d'architecture de données. Les tables en `rouge` représantent des sources de données à plat_
![](./datastructure.png)
# Startup
_le projet dépend de `python 3.12` et de `docker_

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
cd ./data_dumper
```
```bash
python -m poetry install
```
```bash
python -m poetry run python main.py
```

### Unix (bash/zsh)

```bash
python3 -m pip3 install poetry
```
```bash
cd ./data_dumper
```
```bash
python3 -m poetry install
```
```bash
python3 -m poetry run python3 main.py
```