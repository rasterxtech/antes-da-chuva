from src.extract.atlas import FetchedPage, discover_atlas_source


def page(html: str) -> FetchedPage:
    return FetchedPage(
        url="https://official.test/paginas/downloads.xhtml",
        body=html.encode("utf-8"),
        content_type="text/html; charset=utf-8",
        sha256="fixture",
    )


def test_atlas_discovery_resolves_all_resources_and_release(monkeypatch) -> None:
    for name in ("ATLAS_CSV_URL", "ATLAS_XLSX_URL", "ATLAS_MANUAL_URL", "ATLAS_LOG_URL"):
        monkeypatch.delenv(name, raising=False)
    source = discover_atlas_source(
        page(
            """
            <a href="/arquivos/2026/BD_Atlas_1991_2025_v1.1_2026.08.06_Consolidado.xlsx">Excel</a>
            <a href="/arquivos/2026/BD_Atlas_1991_2025_v1.1_2026.08.06_Consolidado.csv">CSV</a>
            <a href="/arquivos/Atlas_Digital_Desastres_Manual_Aplicacao.pdf">PDF</a>
            <a href="/arquivos/2026/2026.08-logs-correcoes.xlsx">Logs</a>
            """
        )
    )

    assert source.source_release == "atlas_1991_2025_v1.1_2026-08-06"
    assert source.first_year == 1991
    assert source.latest_year == 2025
    assert source.source_official_date == "2026-08-06"
    assert source.discovery_mode == "automatic"
    assert set(source.discovered_urls) == {"csv", "xlsx", "manual", "correction_log"}


def test_atlas_discovery_fails_on_ambiguous_csv(monkeypatch) -> None:
    for name in ("ATLAS_CSV_URL", "ATLAS_XLSX_URL", "ATLAS_MANUAL_URL", "ATLAS_LOG_URL"):
        monkeypatch.delenv(name, raising=False)
    ambiguous = page(
        """
        <a href="/BD_Atlas_1991_2025_v1.1_2026.08.06_Consolidado.xlsx">Excel</a>
        <a href="/BD_Atlas_1991_2025_v1.1_2026.08.06_Consolidado.csv">CSV 1</a>
        <a href="/BD_Atlas_1991_2025_v1.2_2026.09.01_Consolidado.csv">CSV 2</a>
        <a href="/manual.pdf">PDF</a>
        <a href="/logs-correcoes.xlsx">Logs</a>
        """
    )

    try:
        discover_atlas_source(ambiguous)
    except RuntimeError as error:
        assert "sem confianca" in str(error)
    else:
        raise AssertionError("A descoberta ambigua deveria falhar")
