with source as (
    select * from {{ source('sample', 'cancer_deaths_agg') }}
),

renamed as (
    select
        cast(year as integer) as year,
        upper(trim(cast(uf as varchar))) as uf,
        upper(trim(cast(sexo as varchar))) as sexo,
        cast(age_group as varchar) as age_group,
        cast(cancer_group as varchar) as cancer_group,
        cast(deaths as double) as deaths,
        coalesce(cast(suppressed as boolean), false) as suppressed
    from source
)

select * from renamed
