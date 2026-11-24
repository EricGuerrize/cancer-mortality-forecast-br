with source as (
    select * from {{ source('sample', 'ill_defined_counts') }}
),

renamed as (
    select
        cast(year as integer) as year,
        upper(trim(cast(uf as varchar))) as uf,
        upper(trim(cast(sexo as varchar))) as sexo,
        cast(age_group as varchar) as age_group,
        cast(deaths_ill_defined as bigint) as deaths_ill_defined
    from source
)

select * from renamed
