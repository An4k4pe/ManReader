# Separare i riquadri fusi — criterio scritto PRIMA (passo 1 di 3)

Ordine deciso con l'utente il 10 settembre 2026, dopo
`RISULTATI_CONFINI_DAL_RIQUADRO.txt`: (1) separare i riquadri fusi dove si
consumano i candidati; (2) il criterio per le schede a una coppia per riga;
(3) scheda contro tabella, insieme all'innesto in IR 2. Ogni passo con il suo
criterio, misurato su **entrambi** i manuali.

## Da dove parte
Su Daggerheart 23 righe-verita' su 149 sono «fuse»: `_DEFAULT_CLUSTER_MARGIN =
5.0` fonde riquadri distanti fino a 10 pt, e gli stacchi fra due schede della
stessa colonna misurano 8,6-12,0 pt. Il candidato fuso **porta** i singoli
riquadri nei suoi `primitive_ids`.

## Il meccanismo, dichiarato prima
`riquadri.separa_riquadri`, nel consumatore. Nessun producer e nessuna soglia
toccati. Per ogni candidato `embedded_visual` e `interior_visual_frame`:

1. i membri visivi: `primitive_ids` → primitive disegno o immagine;
2. i **massimali**: membri il cui bbox non e' contenuto nel bbox di un altro
   membro con bbox diverso;
3. si tengono i massimali che contengono almeno una riga di testo, con la
   stessa regola di appartenenza dell'esperimento (centro della riga,
   `markdown_ir._dentro`);
4. massimali che condividono una riga sono lo stesso riquadro, e si uniscono;
5. se restano almeno due riquadri, il candidato e' sostituito da quelli
   (bbox = unione dei membri); altrimenti resta **com'e'**.

Nessun numero: contenimento e condivisione di una riga sono relazioni.

## Misura
`confini_dal_riquadro.py --senza-tabelle`, con e senza `--separa`, sui due
manuali; verita' invariata (`Thresholds`/`Impulses` su Daggerheart, `Ferocia`
su Dragonbane). Le tabelle si escludono perche' sono il passo 3: con le
tabelle dentro, la regola «vince la regione piu' ampia» coprirebbe l'effetto
della separazione. Il giro con le tabelle si riporta, non si giudica.

## Predizioni
- **P1** Daggerheart, 129 avversari: con `--separa` le fuse scendono a **0** e
  le prese sono **almeno 120**.
- **P2** le 19 righe degli ambienti non cambiano esito: i loro riquadri sono
  gia' uno per scheda.
- **P3** Dragonbane: nessun cambiamento sulle 4 schede (4 prese, 4 dal nome);
  la regione di AZIONI resta com'e'.
- **P4** ogni regione presa comincia dal nome.

## Accettazione
Il passo si accetta se, senza tabelle:
- su Daggerheart le fuse degli avversari sono 0 — una fusa residua e' ammessa
  **solo** se sull'immagine della pagina un solo rettangolo disegnato contiene
  davvero due righe-verita'; altrimenti conta come errore;
- le mancate non aumentano su nessuna pagina rispetto al giro senza `--separa`
  (la separazione non deve perdere righe);
- P3 regge.

P1 con la sua soglia di 120 e P4 si riportano. Se il passo non si accetta, si
dice che cosa e' caduto prima di cambiare qualunque cosa (`AGENTS.MD` §20).
