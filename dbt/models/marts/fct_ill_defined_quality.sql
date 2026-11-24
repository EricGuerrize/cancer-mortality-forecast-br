{#
  Indicador de qualidade: participação de causas mal definidas (R00–R99)
  frente ao total de óbitos por câncer na mesma célula demográfica.
#}
with ill as (
    select * from {{ ref('stg_sim_ill_defined') }}
    where sexo in ('M', 'F')
      and age_group <> 'ignorado'
),

cancer as (
    select
        year,
        uf,
        sexo,
        age_group,
        sum(deaths) as deaths_cancer
    from {{ ref('stg_sim_cancer_deaths') }}
    where not suppressed
      and deaths is not null
      and sexo in ('M', 'F')
      and age_group <> 'ignorado'
    group by 1, 2, 3, 4
),

joined as (
    select
        coalesce(i.year, c.year) as year,
        coalesce(i.uf, c.uf) as uf,
        coalesce(i.sexo, c.sexo) as sexo,
        coalesce(i.age_group, c.age_group) as age_group,
        coalesce(i.deaths_ill_defined, 0) as deaths_ill_defined,
        coalesce(c.deaths_cancer, 0) as deaths_cancer,
        case
            when coalesce(c.deaths_cancer, 0) + coalesce(i.deaths_ill_defined, 0) > 0
                then coalesce(i.deaths_ill_defined, 0)::double
                    / (coalesce(c.deaths_cancer, 0) + coalesce(i.deaths_ill_defined, 0))
            else null
        end as ill_defined_share
    from ill i
    full outer join cancer c
        on i.year = c.year
        and i.uf = c.uf
        and i.sexo = c.sexo
        and i.age_group = c.age_group
)

select * from joined
