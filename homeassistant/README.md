# Picnic MCP Server - Home Assistant Integratie

Deze configuraties maken het mogelijk om de Picnic MCP Server aan te roepen via Home Assistant, inclusief integratie met Google Gemini AI.

## Architectuur

```
┌─────────────────────────────────────────────────────────────┐
│                    Google Gemini AI                          │
│         (via Home Assistant Conversation)                    │
└──────────────────────┬──────────────────────────────────────┘
                       │ Roept script aan
                       ▼
┌─────────────────────────────────────────────────────────────┐
│              Home Assistant Scripts                          │
│    (picnic_product_zoeken_en_toevoegen, etc.)               │
└──────────────────────┬──────────────────────────────────────┘
                       │ Roept rest_command aan
                       ▼
┌─────────────────────────────────────────────────────────────┐
│              Home Assistant REST Commands                    │
│         (picnic_search_products, picnic_add_to_cart)        │
└──────────────────────┬──────────────────────────────────────┘
                       │ HTTP POST naar /call-tool
                       ▼
┌─────────────────────────────────────────────────────────────┐
│              Picnic MCP Server (Port 3000)                   │
│                   Node.js / TypeScript                       │
└──────────────────────┬──────────────────────────────────────┘
                       │ API calls
                       ▼
                ┌──────────────┐
                │  Picnic API  │
                └──────────────┘
```

## Installatie

### Stap 1: MCP Server URL Aanpassen

Open `configuration.yaml` en pas de URL aan naar je MCP server:

```yaml
# Als MCP server op dezelfde machine draait:
url: "http://localhost:3000/call-tool"

# Als MCP server in Docker draait (Home Assistant OS):
url: "http://picnic-mcp-server:3000/call-tool"

# Als MCP server op een ander IP draait:
url: "http://192.168.1.100:3000/call-tool"
```

### Stap 2: Configuratie Toevoegen

**Optie A: Direct toevoegen aan je bestaande configuratie**

Kopieer de inhoud van `configuration.yaml` naar je eigen `/config/configuration.yaml`:

```yaml
# In je configuration.yaml
rest_command:
  picnic_search_products:
    # ... (kopieer van configuration.yaml)
```

Kopieer de inhoud van `scripts.yaml` naar je eigen `/config/scripts.yaml`.

**Optie B: Als aparte bestanden includen**

```yaml
# In je configuration.yaml
rest_command: !include picnic_rest_commands.yaml
script: !include_dir_merge_named scripts/
```

Kopieer dan:
- `configuration.yaml` → `/config/picnic_rest_commands.yaml`
- `scripts.yaml` → `/config/scripts/picnic.yaml`

### Stap 3: Home Assistant Herstarten

```bash
# Via Home Assistant UI: Instellingen → Systeem → Herstarten
# Of via CLI:
ha core restart
```

### Stap 4: Testen

Test de verbinding via Developer Tools → Services:

1. Zoek naar `rest_command.picnic_get_cart`
2. Klik op "Call Service"
3. Controleer de logs voor het resultaat

## Gemini AI Configuratie

### Stap 1: Google Generative AI Integratie Installeren

1. Ga naar Instellingen → Apparaten & Services → Integratie toevoegen
2. Zoek "Google Generative AI Conversation"
3. Voeg je Google AI API key toe

### Stap 2: Gemini Configureren voor Scripts

In de integratie configuratie, voeg exposed entities toe:

```yaml
# Expose alle Picnic scripts aan Gemini
expose_entities:
  - script.picnic_product_zoeken_en_toevoegen
  - script.picnic_winkelwagen_bekijken
  - script.picnic_producten_zoeken
  - script.picnic_winkelwagen_legen
  - script.picnic_bezorgmomenten_bekijken
```

### Stap 3: Gemini Prompt Aanpassen (Optioneel)

Voeg context toe aan je Gemini configuratie:

```yaml
# In de Gemini integratie configuratie
llm_hass_api: assist
prompt: |
  Je bent een slimme huisassistent met toegang tot Picnic boodschappen.

  Beschikbare Picnic acties:
  - script.picnic_product_zoeken_en_toevoegen: Zoek een product en voeg toe
  - script.picnic_winkelwagen_bekijken: Bekijk wat er in het mandje zit
  - script.picnic_producten_zoeken: Zoek naar producten
  - script.picnic_winkelwagen_legen: Leeg het hele mandje
  - script.picnic_bezorgmomenten_bekijken: Bekijk wanneer Picnic kan leveren

  Wanneer iemand vraagt om boodschappen toe te voegen, gebruik het
  picnic_product_zoeken_en_toevoegen script met de product_naam parameter.
```

## Beschikbare Scripts

| Script | Beschrijving | Parameters |
|--------|--------------|------------|
| `picnic_product_zoeken_en_toevoegen` | Zoek en voeg product toe | `product_naam` (verplicht), `aantal` |
| `picnic_product_toevoegen` | Voeg toe via product ID | `product_id` (verplicht), `aantal` |
| `picnic_winkelwagen_bekijken` | Bekijk winkelwagen | - |
| `picnic_product_verwijderen` | Verwijder product | `product_id` (verplicht), `aantal` |
| `picnic_winkelwagen_legen` | Leeg hele winkelwagen | - |
| `picnic_producten_zoeken` | Zoek producten | `zoekterm` (verplicht) |
| `picnic_bezorgmomenten_bekijken` | Bekijk bezorgtijden | - |
| `picnic_lijstjes_bekijken` | Bekijk boodschappenlijstjes | - |
| `picnic_account_bekijken` | Bekijk accountgegevens | - |
| `picnic_categorieen_bekijken` | Bekijk categorieën | - |

## Voorbeelden met Gemini

Na configuratie kun je tegen Gemini zeggen:

- "Voeg melk toe aan mijn Picnic mandje"
- "Zet 2 pakken pindakaas op de Picnic lijst"
- "Wat zit er in mijn Picnic winkelwagen?"
- "Zoek naar hagelslag bij Picnic"
- "Leeg mijn Picnic mandje"
- "Wanneer kan Picnic bezorgen?"

## Troubleshooting

### MCP Server niet bereikbaar

Controleer of de MCP server draait:
```bash
curl http://localhost:3000/health
# Verwacht: {"status":"ok","version":"1.0.7"}
```

### Scripts niet zichtbaar voor Gemini

1. Controleer of de scripts correct geladen zijn:
   - Ga naar Developer Tools → Services
   - Zoek naar "picnic"
   - De scripts moeten zichtbaar zijn

2. Controleer of de scripts exposed zijn aan Gemini:
   - Ga naar de Gemini integratie configuratie
   - Voeg de script entities toe aan de exposed entities

### Zoekresultaten niet zichtbaar

De zoekresultaten worden naar de logs geschreven. Bekijk ze via:
- Instellingen → Systeem → Logboeken
- Filter op "picnic"

## Geavanceerd: Notificaties naar Telefoon

Pas de scripts aan om notificaties naar je telefoon te sturen:

```yaml
# In scripts.yaml, voeg toe aan de sequence:
- service: notify.mobile_app_jouw_telefoon
  data:
    title: "Picnic"
    message: "{{ product_naam }} toegevoegd aan je mandje"
```

Vervang `mobile_app_jouw_telefoon` door je eigen mobile app notificatie service.
