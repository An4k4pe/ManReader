"""Genera PDF sintetici con ground truth dei confini di scheda.

Non e' un manuale reale. Serve solo a falsificare i metodi, mai a confermarli.
"""
from __future__ import annotations
import json, pymupdf

BOLD, REG = "hebo", "helv"
BODY, NAME = 9.0, 12.0
BLACK, DARKRED = (0, 0, 0), (0.5, 0.05, 0.05)
X0, TOP, LEAD, W = 60.0, 70.0, 13.0, 480.0

REC = [
    ("GUERRIERO SCHELETRO", [("Difficolta", "11"), ("Soglie", "7/13"), ("PF", "5"),
      ("Stress", "3"), ("Attacco", "+2"), ("Arma", "Alabarda, mischia, 1d8+3 fis")],
     ["Inarrestabile: spende una Paura per un turno addizionale."]),
    ("ARCIERE DELLE ROVINE", [("Difficolta", "13"), ("Soglie", "9/17"), ("PF", "4"),
      ("Stress", "5"), ("Attacco", "+3"), ("Arma", "Arco lungo, lontano, 2d6 fis"),
      ("Moventi", "Tenere la distanza, colpire i feriti")], []),
    ("CAMPIONE DEL PANTANO", [("Difficolta", "15"), ("Soglie", "12/24"), ("PF", "8"),
      ("Stress", "6"), ("Attacco", "+4"), ("Arma", "Maglio, mischia, 3d8+5 fis")],
     ["Corazza di fango: dimezza i danni fisici finche' non subisce",
      "un colpo critico."]),
    ("SCIAME DI CORVI", [("Difficolta", "9"), ("Soglie", "3/6"), ("PF", "2"),
      ("Stress", "2"), ("Attacco", "+1")],
     ["Nugolo: puo' occupare lo spazio di altre creature."]),
]

def _line(page, y, spans):
    x = X0
    for text, font, size, color in spans:
        page.insert_text((x, y), text, fontname=font, fontsize=size, color=color)
        x += pymupdf.get_text_length(text, fontname=font, fontsize=size)

def bestiary(page, records, gt, tag):
    y = TOP
    for name, fields, prose in records:
        start = y
        _line(page, y, [(name, BOLD, NAME, DARKRED)]); y += LEAD + 4
        for lab, val in fields:
            _line(page, y, [(lab + ": ", BOLD, BODY, BLACK), (val, REG, BODY, BLACK)]); y += LEAD
        for p in prose:
            _line(page, y, [(p, REG, BODY, BLACK)]); y += LEAD
        gt.append({"page": tag, "y0": start - 2, "y1": y - LEAD + 2, "name": name})
        y += 10

def prose_page(page):
    y = TOP
    paras = [("Nota del narratore. ", "La regione paludosa a nord del fiume e' percorsa da"),
             ("", "bande di predoni. Le carovane che la attraversano pagano un pedaggio"),
             ("Attenzione: ", "chi viaggia di notte incontra creature non elencate qui."),
             ("", "Il narratore puo' introdurre incontri casuali usando la tabella"),
             ("Variante. ", "in una campagna piu' cupa, raddoppia le soglie di tutti i"),
             ("", "nemici incontrati nelle sessioni successive alla terza.")]
    for lead, rest in paras:
        spans = ([(lead, BOLD, BODY, BLACK)] if lead else []) + [(rest, REG, BODY, BLACK)]
        _line(page, y, spans); y += LEAD

def rules_list(page):
    y = TOP
    _line(page, y, [("CONDIZIONI", BOLD, NAME, DARKRED)]); y += LEAD + 4
    for term, d in [("Vulnerabile", "i tiri contro di te hanno vantaggio"),
                    ("Trattenuto", "non puoi muoverti ma puoi agire"),
                    ("Spaventato", "hai svantaggio sui tiri d'attacco"),
                    ("Disorientato", "hai svantaggio sui tiri di reazione"),
                    ("Indebolito", "riduci di uno i dadi di danno"),
                    ("Nascosto", "non puoi essere bersagliato direttamente"),
                    ("Potenziato", "aggiungi un dado al prossimo tiro"),
                    ("Stordito", "salti il tuo prossimo turno")]:
        _line(page, y, [(term + ": ", BOLD, BODY, BLACK), (d, REG, BODY, BLACK)]); y += LEAD

def headings_page(page):
    y = TOP
    for h, body in [("PREPARARE LA SESSIONE", ["Prima di giocare, scegli il tono della",
                        "sessione e prepara tre scene di apertura."]),
                    ("CONDURRE IL COMBATTIMENTO", ["Alterna le azioni dei giocatori a quelle",
                        "degli avversari seguendo la narrazione."]),
                    ("CHIUDERE LA SESSIONE", ["Assegna i punti esperienza e annota le",
                        "promesse fatte ai personaggi."])]:
        _line(page, y, [(h, BOLD, NAME, DARKRED)]); y += LEAD + 4
        for b in body:
            _line(page, y, [(b, REG, BODY, BLACK)]); y += LEAD
        y += 10

def main(out):
    doc, gt = pymupdf.open(), []
    bestiary(doc.new_page(width=612, height=792), REC, gt, 0)
    var = [REC[3], REC[1], REC[0]]
    bestiary(doc.new_page(width=612, height=792), var, gt, 1)
    prose_page(doc.new_page(width=612, height=792))
    rules_list(doc.new_page(width=612, height=792))
    headings_page(doc.new_page(width=612, height=792))
    doc.save(out + "/synth.pdf")
    json.dump(gt, open(out + "/ground_truth.json", "w"), indent=1)
    print(f"pagine: {doc.page_count}  schede vere: {len(gt)}  (pagine 2,3,4 = negative)")

main("/tmp/claude-0/-home-user-ManReader/bf3622c8-0f6b-51f8-8f58-2201291c077f/scratchpad/sb")
