{# Taxas brutas e ASR nunca devem ser negativas. #}
select
    year,
    uf,
    sexo,
    cancer_group,
    crude_rate_per_100k
from {{ ref('fct_crude_mortality_rates') }}
where crude_rate_per_100k < 0

union all

select
    year,
    uf,
    sexo,
    cancer_group,
    asr_per_100k as crude_rate_per_100k
from {{ ref('fct_age_standardized_rates') }}
where asr_per_100k < 0
