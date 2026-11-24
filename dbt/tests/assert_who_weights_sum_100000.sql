{#
  Teste singular customizado: a população-padrão OMS deve somar 100_000
  (escala clássica por 100 mil).
#}
select
    sum(standard_population) as total_weight
from {{ ref('who_world_standard_population') }}
having sum(standard_population) <> 100000
