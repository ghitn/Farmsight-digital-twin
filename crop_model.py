class WheatTwin:
    """
    Digital twin for a wheat plant, single-plant mode.
    - Growth driven by GDD with wheat-like thresholds
    - Height never shrinks once achieved (monotonic)
    - Moisture & nitrogen decay slowly over time
    - Health can move UP or DOWN based on combined moisture/nitrogen stress
      and how actions (irrigate/fertilize) change that stress.
    """

    def __init__(self):
        self.age_days = 0.0
        self.gdd = 0.0
        self.stage = "emergence"

        self.height = 3.0         # cm
        self.max_height_reached = 3.0

        self.leaf_count = 1
        self.tiller_count = 0
        self.head_count = 0

        self.health = 80.0         # 0–100
        self.soil_moisture = 35.0  # %
        self.nitrogen = 40.0       # 0–100 index

        self.last_stress = 0.0

    # ---------- GDD and stages ----------

    def _update_gdd(self, temperature_c, dt_days=1.0):
        """One update ≈ 1 day for smoother growth."""
        base_temp = 0.0
        t = max(0.0, temperature_c - base_temp)
        self.gdd += t * dt_days
        self.age_days += dt_days

    def _update_stage(self):
        g = self.gdd
        # your wheat-like thresholds
        if g < 180:
            self.stage = "emergence"
        elif g < 395:
            self.stage = "tillering"
        elif g < 1100:
            self.stage = "stem_elongation"
        elif g < 1400:
            self.stage = "booting"
        elif g < 1560:
            self.stage = "heading"
        elif g < 1740:
            self.stage = "flowering"
        elif g < 1800:
            self.stage = "grain_filling"
        else:
            self.stage = "maturity"

    # ---------- stress & health ----------

    def _compute_stress(self):
        """
        Returns (overall_stress, moisture_stress, nitrogen_stress) in [0,1].

        overall_stress = average of moisture & N stress so improving
        either one can help (what you want: irrigation might hurt,
        but fertilizing can still improve health).
        """
        ideal_moisture_low, ideal_moisture_high = 25.0, 45.0
        ideal_n_low, ideal_n_high = 30.0, 70.0

        # moisture stress
        if self.soil_moisture < ideal_moisture_low:
            moisture_stress = (ideal_moisture_low - self.soil_moisture) / 25.0
        elif self.soil_moisture > ideal_moisture_high:
            moisture_stress = (self.soil_moisture - ideal_moisture_high) / 25.0
        else:
            moisture_stress = 0.0

        # nitrogen stress
        if self.nitrogen < ideal_n_low:
            n_stress = (ideal_n_low - self.nitrogen) / 40.0
        elif self.nitrogen > ideal_n_high:
            n_stress = (self.nitrogen - ideal_n_high) / 40.0
        else:
            n_stress = 0.0

        moisture_stress = max(0.0, min(1.0, moisture_stress))
        n_stress = max(0.0, min(1.0, n_stress))

        # AVERAGE instead of max → fixing one dimension can help overall
        stress = (moisture_stress + n_stress) / 2.0
        return stress, moisture_stress, n_stress

    def _update_health(self):
        """
        Baseline drift each day based on overall stress.
        Health can clearly recover when stress is low.
        """
        stress, _, _ = self._compute_stress()
        self.last_stress = stress

        if stress <= 0.25:
            # Good conditions → recovery (up to about +0.9/day)
            delta = (0.25 - stress) * 3.6
        elif stress <= 0.6:
            # Moderate stress → slight decline or flat
            delta = -(stress - 0.25) * 0.8
        else:
            # High stress → faster decline
            delta = -(stress - 0.6) * 2.5 - 0.3

        self.health = max(0.0, min(100.0, self.health + delta))

    # ---------- structure / height ----------

    def _update_structure(self):
        vigor = 0.5 + 0.5 * (self.health / 100.0)      # 0.5–1.0
        resource_factor = 1.0 - 0.5 * self.last_stress # 0.5–1.0

        max_height = 100.0 * vigor * resource_factor
        max_leaves = int(15 * vigor)
        max_tillers = int(6 * resource_factor)
        max_heads = 6

        max_leaves = max(4, min(15, max_leaves))
        max_tillers = max(1, min(6, max_tillers))

        frac = min(1.0, self.gdd / 1800.0)  # overall progress 0–1

        # smooth height curve (no stage-min jumps)
        if self.stage in ("emergence", "tillering"):
            target_height = max_height * 0.18 * frac
        elif self.stage in ("stem_elongation", "booting"):
            target_height = max_height * (0.18 + 0.53 * frac)
        else:
            target_height = max_height * (0.71 + 0.29 * frac)
        target_height = max(3.0, target_height)

        # monotonic: never shrink
        self.height = max(self.height, target_height)
        self.max_height_reached = max(self.max_height_reached, self.height)

        # leaves
        if self.stage == "emergence":
            self.leaf_count = max(1, int(max_leaves * 0.2 * frac))
        elif self.stage == "tillering":
            self.leaf_count = int(max_leaves * 0.6 * frac)
        else:
            self.leaf_count = int(max_leaves * frac)
        self.leaf_count = max(2, min(max_leaves, self.leaf_count))

        # tillers
        if self.stage in ("tillering", "stem_elongation"):
            self.tiller_count = int(max_tillers * frac)
        else:
            self.tiller_count = max_tillers

        # heads
        if self.stage in ("heading", "flowering", "grain_filling", "maturity"):
            self.head_count = max(1, int(max_heads * frac))
        else:
            self.head_count = 0

    # ---------- public API ----------

    def update(self, weather, dt_days=1.0):
        temp = weather.get("temperature", 18.0)

        self._update_gdd(temp, dt_days)
        self._update_stage()
        self._update_health()
        self._update_structure()

        # slow resource decay so you need occasional actions
        self.soil_moisture -= 0.25 * dt_days
        self.nitrogen      -= 0.1 * dt_days

        self.soil_moisture = max(5.0, min(70.0, self.soil_moisture))
        self.nitrogen      = max(0.0, min(100.0, self.nitrogen))

    def process_action(self, action):
        """
        Compare overall stress BEFORE vs AFTER action.
        If stress drops → health reward; if it increases → penalty.
        So a good fertilization after over-irrigation can still
        bring health back up (stress average improves).
        """
        stress_before, _, _ = self._compute_stress()

        if action == "irrigate":
            self.soil_moisture += 10.0
        elif action == "fertilize":
            self.nitrogen += 10.0

        self.soil_moisture = max(5.0, min(70.0, self.soil_moisture))
        self.nitrogen      = max(0.0, min(100.0, self.nitrogen))

        stress_after, _, _ = self._compute_stress()

        change = stress_before - stress_after  # >0 = improvement
        if change > 0:
            self.health += 15.0 * change   # reward
        elif change < 0:
            self.health += 10.0 * change   # penalty (change is negative)

        self.health = max(0.0, min(100.0, self.health))


# global singleton for app.py
twin = WheatTwin()
