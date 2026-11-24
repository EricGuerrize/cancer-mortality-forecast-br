{# Agrega idade simples IBGE nas faixas quinquenais usadas pelo SIM/OMS. #}
with pop as (
    select * from {{ ref('stg_ibge_population') }}
),

banded as (
    select
        year,
        uf,
        sexo,
        case
            when age >= 85 then '85+'
            else
                lpad(cast((age // 5) * 5 as varchar), 2, '0')
                || '-'
                || lpad(cast((age // 5) * 5 + 4 as varchar), 2, '0')
        end as age_group,
        population
    from pop
),

aggregated as (
    select
        year,
        uf,
        sexo,
        age_group,
        sum(population) as population
    from banded
    group by 1, 2, 3, 4
)

select * from aggregated
