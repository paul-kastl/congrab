from bs4 import BeautifulSoup
import pandas as pd
import argparse
from bs4.element import Tag

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--infinitivo', type=str, default='ser', help="Zu konjugierendes Verb")
    parser.add_argument('--translation', type=str, default='keine Übersetzung', help="die Übersetzung des Infinitivs ins Deutsche")
    parser.add_argument(
        '--include',
        action='append',
        help="Mehrfach möglich: 'Modo' oder 'Modo:Tempo' (z.B. --include 'Imperativo' --include 'Indicativo:Presente')"
    )
    parser.add_argument('--list', action='store_true', help="Liste aller gefundenen Modo:Tempo-Kombinationen ausgeben und beenden")
    args = parser.parse_args()

    html_file = f"{args.infinitivo}.htm"
    with open(html_file, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f, "html.parser")

    rows = []

    # Jeder <h4> ist ein Modus, danach folgen die Zeiten bis zum nächsten <h4>
    for h4 in soup.find_all('h4'):
        modo = h4.get_text(strip=True)

        for elem in h4.find_all_next():
            if elem.name == 'h4':
                break  # nächster Modus erreicht

            if elem.name == 'div' and 'blue-box-wrap' in elem.get('class', []):
                # Zeitform bestimmen
                ptag = elem.find('p')
                tempo = ptag.get_text(strip=True) if ptag else (elem.get('mobile-title') or "").strip()
                if not tempo:
                    continue

                # Konjugationen parsen
                for li in elem.select('ul.wrap-verbs-listing > li'):
                    pronoun_tag = li.find('i', class_='graytxt')
                    pronoun = pronoun_tag.get_text(strip=True) if pronoun_tag else ''

                    if pronoun in ['–', '-', '—', '']:
                        if modo in ['Infinitivo', 'Imperativo', 'Imperativo Negativo']:
                            # Für diese Modi die normalen Personalpronomen einsetzen
                            # Reihenfolge wie im Spanischen/Portugiesischen üblich:
                            pronouns_order = ['eu', 'tu', 'ele/ela/você', 'nós', 'vós', 'eles/elas/vocês']
                            # Wir können hier die aktuelle Zeile als Index nehmen
                            index = len([r for r in rows if r['Modo'] == modo])  # Zählt, wie viele Zeilen schon existieren
                            pronoun = pronouns_order[index % len(pronouns_order)]
                        else:
                            pronoun = "(ohne Pronomen)"

                    # Verbteile einsammeln
                    verb_parts = []
                    for inner in li.find_all('i'):
                        cls = " ".join(inner.get('class', []))
                        if 'verbtxt' in cls or 'auxgraytxt' in cls:
                            text = inner.get_text(strip=True)
                            if text:
                                verb_parts.append(text)
                    verb = " ".join(verb_parts).strip()
                    if not verb:
                        verb = li.get_text(strip=True)

                    rows.append({
                        "Personalpronomen": pronoun,
                        "Modo": modo,
                        "Tempo": tempo,
                        "Konjugation": verb
                    })

    # DataFrame bauen
    df = pd.DataFrame(rows)
    
    # Nur Leerzeichen entfernen, die INNERHALB eines Wortes stehen (ohne Hilfswort davor)
    df['Konjugation'] = df['Konjugation'].apply(lambda x: x[::-1].replace(' ', '', 1)[::-1] if ' ' in x else x)

    # 1. Gerúndio erweitern (6 Zeilen mit estar + Gerundium)
    gerundio_rows = df[df['Tempo'] == 'Gerúndio'].copy()
    if not gerundio_rows.empty:
        gerundio_form = gerundio_rows.iloc[0]['Konjugation']  # z.B. "comp etindo"
        
        # Estar-Konjugation im Presente
        estar_forms = {
            'eu': 'estou',
            'tu': 'estás',
            'ele/ela/você': 'está',
            'nós': 'estamos',
            'vós': 'estais',
            'eles/elas/vocês': 'estão'
        }
        
        # Alte Gerúndio-Zeile(n) entfernen
        df = df[df['Tempo'] != 'Gerúndio']
        
        # Neue 6 Zeilen für Gerúndio erstellen
        new_gerundio = []
        for pronoun, estar in estar_forms.items():
            new_gerundio.append({
                'Personalpronomen': pronoun,
                'Modo': 'Gerúndio',
                'Tempo': 'Gerúndio',
                'Konjugation': f"{estar} {gerundio_form}"
            })
        df = pd.concat([df, pd.DataFrame(new_gerundio)], ignore_index=True)

    # Nur für Debug: alle Kombinationen ausgeben
    if args.list:
        combos = sorted({f"{r['Modo']}:{r['Tempo']}" for r in rows})
        print("Gefundene Modo:Tempo-Kombinationen:")
        for c in combos:
            print(c)
        return

    # "tu" und "vós" rausfiltern
    df = df[~df["Personalpronomen"].isin(["tu", "vós"])]
    #print(df)

    # Extended CSV mit Infinitiv + Übersetzung
    df2 = df.copy()
    df2.insert(0, "Infinitivo", args.infinitivo)
    df2.insert(1, "Übersetzung", args.translation)
    df2 = df2.rename(columns={"Personalpronomen": "pronome pessoal"})
    df2 = df2[["Infinitivo", "Übersetzung", "pronome pessoal", "Tempo", "Modo", "Konjugation"]]

    # Filter nach --include
    if args.include:
        include_set = {s.strip().lower() for s in args.include}
        def row_included(r):
            combo = f"{r['Modo']}:{r['Tempo']}".lower()
            modo_only = r['Modo'].lower()
            return combo in include_set or modo_only in include_set
        df2 = df2[df2.apply(row_included, axis=1)]

    # CSV-Dateiname
    if args.include:
        sanitized = ["_".join(v.replace(":", " - ").split()) for v in args.include]
        filename_extension = "_".join(sanitized)
    else:
        filename_extension = "all"

    # for debug only
    #csv_file = f"{args.infinitivo}_all.csv"
    #df.to_csv(csv_file, encoding="utf-8-sig", index=False, header=False)

    csv_file = f"{args.infinitivo}_{filename_extension}.csv"
    df2.to_csv(csv_file, encoding="utf-8-sig", index=False, header=False)

    print(f"CSV gespeichert unter: {csv_file}")

if __name__ == "__main__":
    main()
