with deaths as (
    select * from {{ ref('stg_sim_cancer_deaths') }}
),

labels as (
    select * from {{ ref('cancer_group_labels') }}
),

joined as (
    select
        d.year,
        d.uf,
        d.sexo,
        d.age_group,
        d.cancer_group,
        l.label_pt as cancer_group_label,
        l.cid_start,
        l.cid_end,
        d.deaths,
        d.suppressed
    from deaths d
    inner join labels l
        on d.cancer_group = l.cancer_group
)

select * from joined
