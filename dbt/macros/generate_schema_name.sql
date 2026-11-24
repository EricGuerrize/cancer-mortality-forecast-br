{% macro generate_schema_name(custom_schema_name, node) -%}
  {#- Mantém schemas staging/intermediate/marts sem prefixar com target schema. -#}
  {%- if custom_schema_name is none -%}
    {{ target.schema }}
  {%- else -%}
    {{ custom_schema_name | trim }}
  {%- endif -%}
{%- endmacro %}
