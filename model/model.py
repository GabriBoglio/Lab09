from database.parco_DAO import ParcoDAO
from database.escursione_DAO import EscursioneDAO
from database.punto_interesse_DAO import PuntoInteresseDAO


class Model:
    def __init__(self):
        self.escursioni_map = {}
        self.punti_interesse_map = {}

        self._pacchetto_ottimo = []
        self._valore_ottimo: int = -1
        self._costo = 0

        self._escursioni_parco = []

        self.load_escursioni()
        self.load_punti_interesse()
        self.load_relazioni()

    @staticmethod
    def load_parchi():
        return ParcoDAO.get_parchi()

    def load_escursioni(self):
        self.escursioni_map = EscursioneDAO.get_escursioni()

    def load_punti_interesse(self):
        self.punti_interesse_map = PuntoInteresseDAO.get_punti_interesse()

    def load_relazioni(self):
        for esc in self.escursioni_map.values():
            esc.punti_interesse = set()
        for punto in self.punti_interesse_map.values():
            punto.escursioni = set()

        relazioni = EscursioneDAO.get_escursioni_punti_interesse()
        for id_escursione, id_punto_interesse in relazioni:
            esc = self.escursioni_map.get(id_escursione)
            punto = self.punti_interesse_map.get(id_punto_interesse)
            if esc is not None and punto is not None:
                esc.punti_interesse.add(punto)
                punto.escursioni.add(esc)

    def _valore_escursione(self, escursione) -> int:
        return sum(punto.voto_visitatori for punto in escursione.punti_interesse)

    def genera_pacchetto(self, id_parco: str, max_giorni: int = None, max_budget: float = None):
        self._pacchetto_ottimo = []
        self._costo = 0
        self._valore_ottimo = -1

        self._escursioni_parco = [
            esc for esc in self.escursioni_map.values()
            if esc.id_parco == id_parco
        ]

        self._ricorsione(
            start_index=0,
            pacchetto_parziale=[],
            durata_corrente=0,
            costo_corrente=0.0,
            valore_corrente=0,
            punti_usati=set(),
            max_giorni=max_giorni,
            max_budget=max_budget,
        )

        if self._valore_ottimo == -1:
            self._valore_ottimo = 0

        return self._pacchetto_ottimo, self._costo, self._valore_ottimo

    def _ricorsione(
        self,
        start_index: int,
        pacchetto_parziale: list,
        durata_corrente: int,
        costo_corrente: float,
        valore_corrente: int,
        punti_usati: set,
        max_giorni: int = None,
        max_budget: float = None,
    ):
        if valore_corrente > self._valore_ottimo:
            self._valore_ottimo = valore_corrente
            self._pacchetto_ottimo = pacchetto_parziale.copy()
            self._costo = costo_corrente

        for i in range(start_index, len(self._escursioni_parco)):
            esc = self._escursioni_parco[i]

            nuova_durata = durata_corrente + esc.durata_giorni
            nuovo_costo = costo_corrente + esc.costo

            rispetta_giorni = (max_giorni is None) or (nuova_durata <= max_giorni)
            rispetta_budget = (max_budget is None) or (nuovo_costo <= max_budget)
            punti_disgiunti = esc.punti_interesse.isdisjoint(punti_usati)

            if rispetta_giorni and rispetta_budget and punti_disgiunti:
                valore_esc = self._valore_escursione(esc)

                pacchetto_parziale.append(esc)
                punti_usati.update(esc.punti_interesse)

                self._ricorsione(
                    start_index=i + 1,
                    pacchetto_parziale=pacchetto_parziale,
                    durata_corrente=nuova_durata,
                    costo_corrente=nuovo_costo,
                    valore_corrente=valore_corrente + valore_esc,
                    punti_usati=punti_usati,
                    max_giorni=max_giorni,
                    max_budget=max_budget,
                )

                pacchetto_parziale.pop()
                punti_usati.difference_update(esc.punti_interesse)