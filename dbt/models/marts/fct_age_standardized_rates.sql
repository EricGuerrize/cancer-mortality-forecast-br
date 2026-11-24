{#
  Taxa de mortalidade padronizada por idade (método direto, população-padrão OMS).
  ASR = Σ (taxa_i × w_i) / Σ w_i × 100000, por year × uf × sexo × cancer_group.
#}
with age_rates as (
    select * from {{ ref('int_deaths_with_population') }}
),

who as (
    select
        age_group,
        standard_population
    from {{ ref('who_world_standard_population') }}
),

weighted as (
    select
        a.year,
        a.uf,
        a.sexo,
        a.cancer_group,
        a.cancer_group_label,
        a.age_group,
        a.deaths,
        a.population,
        a.crude_rate_per_100k,
        w.standard_population,
        a.crude_rate_per_100k * w.standard_population as weighted_rate
    from age_rates a
    inner join who w
        on a.age_group = w.age_group
),

asr as (
    select
        year,
        uf,
        sexo,
        cancer_group,
        cancer_group_label,
        sum(deaths) as deaths,
        sum(population) as population,
        count(*) as age_bands_used,
        sum(weighted_rate) / nullif(sum(standard_population), 0) as asr_per_100k
    from weighted
    group by 1, 2, 3, 4, 5
)

select * from asr
