from __future__ import annotations


MUNIC_WORKSHEET = "Gestao de riscos"

SOURCE_COLUMNS = {
    "codigo_ibge": "CodMun",
    "sigla_uf": "UF",
    "municipio_fonte": "Mun",
    "flood_planning_master_plan": "Mgrd171",
    "flood_planning_land_use_law": "Mgrd172",
    "flood_planning_specific_law": "Mgrd173",
    "landslide_planning_master_plan": "Mgrd174",
    "landslide_planning_land_use_law": "Mgrd175",
    "landslide_planning_specific_law": "Mgrd176",
    "flood_risk_mapping": "Mgrd181",
    "flood_contingency_plan": "Mgrd184",
    "flood_early_warning": "Mgrd186",
    "landslide_risk_mapping": "Mgrd201",
    "landslide_contingency_plan": "Mgrd204",
    "landslide_early_warning": "Mgrd206",
    "municipal_civil_defense_body": "Mgrd212",
    "municipal_civil_defense_unknown": "Mgrd216",
    "civil_defense_budget_provision": "Mgrd225",
    "civil_defense_early_warning": "Mgrd2213",
}

PLANNING_FIELDS = (
    "flood_planning_master_plan_status",
    "flood_planning_land_use_law_status",
    "flood_planning_specific_law_status",
    "landslide_planning_master_plan_status",
    "landslide_planning_land_use_law_status",
    "landslide_planning_specific_law_status",
)

OUTPUT_STATUS_FIELDS = (
    *PLANNING_FIELDS,
    "any_risk_prevention_planning_instrument_status",
    "flood_risk_mapping_status",
    "flood_contingency_plan_status",
    "flood_early_warning_status",
    "landslide_risk_mapping_status",
    "landslide_contingency_plan_status",
    "landslide_early_warning_status",
    "municipal_civil_defense_body_status",
    "civil_defense_budget_provision_status",
    "civil_defense_early_warning_status",
)

SOURCE_STATUSES = {
    "declared_yes",
    "declared_no",
    "refused",
    "not_reported",
    "not_applicable",
    "unknown",
}

GOLD_STATUSES = SOURCE_STATUSES | {"not_in_source"}
