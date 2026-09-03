from src.extract.mapbiomas import (
    FetchedPage,
    discover_mapbiomas_sources,
)


STATISTICS_URL = "https://drive.google.com/uc?id=official&export=download"
LEGEND_URL = "https://brasil.mapbiomas.org/legend_collection_11.csv"


def page(url: str, html: str) -> FetchedPage:
    return FetchedPage(
        url=url,
        body=html.encode("utf-8"),
        content_type="text/html; charset=utf-8",
        sha256="fixture",
    )


def test_discovery_requires_consistent_official_pages() -> None:
    coverage = page(
        "https://official.test/coverage",
        f"""
        <p>A coleção mais recente deste produto é a <strong>Coleção 11</strong>,
        com série histórica de 1985 a 2025.</p>
        <table><tr>
          <td>MAPBIOMAS_BRAZIL-COL.11-BIOME_STATE_MUNICIPALITY</td>
          <td>Biomas, estados e municípios brasileiros</td>
          <td>Tabela em hectares</td>
          <td>v1 - Publicada em 12 de agosto de 2026</td>
        </tr></table>
        <a href="{STATISTICS_URL}">
          MAPBIOMAS_BRAZIL-COL.11-BIOME_STATE_MUNICIPALITY
        </a>
        projects/mapbiomas-public/assets/brazil/lulc/collection11/coverage_v3
        """,
    )
    statistics = page(
        "https://official.test/statistics",
        f"""
        <table><tr data-colecao="Coleção 11" data-iniciativa="Cobertura 30m">
          <td>Biomas, Estados e Municípios | Cobertura 30m - Coleção 11</td>
          <td><a title="Baixar" href="{STATISTICS_URL}">download</a></td>
        </tr></table>
        """,
    )
    legend = page(
        "https://official.test/legend",
        f"""
        <table><tr data-colecao="Coleção 11">
          <td>Cobertura - Códigos de Legenda para uso no R ou Python |
              MapBiomas Brasil (30m) - Coleção 11</td>
          <td><a title="Baixar" href="{LEGEND_URL}">download</a></td>
        </tr></table>
        """,
    )
    urbanization = page(
        "https://official.test/urban",
        "<p>A classe correspondente às áreas urbanizadas é a de id ‘24’.</p>",
    )

    result = discover_mapbiomas_sources(
        coverage_page=coverage,
        statistics_page=statistics,
        legend_page=legend,
        urbanization_page=urbanization,
    )

    assert result.collection_id == "11"
    assert result.collection_version == "v1"
    assert result.first_year == 1985
    assert result.latest_year == 2025
    assert result.source_publication_date == "2026-08-12"
    assert result.statistics_url == STATISTICS_URL
    assert result.legend_url == LEGEND_URL
    assert result.urban_class_id == 24


def test_discovery_fails_when_current_collection_is_ambiguous() -> None:
    ambiguous = page(
        "https://official.test/coverage",
        """
        A coleção mais recente deste produto é a Coleção 11,
        série histórica de 1985 a 2025.
        A coleção mais recente deste produto é a Coleção 12,
        série histórica de 1985 a 2026.
        """,
    )

    try:
        discover_mapbiomas_sources(
            coverage_page=ambiguous,
            statistics_page=page("stats", ""),
            legend_page=page("legend", ""),
            urbanization_page=page("urban", ""),
        )
    except RuntimeError as error:
        assert "sem confianca" in str(error)
    else:
        raise AssertionError("A descoberta ambigua deveria falhar")
