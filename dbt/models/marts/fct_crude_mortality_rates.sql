{#
  Taxa bruta de mortalidade por câncer (por 100 mil),
  agregada em year × uf × sexo × cancer_group.
  Denominador = população total da UF/sexo/ano (todas as faixas etárias).
#}
with deaths as (
    select
        year,
        uf,
        sexo,
        cancer_group,
        cancer_group_label,
        sum(deaths) as deaths
    from {{ ref('int_deaths_with_population') }}
    group by 1, 2, 3, 4, 5
),

population as (
    select
        year,
        uf,
        sexo,
        sum(population) as population
    from {{ ref('int_population_age_group') }}
    group by 1, 2, 3
),

joined as (
    select
        d.year,
        d.uf,
        d.sexo,
        d.cancer_group,
        d.cancer_group_label,
        d.deaths,
        p.population,
        case
            when p.population > 0
                then (d.deaths::double / p.population) * {{ var('rate_scale') }}
            else null
        end as crude_rate_per_100k
    from deaths d
    inner join population p
        on d.year = p.year
        and d.uf = p.uf
        and d.sexo = p.sexo
)

select * from joined
