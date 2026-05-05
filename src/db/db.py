import random

from typing import List, Optional, Literal
from db.tour import Tour


class TourenDB:
    def __init__(self):
        self.touren: List[Tour] = []

    def add_tour(self, tour):
        self.touren.append(tour)

    def get_all_tours(self):
        return self.touren

    def query_tours(
        self,
        n_results: Optional[int] = None,
        public: Optional[bool] = None,
        public_transport: Optional[bool] = None,
        einkehr: Optional[bool] = None,
        kinderfreundlich: Optional[bool] = None,
        hundefreundlich: Optional[bool] = None,
        kinderwagen: Optional[bool] = None,
        baden: Optional[bool] = None,
        schwierigkeit: Optional[Literal["blau", "rot", "schwarz"]] = None,
        min_dauer: Optional[float] = None,  # hours
        max_dauer: Optional[float] = None,
        min_hm_aufstieg: Optional[int] = None,
        max_hm_aufstieg: Optional[int] = None,
    ) -> List[Tour]:
        """Return a list of tours that match all supplied criteria.

        Args:
            n_results (Optional[int]): Maximum number of results to return.
            public_transport (Optional[bool]): Filter by public transport accessibility.
            einkehr (Optional[bool]): Filter by presence of eateries.
            kinderfreundlich (Optional[bool]): Filter by child-friendliness.
            hundefreundlich (Optional[bool]): Filter by dog-friendliness.
            kinderwagen (Optional[bool]): Filter by stroller accessibility.
            baden (Optional[bool]): Filter by swimming availability.
            schwierigkeit (Optional[Literal["blau", "rot", "schwarz"]]):
                Filter by difficulty level.
            min_dauer (Optional[float]): Minimum duration in hours.
            max_dauer (Optional[float]): Maximum duration in hours.
            min_hm_aufstieg (Optional[int]): Minimum ascent in meters.
            max_hm_aufstieg (Optional[int]): Maximum ascent in meters.

        Returns:
            List[Tour]: A list of tours matching the criteria.

        Example:
            db = TourenDB()
            # Add tours to the database...
            results = db.query_tours(public=True, min_dauer=2.0, schwierigkeit="rot", n_results=5, kinderfreundlich=True)
        """

        # Start with the full collection
        result: List[Tour] = self.touren
        random.shuffle(result)

        # ---- Simple field comparisons ---------------------------------
        if schwierigkeit is not None:
            result = [t for t in result if t.schwierigkeit == schwierigkeit]

        if public_transport is not None:
            result = [t for t in result if t.public_transport is public_transport]
        if einkehr is not None:
            result = [t for t in result if t.einkehr is einkehr]
        if kinderfreundlich is not None:
            result = [t for t in result if t.kinderfreundlich is kinderfreundlich]
        if hundefreundlich is not None:
            result = [t for t in result if t.hundefreundlich is hundefreundlich]
        if kinderwagen is not None:
            result = [t for t in result if t.kinderwagen is kinderwagen]
        if baden is not None:
            result = [t for t in result if t.baden is baden]

        # ---- Numeric ranges -------------------------------------------
        if min_dauer is not None:
            result = [t for t in result if t.dauer >= min_dauer]

        if max_dauer is not None:
            result = [t for t in result if t.dauer <= max_dauer]

        if min_hm_aufstieg is not None:
            result = [t for t in result if t.hm_aufstieg >= min_hm_aufstieg]

        if max_hm_aufstieg is not None:
            result = [t for t in result if t.hm_aufstieg <= max_hm_aufstieg]

        # ---- Limit number of results ----------------------------------
        if n_results is not None:
            result = result[:n_results]

        return result
