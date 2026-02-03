# Disk Overview

Aplicativo desktop para Linux inspirado no "Este Computador" do Windows, com painel de unidades (locais e de rede) e barra lateral de favoritos.

## Requisitos

- Python 3.10+
- GTK 3
- PyGObject
- psutil

### Dependencias (Ubuntu/Zorin)

```bash
sudo apt install python3-gi python3-gi-cairo gir1.2-gtk-3.0 python3-psutil
```

## Executar

```bash
python3 -m disk_overview.main
```

## Configuracao

O arquivo de configuracao fica em:

```
~/.config/disk-overview/config.json
```

## Observacoes sobre atalho global

O atalho `Super+E` e configuravel, mas em GTK3 ele so funciona quando a janela esta em foco. Para atalho global real, pode ser necessario integrar com o sistema (ex.: atalho personalizado no GNOME ou lib especifica).
