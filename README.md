# Louis Vuitton — Offline-Klon (de.louisvuitton.com)

Statischer Mirror der deutschen Louis-Vuitton-Seite, inkl. Herren Ready-to-Wear und **183 Produktseiten**.

## Inhalt (`sites/`)

| Pfad | Beschreibung |
|------|----------------|
| `homepage/` | Startseite |
| `herren/ready-to-wear/vollstandige-ready-to-wear/` | Herren Ready-to-Wear (183 Produkte) |
| `produkte/<SKU>/` | Einzelproduktseiten (z. B. `1AK70W`) |
| `kategorie/t-shirts-und-poloshirts/` | Kategorie-Seite |

## Lokal ansehen

```bash
./start_local.sh
# → http://localhost:5000/
```

Oder nur die Seiten:

```bash
cd sites && python3 -m http.server 5000
```

## Neu klonen / erweitern

1. `./start_listener.sh` — Cookie-Listener starten
2. Extension in Opera GX laden (`extension/` → `opera://extensions`)
3. Seiten besuchen → Extension „Seite jetzt speichern“
4. Alle Produkte einer Kategorie: `./clone_products.sh`

## Hinweis

Nur für **private/offline Nutzung**. Design, Bilder und Markeninhalte gehören Louis Vuitton.
