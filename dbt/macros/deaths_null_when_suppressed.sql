{% test deaths_null_when_suppressed(model, column_name, suppressed_column="suppressed") %}
{# Células com contagem < limiar devem ter deaths nulo (supressão LGPD). #}
select *
from {{ model }}
where coalesce({{ suppressed_column }}, false) = true
  and {{ column_name }} is not null
{% endtest %}
