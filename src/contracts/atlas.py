from __future__ import annotations


required_fields = (
    "Protocolo_S2iD",
    "Nome_Municipio",
    "Sigla_UF",
    "regiao",
    "Data_Registro",
    "Data_Evento",
    "Cod_Cobrade",
    "tipologia",
    "descricao_tipologia",
    "grupo_de_desastre",
    "Cod_IBGE_Mun",
    "Setores Censitários",
    "Status",
    "DH_Descricao",
    "DH_MORTOS",
    "DH_FERIDOS",
    "DH_ENFERMOS",
    "DH_DESABRIGADOS",
    "DH_DESALOJADOS",
    "DH_DESAPARECIDOS",
    "DH_AFETADOS_SECA_ESTIAGEM",
    "DH_total_danos_humanos_diretos",
    "DH_OUTROS AFETADOS",
    "DM_Descricao",
    "DM_Uni Habita Danificadas",
    "DM_Uni Habita Destruidas",
    "DM_Uni Habita Valor",
    "DM_Inst Saúde Danificadas",
    "DM_Inst Saúde Destruidas",
    "DM_Inst Saúde Valor",
    "DM_Inst Ensino Danificadas",
    "DM_Inst Ensino Destruidas",
    "DM_Inst Ensino Valor",
    "DM_Inst Serviços Danificadas",
    "DM_Inst Serviços Destruidas",
    "DM_Inst Serviços Valor",
    "DM_Inst Comuni Danificadas",
    "DM_Inst Comuni Destruidas",
    "DM_Inst Comuni Valor",
    "DM_Obras de Infra Danificadas",
    "DM_Obras de Infra Destruidas",
    "DM_Obras de Infra Valor",
    "DM_total_danos_materiais",
    "DA_Descricao",
    "DA_Polui/cont da água",
    "DA_Polui/cont do ar",
    "DA_Polui/cont do solo",
    "DA_Dimi/exauri hídrico",
    "DA_Incêndi parques/APA's/APP's",
    "PEPL_Descricao",
    "PEPL_Assis_méd e emergên(R$)",
    "PEPL_Abast de água pot(R$)",
    "PEPL_sist de esgotos sanit(R$)",
    "PEPL_Sis limp e rec lixo (R$)",
    "PEPL_Sis cont pragas (R$)",
    "PEPL_distrib energia (R$)",
    "PEPL_Telecomunicações (R$)",
    "PEPL_Tran loc/reg/l_curso (R$)",
    "PEPL_Distrib combustíveis(R$)",
    "PEPL_Segurança pública (R$)",
    "PEPL_Ensino (R$)",
    "PEPL_total_publico",
    "PEPR_Descricao",
    "PEPR_Agricultura (R$)",
    "PEPR_Pecuária (R$)",
    "PEPR_Indústria (R$)",
    "PEPR_Comércio (R$)",
    "PEPR_Serviços (R$)",
    "PEPR_total_privado",
    "PE_PLePR",
)

optional_fields: tuple[str, ...] = ()

known_variants = {
    "encoding": ("CP1252",),
    "delimiter": (";",),
    "status": ("Registro", "Reconhecido"),
    "corrected_values_sheet": ("Atlas Valores Corrigidos",),
    "original_values_sheet": ("Atlas Valores Originais",),
    "correction_sheet": ("Cálculo Correção",),
    "disaster_groups_sheet": ("Grupos de Desastres",),
}

unexpected_fields: tuple[str, ...] = ()


COUNT_FIELDS = (
    "DH_MORTOS",
    "DH_FERIDOS",
    "DH_ENFERMOS",
    "DH_DESABRIGADOS",
    "DH_DESALOJADOS",
    "DH_DESAPARECIDOS",
    "DH_AFETADOS_SECA_ESTIAGEM",
    "DH_total_danos_humanos_diretos",
    "DH_OUTROS AFETADOS",
    "DM_Uni Habita Danificadas",
    "DM_Uni Habita Destruidas",
    "DM_Inst Saúde Danificadas",
    "DM_Inst Saúde Destruidas",
    "DM_Inst Ensino Danificadas",
    "DM_Inst Ensino Destruidas",
    "DM_Inst Serviços Danificadas",
    "DM_Inst Serviços Destruidas",
    "DM_Inst Comuni Danificadas",
    "DM_Inst Comuni Destruidas",
    "DM_Obras de Infra Danificadas",
    "DM_Obras de Infra Destruidas",
)

MONETARY_FIELDS = (
    "DM_Uni Habita Valor",
    "DM_Inst Saúde Valor",
    "DM_Inst Ensino Valor",
    "DM_Inst Serviços Valor",
    "DM_Inst Comuni Valor",
    "DM_Obras de Infra Valor",
    "DM_total_danos_materiais",
    "PEPL_Assis_méd e emergên(R$)",
    "PEPL_Abast de água pot(R$)",
    "PEPL_sist de esgotos sanit(R$)",
    "PEPL_Sis limp e rec lixo (R$)",
    "PEPL_Sis cont pragas (R$)",
    "PEPL_distrib energia (R$)",
    "PEPL_Telecomunicações (R$)",
    "PEPL_Tran loc/reg/l_curso (R$)",
    "PEPL_Distrib combustíveis(R$)",
    "PEPL_Segurança pública (R$)",
    "PEPL_Ensino (R$)",
    "PEPL_total_publico",
    "PEPR_Agricultura (R$)",
    "PEPR_Pecuária (R$)",
    "PEPR_Indústria (R$)",
    "PEPR_Comércio (R$)",
    "PEPR_Serviços (R$)",
    "PEPR_total_privado",
    "PE_PLePR",
)


def validate_fields(observed: tuple[str, ...]) -> None:
    if observed == required_fields:
        return
    missing = sorted(set(required_fields) - set(observed))
    unexpected = sorted(set(observed) - set(required_fields))
    raise RuntimeError(
        "Schema Atlas mudou: "
        f"ordem_igual={observed == required_fields}, "
        f"ausentes={missing}, inesperadas={unexpected}"
    )
