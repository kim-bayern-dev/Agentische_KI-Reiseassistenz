from dataclasses import dataclass
from typing import List, Literal, Dict


@dataclass
class Tour:
    tournr: str
    titel: str
    index: str
    gpx: str
    tourentyp: str
    dauer: float
    dauer_tage: int
    hm_aufstieg: int
    hm_abstieg: int
    subtitle: str
    summary: str
    beschreibung: str
    ausgangspunkt: str
    anforderungen: str
    refreshments: str
    varianten: str
    public: bool
    schwierigkeit: Literal["blau", "rot", "schwarz"]
    public_transport: bool
    einkehr: bool
    kinderfreundlich: bool
    hundefreundlich: bool
    kinderwagen: bool
    baden: bool
    tags: List[str]
    bilder: List[Dict]
    pois: List[Dict]

    @staticmethod
    def from_raw_dict(raw_dict: dict) -> "Tour":
        """Create a Tour instance from a raw dictionary.

        Args:
            raw_dict (dict): Raw dictionary containing tour data.

        Returns:
            Tour: An instance of the Tour class.
        """
        # clean bilder
        bilder_raw = raw_dict.get("Bild", [])
        bilder = []
        for b in bilder_raw:
            bilder.append(
                {
                    "bilddatei": b.get("bilddatei", ""),
                    "bildtitel": b.get("bildtitel", ""),
                    "kat": b.get("kat", ""),
                    "longitude": (
                        float(b.get("longitude", 0)) if b.get("longitude") else 0.0
                    ),
                    "latitude": (
                        float(b.get("latitude", 0)) if b.get("latitude") else 0.0
                    ),
                    "bildtext": b.get("bildtext", ""),
                }
            )

        return Tour(
            tournr=raw_dict.get("tournr", ""),
            titel=raw_dict.get("titel", ""),
            index=raw_dict.get("index", ""),
            gpx=raw_dict.get("gpx", ""),
            tourentyp=raw_dict.get("tourentyp", ""),
            dauer=float(raw_dict.get("dauer", 0)),
            dauer_tage=int(raw_dict.get("dauer_tage", 0)),
            hm_aufstieg=int(raw_dict.get("hm_aufstieg", 0)),
            hm_abstieg=int(raw_dict.get("hm_abstieg", 0)),
            subtitle=raw_dict.get("prosa_preserved", {}).get("bold", ""),
            summary=raw_dict.get("prosa_preserved", {}).get("#text", ""),
            beschreibung=raw_dict.get("beschreibung", {})
            .get("content")[1]
            .get("text_preserved", ""),
            ausgangspunkt=raw_dict.get("beschreibung", {})
            .get("content")[0]
            .get("text_preserved", "")
            .get("ausgangspunkt", ""),
            anforderungen=raw_dict.get("beschreibung", {})
            .get("content")[0]
            .get("text_preserved", "")
            .get("anforderungen", ""),
            refreshments=raw_dict.get("beschreibung", {})
            .get("content")[0]
            .get("text_preserved", "")
            .get("refreshments", ""),
            varianten=raw_dict.get("beschreibung", {})
            .get("content")[0]
            .get("text_preserved", "")
            .get("varianten", ""),
            public=raw_dict.get("public", "false") == "true",
            schwierigkeit=raw_dict.get("schwierigkeit", "undefined"),
            public_transport=raw_dict.get("public_transport", "false") == "true",
            einkehr=raw_dict.get("einkehr", "false") == "true",
            kinderfreundlich=raw_dict.get("kinderfreundlich", "false") == "true",
            hundefreundlich=raw_dict.get("hundefreundlich", "false") == "true",
            kinderwagen=raw_dict.get("kinderwagen", "false") == "true",
            baden=raw_dict.get("baden", "false") == "true",
            bilder=bilder,
            pois=raw_dict.get("poi", []),
            tags=raw_dict.get("tag", []),
        )
