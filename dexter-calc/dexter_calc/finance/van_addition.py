class VANChatCalculator(DomainCalculator):
    domain: str = "finance"
    sous_theme: str | None = "van"
    intention: str | None = "calcul"
    label: str = "Calcul VAN / ICA"
    unit: str | None = "€"

    def calc(self, input_: CalculationInput) -> CalculationOutput:
        if input_.base_amount is None or not input_.flows:
            raise CalculationError("Flux initial et liste requis.", code="missing_flows")
        taux = self._resolve_taux(input_)
        flux_initial = valider_montant(input_.base_amount)
        flows = list(input_.flows)
        van = calculer_van_flux(flux_initial, flows, taux)
        ica = round(van / flux_initial, 4) if flux_initial != 0 else 0.0
        return CalculationOutput(
            domain=self.domain,
            sous_theme=self.sous_theme,
            intention=input_.intention or self.intention,
            result=van,
            label="VAN",
            unit=self.unit,
            pedagogical_note="VAN=" + str(van) + ", ICA=" + str(ica) + ".",
            extra={"flux_initial": flux_initial, "flows": flows, "van": van, "ica": ica},
        )

    def derive(self, input_: CalculationInput) -> CalculationOutput:
        if input_.base_amount is None or not input_.flows:
            raise CalculationError("Flux initial et liste requis.", code="missing_flows")
        taux = self._resolve_taux(input_)
        flux_initial = valider_montant(input_.base_amount)
        flows = list(input_.flows)
        ica = round(calculer_van_flux(flux_initial, flows, taux) / flux_initial, 4) if flux_initial != 0 else 0.0
        return CalculationOutput(domain=self.domain, sous_theme=self.sous_theme, result=ica, label="ICA")

    def description(self) -> str:
        return "Outil de calcul VAN/ICA."

    def can_handle(self, input_: CalculationInput) -> bool:
        return input_.domain == "finance" and bool(input_.flows) and input_.base_amount is not None

    def _resolve_taux(self, input_: CalculationInput) -> float:
        taux = input_.discount_rate or input_.tau or input_.rate or input_.rate_fraction
        if taux is None:
            raise CalculationError("Taux requis.", code="missing_rate")
        return valider_taux(taux)

def register_on(registry):
    if hasattr(registry, "register"):
        registry.register(VANChatCalculator)
