{#
  Une óbitos (não suprimidos) à população por faixa etária.
  Sexo I (ignorado) fica sem população IBGE e é excluído das taxas.
#}
with deaths as (
    select * from {{ ref('int_cancer_deaths_labeled') }}
    where not suppressed
      and deaths is not null
      and age_group <> 'ignorado'
      and sexo in ('M', 'F')
),

population as (
    select * from {{ ref('int_population_age_group') }}
),

joined as (
    select
        d.year,
        d.uf,
        d.sexo,
        d.age_group,
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
        and d.age_group = p.age_group
)

select * from joined
