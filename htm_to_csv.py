from bs4 import BeautifulSoup
import pandas as pd
import argparse

def main():

    parser = argparse.ArgumentParser()
    #parser.add_argument('--test', action='store_true', help="Aktiviert den Testmodus.")
    #parser.add_argument('--listparams', action='store_true', help="Listet die Parameter für die ausgewählten Versuche")
    parser.add_argument('--verb', type=str, default = 'ser', help="Zu konjugierendes Verb")
    args = parser.parse_args()

    # Pfad zur heruntergeladenen HTML-Datei
    html_file = f"{args.verb}.htm"

    with open(html_file, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f, "html.parser")

    rows = []

    current_modo = None

    # Wir laufen durch die Kinder der großen Konjugationsbox
    for element in soup.select("div.result-block-api")[0].descendants:
        # Wenn wir eine Modus-Überschrift finden (h4)
        if element.name == "h4":
            current_modo = element.get_text(strip=True)

        # Falls es eine Zeitform-Box ist
        if element.name == "div" and "blue-box-wrap" in element.get("class", []):
            tense_name = element.find("p")
            if tense_name is None:
                continue
            tense_name = tense_name.get_text(strip=True)

            for li in element.select("ul.wrap-verbs-listing > li"):
                # Personalpronomen extrahieren
                pronoun_tag = li.find("i", class_="graytxt")
                pronoun = pronoun_tag.get_text(strip=True) if pronoun_tag else "(ohne Pronomen)"

                # Verbteile (inkl. zusammengesetzter Formen)
                verb_parts = []
                for i in li.find_all("i"):
                    cls = " ".join(i.get("class", []))
                    if "verbtxt" in cls or "auxgraytxt" in cls:
                        verb_parts.append(i.get_text(strip=True))
                verb = " ".join(verb_parts).strip()

                rows.append({
                    "Personalpronomen": pronoun,
                    "Modo": current_modo,
                    "Tempo": tense_name,
                    "Konjugation": verb
                })

    # DataFrame bauen (langes Format)
    df = pd.DataFrame(rows)

    # CSV speichern
    csv_file = "ser_konjugation_long.csv"
    df.to_csv(csv_file, encoding="utf-8-sig", index=False)

    print(f"CSV wurde gespeichert unter: {csv_file}")

if __name__ == "__main__":
    main()

