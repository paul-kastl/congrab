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

    # Dictionary: { Personalpronomen: { Zeitform: Konjugation } }
    data = {}

    # Alle Zeitform-Blöcke finden
    for box in soup.select("div.blue-box-wrap"):
        tense = box.find("p")
        if tense is None:
            continue
        tense_name = tense.get_text(strip=True)

        # Alle Zeilen (li)
        for li in box.select("ul.wrap-verbs-listing > li"):
            # Pronomen (falls vorhanden)
            pronoun_tag = li.find("i", class_="graytxt")
            pronoun = pronoun_tag.get_text(strip=True) if pronoun_tag else ""

            # eigentliche Verbform(en) zusammensetzen
            verb_parts = [i.get_text(strip=True) for i in li.find_all("i") if "verbtxt" in " ".join(i.get("class", []))]
            verb = " ".join(verb_parts).strip()

            # Wenn es kein Personalpronomen gibt (z.B. Infinitivo, Gerúndio),
            # benutzen wir einfach den Infinitiv/Partizip als "Pronomen"-Key
            if not pronoun:
                pronoun = "(ohne Pronomen)"

            if pronoun not in data:
                data[pronoun] = {}
            data[pronoun][tense_name] = verb

    # In DataFrame umwandeln
    df = pd.DataFrame.from_dict(data, orient="index")
    df.index.name = "Personalpronomen"

    # CSV speichern
    csv_file = "ser_konjugation.csv"
    df.to_csv(csv_file, encoding="utf-8-sig")

    print(f"CSV wurde gespeichert unter: {csv_file}")

if __name__ == "__main__":
    main()

