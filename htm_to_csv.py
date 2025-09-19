from bs4 import BeautifulSoup
import pandas as pd
import argparse

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--infinitivo', type=str, default='ser', help="Zu konjugierendes Verb")
    parser.add_argument('--translation', type=str, default='keine Übersetzung', help="die Übersetzung des Infinitivs ins Deutsche")
    parser.add_argument(
    '--include',
    action='append',
    help="Liste von Modo:Tempo-Kombinationen, mehrfach angeben möglich (z.B. --include 'Indicativo:Presente' --include 'Indicativo:Pretérito Perfeito')"
    )
    args = parser.parse_args()

    # Pfad zur heruntergeladenen HTML-Datei
    html_file = f"{args.infinitivo}.htm"

    with open(html_file, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f, "html.parser")

    rows = []
    current_modo = None

    # Durch die Struktur der Konjugationstabelle laufen
    for element in soup.select("div.result-block-api")[0].descendants:
        if element.name == "h4":
            current_modo = element.get_text(strip=True)

        if element.name == "div" and "blue-box-wrap" in element.get("class", []):
            tense_name = element.find("p")
            if tense_name is None:
                continue
            tense_name = tense_name.get_text(strip=True)

            for li in element.select("ul.wrap-verbs-listing > li"):
                pronoun_tag = li.find("i", class_="graytxt")
                pronoun = pronoun_tag.get_text(strip=True) if pronoun_tag else "(ohne Pronomen)"

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

    # DataFrame bauen
    df = pd.DataFrame(rows)

    # "tu" und "vós" entfernen
    df = df[~df["Personalpronomen"].isin(["tu", "vós"])]

    # Erste CSV (komplett)
    csv_file1 = f"{args.infinitivo}_konjugation_long.csv"
    df.to_csv(csv_file1, encoding="utf-8-sig", index=False)

    # Zweite CSV (mit Include-Filter)
    df2 = df.copy()
    df2.insert(0, "Infinitivo", args.infinitivo)
    df2.insert(1, "Übersetzung", args.translation)
    df2 = df2.rename(columns={"Personalpronomen": "pronome pessoal"})
    df2 = df2[["Infinitivo", "Übersetzung", "pronome pessoal", "Tempo", "Modo", "Konjugation"]]

    if args.include:
        # Set aus erlaubten Kombinationen bilden
        include_set = set(args.include)
        df2 = df2[df2.apply(lambda r: f"{r['Modo']}:{r['Tempo']}" in include_set, axis=1)]

    csv_file2 = f"{args.infinitivo}_konjugation_extended.csv"
    df2.to_csv(csv_file2, encoding="utf-8-sig", index=False, header=False)

    print(f"CSV 1 gespeichert unter: {csv_file1}")
    print(f"CSV 2 gespeichert unter: {csv_file2}")

if __name__ == "__main__":
    main()
