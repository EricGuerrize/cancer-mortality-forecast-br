"""CLI Typer: ingest-sim, ingest-ibge, demo, make-sample."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.logging import RichHandler

from ingestion import __version__
from ingestion.config import get_settings
from ingestion.demo import run_demo

app = typer.Typer(
    name="cancer-mortality",
    help="Ingestão DATASUS/IBGE e demo offline — mortalidade por câncer (Brasil).",
    add_completion=False,
)
console = Console()


def _setup_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(rich_tracebacks=True, console=console)],
    )


@app.callback()
def main(
    verbose: Annotated[bool, typer.Option("--verbose", "-v")] = False,
) -> None:
    """Pipeline de mortalidade por câncer — Brasil."""
    _setup_logging(verbose)


@app.command("version")
def version_cmd() -> None:
    """Mostra a versão do pacote."""
    console.print(__version__)


@app.command("ingest-sim")
def ingest_sim_cmd(
    years: Annotated[
        str,
        typer.Option(help="Ano único, lista (2018,2019) ou intervalo (2018-2022)"),
    ] = "2018-2022",
    ufs: Annotated[
        str | None,
        typer.Option(help="UFs separadas por vírgula (default: todas)"),
    ] = None,
    output: Annotated[
        Path | None,
        typer.Option(help="Diretório de saída (default: data/raw)"),
    ] = None,
) -> None:
    """Baixa e processa óbitos SIM (requer extras [sim] / PySUS)."""
    from ingestion.sim import ingest_sim

    settings = get_settings()
    year_list = _parse_years(years)
    uf_list = [u.strip().upper() for u in ufs.split(",")] if ufs else settings.parsed_ufs()
    out = output or settings.raw
    console.print(f"[bold]SIM[/] anos={year_list} ufs={uf_list or 'ALL'} → {out}")
    result = ingest_sim(years=year_list, ufs=uf_list, output_dir=out)
    console.print(result)
    if result["failures"]:
        raise typer.Exit(code=1)


@app.command("ingest-ibge")
def ingest_ibge_cmd(
    output: Annotated[
        Path | None,
        typer.Option(help="Diretório de saída (default: data/raw)"),
    ] = None,
    url: Annotated[
        str | None,
        typer.Option(help="URL do XLSX IBGE (revisão 2024)"),
    ] = None,
) -> None:
    """Baixa projeções populacionais IBGE 2000–2070 (revisão 2024)."""
    from ingestion.ibge import ingest_ibge

    settings = get_settings()
    out = output or settings.raw
    console.print(f"[bold]IBGE[/] → {out}")
    result = ingest_ibge(output_dir=out, url=url)
    console.print(
        {
            "rows": result["rows"],
            "years": f"{result['years'][0]}..{result['years'][-1]}",
            "n_ufs": len(result["ufs"]),
            "parquet": result["parquet"],
        }
    )


@app.command("demo")
def demo_cmd(
    sample_dir: Annotated[
        Path | None,
        typer.Option(help="Diretório com amostras (default: data/sample)"),
    ] = None,
) -> None:
    """Roda a demo offline a partir de data/sample/ (sem rede)."""
    summary = run_demo(sample_dir=sample_dir)
    console.print("[green]Demo concluída com sucesso.[/]")
    console.print(summary)


@app.command("make-sample")
def make_sample_cmd(
    output: Annotated[
        Path | None,
        typer.Option(help="Destino (default: data/sample)"),
    ] = None,
    seed: Annotated[int, typer.Option(help="Semente reprodutível")] = 42,
) -> None:
    """Gera amostra sintética (offline). Preferir make-sample-real para dados públicos reais."""
    from ingestion.sample_data import write_sample_bundle

    settings = get_settings()
    out = output or settings.sample
    paths = write_sample_bundle(out, seed=seed)
    console.print("[green]Amostra sintética gerada:[/]", paths)


@app.command("make-sample-real")
def make_sample_real_cmd(
    years: Annotated[str, typer.Option(help="Anos SIM (ex.: 2020-2022)")] = "2020-2022",
    ufs: Annotated[str, typer.Option(help="UFs separadas por vírgula")] = "AC,SP,RJ",
    output: Annotated[
        Path | None,
        typer.Option(help="Destino (default: data/sample)"),
    ] = None,
) -> None:
    """Baixa SIM+IBGE e grava agregados reais (células < 5 suprimidas) em data/sample/."""
    from ingestion.sample_data import write_real_sample_bundle

    settings = get_settings()
    out = output or settings.sample
    year_list = _parse_years(years)
    uf_list = [u.strip().upper() for u in ufs.split(",") if u.strip()]
    console.print(f"[bold]Amostra real[/] anos={year_list} ufs={uf_list} → {out}")
    paths = write_real_sample_bundle(out, years=year_list, ufs=uf_list)
    console.print("[green]Amostra real gerada:[/]", paths)


def _parse_years(spec: str) -> list[int]:
    spec = spec.strip()
    if "-" in spec and "," not in spec:
        start_s, end_s = spec.split("-", 1)
        start, end = int(start_s), int(end_s)
        if end < start:
            raise typer.BadParameter("Intervalo de anos inválido")
        return list(range(start, end + 1))
    return [int(x.strip()) for x in spec.split(",") if x.strip()]


if __name__ == "__main__":
    app()
