with source as (
    select * from {{ source('sample', 'ibge_population_sample') }}
),

renamed as (
    select
        cast(year as integer) as year,
        upper(trim(cast(uf as varchar))) as uf,
        upper(trim(cast(sexo as varchar))) as sexo,
        cast(age as integer) as age,
        cast(population as bigint) as population
    from source
    where population >= 0
)

select * from renamed
